# evolink-imagegen

一个公开的技能仓库，用于通过 Evolink 异步图片 API 生成离线图片资源。

英文说明见 [README.md](README.md)。

当前打包的参考资料基于 Evolink 官方文档：

- `z-image-turbo` 图片生成文档：
  `https://docs.evolink.ai/en/api-manual/image-series/z-image-turbo/z-image-turbo-image-generate`
- `get-task-detail` 异步任务状态文档：
  `https://docs.evolink.ai/en/api-manual/task-management/get-task-detail`

## 仓库结构

- `skills/evolink-imagegen/`
  可安装的技能目录。通过 GitHub 路径安装技能时，应使用这个目录，例如 `npx skills add`。

## 安装

如果使用 Vercel 风格的安装器，可以执行：

```bash
npx skills add sunshare/evolink-imagegen
```

如果安装器要求你选择具体技能，请选择 `evolink-imagegen`。

如果你的安装器版本支持显式指定技能名，可以使用：

```bash
npx skills add sunshare/evolink-imagegen --skill evolink-imagegen
```

如果使用 Codex 的 GitHub 路径安装器，可以通过技能路径安装：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sunshare/evolink-imagegen \
  --path skills/evolink-imagegen
```

安装完成后，重启 Codex 以加载这个技能。

如果是在其他 agent 中手动安装，可以把 `evolink-imagegen/` 目录复制到对应 agent 的技能目录中。

## 环境变量

- `EVOLINK_API_TOKEN`
- `EVOLINK_API_BASE_URL`
- `EVOLINK_IMAGE_MODEL`

默认值：

- `EVOLINK_API_BASE_URL=https://api.evolink.ai`
- `EVOLINK_IMAGE_MODEL=z-image-turbo`

## 本地测试

```bash
python3 skills/evolink-imagegen/scripts/evolink_imagegen.py generate \
  --prompt "soft watercolor spring garden illustration" \
  --size 16:9 \
  --dry-run
```
