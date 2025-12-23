import subprocess
import os
import json
import sys
import time

# ==================== 默认配置 ====================
DEFAULT_TDL_PATH = "./tdl_MacOS_arm64/tdl"          # tdl 可执行文件路径
DEFAULT_PROXY = "socks5://127.0.0.1:7897"           # 代理
DEFAULT_MODEL_NAME = "YoShiE"
DEFAULT_BASE_URL = "https://t.me/laose_p"
DEFAULT_DOWNLOAD_DIR = os.path.abspath("./model/YoShiE/")
DEFAULT_JSON_PATH = os.path.abspath("./model/Laosep.json")
DEFAULT_TYPE = "/"                                  # / 或 ?comment=
TELEGRAM_GROUP_ID = 2751077071                      # 用于构造文件名，可修改
# ===============================================

def input_with_default(prompt: str, default: str) -> str:
    """带默认值的输入提示"""
    return input(f"{prompt} [默认: {default}]: ").strip() or default

def download_telegram_files(model_name: str, base_url: str, download_dir: str, json_file_path: str, url_type: str):
    """下载Telegram文件（核心函数）"""
    print("=" * 60)
    print("[启动] Telegram 文件批量下载器")
    print("=" * 60)

    print(f"[配置] 模特过滤名称: {model_name}")
    print(f"[配置] 基础URL: {base_url}")
    print(f"[配置] 下载目录: {download_dir}")
    print(f"[配置] JSON文件: {json_file_path}")
    print(f"[配置] URL模式: {url_type}")

    # 检查 tdl 是否存在
    if not os.path.exists(DEFAULT_TDL_PATH):
        print(f"[致命错误] 未找到 tdl 可执行文件: {DEFAULT_TDL_PATH}")
        print("[提示] 请将 tdl 放在脚本同目录下，或修改 DEFAULT_TDL_PATH")
        sys.exit(1)

    # 检查 JSON 文件是否存在
    if not os.path.exists(json_file_path):
        print(f"[错误] JSON 文件不存在: {json_file_path}")
        print("[提示] 请先使用导出工具生成 JSON 文件")
        sys.exit(1)

    # 读取 JSON 文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[错误] 读取 JSON 文件失败: {e}")
        sys.exit(1)

    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    print(f"[信息] 下载目录已准备: {download_dir}")

    # 获取消息列表
    messages = data.get('messages', [])
    total_messages = len(messages)
    if total_messages == 0:
        print("[信息] JSON 中没有消息，任务结束")
        return

    print(f"[信息] 总共发现 {total_messages} 条消息，开始筛选和下载")

    downloaded_count = 0
    skipped_count = 0

    for index, message in enumerate(messages, 1):
        message_id = message.get('id')
        if not message_id:
            continue

        original_file = message.get('file', '')
        if not original_file:
            print(f"[跳过] 消息ID {message_id} 无文件名")
            skipped_count += 1
            continue

        print("\n" + "=" * 50)
        print(f"[进度] {index}/{total_messages} | 消息ID: {message_id}")
        print(f"[文件] 原始文件名: {original_file}")

        # 过滤模型名称
        if model_name.lower() not in original_file.lower():  # 不区分大小写匹配
            print(f"[跳过] 文件名不包含 '{model_name}'，跳过")
            skipped_count += 1
            continue

        # 构造最终文件名
        file_name = f"{TELEGRAM_GROUP_ID}_{message_id}_{original_file}"
        full_path = os.path.join(download_dir, file_name)

        # 检查是否已存在
        if os.path.exists(full_path):
            print(f"[跳过] 文件已存在: {file_name}")
            skipped_count += 1
            continue

        # 构建完整 URL
        full_url = f"{base_url}{url_type}{message_id}"
        print(f"[信息] 下载URL: {full_url}")

        # 构建命令
        cmd = [
            DEFAULT_TDL_PATH,
            '--proxy', DEFAULT_PROXY,
            'dl',
            '-u', full_url,
            '-d', download_dir
        ]

        print("[命令] " + ' '.join(cmd))

        try:
            start_time = time.time()
            print("[状态] 正在下载...")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1
            )

            # 实时输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"[tdl] {output.strip()}")

            return_code = process.returncode
            download_time = time.time() - start_time

            if return_code == 0 and os.path.exists(full_path):
                print(f"[成功] 下载完成 → {file_name}")
                print(f"[统计] 耗时: {download_time:.2f} 秒")
                downloaded_count += 1
            else:
                error_output = process.stderr.read()
                print(f"[失败] 下载失败（返回码: {return_code}）")
                if error_output.strip():
                    print(f"[错误] {error_output.strip()}")
                skipped_count += 1

        except Exception as e:
            print(f"[错误] 下载异常: {str(e)}")
            skipped_count += 1
            continue

    print("\n" + "=" * 60)
    print("[完成] 本次下载任务结束")
    print(f"[统计] 成功下载: {downloaded_count} 个")
    print(f"[统计] 跳过/失败: {skipped_count} 个")
    print(f"[统计] 总处理: {total_messages} 条消息")
    print("=" * 60)


def main():
    print("=" * 60)
    print("欢迎使用 Telegram 文件下载工具（交互版）")
    print("请按提示输入参数，回车使用默认值")
    print("=" * 60)

    model_name = input_with_default("请输入要下载的模特名称（用于过滤）", DEFAULT_MODEL_NAME)
    base_url = input_with_default("请输入基础URL（如 https://t.me/laose_p）", DEFAULT_BASE_URL)
    download_dir = os.path.abspath(input_with_default("请输入下载目录", DEFAULT_DOWNLOAD_DIR))
    json_path = os.path.abspath(input_with_default("请输入JSON文件路径", DEFAULT_JSON_PATH))

    print("\n请选择URL模式：")
    print("  1. /          → 下载主贴文件（默认）")
    print("  2. ?comment=  → 下载评论中的文件")
    type_choice = input("请选择 (1 或 2) [默认: 1]: ").strip() or "1"
    url_type = "/" if type_choice == "1" else "?comment="

    print("\n" + "-" * 60)
    print("参数确认：")
    print(f"   模特名称 → {model_name}")
    print(f"   基础URL  → {base_url}")
    print(f"   下载目录 → {download_dir}")
    print(f"   JSON文件 → {json_path}")
    print(f"   URL模式  → {url_type}")
    print("-" * 60)
    input("\n按回车键开始下载...")

    download_telegram_files(model_name, base_url, download_dir, json_path, url_type)


if __name__ == "__main__":
    main()