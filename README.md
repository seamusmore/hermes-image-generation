# Image Generation

AI image generation skill with provider-based architecture.

## Quick Links

- **Usage**: See [`SKILL.md`](SKILL.md)
- **Detailed Reference**: See [`references/image-editor.md`](references/image-editor.md)
- **Provider Authoring Guide**: See [`references/provider-authoring-guide.md`](references/provider-authoring-guide.md)

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
