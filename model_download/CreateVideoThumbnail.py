import os
import random
import subprocess
from PIL import Image

# 通过后续代码 output_directory = os.path.dirname(video_path) 获取
output_directory = ''


# 将视频封面插入到视频中生成新视频
def insert_thumbnail_into_video(video_path, combined_image_path):
    output_path = output_directory + '\\' + 'output.mp4'

    # 使用FFmpeg将封面插入视频
    ffmpeg_command = ['ffmpeg', '-i', video_path, '-i', combined_image_path, '-map', '0', '-map', '1', '-c', 'copy',
                      '-disposition:v:0', 'default', '-disposition:a:0', 'default', '-disposition:s:0', 'default',
                      '-disposition:v:1', 'attached_pic', '-metadata:s:v:1', 'title=Cover', '-y', output_path]

    subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 覆盖原始文件
    os.replace(output_path, video_path)


# 获取视频时长
def get_video_duration(video_path):
    ffprobe_command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                       'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(result.stdout)
    return duration


# 随机截取视频画面并生成封面图像
def create_video_thumbnail(video_path, i):
    print('\033[32m' + '>>>>>>开始创建第' + i + '个视频截图<<<<<<' + '\033[0m')

    thumbnail_path = output_directory + '\\' + 'thumbnail' + i + '.png'
    # 随机选择时间点
    timestamp = random.uniform(10, get_video_duration(video_path) - 1)
    # 使用FFmpeg截取画面
    ffmpeg_command = ['ffmpeg', '-i', video_path, '-ss', str(timestamp), '-vframes', '1', '-vf', 'scale=320:-1',
                      thumbnail_path]
    subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return thumbnail_path


# 创建4个不同的视频封面图像
def create_video_thumbnails(video_path):
    thumbnails = []
    for i in range(4):
        thumbnail_path = create_video_thumbnail(video_path, str(i))
        thumbnails.append(thumbnail_path)

    print('\033[32m' + '>>>>>>完成创建4个视频截图<<<<<<' + '\033[0m')
    return thumbnails


# 创建4个图片，并将它们组合拼接成一个文件
def create_combined_image(image_paths, output_path):
    print('\033[32m' + '>>>>>>开始合并生成视频封面<<<<<<' + '\033[0m')
    images = []
    for path in image_paths:
        image = Image.open(path)
        images.append(image)

    # 确定拼接图像的大小
    image_width, image_height = images[0].size
    num_images = len(images)
    num_columns = 2
    num_rows = (num_images + num_columns - 1) // num_columns
    width = num_columns * image_width
    height = num_rows * image_height

    # 创建背景图像
    background_color = (0, 0, 0)  # 黑色背景
    combined_image = Image.new('RGB', (width, height), background_color)

    # 拼接图像
    for i, image in enumerate(images):
        column = i % num_columns
        row = i // num_columns
        x_offset = column * image_width
        y_offset = row * image_height
        combined_image.paste(image, (x_offset, y_offset))

    # 保存拼接后的图像
    combined_image.save(output_path, format='PNG', quality=100)
    print('\033[34m' + '>>>>>>视频封面图像生成完毕:' + '\033[0m', output_path)

    return output_path


def create_new_video_with_thumbnails(video_path):
    # 获取视频文件所在的目录路径
    output_directory = os.path.dirname(video_path)
    # 创建4个不同的视频封面图像
    thumbnail_list = create_video_thumbnails(video_path)
    # 拼接后的图像文件路径
    output_path = os.path.join(output_directory, 'combined_image.png')
    # 创建拼接图像调用create_combined_image函数生成合并的图像
    combined_image_path = create_combined_image(thumbnail_list, output_path)
    # 将封面插入视频并生成新视频
    insert_thumbnail_into_video(video_path, combined_image_path)
    # 删除临时生成的封面图像
    for thumbnail in thumbnail_list:
        os.remove(thumbnail)
    # 删除临时生成的封面图像
    os.remove(combined_image_path)
    print('\033[34m' + '>>>>>>视频封面已生成并插入视频，生成新视频文件并覆盖原始文件:' + '\033[0m', video_path)


# # 示例用法
# if __name__ == '__main__':
#     video_path = 'D:\\Desktop\\Temp\\糖心Vlog.淫荡女仆随时供给主人中出-米胡桃.mp4'  # 视频文件路径
#     # 获取视频文件所在的目录路径
#     output_directory = os.path.dirname(video_path)
#     # 创建4个不同的视频封面图像
#     thumbnail_list = create_video_thumbnails(video_path)
#     # 拼接后的图像文件路径
#     output_path = os.path.join(output_directory, 'combined_image.png')
#     # 创建拼接图像调用create_combined_image函数生成合并的图像
#     combined_image_path = create_combined_image(thumbnail_list, output_path)
#     # 将封面插入视频并生成新视频
#     insert_thumbnail_into_video(video_path, combined_image_path)
#     # 删除临时生成的封面图像
#     for thumbnail in thumbnail_list:
#         os.remove(thumbnail)
#     # 删除临时生成的封面图像
#     os.remove(combined_image_path)
#     print('\033[34m' + '>>>>>>视频封面已生成并插入视频，生成新视频文件并覆盖原始文件:' + '\033[0m', video_path)
