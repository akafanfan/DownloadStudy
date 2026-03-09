import json
import subprocess
import os
import sys
import time

tdl_path = ".\\tdl_Windows_64bit\\tdl.exe"


def findIdByJson(output_file, model):
    # 存储符合条件的id列表
    matched_ids = []

    try:
        # 打开并读取JSON文件
        with open(output_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

            # 检查是否存在'messages'字段
            if 'messages' in data and isinstance(data['messages'], list):
                # 遍历所有消息
                for message in data['messages']:
                    # 检查是否包含所需的text
                    if ('text' in message and
                            isinstance(message['text'], str) and
                            model in message['text']):
                        # 去除text中的换行符和制表符
                        cleaned_text = message['text'].replace('\n', ' ').replace('\t', ' ')
                        # 添加包含id和cleaned_text的内容到结果列表
                        matched_ids.append({
                            'id': message['id'],
                            'text': cleaned_text
                        })

    except FileNotFoundError:
        print(f"错误：文件 {output_file} 未找到")
    except json.JSONDecodeError:
        print("错误：文件内容不是有效的JSON格式")
    except Exception as e:
        print(f"发生未知错误：{str(e)}")

    return matched_ids


def execute_download_commands(matched_ids, base_url, download_dir):
    # 检查文件和目录是否存在
    if not os.path.exists(tdl_path):
        print(f"错误: 找不到tdl文件 {tdl_path}")
        return
    if not os.path.exists(download_dir):
        print(f"错误: 找不到下载目录 {download_dir}")
        return

    # 遍历 matched_ids
    for index, item in enumerate(matched_ids, 1):
        # 获取当前 id 和 text
        current_id = str(item['id'])
        text_content = item['text'].replace('\n', ' ').replace('\t', ' ').replace(' ', '')
        new_filename = f"{len(matched_ids) - index + 1}.{text_content}"
        full_command = f"{tdl_path} --proxy http://127.0.0.1:7897 dl -u {base_url}/{current_id} -d {download_dir} --pool 16 --debug"
        try:
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
            # 打印完整命令

            # 在下载目录中查找包含当前ID的文件
            for file in os.listdir(download_dir):
                if current_id in file:
                    # 获取文件扩展名
                    file_ext = os.path.splitext(file)[1]
                    # 构造完整的新文件路径
                    new_filepath = os.path.join(download_dir, f"{new_filename}{file_ext}")
                    # 重命名文件
                    try:
                        os.rename(os.path.join(download_dir, file), new_filepath)
                        print(f"文件已重命名为: {new_filename}{file_ext}")
                        break  # 找到并重命名文件后跳出循环
                    except Exception as e:
                        print(f"重命名文件时出错: {str(e)}")

        except subprocess.CalledProcessError as e:
            print(f"执行命令时出错: {e}")
            print(f"错误输出: {e.stderr}")
        except Exception as e:
            print(f"发生未知错误: {str(e)}")


if __name__ == '__main__':
    # 调用函数并打印结果
    result_ids = findIdByJson("model\\Sexy_Yuki\\Sexy_Yuki.json", "Sexy_Yuki")
    print("解析数量:", len(result_ids))
    print("匹配的ID列表:", result_ids)
    execute_download_commands(result_ids, "https://t.me/laose_p", "model/Sexy_Yuki")
