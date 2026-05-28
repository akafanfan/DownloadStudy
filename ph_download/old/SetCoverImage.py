import os
import subprocess


def set_cover_image(folder_path):
    # 设置当前文件夹路径
    output_folder = folder_path + '\\output'

    # 创建输出目录（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

        # 遍历当前文件夹下的所有.mp4文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.mp4'):
            # 获取视频文件的名称（不带扩展名）
            video_name_without_ext = os.path.splitext(filename)[0]

            # 构造同名的.PNG文件的完整路径
            png_file_path = os.path.join(folder_path, video_name_without_ext + '.png')

            # 构造.mp4文件的完整路径
            mp4_file_path = os.path.join(folder_path, filename)

            # 构造输出文件的完整路径
            output_mp4_file_path = os.path.join(output_folder, filename)

            # 检查是否存在同名的.PNG文件
            if os.path.isfile(png_file_path):
                # 使用ffmpeg设置视频封面
                command = [
                    'ffmpeg',
                    '-i', mp4_file_path,
                    '-i', png_file_path,
                    '-map', '0',
                    '-map', '1',
                    '-c', 'copy',
                    '-disposition:v:0', 'default',
                    '-disposition:a:0', 'default',
                    '-disposition:s:0', 'default',
                    '-disposition:v:1', 'attached_pic',
                    '-metadata:s:v:1', 'title="Cover"',
                    '-y', output_mp4_file_path
                ]
                subprocess.run(command, check=True)
                print(f"Set cover for {output_mp4_file_path}")
            else:
                print(f"No cover image found for {video_name_without_ext}")

    print("Done processing files.")


def main():
    txt_file = 'D:\\小工具\\xv\\Pornhub\\xreindeers'
    set_cover_image(txt_file)


if __name__ == '__main__':
    main()
