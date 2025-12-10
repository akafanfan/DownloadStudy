# 这是一个下载m3u8 视频资源的脚本   无指定序号版，根据资源数组排序 非ffmpeg合并版
# -*- coding: utf-8 -*-
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

path = '/Users/yangfan/Downloads/download/aixi/1/'


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
    # 使用m3u8库获取文件信息
    try:
        video = m3u8.load(url, timeout=20, headers=headers)
    except Exception as e:
        print('\033[31m' + 'm3u8文件资源连接失败！请检查m3u8文件地址并重试.错误代码:' + '\033[0m', e)
        try:
            with open('./fail.txt', 'a', encoding='utf-8') as f:
                f.write(f"{url},{title}\n")
        except Exception as write_error:
            print(f"\033[31m写入失败文件时出错: {write_error}\033[0m")
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
    url1 = ['https://t33.cdn2020.com/video/m3u8/2025/11/07/ff16a832/index.m3u8,麻豆传媒映画.MD-0356.艾熙.夏日美乳少妇的色按初体验.挑逗G点手法全身颤抖痉挛', 'https://t33.cdn2020.com/video/m3u8/2025/10/31/5d03a496/index.m3u8,穿着情趣睡衣等你来让上我-艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/10/23/2cb13c78/index.m3u8,下班不回家被上司压在桌子上操-艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/10/18/64827eee/index.m3u8,麻豆传媒映画.MDSR-0005-6.艾熙.苏畅.艾悠.少妇白洁.第六章.绿帽风云.谁是谁的妻', 'https://t0.97img.com/a1002022/a.m3u8,内涵甜蜜女友.NHAV-090.学霸恋情恶男老师.用身体堵住他的嘴.艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/10/02/8e83b8e4/index.m3u8,麻豆传媒映画.MDSR-0005-5.艾熙.欣晴.少妇白洁.第五章.多情不敢难自抑', 'https://t33.cdn2020.com/video/m3u8/2025/09/13/26a4224d/index.m3u8,麻豆传媒映画.MGL-0007.艾熙.黎芷媗.麻豆万能服务公司.满足兽父心中的妄想', 'https://t33.cdn2020.com/video/m3u8/2025/09/11/6d13d653/index.m3u8,湿透巨乳女友的冷气坏掉之夜-艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/09/12/4483b814/index.m3u8,很久没有被内射了好害羞被顶到点了-艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/09/04/b099081f/index.m3u8,想要被我服务吗你只需要干爆我就好-艾熙', 'https://t33.cdn2020.com/video/m3u8/2025/08/27/8c8a5a5e/index.m3u8,每次去旅行都要被塞满了啦-艾熙', 'https://t0.97img.com/a1001864/a.m3u8,内涵甜蜜女友.NHAV-074.艾熙.搭讪失败的火辣美女是个淫荡骚货', 'https://t33.cdn2020.com/video/m3u8/2025/08/21/8c3d6538/index.m3u8,一个不够用加一个刚刚好-艾熙', 'https://t30.cdn2020.com/video/m3u8/2025/07/30/7a77bafd/index.m3u8,制服的诱惑体育服-艾熙', 'https://t30.cdn2020.com/video/m3u8/2025/07/11/d50bbace/index.m3u8,麻豆传媒映画.MD-0348.艾熙.周宁.黑人干爆亚洲骚穴实录.黑色巨屌激战双女', 'https://t30.cdn2020.com/video/m3u8/2025/06/21/f8af56ef/index.m3u8,麻豆传媒映画.MDSR-0009-1.苏语棠.艾熙.极品嫂子.夏日欲火无套乱伦.情色文学.4P', 'https://t30.cdn2020.com/video/m3u8/2025/05/17/4436d0ba/index.m3u8,麻豆传媒映画.MD-0358.温芮欣.艾熙.京东做爱的外卖总裁.霸道总裁亲自下海操骚屄', 'https://t30.cdn2020.com/video/m3u8/2025/05/02/9a8f785b/index.m3u8,麻豆传媒映画.MDSR-0008-1.艾熙.艾悠.蓝天航空公司的空姐EP1.升迁下的性爱调教', 'https://t30.cdn2020.com/video/m3u8/2025/04/02/fe203cb9/index.m3u8,蜜桃影像传媒.EMX-079.艾熙.极欲女大生的桌底秘密.偷偷的在你身边自慰.要的就是你能操我', 'https://t30.cdn2020.com/video/m3u8/2025/02/07/4ce48e2d/index.m3u8,麻豆传媒映画.MDL-0010-2.艾熙.夏晴子.鲍鱼游戏2.轮奸真假间谍.潮吹爆喷', 'https://t30.cdn2020.com/video/m3u8/2025/02/02/232e8cca/index.m3u8,蜜桃影像传媒.PM-096.艾熙.淫荡女回家过年.性欲来了怎么办', 'https://t0.97img.com/a1000939/a.m3u8,麻豆传媒映画.MDL-0010-1.夏晴子.李蓉蓉.艾熙.苏樱花.吴梦梦.孟若羽.优娜.蕾·利尔·布莱克.鲍鱼游戏2.第一集.黑人26公分巨屌.疯狂抽插', 'https://t25.cdn2020.com/video/m3u8/2024/12/14/1de777c9/index.m3u8,和艾熙的两女性器关-吴梦梦', 'https://t25.cdn2020.com/video/m3u8/2024/12/11/fd2dd82e/index.m3u8,蜜桃影像传媒.EMX-069.艾熙.性感小姨对我性治疗小姨风骚又性感的身体才能治疗我的肿胀']
    download_list(url1)

if __name__ == "__main__":
    main()
