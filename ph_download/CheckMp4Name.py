import os

def check_mp4_name(txt_file, mp4_files):
    directory_path = os.path.dirname(txt_file)
    for mp4_file in mp4_files:
        tmp_name = mp4_file.rstrip('.mp4')
        with open(txt_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if tmp_name in line:
                    new_file_name = line  # 获取line行的值作为新的文件名
                    # 修改文件名
                    old_file_path = os.path.join(directory_path, mp4_file)
                    new_file_path = os.path.join(directory_path, new_file_name + '.mp4')
                    os.rename(old_file_path, new_file_path)
                else:
                    continue

def main():
    txt_file = 'D:\\小工具\\xv\\Pornhub\\xreindeers\\name.txt'
    mp4_files = [f for f in os.listdir('D:\\小工具\\xv\\Pornhub\\xreindeers') if f.endswith('.mp4')]
    check_mp4_name(txt_file, mp4_files)

if __name__ == '__main__':
    main()


