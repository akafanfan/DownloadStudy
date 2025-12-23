import subprocess
import os
import sys
import time
from datetime import datetime, timezone

# ==================== 默认配置 ====================
DEFAULT_TDL_PATH = "./tdl_MacOS_arm64/tdl"          # tdl 可执行文件路径
DEFAULT_PROXY = "socks5://127.0.0.1:7897"           # 代理
DEFAULT_CHAT_ID = 2751077071
DEFAULT_START_DATE = "2025-06-01"                   # 默认开始日期（可修改）
DEFAULT_END_DATE = "2025-12-23"                     # 默认结束日期（可修改为今天或其它）
DEFAULT_OUTPUT_DIR = "/Users/yangfan/PycharmProjects/DownloadStudy/telegram_download/mac/model/"
DEFAULT_OUTPUT_FILE = "Laosep.json"
# ===============================================

def date_to_timestamp(date_str: str) -> int:
    """
    将 yyyy-MM-dd 格式的日期转换为 Unix 时间戳（秒），假设当天 00:00:00 UTC
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # 转为 UTC 时间戳
        timestamp = int(dt.replace(tzinfo=timezone.utc).timestamp())
        return timestamp
    except ValueError:
        return None

def input_with_default(prompt: str, default: str) -> str:
    """
    带默认值的输入提示
    """
    return input(f"{prompt} [默认: {default}]: ").strip() or default

def input_date(prompt: str, default_date: str) -> int:
    """
    专门用于输入日期并转换为时间戳
    """
    while True:
        user_input = input(f"{prompt} (格式: yyyy-MM-dd) [默认: {default_date}]: ").strip()
        if not user_input:
            date_str = default_date
        else:
            date_str = user_input

        timestamp = date_to_timestamp(date_str)
        if timestamp is None:
            print("[错误] 日期格式不正确，请使用 yyyy-MM-dd 格式（如 2025-12-23）")
            continue

        # 转换为当地当天 00:00:00 的时间戳
        print(f"    → 转换结果: {date_str} -> {timestamp} (Unix 时间戳)")
        return timestamp

def export_telegram_chat(chat_id: int, start_time: int, end_time: int, output_path: str):
    print("=" * 60)
    print("[启动] Telegram 聊天记录导出工具（交互输入版）")
    print("=" * 60)

    print(f"[配置] tdl 可执行文件: {DEFAULT_TDL_PATH}")
    print(f"[配置] 代理: {DEFAULT_PROXY}")
    print(f"[配置] 聊天ID: {chat_id}")
    print(f"[配置] 时间范围: {start_time} ~ {end_time}")
    print(f"[配置] 输出文件: {output_path}")

    if not os.path.exists(DEFAULT_TDL_PATH):
        print(f"[致命错误] 未找到 tdl 可执行文件: {DEFAULT_TDL_PATH}")
        print("[提示] 请将 tdl 放在脚本同目录，或修改 DEFAULT_TDL_PATH")
        sys.exit(1)

    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(output_path):
        print(f"[警告] 输出文件已存在，将被覆盖: {output_path}")

    time_range = f"{start_time},{end_time}"

    cmd = [
        DEFAULT_TDL_PATH,
        '--proxy', DEFAULT_PROXY,
        'chat', 'export',
        '-c', str(chat_id),
        '-i', time_range,
        '--with-content',
        '-o', output_path
    ]

    print("\n[命令] 将执行以下命令:")
    print(' '.join(cmd))
    print("\n" + "-" * 60)
    print("[状态] 开始导出聊天记录，请耐心等待（可能需要较长时间）...")

    try:
        start_total = time.time()

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
            bufsize=1
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[tdl] {output.strip()}")

        stderr_output = process.stderr.read()
        return_code = process.returncode
        elapsed = time.time() - start_total

        print("-" * 60)

        if return_code == 0:
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[成功] 聊天记录导出完成！")
                print(f"[文件] {output_path}")
                print(f"[大小] {size_mb:.2f} MB")
                print(f"[统计] 总耗时: {elapsed:.2f} 秒")
            else:
                print(f"[警告] tdl 返回成功，但未生成文件: {output_path}")
        else:
            print(f"[失败] 导出失败！返回码: {return_code}")
            if stderr_output.strip():
                print("[错误输出]")
                print(stderr_output.strip())

    except KeyboardInterrupt:
        print("\n[中断] 用户手动终止程序")
        sys.exit(1)
    except Exception as e:
        print(f"[未知错误] 导出过程中异常: {str(e)}")

    print("=" * 60)
    print("[完成] Telegram 聊天记录导出任务结束")
    print("=" * 60)


def main():
    print("=" * 60)
    print("欢迎使用 Telegram 聊天记录导出工具")
    print("请按提示输入参数，回车使用默认值")
    print("=" * 60)

    # 交互输入
    chat_id_input = input_with_default("请输入聊天/频道 ID", str(DEFAULT_CHAT_ID))
    try:
        chat_id = int(chat_id_input)
    except ValueError:
        print("[错误] 聊天 ID 必须是数字！")
        sys.exit(1)

    start_time = input_date("请输入开始日期", DEFAULT_START_DATE)
    end_time = input_date("请输入结束日期", DEFAULT_END_DATE)

    if start_time >= end_time:
        print("[错误] 开始日期不能晚于或等于结束日期！")
        sys.exit(1)

    default_output_path = os.path.join(DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE)
    output_input = input_with_default("请输入输出 JSON 文件路径", default_output_path)
    output_path = os.path.abspath(output_input)

    print("\n" + "-" * 60)
    print("参数确认完成，即将开始导出...")
    time.sleep(1)

    export_telegram_chat(chat_id, start_time, end_time, output_path)


if __name__ == "__main__":
    main()