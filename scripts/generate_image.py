#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用图像生成入口 — 基于 Provider 架构
支持 wan2.7-image（阿里云百炼）和 cogview-3-flash（智谱 AI）

使用方法:
    python3 generate_image.py "提示词" [--model wan|cogview|auto] [--ref_image PATH] [--size SIZE] [--output PATH] [--n N]

环境变量（在 ~/.hermes/.env 中配置）:
    BAILIAN_API_KEY: 阿里云百炼 API Key（wan2.7-image 需要）
    ZHIPU_API_KEY: 智谱 AI API Key（cogview-flash 需要）

扩展新模型:
    1. 在 providers/ 下新增 provider 文件，继承 ImageProvider
    2. 在 providers/__init__.py 的 PROVIDERS 字典中注册
    3. 无需修改本脚本
"""

import sys
import os

# 把 providers 目录加入 import 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
from providers import get_provider, select_provider


def main():
    parser = argparse.ArgumentParser(
        description="通用图像生成编辑器 - 支持多模型 API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 文生图（默认 cogview 免费模型）
    python3 generate_image.py "一位优雅的东方女性，身穿汉服"

    # 指定模型
    python3 generate_image.py "提示词" --model wan
    python3 generate_image.py "提示词" --model cogview

    # 图生图（自动切换到 wan）
    python3 generate_image.py "海边散步" --ref_image /path/to/image.jpg

    # 指定分辨率
    python3 generate_image.py "咖啡厅" --size 1024x1024

    # 生成多张
    python3 generate_image.py "提示词" --n 3
        """
    )

    parser.add_argument("prompt", type=str, help="图片描述提示词")
    parser.add_argument("--model", type=str, default="auto",
                       choices=["wan", "cogview", "auto"],
                       help="模型选择（默认：auto，优先免费）")
    parser.add_argument("--ref_image", type=str, default=None,
                       help="参考图路径（图生图需要，自动切换到 wan）")
    parser.add_argument("--size", type=str, default=None,
                       help="分辨率（不指定则用模型默认）")
    parser.add_argument("--output", type=str, default=None,
                       help="输出文件路径")
    parser.add_argument("--n", type=int, default=1,
                       help="生成数量（默认：1）")

    args = parser.parse_args()

    # 自动选择模型
    if args.model == "auto":
        need_img2img = args.ref_image is not None
        model_name = select_provider(
            require_txt2img=True,
            require_img2img=need_img2img,
            prefer_free=not need_img2img
        )
        if need_img2img and model_name != "wan":
            print(f"⚠️  图生图仅 WAN 支持，自动切换到 wan...")
            model_name = "wan"
        print(f"🤖 自动选择模型：{model_name}")
    else:
        model_name = args.model

    # 实例化 provider
    provider = get_provider(model_name)

    # 能力检查
    if args.ref_image and not provider.supports("img2img"):
        print(f"⚠️  {provider.display_name} 不支持图生图，尝试自动切换...")
        model_name = select_provider(require_img2img=True)
        provider = get_provider(model_name)
        print(f"🤖 已切换到：{provider.display_name}")

    # 执行生成
    print(f"🎨 使用 {provider.display_name} 生成图片...")
    print(f"提示词：{args.prompt}")
    if args.size:
        print(f"分辨率：{args.size}")
    if args.ref_image:
        print(f"参考图：{args.ref_image}")

    result = provider.generate(
        prompt=args.prompt,
        size=args.size,
        output_path=args.output,
        n=args.n,
        ref_image=args.ref_image,
    )

    # 打印结果
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ 生成成功！")
        print(f"🎨 模型：{result.get('model', 'unknown')}")
        print(f"⏱️  耗时：{result['time']:.2f}秒")
        print(f"📊 数量：{result.get('count', 1)}张")
        for i, img in enumerate(result.get("images", [])):
            print(f"📁 图片 {i+1}: {img['path']}")
    else:
        print("❌ 生成失败！")
        print(f"❌ 模型：{result.get('model', 'unknown')}")
        print(f"❌ 错误：{result['error']}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
