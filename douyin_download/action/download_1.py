from __future__ import annotations

import asyncio
import os
import shutil
import traceback
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
import re
import yaml
from f2.apps.bark.utils import ClientConfManager
from f2.apps.douyin.filter import UserPostFilter
from f2.apps.douyin.handler import main as douyin_main
# 删掉无用导入 from f2.apps import douyin

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

# 3. 扁平路径补丁（模块覆盖逻辑正确，无需改动）
def fake_create_user_folder(kwargs: dict, nickname: Union[str, int]) -> Path:
    if not isinstance(kwargs, dict):
        raise TypeError("kwargs 参数必须是字典")
    base_path = Path(kwargs.get("path", "Download"))
    user_path = base_path / str(nickname)
    resolve_user_path = user_path.resolve()
    resolve_user_path.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG PATH] 真实生成用户文件夹：{resolve_user_path}")
    return resolve_user_path

# 重点：直接替换f2库utils模块里的原函数（正确）
from f2.apps.douyin import utils
utils.create_user_folder = fake_create_user_folder
print("[PATCH] f2库原生 create_user_folder 已替换为扁平单层路径")

# ==========【新增关键补丁：禁用自动昵称重命名】==========
def fake_rename_user_folder(old_path: Path, new_nickname: str) -> Path:
    """
    屏蔽f2自动根据线上博主昵称修改本地文件夹名
    直接返回旧路径，不执行任何重命名操作
    保证：永远使用yml配置写死的custom_nickname文件夹，抖音博主改名不会动本地目录
    """
    print(f"[PATCH-SKIP-RENAME] 跳过目录重命名，保持目录名：{old_path}，线上新昵称：{new_nickname}")
    return old_path

# 覆盖库里面的改名函数，直接废掉自动改名逻辑
utils.rename_user_folder = fake_rename_user_folder
print("[PATCH] f2库原生 rename_user_folder 已禁用，不会因博主昵称变更修改本地文件夹")
# ------------------ 补丁结束 ------------------

def extract_uifid(cookie: str) -> str:
    """从 Cookie 中提取 uifid（优先 UIFID，其次 UIFID_TEMP）"""
    if not cookie:
        return ""
    # 优先匹配 UIFID
    match = re.search(r'(?:^|;\s*)UIFID=([^;]+)', cookie, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 其次匹配 UIFID_TEMP
    match = re.search(r'(?:^|;\s*)UIFID_TEMP=([^;]+)', cookie, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def load_config(config_path: str = "/Users/yangfan/PycharmProjects/DownloadStudy/douyin_download/config/config_0.yml"):
    """加载 YAML 配置文件。"""
    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}")
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg_data = yaml.safe_load(f)
    # 返回 配置内容 + 文件路径
    return cfg_data, config_path


async def download_one_user(link: str, name: str, global_kwargs: dict, interval: str = ""):
    """下载单个用户，强制使用 yml 自定义 name 作为文件夹名"""
    kwargs = {**global_kwargs, "url": link, "custom_nickname": name}

    # ========== 构建 headers（已集成 uifid + x-tt-argus）==========
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json",
    }

    cookie = global_kwargs.get("cookie", "")
    if cookie:
        headers["Cookie"] = cookie

        # 提取并添加 uifid
        uifid = extract_uifid(cookie)
        if uifid:
            headers["uifid"] = uifid
            print(f"[{name}] 已添加 uifid: {uifid[:30]}...")
        else:
            print(f"[{name}] 警告：Cookie 中未找到 UIFID / UIFID_TEMP")

        # 社区验证有效的临时方案（目前可传任意值）
        headers["x-tt-argus"] = "1"

    kwargs["headers"] = headers
    # interval 逻辑不变
    if interval:
        kwargs["interval"] = interval
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{name}] 使用自定义下载范围模式: {interval}")
    else:
        kwargs["interval"] = global_kwargs.get("interval", "")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{name}] 使用全局下载范围模式: {kwargs['interval']}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始处理用户: {name} ({link})")
    # 注释本地无效打印，以补丁输出的真实路径为准
    # print(f"保存路径 → {user_path}")

    try:
        await douyin_main(kwargs)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUCCESS] {name} 下载完成！")
        return True

    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {name} 下载异常: {e}")
        print(traceback.format_exc())
        return False


# =========【二次关键修复】修改补丁函数，优先读取我们传入的custom_nickname =========
# 重新重写补丁函数，优先使用yml自定义名称，没有才用原生昵称
def fake_create_user_folder(kwargs: dict, nickname: Union[str, int]) -> Path:
    if not isinstance(kwargs, dict):
        raise TypeError("kwargs 参数必须是字典")
    base_path = Path(kwargs.get("path", "Download"))
    # 核心：优先取我们手动传入的custom_nickname（yml自定义文件夹名）
    if "custom_nickname" in kwargs and kwargs["custom_nickname"]:
        folder_name = kwargs["custom_nickname"]
    else:
        folder_name = str(nickname)
    user_path = base_path / folder_name
    resolve_user_path = user_path.resolve()
    resolve_user_path.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG PATH] 真实生成用户文件夹：{resolve_user_path}")
    return resolve_user_path

# 重新覆盖函数（必须放在修改fake_create_user_folder之后）
utils.create_user_folder = fake_create_user_folder


async def main():
    """主函数：批量并发下载"""
    try:
        config, config_file_path = load_config()
        douyin_cfg = config["douyin"]
        users = douyin_cfg["users"]
        root_path = Path(douyin_cfg["path"])
        root_path.mkdir(parents=True, exist_ok=True)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 根目录: {root_path}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 共 {len(users)} 个用户待处理")

        semaphore = asyncio.Semaphore(3)
        results = []

        async def task_wrapper(user):
            async with semaphore:
                link = user["link"].strip()
                name = user["name"].strip()
                interval = user.get("interval", "").strip() if user.get("interval") else ""
                success_flag = await download_one_user(link, name, douyin_cfg, interval)
                if success_flag:
                    results.append(True)
                await asyncio.sleep(1)

        tasks = [task_wrapper(user) for user in users]
        await asyncio.gather(*tasks)

        success = len(results)
        print("=" * 70)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 全部任务结束！成功处理 {success}/{len(users)} 个用户")
        print("=" * 70)


        print(f"✅ 开始更新开始时间>>>>>>>>>>>>>>>")
        # 计算昨天日期 YYYY-MM-DD
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        target_interval = f"{yesterday_date}|2999-01-01"

        # 读取配置文件
        with open(config_file_path, "r", encoding="utf-8") as f:
            file_text = f.read()

        # 全局匹配替换 interval 行
        # 正则规则：同时匹配 interval: all  和  interval: 日期|2999-01-01
        match_rule = r"interval:\s*(all|\d{4}-\d{2}-\d{2}\|2999-01-01)"
        new_text = re.sub(match_rule, f"interval: {target_interval}", file_text)
        # 写入修改后内容
        with open(config_file_path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"✅ 修改完成，当前interval：{target_interval}")

    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 主程序异常退出: {e}")
        print(traceback.format_exc())
        raise
    finally:
        log_path = os.path.join("douyin_download", "logs")
        try:
            if os.path.exists(log_path):
                shutil.rmtree(log_path)
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
