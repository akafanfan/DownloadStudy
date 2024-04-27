import os

def create_file(txt_file):
    # 遍历当前文件夹下的所有文件
    for filename in os.listdir(txt_file):
        # 分离文件名和扩展名
        base_name, ext = os.path.splitext(filename)

        # 生成同名无后缀的空文件
        if ext:  # 确保文件有扩展名
            # 构造新文件的完整路径
            new_file_path = os.path.join(txt_file, base_name)

            # 创建空文件
            with open(new_file_path, 'w') as f:
                pass  # 不写入任何内容，创建空文件

            print(f"Created empty file: {new_file_path}")
        else:
            print(f"Skipping file with no extension: {filename}")

def create_file_to_mp4(txt_file):
    # 遍历当前文件夹下的所有文件
    for filename in os.listdir(txt_file):
        # 构造文件的完整路径
        file_path = os.path.join(txt_file, filename)
        # 确保是文件而不是文件夹
        if os.path.isfile(file_path):
            # 分离文件名和扩展名
            base_name, ext = os.path.splitext(filename)
            # 构造新文件的完整路径，扩展名为.mp4
            new_file_path = os.path.join(txt_file, base_name + '.mp4')
            # 重命名文件
            try:
                os.rename(file_path, new_file_path)
                print(f"Renamed file to {new_file_path}")
            except OSError as e:
                print(f"Error renaming file {file_path}: {e}")
        else:
            print(f"Skipping folder or non-file: {filename}")


def main():
    txt_file = 'D:\\小工具\\xv\\Pornhub\\xreindeers\\model'
    # create_file(txt_file)
    create_file_to_mp4(txt_file)

if __name__ == '__main__':
    main()


