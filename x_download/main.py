from __future__ import annotations
import asyncio
import os
import yaml
from pathlib import Path
from datetime import datetime
import traceback
import aiohttp
from urllib.parse import urlparse
from f2.apps.twitter.handler import TwitterHandler
from f2.apps.twitter.utils import UniqueIdFetcher

def load_config(config_path: str = "config.yml"):
    """
    加载 YAML 配置文件。
    参数:
    - config_path: 配置文件的路径，默认是 "config.yml"。
    返回:
    - 解析后的配置字典。
    """
    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}")
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def download_one_user(link: str, name: str, global_kwargs: dict):
    """
    下载单个用户的所有媒体（照片和视频）。
    参数:
    - link: 用户的链接（如 https://x.com/username 或 https://x.com/username/media）。
    - name: 用户的昵称（可选，若为空则从链接提取）。
    - global_kwargs: 全局配置参数字典。
    返回:
    - True 如果下载成功，否则 False。
    """
    # 从链接提取用户名，如果 name 为空
    if not name:
        parsed = urlparse(link)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts[-1] == 'media' and len(path_parts) >= 2:
            name = path_parts[-2]  # 处理 /username/media 格式
        else:
            name = path_parts[-1]  # 处理 /username 格式
        if not name:
            print(f"[ERROR] 无法从链接 {link} 提取用户名")
            return False

    # 确定下载路径
    root_path = Path(global_kwargs["path"])
    if global_kwargs.get("folderize", False):
        user_path = root_path / name
    else:
        user_path = root_path
    user_path.mkdir(parents=True, exist_ok=True)

    # 构造 kwargs
    kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
            "Referer": "https://www.x.com/",
            "Accept": "*/*",
        },
        "proxies": {"http://": None, "https://": None},
        "cookie": global_kwargs.get("cookie", ""),
        "timeout": global_kwargs.get("timeout", 10),
    }

    # 获取用户 ID
    try:
        user_id = await UniqueIdFetcher(kwargs).get_unique_id(link)
        if not user_id:
            print(f"[ERROR] 无法获取用户 {name} 的 ID")
            return False
    except Exception as e:
        print(f"[ERROR] 获取用户 ID 时出错: {e}")
        return False

    try:
        handler = TwitterHandler(kwargs)
        media_count = 0
        max_cursor = ""
        page_counts = global_kwargs.get("page_counts", 20)
        max_counts = global_kwargs.get("max_counts", 0)  # 0 表示无限制？
        interval = global_kwargs.get("interval", "all")
        naming_template = global_kwargs.get("naming", "{created_at}_{text}_{tweet_id}")
        mode = global_kwargs.get("mode", "one")

        async with aiohttp.ClientSession(headers=kwargs["headers"]) as session:
            while True:
                async for tweet_list in handler.fetch_post_tweet(
                    userId=user_id,
                    page_counts=1,  # 逐页处理以控制
                    max_cursor=max_cursor,
                    max_counts=max_counts or 20,
                ):
                    # 假设 tweet_list 是 tweets 的列表，每个 tweet 是 dict
                    for tweet in tweet_list:  # 需调整根据实际 tweet_list 结构
                        if 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
                            for media in tweet['extended_entities']['media']:
                                created_at = tweet['created_at'].replace(' ', '_').replace(':', '-')
                                text = tweet.get('full_text', '')[:50].replace(' ', '_').replace('\n', '')  # 简化
                                tweet_id = tweet['id_str']

                                # 应用 naming template
                                file_name_base = naming_template.format(
                                    created_at=created_at,
                                    desc=text,
                                    aweme_id=tweet_id,  # 兼容 aweme_id 作为 tweet_id
                                    tweet_id=tweet_id,
                                    # 可添加更多占位
                                )

                                if media['type'] == 'photo':
                                    url = media['media_url_https']
                                    ext = url.split('.')[-1]
                                    file_path = user_path / f"{file_name_base}.{ext}"
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            with open(file_path, 'wb') as f:
                                                f.write(await resp.read())
                                    media_count += 1
                                elif media['type'] in ['video', 'animated_gif']:
                                    variants = media['video_info']['variants']
                                    best_variant = max(variants, key=lambda v: v.get('bitrate', 0))
                                    url = best_variant['url']
                                    ext = 'mp4' if media['type'] == 'video' else 'gif'
                                    file_path = user_path / f"{file_name_base}.{ext}"
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            with open(file_path, 'wb') as f:
                                                f.write(await resp.read())
                                    media_count += 1

                # 更新 cursor 以分页
                if 'next_cursor' in tweet_list.metadata:  # 假设有 metadata
                    max_cursor = tweet_list.metadata['next_cursor']
                else:
                    break  # 无更多页

                if page_counts > 0:
                    page_counts -= 1
                if page_counts == 0:
                    break

                await asyncio.sleep(5)  # 防限流

        print(f"[INFO] 用户 {name} 下载完成，共 {media_count} 个媒体文件")
        return True
    except Exception as e:
        print(f"[ERROR] 下载用户 {name} 时出错: {e}")
        print(traceback.format_exc())
        return False

async def main():
    """
    主函数：加载配置，逐个处理用户列表，实现批量下载。
    """
    try:
        config = load_config()
        twitter_cfg = config["twitter"]
        users = twitter_cfg["users"]
        root_path = Path(twitter_cfg["path"])
        root_path.mkdir(parents=True, exist_ok=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 根目录: {root_path}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 共 {len(users)} 个用户待处理")
        success = 0
        max_connections = twitter_cfg.get("max_connections", 5)
        semaphore = asyncio.Semaphore(max_connections)
        tasks = []
        for user in users:
            link = user["link"].strip()
            name = user.get("name", "").strip()
            async def wrapped_download():
                async with semaphore:
                    return await download_one_user(link, name, twitter_cfg)
            tasks.append(wrapped_download())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if not isinstance(result, Exception) and result:
                success += 1

        print("=" * 70)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 全部任务结束！成功处理 {success}/{len(users)} 个用户")
        print("=" * 70)
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 主程序异常退出: {e}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(main())