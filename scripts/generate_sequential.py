#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
序列图像生成入口 — 基于 Provider 架构
使用支持 sequential 能力的 provider 生成组图，适合绘本、故事板等场景

使用方法:
    python3 generate_sequential.py "提示词" [--model MODEL] [--count N] [--size SIZE] [--ref_image PATH] [--output_dir DIR]

环境变量（在 ~/.hermes/.env 中配置）:
    BAILIAN_API_KEY: 阿里云百炼 API Key

扩展新模型:
    1. 在 providers/ 下新增 provider，实现 generate_sequential 方法
    2. 在 providers/__init__.py 中注册
    3. 无需修改本脚本
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
from providers import get_provider, select_provider


def main():
    parser = argparse.ArgumentParser(
        description="序列图像生成器 - 组图/绘本模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成 12 张序列图像
    python3 generate_sequential.py "一个穿红裙的小女孩在花园里追逐蝴蝶" --count 12

    # 指定模型和分辨率
    python3 generate_sequential.py "星空下的海边小镇" --model wan --size 1920*1080 --count 8

    # 带参考图（保持角色一致性）
    python3 generate_sequential.py "在图书馆看书" --ref_image /path/to/character.png --count 10
        """
    )

    parser.add_argument("prompt", type=str, help="图片描述提示词")
    parser.add_argument("--count", type=int, default=12,
                       help="生成总数量（1-100，默认 12）")
    parser.add_argument("--model", type=str, default="auto",
                       choices=["wan", "cogview", "auto"],
                       help="模型选择（默认：auto，优先选择支持组图的模型）")
    parser.add_argument("--size", type=str, default=None,
                       help="分辨率（不指定则用模型默认）")
    parser.add_argument("--ref_image", type=str, default=None,
                       help="参考图路径（可选，用于保持角色一致性）")
    parser.add_argument("--output_dir", type=str, default=None,
                       help="输出目录（默认：~/.hermes/images/sequential/系列_时间戳/）")

    args = parser.parse_args()

    if args.count < 1 or args.count > 100:
        print(f"❌ 数量必须在 1-100 之间，当前：{args.count}")
        return 1

    # 自动选择模型
    if args.model == "auto":
        model_name = select_provider(
            require_txt2img=True,
            require_sequential=True
        )
        print(f"🤖 自动选择模型：{model_name}")
    else:
        model_name = args.model

    # 实例化 provider
    provider = get_provider(model_name)

    # 组图能力检查
    if not provider.supports("sequential"):
        print(f"❌ {provider.display_name} 不支持组图模式")
        # 尝试自动切换
        try:
            model_name = select_provider(require_sequential=True)
            provider = get_provider(model_name)
            print(f"🤖 自动切换到：{provider.display_name}")
        except ValueError as e:
            print(f"❌ 无法自动切换：{e}")
            return 1

    # 构建输出目录
    output_dir = args.output_dir
    if not output_dir:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.expanduser(f"~/.hermes/images/sequential/series_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"📖 序列图像生成任务")
    print(f"{'='*60}")
    print(f"🎨 模型：{provider.display_name}")
    print(f"📁 输出目录：{output_dir}")
    if args.size:
        print(f"📐 分辨率：{args.size}")
    print(f"📊 数量：{args.count} 张")
    print(f"{'='*60}\n")

    # 执行组图生成
    result = provider.generate_sequential(
        prompt=args.prompt,
        count=args.count,
        size=args.size,
        ref_image=args.ref_image,
        output_dir=output_dir,
    )

    # 打印结果
    print(f"\n{'='*60}")
    if result["success"]:
        print("✅ 全部完成！")
        print(f"🎨 模型：{result.get('model', 'unknown')}")
        print(f"⏱️  总耗时：{result['time']:.1f} 秒")
        print(f"📊 总数量：{result.get('count', 0)} 张")
        print(f"📁 输出目录：{output_dir}")
    else:
        print("❌ 生成失败！")
        print(f"❌ 错误：{result['error']}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
