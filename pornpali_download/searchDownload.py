#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pornpali.net 搜索结果页批量下载器
输入搜索地址（或关键词）+ 页码，下载当前页所有视频
保存路径: ./download/搜索词/页码/
"""

import re
import os
import time
import logging
import subprocess
import requests
from urllib.parse import urlparse, parse_qs

# ==================== 全局日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("pornpali")
# =====================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://pornpali.net/",
    "Origin": "https://pornpali.net",
    "Accept": "application/json, text/plain, */*",
}

DOWNLOAD_ROOT = "D://x下载//download"
DEFAULT_QUALITY = "480"
MIN_FILE_SIZE = 100 * 1024  # 小于 100KB 视为无效文件，重新下载


def parse_search_input(raw: str) -> tuple[str, str]:
    """
    从搜索地址或关键词中解析出 keyword 和 video_type
    支持完整 URL 或纯关键词
    """
    raw = raw.strip()
    video_type = "short"  # 默认 short

    if raw.startswith("http"):
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query)

        # 优先从 query 参数取
        keyword = (qs.get("s") or qs.get("keyword") or [None])[0]
        if qs.get("video_type"):
            video_type = qs["video_type"][0]

        # 如果 query 里没有，尝试从 path 里取 /search/xxx
        if not keyword:
            m = re.search(r"/search/([^/?#]+)", parsed.path)
            if m:
                keyword = m.group(1)

        if not keyword:
            raise ValueError("无法从地址中解析出搜索关键词")
    else:
        keyword = raw

    return keyword, video_type


def get_search_videos(keyword: str, page: int = 1, video_type: str = "short") -> list[dict]:
    """获取搜索结果指定页的视频列表"""
    api = "https://api.pornpali.net/pwa/videos/short/keyword"
    params = {
        "lang": "sc",
        "platform": "web",
        "limit": 25,
        "page": page,
        "video_type": video_type,
        "s": keyword,
        "token": "",
        "keyword": keyword,
        "order": "relevance",
    }
    resp = requests.get(api, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status", {}).get("code") != 200:
        raise RuntimeError(f"接口返回错误: {data}")

    videos = data["response"].get("videos", [])
    total = data["response"].get("total_results", 0)
    log.info(f"搜索词: {keyword} | 第 {page} 页 | 本页 {len(videos)} 个视频 | 总计约 {total}")
    return videos


def get_m3u8_url(video_id: str, quality: str = "480") -> tuple[str, str]:
    api = f"https://api.pornpali.net/pwa/video/info/{video_id}"
    params = {
        "lang": "sc",
        "platform": "web",
        "limit": 25,
        "token": "",
        "video_type": "short"
    }
    resp = requests.get(api, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status", {}).get("code") != 200:
        raise RuntimeError(f"接口返回错误: {data}")

    video_urls = data["response"].get("video_urls", {})
    path = video_urls.get(quality)

    if not path:
        for q in ["480", "240"]:
            if q in video_urls:
                path = video_urls[q]
                log.warning(f"没有 {quality}p，改用 {q}p")
                break
        else:
            raise RuntimeError("未找到可用画质")

    full_url = "https://api.pornpali.net" + path
    title = data["response"].get("video_title", video_id)
    return full_url, title


def download_with_ffmpeg(m3u8_url: str, output_path: str):
    """使用 ffmpeg 下载，并保留进度输出"""
    log.info(f" 开始下载 -> {output_path}")

    cmd = [
        "ffmpeg",
        "-headers", "Referer: https://pornpali.net/\r\nOrigin: https://pornpali.net/\r\n",
        "-user_agent", HEADERS["User-Agent"],
        "-i", m3u8_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_path,
        "-y",
        "-loglevel", "info",
        "-stats",
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 下载失败，退出码: {result.returncode}")

    log.info(f" 下载完成 -> {output_path}")


def main():
    raw = input("请输入搜索地址或关键词 (例如 https://pornpali.net/search/newyearst6?video_type=short&s=newyearst6): ").strip()
    page = int(input("请输入页码 (默认1): ").strip() or "1")

    try:
        keyword, video_type = parse_search_input(raw)
    except ValueError as e:
        log.error(str(e))
        return

    log.info(f"解析结果 → 关键词: {keyword} | video_type: {video_type} | 页码: {page}")

    # 安全目录名
    safe_keyword = re.sub(r'[\\/:*?"<>|]', '_', keyword).strip() or "search"
    save_dir = os.path.join(DOWNLOAD_ROOT, safe_keyword, str(page))
    os.makedirs(save_dir, exist_ok=True)
    log.info(f"保存目录: {save_dir}")

    try:
        videos = get_search_videos(keyword, page, video_type)
        if not videos:
            log.info("本页没有视频，结束")
            return

        id_list = [v["video_id"] for v in videos]
        log.info(f"ID列表: {id_list}")

        success = 0
        skipped = 0
        failed = []

        for idx, video_id in enumerate(id_list, 1):
            log.info(f"[{idx}/{len(id_list)}] 正在处理 ID: {video_id}")
            try:
                m3u8_url, title = get_m3u8_url(video_id, DEFAULT_QUALITY)
                safe_title = re.sub(r'[\\/:*?"<>|]', '_', title).strip()
                if not safe_title:
                    safe_title = video_id
                output_path = os.path.join(save_dir, f"{safe_title}.mp4")

                # 文件存在判断
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    if file_size > MIN_FILE_SIZE:
                        log.info(f" [跳过] 文件已存在 ({file_size // 1024} KB): {safe_title}.mp4")
                        skipped += 1
                        success += 1
                        continue
                    else:
                        log.warning(f" [重下] 文件过小 ({file_size} 字节)，重新下载")
                        os.remove(output_path)

                log.info(f" [下载] {safe_title}")
                download_with_ffmpeg(m3u8_url, output_path)
                log.info(f" [完成] {output_path}")
                success += 1
                time.sleep(3)

            except Exception as e:
                log.error(f" [失败] {e}")
                failed.append(video_id)

        log.info("=" * 50)
        log.info(f"本页完成 | 成功: {success}/{len(id_list)} (跳过: {skipped})")
        if failed:
            log.warning(f"失败的ID: {failed}")

    except Exception as e:
        log.error(f"处理失败: {e}")


if __name__ == "__main__":
    main()