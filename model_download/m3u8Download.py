# 这是一个下载m3u8 视频资源的脚本   无指定序号版，根据资源数组排序 非ffmpeg合并版
import os
import re
import m3u8
import time
import requests
import concurrent.futures
from Crypto.Cipher import AES
from concurrent.futures import as_completed
import glob
import shutil
import threading
import datetime

from model_download.CreateVideoThumbnail import create_new_video_with_thumbnails

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'Zh-CN, zh;q=0.9, en-gb;q=0.8, en;q=0.7'
}

path = './download/'


# 红色：\033[31m
# 蓝色：\033[34m
# 绿色：\033[32m
# \033[0m

# 判断是否为网站地址
def reurl(url):
    pattern = re.compile(r'^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+')
    m = pattern.search(url)
    if m is None:
        return False
    else:
        return True


# 获取密钥（针对有些m3u8文件中的视频需要key去解密下载的视频）
def get_key(key_str, url):
    keyinfo = str(key_str)
    method_pos = keyinfo.find('METHOD')
    comma_pos = keyinfo.find(",")
    method = keyinfo[method_pos:comma_pos].split('=')[1]
    uri_pos = keyinfo.find("URI")
    quotation_mark_pos = keyinfo.rfind('"')
    key_url = keyinfo[uri_pos:quotation_mark_pos].split('"')[1]
    if not reurl(key_url):
        key_url = url.rsplit("/", 1)[0] + "/" + key_url
    res = requests.get(key_url, headers=headers)
    key = res.content
    print(method)
    print(key.decode('utf-8', 'ignore'))
    return method, key


# 下载文件
# down_url:ts文件地址
# url:*.m3u8文件地址
# decrypt:是否加密
# down_path:下载地址
# key:密钥
def download(down_url, url, decrypt, down_path, key):
    if not reurl(down_url):
        if len(down_url.rsplit("/", 1)) > 1:
            filename = down_url.rsplit("/", 1)[1]
        else:
            filename = down_url
        down_url = url.rsplit("/", 1)[0] + "/" + down_url
    else:
        filename = down_url.rsplit("/", 1)[1]
    down_ts_path = down_path + "/{0}".format(filename)
    if os.path.exists(down_ts_path):
        print('\033[31m' + '文件 ' + filename + ' 已经存在，跳过下载.' + '\033[0m')
    else:
        try:
            res = requests.get(down_url, stream=True, verify=False, headers=headers)
            print('\033[32m' + '正在下载资源：' + filename + '' + '\033[0m')
        except Exception as e:
            print('\033[31m' + 'requests error:' + '\033[0m', e)
            return
        if decrypt:
            cryptor = AES.new(key, AES.MODE_CBC, key)

        with open(down_ts_path, "wb+") as file:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    if decrypt:
                        file.write(cryptor.decrypt(chunk))
                    else:
                        file.write(chunk)
            print('\033[32m' + '文件:[' + filename + ']已保存到[' + down_path + ']目录.' + '\033[0m')
    # 获取当前线程的信息
    current_thread = threading.current_thread()
    thread_info = f"线程名称: {current_thread.name}, 线程ID: {current_thread.ident}"
    return thread_info, "success"


# 合并ts文件
# dest_file:合成文件名
# source_path:ts文件目录
# ts_list:文件列表
# delete:合成结束是否删除ts文件
def merge_to_mp4(dest_file, source_path, ts_list):
    files = glob.glob(source_path + '/*.ts')
    if len(files) != len(ts_list):
        print('\033[31m' +
              "文件不完整，已取消合并！请重新执行一次脚本，完成未下载的文件。\n"
              "如果确认已下载完所有文件，请检查下载目录移除其它无关的ts文件。" + '\033[0m')
        return
    print('\033[34m' + '>>>>>>开始合并[' + source_path + ']目录的ts视频<<<<<<' + '\033[0m')

    with open(dest_file, 'wb') as fw:
        for file in ts_list:
            with open(source_path + "/" + file, 'rb') as fr:
                fw.write(fr.read())

    # 合并完成后删除临时文件
    print('\033[34m' + '>>>>>>开始删除[' + source_path + ']目录的临时ts文件<<<<<<' + '\033[0m')
    shutil.rmtree(source_path)
    print('\033[34m' + '合并完成！ 文件名：' + dest_file + '' + '\033[0m')
    return dest_file


def ready_download(url, title):
    # 设置下载路径
    down_path = path + title
    # 判断文件是否存在
    if os.path.exists(down_path + '.mp4'):
        print('\033[31m' + '文件' + down_path + '已经存在不用重复下载:' + '\033[0m')
        return

    # 禁止安全谁提示信息
    requests.packages.urllib3.disable_warnings()
    print()
    print('\033[34m' + '>>>>>>开始分析m3u8文件资源<<<<<<' + '\033[0m')
    # 使用m3u8库获取文件信息
    try:
        video = m3u8.load(url, timeout=20, headers=headers)
    except Exception as e:
        print('\033[31m' + 'm3u8文件资源连接失败！请检查m3u8文件地址并重试.错误代码:' + '\033[0m', e)
        return
    # 设置是否加密标志
    decrypt = False
    # ts列表
    ts_list = []
    # 判断是否加密
    key = ''
    if video.keys[0] is not None:
        method, key = get_key(video.keys[0], url)
        decrypt = True
    # 判断是否需要创建文件夹
    if not os.path.exists(down_path):
        # 创建所需的多级目录
        os.makedirs(down_path, exist_ok=True)
    # 把ts文件名添加到列表中
    for filename in video.segments:
        if len(filename.uri.rsplit("/", 1)) > 1:
            ts_list.append(filename.uri.rsplit("/", 1)[1])
        else:
            ts_list.append(filename.uri)
            # 开启线程池
    print('\033[34m' + '>>>>>>TS分片数' + str(len(ts_list)) + '<<<<<<' + '\033[0m')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        obj_list = []
        begin = time.time()  # 记录线程开始时间
        for i in range(len(video.segments)):
            obj = executor.submit(download, video.segments[i].uri, url, decrypt, down_path, key)
            obj_list.append(obj)
        # 查看线程池是否结束
        for future in as_completed(obj_list):
            data = future.result()
            print('\033[32m' 'completed result:' + '\033[0m', data)
        video = merge_to_mp4(path + title + '.mp4', down_path, ts_list)  # 合并ts文件
        # 创建视频缩略图
        # create_new_video_with_thumbnails(video)
        times = time.time() - begin  # 记录线程完成时间
        formatted_time = str(datetime.timedelta(seconds=times))
        print('\033[34m' + '总消耗时间: {}'.format(formatted_time) + '\033[0m')


def download_list(m3u8_list):
    i = 1
    for _ in m3u8_list:
        info = _.split(',')
        url = info[0]
        title = info[1]
        print('\033[32m' + '开始下载第' + str(i) + '个视频:' + '\033[0m')
        print('\033[33m' + '<' + title + '> :' + url + '\033[0m')
        ready_download(url, title)
        i += 1

# 使用示例
def main():
    url = ['https://t30.cdn2020.com/video/m3u8/2025/02/19/05282ec1/index.m3u8,糖心Vlog.内射性感OL-苏小涵', 'https://t30.cdn2020.com/video/m3u8/2025/02/16/e836ee75/index.m3u8,糖心Vlog.嫂子的肉体风险-苏小涵', 'https://t30.cdn2020.com/video/m3u8/2025/01/27/7eb80a41/index.m3u8,糖心Vlog.租赁女友性体验-苏小涵', 'https://t30.cdn2020.com/video/m3u8/2025/01/23/9f5f917e/index.m3u8,糖心Vlog.淫荡小妈蜜穴保密-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/12/25/54304107/index.m3u8,糖心Vlog.淫荡麋鹿圣诞献身-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/12/11/6fbd61ec/index.m3u8,糖心Vlog.渴望被调教的骚母狗-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/11/07/c5af0e18/index.m3u8,糖心Vlog.业绩爆棚的秘密-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/10/10/5650985b/index.m3u8,糖心Vlog.淫欲审判官的特殊审问题-苏小涵', 'https://t0.97img.com/a1000480/a.m3u8,巨乳护士肉棒治疗.把人家骚穴操坏.可是需要赔偿的哦-苏小涵', 'https://t0.97img.com/a1000434/a.m3u8,巨乳人妻裸足足交侍奉.边打电话边挨操.精液射满身 苏小涵', 'https://t0.97img.com/a1000415/a.m3u8,苏小涵.蜘蛛女的榨精惩罚.小M快进来被调教', 'https://t25.cdn2020.com/video/m3u8/2024/09/17/67a604fa/index.m3u8,糖心Vlog.嫦娥仙子的性幻想-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/09/13/86ea3ab8/index.m3u8,糖心Vlog.女高中生的色诱淫技-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/09/02/851cf4da/index.m3u8,糖心Vlog.主人的肉棒惩罚-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/30/2792e9e7/index.m3u8,糖心Vlog.奉献女友还债-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/25/2d36b1c4/index.m3u8,糖心Vlog.可爱邻家骚妹丝足榨精-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/25/95b097d3/index.m3u8,糖心Vlog.S属性女房东公狗调教-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/19/60ff6f6a/index.m3u8,糖心Vlog.富婆的肉体游戏-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/16/080d277d/index.m3u8,糖心Vlog.淫荡女大按摩淫技-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/16/82280f2d/index.m3u8,糖心Vlog.榨干人类的精液-苏小涵', 'https://t25.cdn2020.com/video/m3u8/2024/08/14/22415b28/index.m3u8,糖心Vlog,秘书的报答-苏小涵']
    download_list(url)

if __name__ == "__main__":
    main()
