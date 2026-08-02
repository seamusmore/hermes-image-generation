"""Hermes image_gen backend — unified provider for WAN 2.7, CogView-3-Flash, Agnes Image 2.1."""

from __future__ import annotations
import base64, json, logging, os
from typing import Any, Dict, List, Optional
import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO, ImageGenProvider, error_response,
    normalize_reference_images, resolve_aspect_ratio,
    save_url_image, success_response,
)

logger = logging.getLogger(__name__)

# ── model registry ────────────────────────────────────────────────────────
_MODELS = [
    {
        "id": "wan2.7-image",
        "display": "WAN 2.7",
        "speed": "~15-30s",
        "strengths": "High quality portraits, anime, general scenes; img2img",
        "price": "Paid (DashScope)",
        "provider": "wan",
    },
    {
        "id": "cogview-3-flash",
        "display": "CogView-3-Flash",
        "speed": "~5-10s",
        "strengths": "Fast, general scenes, free tier",
        "price": "Free",
        "provider": "cogview",
    },
    {
        "id": "agnes-image-2.1-flash",
        "display": "Agnes Image 2.1 Flash",
        "speed": "~10-20s",
        "strengths": "High-detail visuals, complex composition, img2img",
        "price": "Free",
        "provider": "agnes",
    },
]

# ── helpers ───────────────────────────────────────────────────────────────
_MIME_MAP = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

def _image_to_b64(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = _MIME_MAP.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

def _src_to_b64(src: str) -> str:
    if src.startswith(("http://", "https://")):
        r = requests.get(src, timeout=30); r.raise_for_status()
        ct = r.headers.get("Content-Type", "image/png")
        return f"data:{ct};base64,{base64.b64encode(r.content).decode()}"
    return _image_to_b64(src)

# ── per-model generate ────────────────────────────────────────────────────

def _generate_wan(prompt, aspect, ref_b64_list, n) -> tuple:
    sizes = {"landscape": "1280*720", "square": "1280*1280", "portrait": "720*1280"}
    content: List[Dict[str, Any]] = [{"text": prompt}]
    modality = "text"
    if ref_b64_list:
        for b in ref_b64_list: content.append({"image": b})
        modality = "image"
    payload = {
        "model": "wan2.7-image",
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": {"thinking_mode": True, "watermark": False, "n": n,
                       "enable_sequential": False, "size": sizes.get(aspect, "1280*720")},
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"}
    r = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                       headers=headers, json=payload, timeout=60)
    r.raise_for_status(); data = r.json()
    choices = data.get("output", {}).get("choices", [])
    if not choices: raise RuntimeError("No choices in WAN response")
    for c in choices:
        for item in c.get("message", {}).get("content", []):
            if item.get("image"): return item["image"], modality
    raise RuntimeError("No image in WAN response")


def _generate_cogview(prompt, aspect, n) -> tuple:
    sizes = {"landscape": "1344x768", "square": "1024x1024", "portrait": "768x1344"}
    payload = {"model": "cogview-3-flash", "prompt": prompt, "size": sizes.get(aspect, "1024x1024"), "n": n}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['ZHIPU_API_KEY']}"}
    r = requests.post("https://open.bigmodel.cn/api/paas/v4/images/generations",
                       headers=headers, json=payload, timeout=60)
    r.raise_for_status(); data = r.json()
    if "data" not in data or not data["data"]: raise RuntimeError(f"CogView failed: {data}")
    return data["data"][0]["url"], "text"


def _generate_agnes(prompt, aspect, ref_urls) -> tuple:
    params = {"landscape": ("2K", "16:9"), "square": ("2K", "1:1"), "portrait": ("2K", "9:16")}
    tier, ratio = params.get(aspect, ("2K", "16:9"))
    payload: Dict[str, Any] = {"model": "agnes-image-2.1-flash", "prompt": prompt, "size": tier, "ratio": ratio}
    if ref_urls: payload.setdefault("extra_body", {})["image"] = ref_urls
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['AGNES_API_KEY']}"}
    r = requests.post("https://api.agnes-ai.com/v1/images/generations",
                       headers=headers, json=payload, timeout=60)
    r.raise_for_status(); data = r.json()
    if not data.get("data"): raise RuntimeError(f"Agnes failed: {data}")
    return data["data"][0].get("url") or data["data"][0].get("b64_json", ""), "text"


# ── provider ──────────────────────────────────────────────────────────────

class MultiImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str: return "image-generation"
    @property
    def display_name(self) -> str: return "Image Generation (multi-model)"
    def is_available(self) -> bool:
        return bool(os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ZHIPU_API_KEY") or os.environ.get("AGNES_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]: return _MODELS
    def default_model(self) -> Optional[str]: return "wan2.7-image"

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Image Generation (multi-model)",
            "badge": "paid + free",
            "tag": "WAN 2.7, CogView-3-Flash, Agnes Image 2.1 — text-to-image & image editing",
            "env_vars": [
                {"key": "DASHSCOPE_API_KEY", "prompt": "DashScope API key (WAN)", "url": "https://bailian.console.aliyun.com/"},
                {"key": "ZHIPU_API_KEY", "prompt": "Zhipu API key (CogView)", "url": "https://open.bigmodel.cn/usercenter/apikeys"},
                {"key": "AGNES_API_KEY", "prompt": "Agnes API key", "url": "https://platform.agnes-ai.com/"},
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text", "image"], "max_reference_images": 4}

    def generate(self, prompt: str, aspect_ratio: str = DEFAULT_ASPECT_RATIO, *,
                 image_url: Optional[str] = None,
                 reference_image_urls: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)
        model_id = kwargs.get("model") or self.default_model() or "wan2.7-image"

        if not prompt:
            return error_response(error="Prompt is required", error_type="invalid_input",
                                  provider="image-generation", prompt="", aspect_ratio=aspect)

        # resolve model metadata
        model_meta = next((m for m in _MODELS if m["id"] == model_id), None)
        if not model_meta:
            return error_response(error=f"Unknown model: {model_id}", error_type="invalid_input",
                                  provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)

        provider_key = model_meta["provider"]

        # check API key
        key_map = {"wan": "DASHSCOPE_API_KEY", "cogview": "ZHIPU_API_KEY", "agnes": "AGNES_API_KEY"}
        if not os.environ.get(key_map.get(provider_key, "")):
            return error_response(error=f"{key_map[provider_key]} is not set", error_type="auth_error",
                                  provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)

        n = max(1, min(int(kwargs.get("num_images", 1)), 4))

        # encode reference images
        ref_b64_list: List[str] = []
        ref_url_list: List[str] = []
        if image_url:
            ref_url_list.append(image_url)
            try: ref_b64_list.append(_src_to_b64(image_url))
            except Exception as exc:
                return error_response(error=f"Failed to encode ref: {exc}", error_type="invalid_input",
                                      provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)
        refs = normalize_reference_images(reference_image_urls)
        if refs:
            for src in refs:
                ref_url_list.append(src)
                try: ref_b64_list.append(_src_to_b64(src))
                except Exception as exc:
                    return error_response(error=f"Failed to encode ref: {exc}", error_type="invalid_input",
                                          provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)

        try:
            if provider_key == "wan":
                img_url, modality = _generate_wan(prompt, aspect, ref_b64_list, n)
            elif provider_key == "cogview":
                if ref_url_list:
                    return error_response(error="CogView does not support img2img", error_type="invalid_input",
                                          provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)
                img_url, modality = _generate_cogview(prompt, aspect, n)
            else:  # agnes
                img_url, modality = _generate_agnes(prompt, aspect, ref_url_list)
        except Exception as exc:
            return error_response(error=str(exc), error_type=type(exc).__name__,
                                  provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)

        if not img_url:
            return error_response(error="No image returned", error_type="provider_error",
                                  provider="image-generation", model=model_id, prompt=prompt, aspect_ratio=aspect)

        try:
            image = str(save_url_image(img_url, prefix=provider_key))
        except Exception:
            image = img_url

        return success_response(image=image, model=model_id, prompt=prompt, aspect_ratio=aspect,
                                provider="image-generation", modality=modality)


def register(ctx) -> None:
    ctx.register_image_gen_provider(MultiImageGenProvider())
