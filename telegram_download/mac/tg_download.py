import subprocess
import os
import json
import sys
import time

telegram_group_id = 2751077071

def download_telegram_files(model_name,base_url, download_dir, json_file_path,type):
    """
    下载Telegram文件

    Args:
        base_url (str): Telegram基础URL
        download_dir (str): 下载目录
        json_file_path (str): JSON文件路径
    """
    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[错误] 读取JSON文件失败: {e}")
        return

    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    print(f"[信息] 下载目录已准备: {download_dir}")

    # 获取消息列表
    messages = data.get('messages', [])
    total_messages = len(messages)
    print(f"[信息] 总共需要下载 {total_messages} 个文件")

    # 遍历所有消息并下载
    for index, message in enumerate(messages, 1):
        message_id = message.get('id')
        if not message_id:
            continue
        print("\n" + "="*50)
        print(f"[进度] {index}/{total_messages}")
        print(f"[信息] 开始处理消息ID: {message_id}")
        file_name = f"{telegram_group_id}_{message_id}_{message.get('file')}"
        print(f"[信息] 开始处理消息文件名: {message.get('file')}")
        if model_name not in message.get("file", ""):
            print(f"[跳过] 消息ID {message_id} 不包含 {model_name}，跳过下载")
            continue

        # 【新增】检查文件是否已存在
        if os.path.exists(download_dir+ '/' + file_name):
            print(f"[跳过] 文件已存在: {file_name}")
            continue
        # 构建完整的URL
        full_url = f"{base_url}{type}{message_id}"
        print(f"[信息] 完整URL: {full_url}")

        # 构建命令
        cmd = [
            './tdl_MacOS_arm64/tdl',
            '--proxy', 'socks5://127.0.0.1:7897',
            'dl',
            '-u', full_url,
            '-d', download_dir
        ]

        # 打印完整命令
        print("[命令] 执行命令:")
        print(' '.join(cmd))

        try:
            start_time = time.time()
            print("[状态] 开始下载...")

            # 执行命令，实时显示输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )

            # 实时打印输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"[输出] {output.strip()}")

            # 获取返回码
            return_code = process.poll()

            # 计算下载时间
            download_time = time.time() - start_time

            if return_code == 0:
                print(f"[成功] 消息ID {message_id} 下载完成！")
                print(f"[统计] 耗时: {download_time:.2f}秒")
            else:
                error_output = process.stderr.read()
                print(f"[失败] 消息ID {message_id} 下载失败！")
                print(f"[错误] 返回码: {return_code}")
                print(f"[错误] 错误信息: {error_output}")

        except subprocess.TimeoutExpired:
            print(f"[超时] 消息ID {message_id} 下载超时！")
            continue
        except FileNotFoundError:
            print("[致命错误] 找不到tdl可执行文件，请确保路径正确")
            sys.exit(1)
        except Exception as e:
            print(f"[错误] 消息ID {message_id} 下载时发生未知错误: {str(e)}")
            continue

    print("\n" + "="*50)
    print("[完成] 所有文件下载任务已结束")

if __name__ == "__main__":
    print("="*50)
    print("[启动] Telegram文件下载器")
    print("="*50)

    # 配置参数
    MODEL_NAME = "YoShiE"
    BASE_URL = "https://t.me/laose_p"
    DOWNLOAD_DIR = os.path.abspath("./model/YoShiE/")
    JSON_FILE_PATH = os.path.abspath("model/YoShiE.json")
    TYPE = '/' # '?comment='：评论 or '/'
    print(f"[配置] 模特名称: {MODEL_NAME}")
    print(f"[配置] 下载目录: {DOWNLOAD_DIR}")
    print(f"[配置] JSON文件路径: {JSON_FILE_PATH}")
    print(f"[配置] 基础URL: {BASE_URL}")
    print(f"[配置] 模式: {TYPE}")

    # 执行下载
    download_telegram_files(MODEL_NAME,BASE_URL, DOWNLOAD_DIR, JSON_FILE_PATH,TYPE)
