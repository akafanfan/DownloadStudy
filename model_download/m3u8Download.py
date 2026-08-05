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

path = 'D:\\x下载\\download\\'


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


def ready_download(model_name, url, title, page):
    # 设置下载路径
    down_path = path + model_name + '\\' + str(page) + '\\' + title
    video_file = down_path + '.mp4'
    # 判断文件是否存在
    if os.path.exists(video_file):
        print('\033[31m' + '文件' + video_file + ' 已经存在不用重复下载:' + '\033[0m')
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
    max_threads = 32  # 你可以改成 8、10、16、20、32 等，根据你的网速和机器性能调整
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        obj_list = []
        begin = time.time()  # 记录线程开始时间
        for i in range(len(video.segments)):
            obj = executor.submit(download, video.segments[i].uri, url, decrypt, down_path, key)
            obj_list.append(obj)
        # 查看线程池是否结束
        for future in as_completed(obj_list):
            data = future.result()
            print('\033[32m' 'completed result:' + '\033[0m', data)
        final_video_path = os.path.dirname(down_path) + os.sep + title + '.mp4'
        video = merge_to_mp4(final_video_path, down_path, ts_list)
        # 创建视频缩略图
        # create_new_video_with_thumbnails(video)
        times = time.time() - begin  # 记录线程完成时间
        formatted_time = str(datetime.timedelta(seconds=times))
        print('\033[34m' + '总消耗时间: {}'.format(formatted_time) + '\033[0m')


def download_list(model_name, m3u8_list, page):
    i = 1
    m3u8_list
    print(f'准备下视频数量{len(m3u8_list)}')
    for _ in m3u8_list:
        info = _.split(',')
        url = info[0]
        title = info[1]
        print('\033[32m' + '开始下载第' + str(i) + '个视频:' + '\033[0m')
        print('\033[33m' + '<' + title + '> :' + url + '\033[0m')
        ready_download(model_name, url, title, page)
        i += 1


# 使用示例
def main():
    m3u8_list = ['https://t33.cdn2020.com/video/m3u8/2025/11/05/85967d86/index.m3u8,埃及猫-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/11/04/1827654b/index.m3u8,瑶瑶的恋足癖与精液面包-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/11/01/f05b5f81/index.m3u8,小姨子勾搭姐夫-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/10/31/586c74fe/index.m3u8,日向雏田cosplay-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/10/30/5a2d3fd7/index.m3u8,让情侣感情升温的小游戏-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/10/29/374a01a5/index.m3u8,出差的老婆-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/10/13/ea298a06/index.m3u8,健身姐姐的诱惑-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/09/05/7824a536/index.m3u8,房东女儿的补课费-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/27/b002270e/index.m3u8,老婆带装满别的男人精液的套子回来戴到的鸡巴上做爱-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/25/9cae8d11/index.m3u8,健身教练偷情-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/24/f6c34605/index.m3u8,调皮的妹妹-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/22/e7a27993/index.m3u8,老婆带装满精液的套子回来戴到老公鸡巴上-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/21/fb1cb5e4/index.m3u8,万圣节绿帽特辑老公抱着身为幽灵的我让单男操-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/18/e28c874e/index.m3u8,闺蜜加精液奥利奥-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/17/ce4c0e59/index.m3u8,COS秀被榜一大哥内射-汐梦瑶', 'https://t33.cdn2020.com/video/m3u8/2025/08/12/0d3b44a5/index.m3u8,舔腋下舔脚闺蜜视频颜射-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/07/23/375c6115/index.m3u8,瑶瑶的学生时代回忆那年青涩的她被操的样子-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/07/20/39c0e52e/index.m3u8,用撕咬的方式口交狠狠的用牙齿咬鸡巴包皮-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/07/11/f5aa04e7/index.m3u8,深夜病栋-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/07/11/00a926ad/index.m3u8,公园露出挑战路人3P-汐梦瑶', 'https://t0.97img.com/a1001499/a.m3u8,把鄙视我的护士汐梦瑶操到生娃吧！绝顶高潮内射子宫', 'https://t30.cdn2020.com/video/m3u8/2025/06/29/da23a6f2/index.m3u8,出轨单男时给绿帽老公打电话被内射-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/06/23/619183c2/index.m3u8,在公园里让群友操自己老婆-汐梦瑶', 'https://t30.cdn2020.com/video/m3u8/2025/06/22/a14b3249/index.m3u8,结婚当天叫伴郎团一起操新娘-汐梦瑶']
    download_list('汐梦瑶',m3u8_list,2)

if __name__ == "__main__":
    i = 1
    while i <= 3:
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(f'第{i}次运行下载')
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        main()
        i += 1
