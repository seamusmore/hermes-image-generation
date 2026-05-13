---
title: Provider Authoring Guide
description: How to add a new image generation model to the image-generation skill via the provider abstraction.
version: 1.0.0
---

# Provider Authoring Guide

The `image-generation` skill uses a **provider architecture** so new models can be added without touching the CLI entry scripts (`generate_image.py`, `generate_sequential.py`).

## Core Philosophy

- **Capability Declaration**: Each provider announces what it can do (`txt2img`, `img2img`, `sequential`, `free`, `sizes`).
- **Auto-Selection**: Entry scripts query capabilities and automatically pick the right provider for the job.
- **Uniform Return Format**: All providers return the same `dict` shape from `generate()`.

## Provider Contract

### 1. Inherit `ImageProvider`

```python
from providers.base import ImageProvider
from providers.utils import get_api_key, download_image, build_output_path

class MyProvider(ImageProvider):
    name = "myprovider"
    display_name = "my-model-v1"
    capabilities = {
        "txt2img": True,
        "img2img": False,
        "sequential": False,
        "free": True,
        "sizes": ["1024x1024", "512x512"],
    }
```

### 2. Implement `generate()`

Signature (must accept these kwargs):

```python
def generate(self, *, prompt: str, size: Optional[str] = None,
             output_path: Optional[str] = None, n: int = 1,
             ref_image: Optional[str] = None, **kwargs) -> dict:
```

Return format (strict):

```python
{
    "success": True / False,
    "model": self.display_name,
    "images": [{"url": "...", "path": "/abs/path/to/file"}, ...],
    "time": 12.34,
    "count": 1,
    "error": None / "error message",
}
```

Use `build_output_path()` from `providers.utils` to handle default naming.

### 3. Optionally implement `generate_sequential()`

Only if the model supports grouped/sequential generation (storyboards, comics).

```python
def generate_sequential(self, *, prompt: str, count: int = 12,
                        size: Optional[str] = None,
                        ref_image: Optional[str] = None,
                        output_dir: Optional[str] = None,
                        **kwargs) -> dict:
```

If not implemented, the base class raises `NotImplementedError`.

### 4. Register in `providers/__init__.py`

```python
PROVIDERS = {
    "wan": WanProvider,
    "cogview": CogviewProvider,
    "myprovider": MyProvider,  # <-- add here
}
```

That's it. `generate_image.py` and `generate_sequential.py` will automatically recognize it.

## Capability Semantics

| Capability | Meaning | Used by |
|------------|---------|---------|
| `txt2img` | Supports text-to-image generation | `generate_image.py` (always required) |
| `img2img` | Supports image-to-image (reference image) | `generate_image.py` (when `--ref_image` provided) |
| `sequential` | Supports grouped/sequential generation | `generate_sequential.py` |
| `free` | No cost / generous free tier | Auto-selection (preferred when no special capabilities needed) |
| `sizes` | List of supported resolutions | Resolution validation (optional) |

## Auto-Selection Logic

```python
from providers import select_provider

# Text-to-image, prefer free
select_provider(require_txt2img=True, prefer_free=True)

# Must support img2img
select_provider(require_txt2img=True, require_img2img=True)

# Must support sequential
select_provider(require_sequential=True)
```

The first matching provider is returned. When `prefer_free=True`, free providers are checked first.

## Shared Utilities (`providers/utils.py`)

| Function | Purpose |
|----------|---------|
| `get_api_key(env_key)` | Reads API key from `~/.hermes/.env` |
| `image_to_base64(path)` | Converts local image to base64 data URI |
| `download_image(url, path)` | Downloads image to local path |
| `ensure_output_dir(path)` | Creates directories if missing |
| `build_output_path(...)` | Generates output path with timestamp/index |

## Pitfalls

- **Do not hardcode paths**: Always use `os.path.expanduser("~/.hermes/...")` or accept paths via parameters.
- **Do not hardcode API keys**: Use `get_api_key()` which centralizes key management.
- **Return uniform dicts**: Entry scripts depend on the `success` / `images` / `error` keys. Missing keys cause crashes.
- **Keep `ref_image` optional**: Even if your model doesn't support img2img, accept the parameter and return a clear error in the dict.
- **Name collisions**: The `name` class attribute must be unique across all providers; it is the CLI `--model` value.
