import sys
import subprocess
import datetime
import os
tdl_path = ".\\tdl_Windows_64bit\\tdl.exe"


def execute_tdl_export(chat_id, start_time, end_time, output_file, model):
    try:
        # 构建完整的输出文件路径
        full_output_path = f"{output_file}/{model}.json"

        # 如果文件已存在，先删除它
        if os.path.exists(full_output_path):
            print(f"文件已存在，正在删除: {full_output_path}")
            os.remove(full_output_path)
        # ./tdl --proxy http://127.0.0.1:7890  chat export -c 1813595356 -i 1727712000,1758186249 -o ./jadeuly1.json
        full_command = f"{tdl_path} --proxy http://127.0.0.1:7897 chat export -c {chat_id} -i {start_time},{end_time} --with-content -o {output_file}/{model}.json "
        # 执行命令
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(f"执行命令: {full_command}")
        result = subprocess.run(full_command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8')
        # 打印输出
        print("命令执行成功:")
        # print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"执行命令时出错: {e}")
        print(f"错误输出: {e.stderr}")
    except Exception as e:
        print(f"发生未知错误: {str(e)}")

def date_to_timestamp(date_str):
    """
    将日期字符串(YYYY-MM-DD)转换为毫秒时间戳
    """
    # 将日期字符串转换为datetime对象
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    # 转换为时间戳
    return int(dt.timestamp())

if __name__ == "__main__":
    chat_id = "1494500172"
    start_time = date_to_timestamp("2025-7-1")
    end_time = int(datetime.datetime.now().timestamp())
    output_file = "model/Sexy_Yuki"
    model = "Sexy_Yuki"
    execute_tdl_export(chat_id, start_time, end_time, output_file, model)


# https://t.me/siwaheels/
# 1494500172
#Sexy_Yuki
#
#
# https://t.me/laowangshitu2/
# 1813595356
#ssrpeach