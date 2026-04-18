# evolink-imagegen

Public skill repo for generating offline images through the Evolink async image API.

The packaged reference is based on the official Evolink:

- `z-image-turbo` image-generation document:
  `https://docs.evolink.ai/en/api-manual/image-series/z-image-turbo/z-image-turbo-image-generate`
- `get-task-detail` async task-status document:
  `https://docs.evolink.ai/en/api-manual/task-management/get-task-detail`

## Repo Layout

- `skills/evolink-imagegen/`
  The installable skill directory. This is the path to use with GitHub-based skill installers such as `npx skills add`.

## Install

For the Vercel-style installer, use:

```bash
npx skills add <owner>/evolink-imagegen
```

If the installer asks which skill to add, choose `evolink-imagegen`.

For explicit selection, use the skill name if your installer version supports it:

```bash
npx skills add <owner>/evolink-imagegen --skill evolink-imagegen
```

For Codex's GitHub-path installer, install with the skill path:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo <owner>/evolink-imagegen \
  --path skills/evolink-imagegen
```

After installing, restart Codex to pick up the new skill.

For manual installation in other agents, copy the `evolink-imagegen/` directory into that agent's skills directory.

## Environment Variables

- `EVOLINK_API_TOKEN`
- `EVOLINK_API_BASE_URL`
- `EVOLINK_IMAGE_MODEL`

Defaults:

- `EVOLINK_API_BASE_URL=https://api.evolink.ai`
- `EVOLINK_IMAGE_MODEL=z-image-turbo`

## Local Test

```bash
python3 skills/evolink-imagegen/scripts/evolink_imagegen.py generate \
  --prompt "soft watercolor spring garden illustration" \
  --size 16:9 \
  --dry-run
```
