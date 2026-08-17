# -*- coding: utf-8 -*-
import os
import random
from time import sleep
import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# 忽略不安全请求的警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 真实的 User-Agent 伪装
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]


def get_headers():
    """每次请求随机生成伪装头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://fapopedia.net/",
        "Upgrade-Insecure-Requests": "1"
    }


def get_playlist(page_url):
    """【第一步】解析列表页，获取详情页链接集合"""
    try:
        response = requests.get(page_url, headers=get_headers(), timeout=15, verify=False)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"请求列表页失败: {e}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    link_list = []

    outer_div = soup.find("div", class_="shrt-blk")
    if not outer_div:
        return []

    short_divs = outer_div.find_all("div", class_="shrt")
    for div in short_divs:
        a_tag = div.find("a")
        if a_tag and a_tag.get("href"):
            link_list.append(a_tag["href"])

    return link_list


def get_image_url(detail_url):
    """【第二步】访问详情页，解析出真实大图的下载地址"""
    try:
        response = requests.get(detail_url, headers=get_headers(), timeout=15, verify=False)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"请求详情页失败 {detail_url}: {e}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # 定位大图容器
    lrg_blk = soup.find("div", class_="lrg-pc-blk")
    if lrg_blk:
        lrg_pc = lrg_blk.find("div", class_="lrg-pc")
        if lrg_pc:
            a_tag = lrg_pc.find("a")
            if a_tag and a_tag.get("href"):
                return a_tag["href"]

            # 兜底寻找 img 标签
            img_tag = lrg_pc.find("img")
            if img_tag and img_tag.get("src"):
                return img_tag["src"]

    return None


def download_image(img_url, base_dir="download"):
    """【第三步】将图片下载到当前文件同目录下的 ./download 文件夹"""
    if not img_url:
        return

    # 获取当前脚本文件所在的绝对路径，并拼接出 ./download 目标路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(current_dir, base_dir)

    # 如果目录不存在则创建
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 从 URL 提取原文件名（例如：0344.jpg）
    filename = img_url.split('/')[-1]
    save_path = os.path.join(save_dir, filename)

    try:
        print(f"   [下载中] -> {img_url}")
        response = requests.get(img_url, headers=get_headers(), timeout=20, verify=False, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"   [成功] 图片已保存至: {save_path}")
    except Exception as e:
        print(f"   [失败] 下载图片出错: {e}")


def main(start_page, end_page):
    all_detail_links = []

    # 1. 抓取所有详情页链接
    print("=== 开始第一阶段：收集详情页链接 ===")
    for page in range(start_page, end_page + 1):
        url = f"https://fapopedia.net/kermitmeji-nude-leaks/{page}/#photos"
        print(f"正在扫描第 {page} 页...")
        playlist = get_playlist(url)
        all_detail_links.extend(playlist)
        sleep(random.uniform(1.0, 2.0))

    print(f"\n链接收集完毕，共找到 {len(all_detail_links)} 个详情页。")
    print("=== 开始第二阶段：进入详情页下载图片 ===")

    # 2. 遍历详情页并下载图片
    for index, detail_url in enumerate(all_detail_links, 1):
        print(f"\n[{index}/{len(all_detail_links)}] 正在处理页面: {detail_url}")

        # 获取大图地址
        img_url = get_image_url(detail_url)

        if img_url:
            # 下载大图
            download_image(img_url)
        else:
            print("   [提示] 该页面未找到图片元素。")

        # 频率控制，保护 IP
        sleep(random.uniform(1.0, 2.5))

    print("\n================== 所有下载任务已完成 ==================")


if __name__ == '__main__':
    # 示例：跑第 1 页到第 2 页的所有图片
    main(1, 6)