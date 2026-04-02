#!/usr/bin/env python3
"""
AI News Collector - 每8小时收集AI领域最新新闻
输出到: /home/admin/projects/claw-inbox/ai_news/
所有内容合并为一个中文汇总文档
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# 配置
OUTPUT_DIR = Path("/home/admin/projects/claw-inbox/ai_news")
REPO_DIR = Path("/home/admin/projects/claw-inbox")

# 读取 Tavily API Key
TAVILY_API_KEY = ""
try:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        TAVILY_API_KEY = config.get("plugins", {}).get("entries", {}).get("tavily", {}).get("config", {}).get("webSearch", {}).get("apiKey", "")
except:
    pass

# 搜索关键词 (英文搜索)
SEARCH_QUERIES = [
    "AI artificial intelligence latest breakthrough 2025",
    "OpenAI GPT-5 ChatGPT new model announcement",
    "Google Gemini 2.0 AI updates features",
    "Anthropic Claude 3.5 Sonnet AI capabilities",
    "Meta Llama 3 AI model release",
    "Microsoft Copilot AI integration news",
    "AI agent autonomous systems research",
    "generative AI enterprise adoption trends"
]

def run_tavily_search(query, max_results=5):
    """调用 Tavily API 搜索"""
    if not TAVILY_API_KEY:
        return None
    
    try:
        import urllib.request
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        data = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "topic": "news",
            "max_results": max_results,
            "time_range": "day",
            "include_answer": True,
            "include_raw_content": True
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Search error: {e}")
        return None

def generate_tags(articles):
    """生成标签，最多3个"""
    tags = ["ai-news"]
    
    all_text = " ".join([a.get("title", "") + " " + a.get("content", "") for a in articles]).lower()
    
    companies = {
        "openai": "openai", "gpt": "openai", "chatgpt": "openai",
        "google": "google", "gemini": "google",
        "anthropic": "anthropic", "claude": "anthropic",
        "meta": "meta", "llama": "meta",
        "microsoft": "microsoft", "copilot": "microsoft",
        "deepseek": "deepseek", "nvidia": "nvidia"
    }
    
    found = set()
    for k, v in companies.items():
        if k in all_text and v not in tags:
            found.add(v)
    
    for tag in found:
        if len(tags) < 3:
            tags.append(tag)
    
    return tags

def create_news_entry(article, index):
    """创建单条新闻的中文内容"""
    title = article.get("title", "Untitled")
    url = article.get("url", "")
    content = article.get("content", "")
    raw_content = article.get("raw_content", "")
    answer = article.get("answer", "")
    published = article.get("published_date", "")
    
    full_content = raw_content if raw_content else content
    
    # 核心摘要
    if answer:
        core = f"本文讨论了{title}相关的最新动态。{answer[:300]}"
    else:
        core = f"本文报道了{title}。{full_content[:250]}"
    
    entry = f"""### 核心摘要

{core}

### 背景信息

该新闻涉及人工智能领域的最新发展。随着AI技术的快速发展，各大科技公司不断推出新的模型和功能。

**事件来龙去脉：**
- 该报道聚焦于{title}的最新进展
- 反映了当前AI行业的技术趋势和市场动态
- 相关技术可能对行业应用产生深远影响

### 值得关注的重点

- 该新闻反映了AI领域的最新技术进展，值得关注其技术细节
- 可能对相关公司的市场地位和商业模式产生重要影响
- 建议持续关注相关技术的后续更新和应用落地情况

**来源**: [{url}]({url})
"""
    
    return entry

def create_combined_markdown(articles):
    """创建合并的 Markdown 文档"""
    timestamp = datetime.now(timezone.utc)
    date_str = timestamp.strftime("%Y年%m月%d日")
    filename_date = timestamp.strftime("%Y%m%d_%H%M")
    
    # 生成标签
    tags = generate_tags(articles)
    
    # 构建文档头部
    md_content = f"""---
title: "AI 领域最新新闻汇总"
date: {timestamp.isoformat()}
tags: {json.dumps(tags)}
---

# AI 领域最新新闻汇总

> 收集时间：{date_str}  
> 数据来源：Tavily 搜索

---

"""
    
    # 添加每条新闻
    for i, article in enumerate(articles[:5], 1):  # 最多5条
        title = article.get("title", "Untitled")
        md_content += f"## 新闻{i}：{title}\n\n"
        md_content += create_news_entry(article, i)
        md_content += "\n---\n\n"
    
    # 添加总结
    md_content += f"""## 总结与趋势洞察

### 当前 AI 领域主要趋势

1. **技术迭代加速**：AI模型更新速度持续加快，竞争日趋激烈
2. **应用场景扩展**：从文本生成到多模态应用，AI能力边界不断拓展
3. **商业化推进**：各大厂商加速AI技术的商业落地和变现

### 值得持续关注的方向

- **大模型能力演进**：关注各大厂商旗舰模型的性能提升
- **Agentic AI发展**：AI自主执行复杂任务的能力
- **多模态融合**：文本、图像、音频、视频的统一处理能力
- **行业应用落地**：AI在专业领域的实际应用案例

---

*本文档由 AI 新闻收集管家自动生成于 {timestamp.strftime("%Y-%m-%d %H:%M UTC")}*
"""
    
    filename = f"ai_news_{filename_date}.md"
    return filename, md_content

def git_push():
    """推送更改到 GitHub"""
    try:
        os.chdir(REPO_DIR)
        subprocess.run(["git", "config", "user.email", "claw@bot.local"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Claw Bot"], capture_output=True)
        
        subprocess.run(["git", "add", "ai_news/"], check=False, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"AI News: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"],
            capture_output=True
        )
        if result.returncode == 0:
            subprocess.run(["git", "push", "origin", "main"], check=False, capture_output=True)
            print("Git push completed")
    except Exception as e:
        print(f"Git push warning: {e}")

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting AI News collection...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not TAVILY_API_KEY:
        print("ERROR: TAVILY_API_KEY not found")
        sys.exit(1)
    
    all_articles = []
    
    for i, query in enumerate(SEARCH_QUERIES[:3]):
        print(f"Searching: {query}")
        result = run_tavily_search(query, max_results=3)
        if result and "results" in result:
            all_articles.extend(result["results"])
    
    # 去重
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    
    print(f"Found {len(unique_articles)} unique articles")
    
    if unique_articles:
        try:
            filename, content = create_combined_markdown(unique_articles)
            filepath = OUTPUT_DIR / filename
            filepath.write_text(content, encoding="utf-8")
            print(f"Saved combined document: {filename}")
        except Exception as e:
            print(f"Error saving document: {e}")
    
    git_push()
    print(f"[{datetime.now(timezone.utc).isoformat()}] AI News collection completed")

if __name__ == "__main__":
    main()
