#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pornpali.net 多用户批量下载器
- 读取 config.yaml 中的 userlist
- 支持分页区间、按发布时间过滤、文件存在跳过
- 仅从第1页完整跑完时回写该用户的 interval 为当天 00:00:00
- 全局下载根目录 + 用户名子文件夹
"""

import re
import os
import time
import logging
import subprocess
from datetime import datetime, date
from pathlib import Path

import requests
import yaml

# ==================== 全局日志 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pornpali")

# ==================== 常量 ====================
CONFIG_FILE = Path(__file__).resolve().parent / "config.yaml"

# 全局下载根目录（所有用户都放在这个目录下，用户名作为子文件夹）
DOWNLOAD_ROOT = Path(r"D:\x下载\download")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://pornpali.net/",
    "Origin": "https://pornpali.net",
    "Accept": "application/json, text/plain, */*",
}
DEFAULT_QUALITY = "480"
MIN_FILE_SIZE = 100 * 1024  # 小于 100KB 视为无效，重新下载


# ==================== 配置读写 ====================
def load_config(path: Path = CONFIG_FILE) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(cfg: dict, path: Path = CONFIG_FILE):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    log.info(f"配置已写回: {path}")


def update_user_interval(cfg: dict, user_name: str, new_interval: str, path: Path = CONFIG_FILE):
    """只更新指定用户的 interval，并写回配置文件"""
    for user in cfg.get("userlist", []):
        if user.get("name") == user_name:
            old = user.get("interval")
            user["interval"] = new_interval
            save_config(cfg, path)
            log.info(f"[{user_name}] interval 已更新: {old} -> {new_interval}")
            return
    log.warning(f"未找到用户 {user_name}，无法更新 interval")


# ==================== API ====================
def get_actor_videos(actor_slug: str, page: int = 1) -> tuple[list[dict], str]:
    api = f"https://api.pornpali.net/pwa/actor/info/{actor_slug}"
    params = {
        "lang": "sc",
        "platform": "web",
        "limit": 25,
        "page": page,
        "token": "",
        "order": "time",
        "video_type": "short",
    }
    resp = requests.get(api, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status", {}).get("code") != 200:
        raise RuntimeError(f"接口返回错误: {data}")

    videos = data["response"].get("videos", [])
    actor_name = data["response"].get("actor_name", actor_slug)
    log.info(f"模特: {actor_name} | 第 {page} 页 | 共 {len(videos)} 个视频")
    return videos, actor_name


def get_m3u8_url(video_id: str, quality: str = "480") -> tuple[str, str]:
    api = f"https://api.pornpali.net/pwa/video/info/{video_id}"
    params = {
        "lang": "sc",
        "platform": "web",
        "limit": 25,
        "token": "",
        "video_type": "short",
    }
    resp = requests.get(api, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status", {}).get("code") != 200:
        raise RuntimeError(f"接口返回错误: {data}")

    video_urls = data["response"].get("video_urls", {})
    path = video_urls.get(quality)

    if not path:
        for q in ("480", "240"):
            if q in video_urls:
                path = video_urls[q]
                log.warning(f"没有 {quality}p，改用 {q}p")
                break
        else:
            raise RuntimeError("未找到可用画质")

    full_url = "https://api.pornpali.net" + path
    title = data["response"].get("video_title", video_id)
    return full_url, title


# ==================== 时间判断 ====================
def parse_time(s: str) -> datetime:
    """解析 'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DD'"""
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {s}")


def should_skip_by_interval(page: int, upload_date_str: str, interval_str: str) -> bool:
    """
    仅在第 1 页判断：
    视频发布时间 < interval → 跳过
    """
    if page != 1:
        return False
    if not interval_str or not upload_date_str:
        return False
    try:
        upload_dt = parse_time(upload_date_str)
        interval_dt = parse_time(interval_str)
        if upload_dt < interval_dt:
            return True
    except ValueError as e:
        log.warning(f"时间解析失败，不按 interval 跳过: {e}")
    return False


# ==================== 下载 ====================
def download_with_ffmpeg(m3u8_url: str, output_path: str):
    log.info(f" 开始下载 -> {output_path}")
    cmd = [
        "ffmpeg",
        "-headers", "Referer: https://pornpali.net/\r\nOrigin: https://pornpali.net/\r\n",
        "-user_agent", HEADERS["User-Agent"],
        "-i", m3u8_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        str(output_path),
        "-y",
        "-loglevel", "error",
        "-stats",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 下载失败，退出码: {result.returncode}")
    log.info(f" 下载完成 -> {output_path}")


def safe_filename(title: str, fallback: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", (title or "").strip())
    return name if name else fallback


# ==================== 单用户处理 ====================
def process_user(user: dict, cfg: dict) -> dict:
    name = user["name"]
    # 全局路径 + 用户名作为子文件夹
    save_path = DOWNLOAD_ROOT / name
    interval = user.get("interval") or "1970-01-01 00:00:00"
    start_page = int(user.get("model_start_page", 1))
    end_page = int(user.get("model_end_page", start_page))

    if start_page > end_page:
        log.error(f"[{name}] 起始页 {start_page} > 结束页 {end_page}，跳过该用户")
        return {"success": 0, "skipped": 0, "failed": []}

    log.info("=" * 55)
    log.info(f"开始处理用户: {name}")
    log.info(f" 保存根目录: {save_path}")
    log.info(f" interval: {interval}")
    log.info(f" 页码范围: {start_page} ~ {end_page}")
    log.info("=" * 55)

    total_success = 0
    total_skipped = 0
    total_failed = []

    for page in range(start_page, end_page + 1):
        log.info("-" * 40)
        log.info(f"[{name}] 正在处理第 {page} 页")
        log.info("-" * 40)

        try:
            videos, _ = get_actor_videos(name, page)
            if not videos:
                log.info(f"[{name}] 第 {page} 页没有视频，跳过")
                continue

            # 保存路径: DOWNLOAD_ROOT / 用户名 / 页码/
            page_dir = save_path / str(page)
            page_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"保存目录: {page_dir}")

            id_list = [str(v["video_id"]) for v in videos]
            log.info(f"ID列表: {id_list}")

            for idx, video in enumerate(videos, 1):
                video_id = str(video["video_id"])
                upload_date = video.get("video_upload_date") or video.get("video_release_date") or ""
                list_title = video.get("video_title") or video_id

                log.info(f"[{idx}/{len(videos)}] 正在处理 ID: {video_id}")

                # 第1页 + 发布时间 < interval → 跳过
                if should_skip_by_interval(page, upload_date, interval):
                    log.info(
                        f" [跳过-时间] 发布时间 {upload_date} < interval {interval} | {list_title[:40]}"
                    )
                    total_skipped += 1
                    total_success += 1
                    continue

                try:
                    m3u8_url, title = get_m3u8_url(video_id, DEFAULT_QUALITY)
                    safe_title = safe_filename(title, video_id)
                    output_path = page_dir / f"{safe_title}.mp4"

                    if output_path.exists():
                        file_size = output_path.stat().st_size
                        if file_size > MIN_FILE_SIZE:
                            log.info(
                                f" [跳过-已存在] ({file_size // 1024} KB): {safe_title}.mp4"
                            )
                            total_skipped += 1
                            total_success += 1
                            continue
                        log.warning(f" [重下] 文件过小 ({file_size} 字节)")
                        output_path.unlink(missing_ok=True)

                    log.info(f" [下载] {safe_title}")
                    download_with_ffmpeg(m3u8_url, str(output_path))
                    total_success += 1
                    time.sleep(1)

                except Exception as e:
                    log.error(f" [失败] {e}")
                    total_failed.append(video_id)

        except Exception as e:
            log.error(f"[{name}] 第 {page} 页处理失败: {e}")

    # 仅从第1页跑完时回写 interval 为当天 00:00:00
    if start_page == 1:
        today_zero = datetime.combine(date.today(), datetime.min.time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        update_user_interval(cfg, name, today_zero)
    else:
        log.info(f"[{name}] 起始页不是 1，不回写 interval")

    log.info(
        f"[{name}] 完成 | 成功: {total_success} (跳过: {total_skipped}) | 失败: {len(total_failed)}"
    )
    if total_failed:
        log.warning(f"[{name}] 失败ID: {total_failed}")

    return {
        "success": total_success,
        "skipped": total_skipped,
        "failed": total_failed,
    }


# ==================== 主入口 ====================
def main():
    log.info("=" * 55)
    log.info("pornpali.net 多用户批量下载器")
    log.info(f"全局下载目录: {DOWNLOAD_ROOT}")
    log.info("=" * 55)

    try:
        cfg = load_config()
    except Exception as e:
        log.error(f"读取配置失败: {e}")
        return

    userlist = cfg.get("userlist") or []
    if not userlist:
        log.error("config.yaml 中 userlist 为空")
        return

    log.info(f"共 {len(userlist)} 个用户待处理")

    for user in userlist:
        name = user.get("name")
        if not name:
            log.warning("跳过无 name 的配置项")
            continue
        try:
            process_user(user, cfg)
        except Exception as e:
            log.error(f"用户 {name} 处理异常: {e}")

    log.info("=" * 55)
    log.info("全部用户处理结束")


if __name__ == "__main__":
    main()