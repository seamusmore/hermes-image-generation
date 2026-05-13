#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAN 2.7 Image Provider
支持文生图、图生图、组图模式。
"""

import os
import time
import requests
from datetime import datetime

from .base import ImageProvider
from .utils import get_api_key, image_to_base64, download_image, ensure_output_dir, build_output_path


WAN_SIZES = [
    "1280*1280", "1280*720", "720*1280", "1280*853", "853*1280",
    "1536*1024", "1024*1536", "1920*1080", "1080*1920", "2048*2048"
]


class WanProvider(ImageProvider):
    name = "wan"
    display_name = "wan2.7-image"
    capabilities = {
        "txt2img": True,
        "img2img": True,
        "sequential": True,
        "free": False,
        "sizes": WAN_SIZES,
    }

    def __init__(self):
        self.api_key = get_api_key("BAILIAN_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc"

    def _build_sync_payload(self, prompt, size, n, ref_image=None):
        messages_content = [{"text": prompt}]
        if ref_image:
            messages_content.append({"image": image_to_base64(ref_image)})

        return {
            "model": "wan2.7-image",
            "input": {
                "messages": [{"role": "user", "content": messages_content}]
            },
            "parameters": {
                "thinking_mode": True,
                "watermark": False,
                "n": n,
                "enable_sequential": False,
                "size": size,
            }
        }

    def _build_async_payload(self, prompt, size, n, ref_image=None):
        messages_content = []
        if ref_image:
            messages_content.append({"image": image_to_base64(ref_image)})
        messages_content.append({"text": prompt})

        return {
            "model": "wan2.7-image",
            "input": {
                "messages": [{"role": "user", "content": messages_content}]
            },
            "parameters": {
                "enable_sequential": True,
                "n": n,
                "size": size,
                "watermark": False,
            }
        }

    def _download_images(self, choices, output_path, default_dir, prefix):
        images = []
        for i, choice in enumerate(choices):
            content_list = choice.get("message", {}).get("content", [])
            for item in content_list:
                image_url = item.get("image")
                if not image_url:
                    continue
                path = build_output_path(
                    output_path=output_path,
                    default_dir=default_dir,
                    prefix=prefix,
                    ext=".png",
                    index=i + 1
                )
                download_image(image_url, path)
                images.append({"url": image_url, "path": path})
        return images

    def generate(self, *, prompt, size=None, output_path=None, n=1,
                 ref_image=None, **kwargs):
        size = size or "1280*1280"
        default_dir = os.path.expanduser("~/.hermes/images")
        ensure_output_dir(default_dir)

        payload = self._build_sync_payload(prompt, size, n, ref_image)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        start = datetime.now()
        try:
            resp = requests.post(
                f"{self.base_url}/multimodal-generation/generation",
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            result = resp.json()

            choices = result.get("output", {}).get("choices", [])
            if not choices:
                return {"success": False, "error": "响应中没有 choices", "model": self.display_name}

            images = self._download_images(choices, output_path, default_dir, "wan")
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

    def generate_sequential(self, *, prompt, count=12, size=None,
                            ref_image=None, output_dir=None, **kwargs):
        size = size or "1920*1080"
        output_dir = output_dir or os.path.expanduser("~/.hermes/images/sequential")
        os.makedirs(output_dir, exist_ok=True)

        # 保存提示词
        prompt_file = os.path.join(output_dir, "prompt.txt")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(f"提示词：{prompt}\n")
            f.write(f"模型：{self.display_name}\n")
            f.write(f"分辨率：{size}\n")
            f.write(f"总数量：{count}\n")

        payload = self._build_async_payload(prompt, size, count, ref_image)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable"
        }

        start = datetime.now()
        try:
            # 提交异步任务
            resp = requests.post(
                f"{self.base_url}/image-generation/generation",
                headers=headers, json=payload, timeout=30
            )
            resp.raise_for_status()
            result = resp.json()

            task_id = result.get("output", {}).get("task_id")
            if not task_id:
                return {"success": False, "error": f"未获取到 task_id：{result}", "model": self.display_name}

            # 轮询
            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            query_headers = {"Authorization": f"Bearer {self.api_key}"}
            max_retries = 1800

            for i in range(max_retries):
                time.sleep(1)
                q = requests.get(query_url, headers=query_headers, timeout=30)
                q.raise_for_status()
                qr = q.json()
                status = qr.get("output", {}).get("task_status")

                if status == "SUCCEEDED":
                    break
                elif status == "FAILED":
                    return {"success": False, "error": qr.get("message", "任务失败"), "model": self.display_name}
                if (i + 1) % 10 == 0:
                    print(f"   ⏳ 等待中... ({i+1}秒)")
            else:
                return {"success": False, "error": "任务超时（超过30分钟）", "model": self.display_name}

            # 提取结果
            choices = qr.get("output", {}).get("choices", [])
            images = []
            img_idx = 0
            for choice in choices:
                for item in choice.get("message", {}).get("content", []):
                    url = item.get("image")
                    if not url:
                        continue
                    img_idx += 1
                    path = os.path.join(output_dir, f"page_{img_idx:02d}.png")
                    download_image(url, path)
                    images.append({"url": url, "path": path, "page": img_idx})

            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "model": self.display_name,
                "images": images,
                "time": elapsed,
                "count": len(images),
                "output_dir": output_dir,
                "error": None,
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"网络请求失败：{e}", "model": self.display_name}
        except Exception as e:
            return {"success": False, "error": str(e), "model": self.display_name}
