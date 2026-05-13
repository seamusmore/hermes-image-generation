---
name: image-generation
description: AI image generation — multi-model workflows, resolution tables, and prompt engineering for WAN, CogView, and other image models.
author: Luna
category: openclaw-imports
version: 2.2.0
triggers:
  - "生成图片"
  - "画图"
  - "图像生成"
  - "文生图"
  - "图生图"
  - "image editor"
---

# Image Generation

## When to use

Use when the user wants to generate, edit, or refine images with AI models:
- **General image creation** — landscapes, objects, scenes, art styles
- **Model selection** — choose the right model for the job
- **Resolution/aspect ratio optimization** — match model-native resolutions to avoid quality loss

## Configuration

Create or edit `~/.hermes/.env`:

```bash
# 阿里云百炼 API Key（wan2.7-image 需要，图生图必需）
BAILIAN_API_KEY=sk-xxxxxxxxxxxxxxxx

# 智谱 AI API Key（cogview-3-flash，免费模型）
ZHIPU_API_KEY=your_zhipu_api_key
```

**Default output directory**: `~/.hermes/images/`

## Supported Models

| Model | Strengths | Typical resolutions |
|-------|-----------|---------------------|
| **WAN 2.7 (wan2.7-image)** | High quality, good for portraits and anime | 512×512, 768×1344, 1024×1024 |
| **CogView-3-Flash** | Fast, good for general scenes | 768×1344, 1024×1024, 1024×1536 |

Auto-switching rules apply based on prompt content and user preference.

## Scripts

- `scripts/generate_image.py` — general image generation (txt2img + img2img)
- `scripts/generate_sequential.py` — sequential/multi-frame generation (requires sequential-capable provider)

## Providers

- `providers/` — provider architecture for multi-model support
  - `base.py` — abstract base class with capability declarations
  - `wan_provider.py` — WAN 2.7 (txt2img + img2img + sequential)
  - `cogview_provider.py` — CogView-3-Flash (txt2img only, free)
  - `__init__.py` — registry + factory functions
  - `utils.py` — shared utilities (base64, download, env key loading)

Adding a new model:
1. Create a new provider file inheriting `ImageProvider`
2. Declare capabilities and implement required methods
3. Register in `providers/__init__.py`
4. No script changes needed

## Quick Start

### Text-to-image (default: cogview, free)

```bash
cd ~/.hermes/skills/openclaw-imports/image-generation
python3 scripts/generate_image.py "一位优雅的东方女性，身穿汉服，站在古典园林中"
```

### Image-to-image (auto-switches to WAN)

```bash
python3 scripts/generate_image.py "海边散步" --ref_image "/path/to/reference.jpg"
```

### Sequential generation (WAN, storyboard style)

```bash
python3 scripts/generate_sequential.py "一个穿红裙的小女孩在花园里追逐蝴蝶" --count 12
```

### Specify model

```bash
python3 scripts/generate_image.py "提示词" --model wan
python3 scripts/generate_image.py "提示词" --model cogview
```

### Specify resolution

```bash
# WAN resolutions (use * separator)
python3 scripts/generate_image.py "咖啡厅" --model wan --size 720*1280

# CogView resolutions (use x separator)
python3 scripts/generate_image.py "咖啡厅" --model cogview --size 1024x1024
```

### Generate multiple images

```bash
python3 scripts/generate_image.py "提示词" --model cogview --n 3
```

## Model Comparison

| Feature | wan2.7-image | cogview-3-flash |
|---------|--------------|-----------------|
| Provider | Alibaba Cloud DashScope | Zhipu AI |
| Cost | Paid | **Free** |
| Text-to-image | Yes | Yes |
| Image-to-image | Yes | No |
| Batch generation | Yes | Yes |
| Default resolution | 1280*1280 | 1024x1024 |

## WAN 2.7 Supported Resolutions

| Resolution | Ratio | Use case |
|------------|-------|----------|
| 1280*1280 | 1:1 | General, avatar (default) |
| 720*1280 | 9:16 | Selfie, full-body, phone wallpaper |
| 853*1280 | 2:3 | Half-body, portrait |
| 1024*1536 | 2:3 | Vertical portrait |
| 1080*1920 | 9:16 | Full HD vertical |
| 1280*720 | 16:9 | Landscape, desktop wallpaper |
| 1280*853 | 3:2 | Landscape portrait |
| 1536*1024 | 3:2 | Landscape scene |
| 1920*1080 | 16:9 | Full HD landscape |
| 2048*2048 | 1:1 | Ultra HD square |

**Note**: All WAN resolutions must be multiples of 16.

## CogView Supported Resolutions

- 1024x1024 (square, default)
- 768x1344, 864x1152 (vertical)
- 1344x768, 1152x864 (horizontal)
- 1440x720 (ultra-wide)
- 720x1440 (ultra-tall)

## Pitfalls

- **Arm/hand connection** — low resolutions (512×512) often produce disconnected limbs; use 768+ for full-body shots
- **Non-native resolutions** — upscaling/downscaling from model-native sizes reduces sharpness
- **API keys** — store in `~/.hermes/.env`, never hardcode
- **Image-to-image limitation** — only WAN supports img2img; cogview will auto-switch to WAN when `--ref_image` is provided
- **Resolution format** — WAN uses `*` (e.g. `1280*1280`), CogView uses `x` (e.g. `1024x1024`)

## References

- `references/image-editor.md` — detailed resolution tables, troubleshooting, prompt engineering tips
- `references/provider-authoring-guide.md` — how to add a new model provider (capability contract, registry, auto-selection)
