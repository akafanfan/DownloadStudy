# -*- coding: utf-8 -*-
import os
import random
import subprocess
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup, Tag
import re
import json
import time  # 用于延时，避免请求过快
from model_download.m3u8Download import download_list
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin


video_head = 'https://taiav.com/cn/movie/'
url_head = 'https://taiav.com/cn/tag/'
# 一组常见的真实 User-Agent（更新到 2025 年最新浏览器版本，可自行扩展）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Edg/131.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
]


#https://taiav.com/cn/tag/%E5%A7%9A%E5%AE%9B%E5%84%BF?page=1
def main(page):
    # https://taiav.com/cn/tag/%E5%87%AF%E8%92%82?page=1
    model_name = '%E5%87%AF%E8%92%82'
    base_url = (url_head + model_name+'?page={}')

    url = base_url.format(page)
    print(f"\n正在采集第 {page} 页: {url}")

    playlist = get_playlist(url)
    print(f"第 {page} 页 - 当前采集网址明细 playlist: {playlist}")

    # 如果当前页没有内容，结束采集
    if not playlist:
        print(f"第 {page} 页无内容，所有页面采集完毕，程序结束。")
    time.sleep(2)  # 可根据实际情况调整为 1~5 秒
    # 生成当前页的 m3u8 列表
    m3u8_list = create_m3u8_list(playlist)
    print(f"第 {page} 页 - m3u8_list: {m3u8_list}")

    # 打印当前页的序号和链接（本页从1开始编号）
    for index, item in enumerate(m3u8_list, start=1):
        print(f"{index}. {item}")

    # 每页采集完成后，立即下载本页的内容
    if m3u8_list:
        print(f"第 {page} 页采集完成，开始下载本页 {len(m3u8_list)} 个视频...")
        # download_list(model_name, m3u8_list, page)
        print(f"第 {page} 页下载任务已提交/完成。")
    else:
        print(f"第 {page} 页没有可下载的 m3u8 链接。")

    # 翻到下一页
    # page += 1

    # 建议保留延时，防止请求过快被网站屏蔽
    # time.sleep(2)  # 可根据实际情况调整为 1~5 秒


def get_playlist(url: str) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    # 用 html.parser 或 lxml 都可以，lxml 通常更快
    soup = BeautifulSoup(response.text, 'html.parser')

    playlist = []

    # 精确匹配截图中划线部分：所有 movie-card 里的 <a href="/cn/movie/xxx"> 和 img 的 alt
    for card in soup.select('div.movie-card'):
        # 提取 href（截图中第一条红线）
        a_tag = card.select_one('a[href]')
        if not a_tag:
            continue
        href = a_tag.get('href', '').strip()
        if '/movie/' not in href:
            continue

        # 构造完整 URL
        full_url =video_head + href if href.startswith('/') else href

        # 提取 alt 标题（截图中第二条红线）
        img_tag = card.select_one('img[alt]')
        title = img_tag.get('alt', '').strip() if img_tag else '未知标题'

        # 按你要求的格式组合
        item = f"{full_url}+{title}"
        playlist.append(item)

    return playlist


def create_m3u8_list(playlist):
    res_list = []
    print(f"开始获取m3u8链接，共 {len(playlist)} 个视频")
    for i, url in enumerate(playlist):
        print(i + 1, " 开始获取m3u8链接 ", url)
        tmp = url.split('+')
        title = tmp[1]
        # sleep(5)  # 如果需要可以保留
        # m3u8 = get_video_m3u8(tmp[0])
        if m3u8:  # 如果 m3u8 不为 None 且不为空字符串
            res_list.append(m3u8 + ',' + title)
            print(f"第 {i + 1} 个视频 - {title} 的m3u8 获取成功：{m3u8}")
        else:
            print(f"警告: 获取失败，跳过视频 - {title} ({tmp[1]})")

    print(f"m3u8_list: {res_list}")
    return res_list


def get_taiav_m3u8(movie_url: str, quality: str = "1280") -> str | None:
    """
    从 taiav.com 视频页提取当前 m3u8（带 sign 等参数）
    quality: "1280" (720p 默认), "1920" (1080p) 等，看页面下拉选项
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Referer': movie_url,
        'Accept': 'application/json',
    }

    # 从 URL 提取 ID
    if '/movie/' not in movie_url:
        return None
    movie_id = movie_url.split('/movie/')[-1].split('?')[0].strip()

    api_url = f"https://taiav.com/api/getmovie?type={quality}&id={movie_id}"

    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        if 'm3u8' in data and data['m3u8']:
            # 通常是相对路径，转成完整 URL
            m3u8_path = data['m3u8'].lstrip('/')
            full_m3u8 = urljoin("https://taiav.com/", m3u8_path)
            print("获取成功:", full_m3u8)
            return full_m3u8

        print("API 无 m3u8:", data.get('message', '未知错误'))
        return None

    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_taiav_video(
        m3u8_url: str,
        output_file: str,  # ← 必填：完整的输出文件名（含路径和扩展名）
        quality: str = "1280",
        ffmpeg_path: str = "ffmpeg",
        extra_ffmpeg_args: list = None,
        timeout_get_m3u8: int = 15,
        show_progress: bool = True,
        http_proxy="http://127.0.0.1:7897",   # 改成你的代理端口
        https_proxy="http://127.0.0.1:7897"
) -> bool:
    """
    参数:
        m3u8_url         : 视频m3u8_url链接
        output_file       : 输出文件名（例如 "D:/videos/姚宛儿_浴室.mp4"），必须包含 .mp4 扩展名
        quality           : 分辨率 "1280"(默认720p) 或 "1920"等
        ffmpeg_path       : ffmpeg 可执行文件路径（默认使用系统 PATH 中的 ffmpeg）
        extra_ffmpeg_args : 额外 ffmpeg 参数，例如 ["-ss", "00:01:00", "-t", "00:10:00"]
        timeout_get_m3u8  : 获取 m3u8 的超时秒数
        show_progress     : 是否打印进度信息

    返回:
        bool: 下载是否成功
    """
    if not output_file.lower().endswith(('.mp4', '.mkv', '.ts')):
        print("警告：建议输出文件以 .mp4 结尾")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # 自动创建目录

    print(f"目标保存路径: {output_path.absolute()}")

    # 1. 获取 m3u8
    # 2. 构建 ffmpeg 命令
    cmd = [
        ffmpeg_path,
        "-headers", f"Referer: {m3u8_url}\r\n",
        "-i", m3u8_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-y"  # 覆盖已有文件
    ]

    if extra_ffmpeg_args:
        cmd.extend(extra_ffmpeg_args)

    cmd.append(str(output_path))

    if show_progress:
        print("即将执行的 ffmpeg 命令：")
        print(" ".join(cmd))

    # 3. 执行下载（使用 Popen 实时读取输出，避免“没反应”）
    try:
        start_time = time.time()

        env = os.environ.copy()
        if http_proxy:
            env["http_proxy"] = http_proxy
            env["HTTP_PROXY"] = http_proxy
        if https_proxy:
            env["https_proxy"] = https_proxy
            env["HTTPS_PROXY"] = https_proxy

        # 关键修复：使用 utf-8 编码 + errors='replace' 处理非法字符
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',  # ← 核心：替换非法字符，避免 GBK 解码崩溃
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # 实时打印输出
        for line in iter(process.stdout.readline, ''):
            print(line.strip())

        return_code = process.wait()

        elapsed = time.time() - start_time

        if return_code == 0:
            print(f"\n下载完成！用时 {elapsed:.1f} 秒")
            print(f"文件已保存至: {output_path.absolute()}")
            return True
        else:
            print(f"\nffmpeg 异常结束，返回码: {return_code}")
            return False

    except FileNotFoundError:
        print(f"\n错误：找不到 ffmpeg → {ffmpeg_path}")
        return False

    except Exception as e:
        print(f"\n意外错误: {e}")
        return False

if __name__ == "__main__":
    url = "https://taiav.com/cn/movie/683d16c08bb62c0d8cc5b5aa"
    m3u8 = get_taiav_m3u8(url, quality="1280")
    if m3u8:
        print("当前 m3u8:", m3u8)
        # 示例输出可能像：
        # https://taiav
    success = download_taiav_video(
        m3u8_url=m3u8,
        output_file="D:/Documents/GitHub/DownloadStudy/tai_download/model/姚宛儿_浴室尿失禁.mp4"
    )