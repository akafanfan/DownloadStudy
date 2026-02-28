from __future__ import annotations

import asyncio
import os
import time
import yaml
from pathlib import Path
from datetime import datetime
import traceback

from f2.apps.douyin.handler import main as douyin_main  # 关键：直接调用 handler 的 main 函数，用于处理抖音下载逻辑


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
    下载单个用户的所有作品（纯库调用）。

    参数:
    - link: 用户的分享链接。
    - name: 用户的昵称，用于创建子文件夹。
    - global_kwargs: 全局配置参数字典。

    返回:
    - True 如果下载成功，否则 False。
    """
    user_path = Path(global_kwargs["path"]) / name
    user_path.mkdir(parents=True, exist_ok=True)  # 确保用户子文件夹存在

    # 构造本次下载的参数字典：合并全局配置和当前用户的 URL
    kwargs = {**global_kwargs, "url": link}

    # 关键修复：主动传入 headers dict，避免源码中 get("headers") 为 None
    kwargs["headers"] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json",
    }

    # 如果 yaml 中有 cookie，合并到 headers["Cookie"]
    if "cookie" in kwargs:
        kwargs["headers"]["Cookie"] = kwargs["cookie"]

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始处理用户: {name} ({link})")
    print(f"保存路径 → {user_path}")

    try:
        # 核心调用：异步运行 F2 的 douyin main 函数
        await douyin_main(kwargs)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUCCESS] {name} 下载完成！")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {name} 下载异常: {e}")
        print(traceback.format_exc())
        return False


async def main():
    """
    主函数：加载配置，逐个处理用户列表，实现批量下载。
    """
    try:
        config = load_config()
        douyin_cfg = config["douyin"]
        users = douyin_cfg["users"]
        root_path = Path(douyin_cfg["path"])
        root_path.mkdir(parents=True, exist_ok=True)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 根目录: {root_path}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 共 {len(users)} 个用户待处理")

        success = 0
        for user in users:
            link = user["link"].strip()
            name = user["name"].strip()

            success_flag = await download_one_user(link, name, douyin_cfg)
            if success_flag:
                success += 1

            # 防限流：每个用户下载后等待 10 秒
            await asyncio.sleep(10)

        print("=" * 70)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 全部任务结束！成功处理 {success}/{len(users)} 个用户")
        print("=" * 70)

    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 主程序异常退出: {e}")
        print(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(main())