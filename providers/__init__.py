#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provider 注册表与工厂函数。
新增模型时，只需在 PROVIDERS 字典中注册。
"""

from .wan_provider import WanProvider
from .cogview_provider import CogviewProvider

# 注册所有 provider
# key: 用户指定的模型名（与 --model 参数对应）
# value: Provider 类（未实例化）
PROVIDERS = {
    "wan": WanProvider,
    "cogview": CogviewProvider,
    # 新增模型时在这里注册，例如：
    # "dalle": DalleProvider,
    # "tongyi": TongyiProvider,
}

# 默认模型（优先免费模型）
DEFAULT_PROVIDER = "cogview"


def get_provider(name: str = None):
    """
    根据名称获取 Provider 实例。
    如果 name 为 None 或 "auto"，返回默认 provider。
    """
    if name is None or name == "auto":
        name = DEFAULT_PROVIDER
    name = name.lower()

    if name not in PROVIDERS:
        raise ValueError(
            f"不支持的模型：{name}，"
            f"支持的模型：{list(PROVIDERS.keys())}"
        )
    return PROVIDERS[name]()


def list_providers() -> dict:
    """返回所有 provider 的能力概览。"""
    return {
        name: {
            "name": cls.name,
            "display_name": cls.display_name,
            "capabilities": cls.capabilities,
        }
        for name, cls in PROVIDERS.items()
    }


def select_provider(require_txt2img: bool = True,
                    require_img2img: bool = False,
                    require_sequential: bool = False,
                    prefer_free: bool = False) -> str:
    """
    根据能力需求自动选择最优 provider。
    返回 provider 名，由调用者再 get_provider() 实例化。
    """
    candidates = []
    for name, cls in PROVIDERS.items():
        caps = cls.capabilities
        if require_txt2img and not caps.get("txt2img"):
            continue
        if require_img2img and not caps.get("img2img"):
            continue
        if require_sequential and not caps.get("sequential"):
            continue
        candidates.append((name, caps.get("free", False)))

    if not candidates:
        req = []
        if require_txt2img:
            req.append("txt2img")
        if require_img2img:
            req.append("img2img")
        if require_sequential:
            req.append("sequential")
        raise ValueError(f"没有满足 {req} 的 provider")

    if prefer_free:
        # 优先免费
        for name, is_free in candidates:
            if is_free:
                return name
    return candidates[0][0]
