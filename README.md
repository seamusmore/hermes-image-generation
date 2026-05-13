# Image Generation

AI image generation skill with provider-based architecture.

## Quick Links

- **Usage**: See [`SKILL.md`](SKILL.md)
- **Detailed Reference**: See [`references/image-editor.md`](references/image-editor.md)
- **Provider Authoring Guide**: See [`references/provider-authoring-guide.md`](references/provider-authoring-guide.md)

## Installation

### Recommended (via Hermes CLI)

```bash
hermes skills install https://github.com/seamusmore/hermes-image-generation.git
```

Then restart the gateway for the skill to take effect.

### Manual

```bash
git clone https://github.com/seamusmore/hermes-image-generation.git \
  ~/.hermes/skills/image-generation
```

Then restart the gateway.

## Configuration

API keys are read from `~/.hermes/.env`. Create or edit the file and add:

```bash
# Alibaba Cloud DashScope (required for WAN 2.7, especially image-to-image)
BAILIAN_API_KEY=sk-xxxxxxxxxxxxxxxx

# Zhipu AI (free model, only text-to-image)
ZHIPU_API_KEY=your_zhipu_api_key
```

**Default output directory**: `~/.hermes/images/`

## Architecture

```
image-generation/
├── scripts/
│   ├── generate_image.py       # General image generation entry
│   └── generate_sequential.py  # Sequential/storyboard generation
├── providers/                  # Pluggable provider architecture
│   ├── __init__.py             # Registry + factory functions
│   ├── base.py                 # Abstract base class with capability declarations
│   ├── utils.py                # Shared utilities
│   ├── wan_provider.py         # WAN 2.7 (txt2img + img2img + sequential)
│   └── cogview_provider.py     # CogView-3-Flash (txt2img only, free)
├── references/
│   ├── image-editor.md
│   └── provider-authoring-guide.md
├── SKILL.md
├── LICENSE
└── README.md
```

## Adding a New Model

1. Create a new provider file under `providers/` inheriting `ImageProvider`
2. Declare capabilities and implement `generate()` (and optionally `generate_sequential()`)
3. Register in `providers/__init__.py`
4. No script changes needed

## License

MIT — Copyright (c) 2026 Seamus
