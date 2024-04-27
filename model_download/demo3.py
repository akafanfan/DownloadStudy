# 这是一个下载m3u8 视频资源的脚本   无指定序号版，根据资源数组排序 非ffmpeg合并版
import os
import re
import sys
import m3u8
import glob
import time
import requests
import concurrent.futures
from Crypto.Cipher import AES
from concurrent.futures import as_completed

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'Zh-CN, zh;q=0.9, en-gb;q=0.8, en;q=0.7'
}


# 判断是否为网站地址
def reurl(url):
    pattern = re.compile(r'^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+')
    m = pattern.search(url)
    if m is None:
        return False
    else:
        return True


# 获取密钥（针对有些m3u8文件中的视频需要key去解密下载的视频）
def getKey(keystr, url):
    keyinfo = str(keystr)
    method_pos = keyinfo.find('METHOD')
    comma_pos = keyinfo.find(",")
    method = keyinfo[method_pos:comma_pos].split('=')[1]
    uri_pos = keyinfo.find("URI")
    quotation_mark_pos = keyinfo.rfind('"')
    key_url = keyinfo[uri_pos:quotation_mark_pos].split('"')[1]
    if reurl(key_url) == False:
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
def download(down_url, url, decrypt, down_path, key, nameid):
    if reurl(down_url) == False:
        if len(down_url.rsplit("/", 1)) > 1:
            filename = down_url.rsplit("/", 1)[1]
        else:
            filename = down_url
        down_url = url.rsplit("/", 1)[0] + "/" + down_url
    else:
        filename = down_url.rsplit("/", 1)[1]
    down_ts_path = down_path + "/{0}".format(filename)
    if os.path.exists(down_ts_path):
        print('文件 ' + filename + ' 已经存在，跳过下载.')
    else:
        try:
            res = requests.get(down_url, stream=True, verify=False, headers=headers)
            print('正在下载资源：' + filename + '')
        except Exception as e:
            print('requests error:', e)
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
            print('文件:[' + filename + ']已保存到[' + down_path + ']目录.')


# 合并ts文件
# dest_file:合成文件名
# source_path:ts文件目录
# ts_list:文件列表
# delete:合成结束是否删除ts文件
def merge_to_mp4(dest_file, source_path, ts_list, delete=True):
    files = glob.glob(source_path + '/*.ts')
    if len(files) != len(ts_list):
        print(
            "文件不完整，已取消合并！请重新执行一次脚本，完成未下载的文件。\n如果确认已下载完所有文件，请检查下载目录移除其它无关的ts文件。")
        return
    print('开始合并[' + source_path + ']目录的ts视频...')

    with open(dest_file, 'wb') as fw:
        for file in ts_list:
            with open(source_path + "/" + file, 'rb') as fr:
                fw.write(fr.read())
            if delete:
                os.remove(file)
        print('合并完成！ 文件名：' + dest_file + '')


def main():
    url = "https://xxxx/hls/index.m3u8"  # 下载地址,通过 cmd 传入或输入

    print('\n')
    print('参数说明:脚本后面面添加 m3u8地址参数，如打开CMD(终端命令)模式输入：m3u8dl http://xxx.xxx.com/xxx.m3u8')
    print('\n')
    print('    如果m3u8地址访问不到，提示错误，多重复几次就好。前提是确认在线能观看可下载到m3u8文件。')
    print('    下载中途不动了或者关机，可关闭取消下载，再次打开继续下载。')
    print('    有些文件一次下载不到，需要多次执行下载。')
    print('    等所有文件下载完后自动合成一个视频，注意看提示。')
    print('\n')

    if len(sys.argv) > 1:
        url = (sys.argv[1])
    else:
        print('亲，没有添加m3u8地址,请在下方输入:')
        url = input()

    # 禁止安全谁提示信息
    requests.packages.urllib3.disable_warnings()

    print('开始分析m3u8文件资源...')
    # 使用m3u8库获取文件信息
    try:
        video = m3u8.load(url, timeout=20, headers=headers)
    except Exception as e:
        print('m3u8文件资源连接失败！请检查m3u8文件地址并重试.错误代码:', e)
        return

    # 设置下载路径
    down_path = "tmp"
    # 设置是否加密标志
    decrypt = False
    # ts列表
    ts_list = []
    # 判断是否加密
    key = ''
    if video.keys[0] is not None:
        method, key = getKey(video.keys[0], url)
        decrypt = True
    # 判断是否需要创建文件夹
    if not os.path.exists(down_path):
        os.mkdir(down_path)
    # 把ts文件名添加到列表中
    for filename in video.segments:
        if len(filename.uri.rsplit("/", 1)) > 1:
            ts_list.append(filename.uri.rsplit("/", 1)[1])
        else:
            ts_list.append(filename.uri)
            # 开启线程池
    with concurrent.futures.ThreadPoolExecutor() as executor:
        obj_list = []
        begin = time.time()  # 记录线程开始时间
        for i in range(len(video.segments)):
            obj = executor.submit(download, video.segments[i].uri, url, decrypt, down_path, key, i)
            obj_list.append(obj)
        # 查看线程池是否结束
        for future in as_completed(obj_list):
            data = future.result()
            # print('completed result:',data)
        merge_to_mp4('finalvideo.mp4', down_path, ts_list)  # 合并ts文件
        times = time.time() - begin  # 记录线程完成时间
        print('总消耗时间:' + str(times) + '')


if __name__ == "__main__":
    main()