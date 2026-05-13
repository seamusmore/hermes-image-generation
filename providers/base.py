#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Provider 抽象基类
所有图像生成 Provider 必须继承此类，并声明自身能力。
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class ImageProvider(ABC):
    """
    图像生成 Provider 抽象基类。
    每个子类必须声明 name、display_name 和 capabilities。
    """

    # 子类覆盖：模型唯一标识
    name: str = ""
    # 子类覆盖：用户可读的显示名
    display_name: str = ""
    # 子类覆盖：能力声明
    capabilities: dict = {}
    """
    capabilities 示例：
    {
        "txt2img": True,        # 支持文生图
        "img2img": False,       # 支持图生图
        "sequential": False,    # 支持组图/序列生成
        "free": False,          # 是否免费
        "sizes": ["1024x1024"], # 支持的分辨率列表
    }
    """

    @abstractmethod
    def generate(self, *, prompt: str, size: Optional[str] = None,
                 output_path: Optional[str] = None, n: int = 1,
                 ref_image: Optional[str] = None, **kwargs) -> dict:
        """
        单张/批量生成图片。

        必须返回统一格式：
        {
            "success": bool,
            "model": str,
            "images": [{"url": str, "path": str}, ...],
            "time": float,
            "count": int,
            "error": str | None,
        }
        """
        ...

    def generate_sequential(self, *, prompt: str, count: int = 12,
                            size: Optional[str] = None,
                            ref_image: Optional[str] = None,
                            output_dir: Optional[str] = None,
                            **kwargs) -> dict:
        """
        组图/序列生成（可选实现）。
        默认抛出 NotImplementedError，表示不支持。
        """
        raise NotImplementedError(
            f"Provider '{self.name}' 不支持组图模式"
        )

    def supports(self, capability: str) -> bool:
        """查询是否支持某项能力"""
        return self.capabilities.get(capability, False)
