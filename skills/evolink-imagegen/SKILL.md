---
name: evolink-imagegen
description: "Generate offline images through the Evolink async image API. Use when the user wants illustrations, concept art, marketing assets, UI materials, or batch image jobs with documented models like z-image-turbo. Includes a local script to submit tasks, poll status, and download results."
---
# Evolink ImageGen

Use this skill when the task is to generate offline image assets through the Evolink async image API.

This skill is for curated asset generation, not runtime product logic.

## When To Use

Use it when the user asks to:

- generate illustrations or concept art through Evolink
- create marketing or product art assets offline
- submit, poll, or download async image jobs
- use documented models such as `z-image-turbo`

Do not use it for:

- runtime image generation inside the core product loop
- deterministic UI or game visuals that should stay in code

## What To Read

Start with:

- `references/evolink-api.md`

Only read other project files if the current workspace has its own prompt library, asset plan, or brand rules that should drive the prompt.

That reference is based on the official Evolink image-generation doc and the official task-detail polling doc.

## Environment

Keep these environment variables aligned with the host project when possible:

- `EVOLINK_API_TOKEN`
- `EVOLINK_API_BASE_URL`
- `EVOLINK_IMAGE_MODEL`

## Rules

- Use `--dry-run` before paid live requests unless the user explicitly wants immediate generation.
- Ask before making live API calls that spend quota.
- Save outputs promptly because remote result URLs are temporary.
- Do not ask the model to render readable UI text, logos, or watermarks inside production images unless the user explicitly wants that risk.
- Keep text-safe space for surfaces that will receive HTML or design overlays later.

## Workflow

### 1. Lock the asset intent

Identify:

- asset purpose
- target surface
- art direction
- size or aspect ratio
- text-safe zones
- number of desired variants

### 2. Prepare the prompt

If the workspace already has an approved prompt library or design system, use that instead of improvising a new visual direction.

### 3. Dry run first

Preview the exact request payload without calling the API:

```bash
python3 scripts/evolink_imagegen.py generate \
  --prompt "soft watercolor spring garden illustration, calm sky, text-safe left area" \
  --size 16:9 \
  --dry-run
```

### 4. Run a live generation after approval

```bash
export EVOLINK_API_TOKEN=...
python3 scripts/evolink_imagegen.py generate \
  --prompt "soft watercolor spring garden illustration, calm sky, text-safe left area" \
  --size 16:9
```

### 5. Use async-only flows when needed

Submit without polling:

```bash
python3 scripts/evolink_imagegen.py submit \
  --prompt "storybook botanical ornament board, clean spacing, no text" \
  --size 1:1
```

Poll an existing task and download the result:

```bash
python3 scripts/evolink_imagegen.py poll \
  --task-id task-unified-1234567890-example
```

### 6. Override the model only when needed

```bash
python3 scripts/evolink_imagegen.py generate \
  --model z-image-turbo \
  --prompt "editorial botanical illustration, soft gouache, broad text-safe center" \
  --size 4:3
```

The script keeps `--model` configurable, but the current packaged reference is based on the official `z-image-turbo` generation document.

## Output Behavior

The script writes a run directory containing:

- `request.json`
- `task-submitted.json`
- `task-final.json`
- downloaded image files when available

Default output base directory:

- `generated/evolink-imagegen/`

## Notes

- Supported ratio presets include `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `9:16`, `16:9`, `1:2`, and `2:1`.
- Use `--seed` when you want more reproducible variations.
- If the API changes, update `references/evolink-api.md` and the script together.
