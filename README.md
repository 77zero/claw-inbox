# Claw Inbox

AI 自动收集的内容仓库，来自各种来源的精选信息。

## 目录结构

```
claw-inbox/
├── ai_news/        # AI 新闻日报
├── youtube/        # YouTube 视频笔记
├── podcast/        # 播客笔记
├── zhihu_star/     # 知识星球精华
└── x_posts/        # X/Twitter 精选
```

## 来源

内容由 [OpenClaw](https://github.com/openclaw) 自动收集和整理。

## 格式

所有内容使用 Markdown 格式，包含 YAML Frontmatter：

```yaml
---
title: "标题"
source: "来源"
date: "2024-01-15"
tags:
  - "tag1"
  - "tag2"
---
```

## 更新频率

- AI 新闻：每 8 小时
- YouTube：每 24 小时
- 播客：每 12 小时
- 知识星球：每 6 小时
- X/Twitter：每 4 小时
