import subprocess
import sys
import io
import time
import requests
import m3u8
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
# }
#
#
# def AESDecrypt(cipher_text, key, iv):
#     cipher_text = pad(data_to_pad=cipher_text, block_size=AES.block_size)
#     aes = AES.new(key=key, mode=AES.MODE_CBC, iv=key)
#     cipher_text = aes.decrypt(cipher_text)
#     return cipher_text
#
#
# def download_m3u8_video(url, save_name):
#     playlist = m3u8.load(uri=url, headers=headers)
#     key = requests.get(playlist.keys[-1].uri, headers=headers).content
#
#     n = len(playlist.segments)
#     size = 0
#     start = time.time()
#     for i, seg in enumerate(playlist.segments, 1):
#         r = requests.get(seg.absolute_uri, headers=headers)
#         data = r.content
#         data = AESDecrypt(data, key=key, iv=key)
#         size += len(data)
#         with open(save_name, "ab" if i != 1 else "wb") as f:
#             f.write(data)
#         print(
#             f"\r下载进度({i}/{n})，已下载：{size / 1024 / 1024:.2f}MB，下载已耗时：{time.time() - start:.2f}s", end=" ")
#

def download_by_N_m3u8DL(m3u8, title):
    exe_path = r"/NewOrigin/tool/N_m3u8DL/N_m3u8DL-CLI_v3.0.2.exe"
    url = m3u8
    save_name = title
    work_dir = r"D:\Documents\PyCharmProjects\DownloadStudy\NewOrigin\Output"
    command = [
        exe_path,
        url,
        "--workDir", work_dir,
        "--saveName", save_name,
        "--headers", "Referer:https://lbjx9.com/",
        "--proxyAddress", "socks5://127.0.0.1:26001",
        "--enableDelAfterDone"
    ]
    subprocess.run(command,encoding='utf-8')

if __name__ == '__main__':
    download_by_N_m3u8DL('https://t25.cdn2020.com/video/m3u8/2024/04/19/a6e0e6b4/index.m3u8','性爱女僕-辛尤里')
    # download_m3u8_video('https://t25.cdn2020.com/video/m3u8/2024/04/19/a6e0e6b4/index.m3u8', '性爱女僕-辛尤里.mp4')