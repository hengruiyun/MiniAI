#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的搜索接口，提取server.py的核心搜索功能
"""

import asyncio
import os
import sys
import json
import logging
from html import escape

import httpx
from bs4 import BeautifulSoup

# 配置
API_URL = os.environ.get("SEARXNG_API_URL", "https://searx.bndkt.io")
COOKIE = os.environ.get("SEARXNG_COOKIE", "")
USER_AGENT = os.environ.get(
    "SEARXNG_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
)
REQUEST_TIMEOUT = int(os.environ.get("SEARXNG_REQUEST_TIMEOUT", "10"))

HEADERS = {
    "User-Agent": USER_AGENT,
    "content-type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Cookie": COOKIE,
}

async def perform_search(
    query: str,
    category: str = "general",
    language: str = "auto",
    safe_search: int = 1,
    time_range: str = "",
    output_format: str = "html",
) -> str:
    """
    执行搜索并返回结果
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query parameter is required and must be a string")

    if not API_URL:
        raise ValueError("SEARXNG_API_URL environment variable is not set")

    params = {
        "q": query,
        "language": language,
        "time_range": time_range,
        "safe_search": safe_search,
        "categories": category,
        "theme": "simple",
        "format": "html" if "searx.bndkt.io" in API_URL else "json",
    }

    api_url = API_URL
    if api_url.endswith("/"):
        api_url = api_url[:-1]

    search_url = f"{api_url}/search"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                search_url, data=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            if params["format"] == "json":
                data = response.json()
                return parse_json_response(data, output_format, category)
            else:
                data = response.text
                return parse_html_response(data, output_format, category)

    except httpx.HTTPError as e:
        raise RuntimeError(f"HTTP Error: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON decode failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

def parse_html_response(data: str, output_format: str, category: str) -> str:
    """
    解析HTML响应数据
    """
    # 检查是否为无结果页面
    if """<div class="dialog-error-block" role="alert">""" in data:
        return "未找到相关结果。您可以尝试：\n- 使用不同的关键词\n- 简化搜索查询\n- 检查拼写错误"

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(data, "html.parser")

    # 找到 id="urls" 的 div
    urls_div = soup.find("div", id="urls")
    if not urls_div:
        return "未找到搜索结果"

    # 提取所有 article 标签
    articles = urls_div.find_all("article", class_="result")

    if not articles:
        return "未找到搜索结果"

    # 解析通用搜索结果
    return parse_general_html_results(articles, output_format)

def parse_general_html_results(articles: list, output_format: str) -> str:
    """
    解析通用搜索结果
    """
    parsed_results = []

    for article in articles:
        # 提取标题和链接 - 查找 h3 > a 结构
        title_link = article.find("h3")
        if title_link:
            link_tag = title_link.find("a", href=True)
            if link_tag:
                url = link_tag["href"]
                title = link_tag.get_text(strip=True)
            else:
                continue
        else:
            continue

        # 提取描述/内容 - 查找 p.content
        description = ""
        content_p = article.find("p", class_="content")
        if content_p:
            description = content_p.get_text(strip=True)

        # 提取引擎信息
        engines = []
        engines_div = article.find("div", class_="engines")
        if engines_div:
            engine_spans = engines_div.find_all("span")
            engines = [
                span.get_text(strip=True)
                for span in engine_spans
                if span.get_text(strip=True)
            ]

        if output_format == "json":
            result_data = {
                "title": escape(title),
                "url": escape(url),
                "description": escape(description),
            }
            if engines:
                result_data["engines"] = engines
            parsed_results.append(result_data)
        else:
            # HTML格式输出
            engines_info = (
                f"<small>搜索引擎: {', '.join(engines)}</small><br>" if engines else ""
            )
            html = (
                f"<div style='margin-bottom: 1.5em; border-left: 3px solid #007acc; padding-left: 15px;'>"
                f"<h3><a href='{escape(url)}' target='_blank' style='color: #007acc; text-decoration: none;'>{escape(title)}</a></h3>"
                f"<p style='color: #666; margin: 5px 0;'>{escape(description)}</p>"
                f"{engines_info}"
                f"<small style='color: #999;'>{escape(url)}</small>"
                f"</div>"
            )
            parsed_results.append(html)

    if output_format == "json":
        return json.dumps(parsed_results, ensure_ascii=False, indent=2)
    else:
        return "\n".join(parsed_results)

def parse_json_response(data: dict, output_format: str, category: str) -> str:
    """
    解析JSON响应数据
    """
    if "results" not in data or not data["results"]:
        return "未找到相关结果"

    parsed_results = []
    
    for result in data["results"]:
        title = result.get("title", "")
        url = result.get("url", "")
        description = result.get("content", "")
        engines = result.get("engines", [])

        if output_format == "json":
            result_data = {
                "title": escape(title),
                "url": escape(url),
                "description": escape(description),
            }
            if engines:
                result_data["engines"] = engines
            parsed_results.append(result_data)
        else:
            # HTML格式输出
            engines_info = (
                f"<small>搜索引擎: {', '.join(engines)}</small><br>" if engines else ""
            )
            html = (
                f"<div style='margin-bottom: 1.5em; border-left: 3px solid #007acc; padding-left: 15px;'>"
                f"<h3><a href='{escape(url)}' target='_blank' style='color: #007acc; text-decoration: none;'>{escape(title)}</a></h3>"
                f"<p style='color: #666; margin: 5px 0;'>{escape(description)}</p>"
                f"{engines_info}"
                f"<small style='color: #999;'>{escape(url)}</small>"
                f"</div>"
            )
            parsed_results.append(html)

    if output_format == "json":
        return json.dumps(parsed_results, ensure_ascii=False, indent=2)
    else:
        return "\n".join(parsed_results)

async def main():
    """
    命令行接口
    """
    if len(sys.argv) < 2:
        print("用法: python simple_search.py <搜索查询>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        result = await perform_search(query)
        print(result)
    except Exception as e:
        print(f"搜索失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
