import subprocess
import os
import json
import sys
import time

# ==================== 默认配置 ====================
DEFAULT_TDL_PATH = ".\\tdl_Windows_64bit\\tdl.exe"          # tdl 可执行文件路径
DEFAULT_PROXY = "http://127.0.0.1:7897"           # 代理
DEFAULT_MODEL_NAME = None
DEFAULT_BASE_URL = "https://t.me/laose_p"
DEFAULT_DOWNLOAD_DIR = os.path.abspath(".\\model\\Linxiaoting\\")
DEFAULT_JSON_PATH = os.path.abspath(".\\model\\Linxiaoting\\Linxiaoting.json")
DEFAULT_TYPE = "/"                                  # / 或 ?comment=
TELEGRAM_GROUP_ID = 2521494079                      # 用于构造文件名，可修改
# ===============================================

def input_with_default(prompt: str, default: str) -> str:
    """带默认值的输入提示"""
    return input(f"{prompt} [默认: {default}]: ").strip() or default

def download_telegram_files(model_name: str, base_url: str, group_id:str ,download_dir: str, json_file_path: str, url_type: str):
    """下载Telegram文件（核心函数）"""
    print("=" * 60)
    print("[启动] Telegram 文件批量下载器")
    print("=" * 60)

    print(f"[配置] 模特过滤名称: {model_name}")
    print(f"[配置] 基础URL: {base_url}")
    print(f"[配置] 组ID: {group_id}")
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

    #开始循环
    for index, message in enumerate(messages, 1):
        message_id = message.get('id')
        if not message_id:
            continue

        original_file = message.get('file', '')
        text = message.get('text', '')  # 获取text内容

        if not original_file:
            print(f"[跳过] 消息ID {message_id} 无文件名")
            skipped_count += 1
            continue

        print("\n" + "=" * 50)
        print(f"[进度] {index}/{total_messages} | 消息ID: {message_id}")
        print(f"[文件] 原始文件名: {original_file}")
        if text:  # 如果有text内容，也打印出来
            print(f"[文本] 内容: {text}")

        if model_name:
            # 过滤模型名称 - 检查文件名和文本内容
            file_match = model_name.lower() in original_file.lower()
            text_match = model_name.lower() in text.lower()
            if not (file_match or text_match):  # 文件名和文本都不包含model_name时才跳过
                print(f"[跳过] 文件名不包含 '{model_name}'，跳过")
                skipped_count += 1
                continue

        # 固定模板片段，原样输出 {{filenamify .FileName}}
        file_tpl = "{{filenamify .FileName}}"
        # 判断text是否为空，动态拼接中间文本部分
        if text.strip():
            template_text = f"{model_name}_{text}_{file_tpl}"
        else:
            template_text = f"{model_name}_{file_tpl}"
        full_path = os.path.join(download_dir, template_text)
        # # 检查是否已存在
        # if os.path.exists(full_path):
        #     print(f"[跳过] 文件已存在: {template_text}")
        #     skipped_count += 1
        #     continue

        # 构建完整 URL
        full_url = f"{base_url}{url_type}{message_id}"
        print(f"[信息] 下载URL: {full_url}")

        # 构建命令
        cmd = [
            DEFAULT_TDL_PATH,
            '--proxy', DEFAULT_PROXY,
            'dl',
            '--template', template_text,
            '--skip-same',
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
                bufsize=1,
                encoding='utf-8'
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
                print(f"[成功] 下载完成 → {template_text}")
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
    print("欢迎使用 Telegram 文件下载工具（批量参数版）")
    print("参数格式（逗号分隔，顺序不能变）：")
    print("模特名称,基础URL,群组ID,下载目录,JSON路径,模式(1主贴/2评论)")
    print("示例：xiaohong,https://t.me/test,2521494079,./tg_down,./save.json,1")
    print("=" * 60)

    # 读取一行输入，逗号分割
    raw_input_str = input("\n请一次性输入全部参数，逗号分隔：").strip()
    while not raw_input_str:
        raw_input_str = input("输入不能为空，请重新输入：").strip()

    # 分割参数，去除每个参数前后空格
    args_list = [arg.strip() for arg in raw_input_str.split(",")]
    if len(args_list) != 6:
        print(f"参数数量错误！需要6个参数，你输入了{len(args_list)}个")
        return

    # 按顺序拆分6个参数
    model_name, base_url, group_id, raw_download_dir, raw_json_path, type_choice = args_list

    # 处理路径绝对化
    download_dir = os.path.abspath(raw_download_dir)
    json_path = os.path.abspath(raw_json_path)

    # 转换url类型
    url_type = "/" if type_choice == "1" else "?comment="

    # 参数确认输出
    print("\n" + "-" * 60)
    print("参数确认：")
    print(f"   模特名称 → {model_name}")
    print(f"   基础URL  → {base_url}")
    print(f"   组ID      → {group_id}")
    print(f"   下载目录  → {download_dir}")
    print(f"   JSON文件  → {json_path}")
    print(f"   URL模式   → {url_type}")
    print("-" * 60)
    input("\n按回车键开始下载...")

    download_telegram_files(model_name, base_url, group_id, download_dir, json_path, url_type)



if __name__ == "__main__":
    main()