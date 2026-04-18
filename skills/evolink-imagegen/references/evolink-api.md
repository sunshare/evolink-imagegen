# Evolink API Reference

This skill uses the Evolink async image generation API.

This reference is distilled from the official Evolink:

- `z-image-turbo` image-generation documentation
- `get-task-detail` async task-status documentation

Canonical URLs:

- `https://docs.evolink.ai/en/api-manual/image-series/z-image-turbo/z-image-turbo-image-generate`
- `https://docs.evolink.ai/en/api-manual/task-management/get-task-detail`

## Base URL

- `https://api.evolink.ai`

Override with:

- `EVOLINK_API_BASE_URL`
- `--base-url`

## Auth

Use bearer auth with:

- `EVOLINK_API_TOKEN`

## Submit Image Generation

`POST /v1/images/generations`

Required JSON fields:

- `model`
- `prompt`

Common optional fields:

- `size`
- `seed`
- `nsfw_check`
- `callback_url`

Documented model name in the current official generation doc:

- `z-image-turbo`

The script still exposes `--model` so you can override it if your account has access to other image models, but only `z-image-turbo` is treated as documented here.

Common ratio presets:

- `1:1`
- `2:3`
- `3:2`
- `3:4`
- `4:3`
- `9:16`
- `16:9`
- `1:2`
- `2:1`

The response returns an async task id. It does not return the finished image immediately.

## Poll Task Status

`GET /v1/tasks/{task_id}`

Typical task statuses:

- `pending`
- `processing`
- `completed`
- `failed`

When completed, `results` contains downloadable image URLs.

## Error Shape

Error responses use an `error` object with fields such as:

- `code`
- `message`
- `type`

Typical failure classes:

- auth failure
- model access denied
- quota exceeded
- rate limited
- content policy violation

## Operational Notes

- Result URLs are temporary, so download them promptly.
- Use dry-run planning before quota-spending live requests.
- Prefer curated prompt libraries and human review for production assets.
