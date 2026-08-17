import os

def rename_files_by_separator(folder_path, separator):
    """
    读取指定文件夹下的所有文件，按照指定字符分割文件名，并保留后面的部分进行重命名。

    :param folder_path: 目标文件夹路径
    :param separator: 分隔字符
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在！")
        return

    # 获取文件夹下所有文件和子文件夹名称
    try:
        items = os.listdir(folder_path)
    except PermissionError:
        print(f"错误：没有权限访问文件夹 '{folder_path}'！")
        return

    for item in items:
        old_path = os.path.join(folder_path, item)

        # 仅处理文件，跳过子文件夹
        if not os.path.isfile(old_path):
            continue

        # 分离文件名和扩展名 (例如: 'test_file.txt' -> ('test_file', '.txt'))
        name, ext = os.path.splitext(item)

        # 如果文件名中包含指定的分隔符，则进行分割
        if separator in name:
            # 按分隔符分割，取最后一部分作为新名字
            # 例如: 'project_module_file' 分割符为 '_' -> 取 'file'
            new_name_part = name.split(separator)[-1]

            # 组合新的完整文件名（保留原扩展名）
            new_filename = f"{new_name_part}{ext}"
            new_path = os.path.join(folder_path, new_filename)

            # 安全检查：如果新文件名与原文件名相同，则跳过
            if old_path == new_path:
                print(f"跳过：'{item}' 分割后名字未发生变化。")
                continue

            # 安全检查：如果新文件名已存在，避免覆盖原文件
            if os.path.exists(new_path):
                print(f"警告：文件 '{item}' 重命名为 '{new_filename}' 失败，因为目标文件已存在！")
                continue

            # 执行重命名
            try:
                os.rename(old_path, new_path)
                print(f"成功：'{item}' -> '{new_filename}'")
            except Exception as e:
                print(f"错误：重命名 '{item}' 时发生异常：{e}")
        else:
            print(f"跳过：'{item}' 中未找到分隔符 '{separator}'。")

if __name__ == "__main__":
    # ===== 在这里修改你的配置 =====
    # 指定你要处理的文件夹路径（例如：Windows下用 r"D:\my_files"，Mac/Linux下用 "/Users/name/my_files"）
    TARGET_FOLDER = r"D:\Documents\GitHub\DownloadStudy\telegram_download\win\model\xmy"

    # 指定分割字符（例如：'_'、'-'、' ' 等）
    SEPARATOR = "【#汐梦瑶】"

    print(f"开始处理文件夹: {TARGET_FOLDER}")
    print(f"使用的分隔符: '{SEPARATOR}'")
    print("-" * 30)

    rename_files_by_separator(TARGET_FOLDER, SEPARATOR)

    print("-" * 30)
    print("处理完成！")
