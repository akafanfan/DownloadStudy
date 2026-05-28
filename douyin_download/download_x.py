from __future__ import annotations

import asyncio
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Union

import yaml
from f2.apps.bark.utils import ClientConfManager
from f2.apps.douyin.filter import UserPostFilter
# 先导入所有需要的 f2 模块
from f2.apps.twitter.handler import main as twitter_main
from f2.apps.douyin.utils import create_user_folder  # ← 新增导入这个
# 导入 f2 twitter 主函数（关键！）



# ------------------ 补丁区 ------------------

# 1. 跳过 live.mp4
def fake_images_video(self):
    return []


UserPostFilter.images_video = property(fake_images_video)
print("[PATCH] UserPostFilter.images_video 已替换为 []")


# 2. 禁用 Bark
def fake_enable_bark(cls):
    return False


ClientConfManager.enable_bark = classmethod(fake_enable_bark)
print("[PATCH] Bark 已强制禁用")

# 3. 扁平路径（最关键修改在这里）
def fake_create_user_folder(kwargs: dict, nickname: Union[str, int]) -> Path:
    if not isinstance(kwargs, dict):
        raise TypeError("kwargs 参数必须是字典")
    # 创建基础路径
    base_path = Path(kwargs.get("path", "Download"))
    # 添加下载模式和用户名
    user_path = (
        base_path / str(nickname)
    )
    # 获取绝对路径并确保它存在
    resolve_user_path = user_path.resolve()
    # 创建目录
    resolve_user_path.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG PATH] 用户文件夹：{resolve_user_path}")
    return resolve_user_path

create_user_folder = fake_create_user_folder
print("[PATCH] create_or_rename_user_folder 已替换为扁平路径版本")


# ------------------ 补丁结束 ------------------



def load_config(config_path: str = "config.yml"):
    """
    加载 YAML 配置文件。
    """
    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}")
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



async def download_one_user(link: str, name: str, global_kwargs: dict):
    """
    下载单个用户的所有作品（通过调用库的 main 函数，但已通过补丁跳过 live.mp4）
    """
    user_path = Path(global_kwargs["path"]) / name

    # 路径直接用配置里的 path
    # user_path = Path(global_kwargs["path"])
    user_path.mkdir(parents=True, exist_ok=True)

    # 合并所有配置：全局配置 + 当前用户链接
    kwargs = {**global_kwargs, "url": link}

    # ===================== 关键：直接使用你配置里的 headers =====================
    # 自动带上 X-Csrf-Token、User-Agent、Referer
    kwargs["headers"] = global_kwargs["headers"]

    # 自动把配置里的 cookie 塞进 headers（必须）
    if "cookie" in global_kwargs and global_kwargs["cookie"]:
        kwargs["headers"]["Cookie"] = global_kwargs["cookie"]
    # ==========================================================================

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始处理: {name}")
    print(f"链接 → {link}")
    print(f"保存路径 → {user_path}")

    try:
        # 核心调用：使用 f2 的 douyin main 函数（已打补丁，不会下 live.mp4）
        await twitter_main(kwargs)
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
        douyin_cfg = config["twitter"]
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

            # 防限流：每个用户下载后等待一段时间（可根据实际情况调整）
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