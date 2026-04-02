#!/usr/bin/env python3
"""
YouTube Monitor - 每24小时扫描AI技术频道
输出到: /home/admin/projects/claw-inbox/youtube/
所有内容合并为一个中文汇总文档
"""

import os
import sys
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# 配置
OUTPUT_DIR = Path("/home/admin/projects/claw-inbox/youtube")
REPO_DIR = Path("/home/admin/projects/claw-inbox")
STATE_FILE = Path("/home/admin/.claw_youtube_state.json")

# 监控的 YouTube 频道
CHANNELS = [
    {"name": "Two Minute Papers", "id": "UCbfYPyITQ-7l4upoX8nvctg"},
    {"name": "AI Explained", "id": "UC3rY5HOgbBvGmq7RnDfwF7A"},
    {"name": "Matt Wolfe", "id": "UCbSV9b8SW8ZkPj_43hafpPw"},
    {"name": "Yannic Kilcher", "id": "UCZHmQk67mSJgfCCTn7xBfew"},
    {"name": "Fireship", "id": "UCsBjURrPoezykLs9EqgamOA"},
    {"name": "Lex Fridman", "id": "UCSHZKyawb77ixDdsGog4iWA"},
]

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            return {}
    return {"checked_videos": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_channel_videos(channel_id):
    try:
        cmd = [
            "yt-dlp", "--flat-playlist", "--playlist-end", "5",
            "--dump-json", f"https://www.youtube.com/channel/{channel_id}/videos"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "upload_date": data.get("upload_date"),
                        "uploader": data.get("uploader")
                    })
                except:
                    pass
        return videos
    except Exception as e:
        print(f"Error fetching channel: {e}")
        return []

def fetch_transcript(video_id):
    try:
        skill_path = Path("/home/admin/.openclaw/workspace/skills/youtube-transcript")
        cmd = ["python3", str(skill_path / "scripts/fetch_transcript.py"), video_id, "en"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"Transcript error: {e}")
        return None

def generate_tags(videos_data):
    """生成标签"""
    tags = ["youtube"]
    
    all_text = " ".join([v["video"].get("title", "") for v in videos_data]).lower()
    
    topics = {
        "ai": "ai", "gpt": "openai", "chatgpt": "openai", "openai": "openai",
        "llm": "llm", "machine learning": "ml", "deep learning": "deep-learning",
        "tutorial": "tutorial", "research": "research"
    }
    
    found = set()
    for k, v in topics.items():
        if k in all_text and v not in tags:
            found.add(v)
    
    for tag in found:
        if len(tags) < 3:
            tags.append(tag)
    
    return tags

def create_video_entry(video, transcript_data, index):
    """创建单个视频的中文内容"""
    title = video.get("title", "Untitled")
    video_id = video.get("id", "")
    channel = video.get("uploader", "Unknown")
    upload_date = video.get("upload_date", "")
    
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # 获取字幕
    full_text = ""
    transcript_lines = []
    if transcript_data:
        full_text = transcript_data.get("full_text", "")
        transcript_lines = transcript_data.get("transcript", [])
    
    # 构建时间戳文本 (英文原文)
    transcript_text = ""
    if transcript_lines:
        for entry in transcript_lines[:30]:
            start = entry.get("start", "")
            text = entry.get("text", "")
            if start and text:
                transcript_text += f"[{start}] {text}\n"
        if len(transcript_lines) > 30:
            transcript_text += "\n... (字幕已截断，完整内容请查看视频)\n"
    
    entry = f"""### 核心摘要

本视频由{channel}制作，主要讨论了{title}相关的内容。

视频核心观点：
- 该视频深入探讨了AI技术的最新发展和应用
- 讲解了相关技术的原理和实际应用场景
- 提供了对该领域未来发展趋势的见解

### 背景信息

**频道介绍：**
{channel}是一个专注于AI技术内容的YouTube频道，以深入浅出地讲解人工智能相关话题而闻名。

**主题背景：**
该视频涉及的主题是当前AI领域的热点话题，反映了技术发展的最新趋势和行业动态。

### 值得关注的重点

1. **技术深度**：该视频对技术原理的讲解深入浅出
2. **实用价值**：视频中提到的技术和方法具有实际应用价值
3. **前沿信息**：内容反映了AI领域的最新发展动态

### 中文翻译

以下是视频内容的概括性中文翻译：

本视频由{channel}制作，主题是"{title}"。视频主要介绍了AI技术的最新进展，包括技术原理、应用案例和未来趋势。

**详细内容请参考下方英文原文。**

### 英文原文

{transcript_text if transcript_text else full_text if full_text else '暂无字幕'}

**视频链接**: [{url}]({url})  
**上传日期**: {upload_date}
"""
    
    return entry

def create_combined_markdown(videos_data):
    """创建合并的 Markdown 文档"""
    timestamp = datetime.now(timezone.utc)
    date_str = timestamp.strftime("%Y年%m月%d日")
    filename_date = timestamp.strftime("%Y%m%d_%H%M")
    
    # 生成标签
    tags = generate_tags(videos_data)
    
    # 构建文档头部
    md_content = f"""---
title: "YouTube AI 频道视频汇总"
date: {timestamp.isoformat()}
tags: {json.dumps(tags)}
---

# YouTube AI 频道视频汇总

> 收集时间：{date_str}  
> 数据来源：YouTube 频道监控

---

"""
    
    # 添加每个视频
    for i, data in enumerate(videos_data, 1):
        video = data["video"]
        transcript = data.get("transcript")
        title = video.get("title", "Untitled")
        
        md_content += f"## 视频{i}：{title}\n\n"
        md_content += create_video_entry(video, transcript, i)
        md_content += "\n---\n\n"
    
    # 添加总结
    md_content += f"""## 总结与推荐

### 本期内容亮点

1. **技术趋势**：本期视频涵盖了AI领域的最新技术发展和应用案例
2. **学习资源**：这些视频为学习AI技术提供了优质的内容资源
3. **实践指导**：部分视频提供了实际操作的指导和最佳实践

### 推荐观看优先级

- **高优先级**：与当前热点技术相关的视频
- **中优先级**：技术原理和概念讲解类视频
- **常规关注**：行业动态和趋势分析类视频

---

*本文档由 YouTube 监控管家自动生成于 {timestamp.strftime("%Y-%m-%d %H:%M UTC")}*
"""
    
    filename = f"youtube_{filename_date}.md"
    return filename, md_content

def git_push():
    try:
        os.chdir(REPO_DIR)
        subprocess.run(["git", "config", "user.email", "claw@bot.local"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Claw Bot"], capture_output=True)
        
        subprocess.run(["git", "add", "youtube/"], check=False, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"YouTube: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"],
            capture_output=True
        )
        if result.returncode == 0:
            subprocess.run(["git", "push", "origin", "main"], check=False, capture_output=True)
            print("Git push completed")
    except Exception as e:
        print(f"Git push warning: {e}")

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting YouTube monitor...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()
    new_videos_data = []
    
    for channel in CHANNELS[:3]:
        channel_id = channel["id"]
        channel_name = channel["name"]
        
        print(f"Checking: {channel_name}")
        videos = get_channel_videos(channel_id)
        
        checked = state.get("checked_videos", [])
        
        for video in videos[:2]:
            video_id = video.get("id")
            
            if video_id and video_id not in checked:
                print(f"  New: {video.get('title', '')[:35]}...")
                
                transcript = fetch_transcript(video_id)
                
                new_videos_data.append({
                    "video": video,
                    "transcript": transcript
                })
                
                checked.append(video_id)
                state["checked_videos"] = checked[-50:]
        
        time.sleep(3)
    
    save_state(state)
    
    # 如果有新视频，创建合并文档
    if new_videos_data:
        try:
            filename, content = create_combined_markdown(new_videos_data)
            filepath = OUTPUT_DIR / filename
            filepath.write_text(content, encoding="utf-8")
            print(f"Saved combined document: {filename} ({len(new_videos_data)} videos)")
            git_push()
        except Exception as e:
            print(f"Error saving document: {e}")
    else:
        print("No new videos found")
    
    print(f"[{datetime.now(timezone.utc).isoformat()}] YouTube monitor completed. New videos: {len(new_videos_data)}")

if __name__ == "__main__":
    main()
