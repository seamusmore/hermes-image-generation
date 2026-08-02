# Hermes Image Generation Plugin

Multi-model image generation backend for [Hermes Agent](https://github.com/NousResearch/hermes-agent). One plugin, three models.

## Models

| Model ID | Backend | API | Text-to-Image | Image-to-Image | Price |
|----------|---------|-----|:---:|:---:|:---:|
| `wan2.7-image` | WAN 2.7 | Alibaba DashScope | ✅ | ✅ | Paid |
| `cogview-3-flash` | CogView-3-Flash | Zhipu AI | ✅ | ❌ | Free |
| `agnes-image-2.1-flash` | Agnes Image 2.1 | Agnes AI | ✅ | ✅ | Free |

## Installation

### Hermes CLI (recommended)

```bash
hermes plugins install https://github.com/seamusmore/hermes-image-generation.git
```

### Manual

```bash
git clone https://github.com/seamusmore/hermes-image-generation.git \
  ~/.hermes/plugins/image_gen/image-generation

hermes plugins enable image-generation
```

Restart the gateway:

```bash
hermes gateway restart
```

## Configuration

Set the provider in `config.yaml`:

```yaml
image_gen:
  provider: image-generation
  model: wan2.7-image
```

Or via CLI:

```bash
hermes config set image_gen.provider image-generation
hermes config set image_gen.model wan2.7-image
```

API keys in `~/.hermes/.env`:

```bash
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx   # WAN 2.7
ZHIPU_API_KEY=your_zhipu_api_key        # CogView-3-Flash
AGNES_API_KEY=your_agnes_api_key        # Agnes Image 2.1
```

## Switching Models

Change `image_gen.model` in `config.yaml` or via CLI:

```bash
hermes config set image_gen.model wan2.7-image
hermes config set image_gen.model cogview-3-flash
hermes config set image_gen.model agnes-image-2.1-flash
```

Restart gateway after switching. Or use `hermes tools` → Image Generation to pick interactively.

## Usage

In chat, describe what you want and Hermes will call `image_generate`:

> "Generate a landscape of a mountain lake at sunset"

### Aspect Ratios

`landscape` (16:9), `square` (1:1), `portrait` (9:16).

### Image-to-Image

WAN 2.7 and Agnes support image editing. Attach or reference an image and describe the edit:

> "Add snow to the mountain peaks in this photo"

### Resolution Mapping

| Aspect Ratio | WAN 2.7 | CogView | Agnes |
|-------------|---------|---------|-------|
| landscape | 1280×720 | 1344×768 | 2K 16:9 |
| square | 1280×1280 | 1024×1024 | 2K 1:1 |
| portrait | 720×1280 | 768×1344 | 2K 9:16 |

## License

MIT — Copyright (c) 2026 Seamus
