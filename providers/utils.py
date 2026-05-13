#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provider 公共工具函数
"""

import os
import base64
import requests
from datetime import datetime

HERMES_ENV = os.path.expanduser("~/.hermes/.env")
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/.hermes/images")


def get_api_key(env_key: str) -> str:
    """从 ~/.hermes/.env 或环境变量读取 API Key"""
    for env_path in [HERMES_ENV]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == env_key:
                                api_key = v.strip()
                                if api_key:
                                    return api_key
            except Exception:
                pass

    api_key = os.getenv(env_key)
    if not api_key:
        raise ValueError(f"未找到 {env_key}，请先在 ~/.hermes/.env 中配置")
    return api_key


def image_to_base64(image_path: str) -> str:
    """将本地图片转换为 base64 编码"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"参考图文件不存在：{image_path}")

    with open(image_path, "rb") as f:
        image_data = f.read()

    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/jpeg")

    return f"data:{mime_type};base64,{base64.b64encode(image_data).decode('utf-8')}"


def download_image(url: str, output_path: str) -> None:
    """下载图片到本地"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)


def ensure_output_dir(path: str = None, default: str = DEFAULT_OUTPUT_DIR) -> str:
    """确保输出目录存在"""
    d = path or default
    os.makedirs(d, exist_ok=True)
    return d


def build_output_path(output_path: str = None, default_dir: str = DEFAULT_OUTPUT_DIR,
                      prefix: str = "img", ext: str = ".png", index: int = None) -> str:
    """构建输出文件路径"""
    if output_path:
        if index is not None and index > 0:
            base, old_ext = os.path.splitext(output_path)
            return f"{base}_{index}{old_ext or ext}"
        return output_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{prefix}_{timestamp}"
    if index is not None:
        fname += f"_{index}"
    fname += ext
    return os.path.join(default_dir, fname)
