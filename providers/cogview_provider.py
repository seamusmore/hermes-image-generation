#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CogView-3-Flash Provider
仅支持文生图，免费模型。
"""

import os
import requests
from datetime import datetime

from .base import ImageProvider
from .utils import get_api_key, download_image, ensure_output_dir, build_output_path


COGVIEW_SIZES = [
    "1024x1024", "768x1344", "864x1152", "1344x768",
    "1152x864", "1440x720", "720x1440"
]


class CogviewProvider(ImageProvider):
    name = "cogview"
    display_name = "cogview-3-flash"
    capabilities = {
        "txt2img": True,
        "img2img": False,
        "sequential": False,
        "free": True,
        "sizes": COGVIEW_SIZES,
    }

    def __init__(self):
        self.api_key = get_api_key("ZHIPU_API_KEY")

    def generate(self, *, prompt, size=None, output_path=None, n=1,
                 ref_image=None, **kwargs):
        if ref_image:
            return {
                "success": False,
                "error": "cogview-3-flash 不支持图生图",
                "model": self.display_name,
            }

        size = size or "1024x1024"
        default_dir = os.path.expanduser("~/.hermes/images")
        ensure_output_dir(default_dir)

        url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "cogview-3-flash",
            "prompt": prompt,
            "size": size,
            "n": n
        }

        start = datetime.now()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            result = resp.json()

            if "data" not in result or not result["data"]:
                return {"success": False, "error": f"生成失败：{result}", "model": self.display_name}

            images = []
            for i, img_data in enumerate(result["data"]):
                image_url = img_data["url"]
                path = build_output_path(
                    output_path=output_path,
                    default_dir=default_dir,
                    prefix="cogview",
                    ext=".jpg",
                    index=i + 1
                )
                download_image(image_url, path)
                images.append({"url": image_url, "path": path})

            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "model": self.display_name,
                "images": images,
                "time": elapsed,
                "count": len(images),
                "error": None,
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"网络请求失败：{e}", "model": self.display_name}
        except Exception as e:
            return {"success": False, "error": str(e), "model": self.display_name}
