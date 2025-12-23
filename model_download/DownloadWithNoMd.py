# -*- coding: utf-8 -*-
from time import sleep

import requests
from bs4 import BeautifulSoup, Tag
import re
import json
import time  # 用于延时，避免请求过快
from model_download.m3u8Download import download_list
from urllib3.exceptions import InsecureRequestWarning

url_head = 'https://91md.me'


# def main():
#     m3u8_list = ['https://t21.cdn2020.com/video/m3u8/2023/01/10/2ab0b007/index.m3u8,糖心Vlog.淫荡女仆随时供给主人中出-米胡桃']
#     download_list(m3u8_list)
# %E8%8B%8F%E5%B0%8F%E6%B6%B5.html  苏小涵
# %E8%89%BE%E7%86%99 艾熙
def main(page):
    model_name = '苏小涵'
    base_url = (url_head + '/index.php/vod/search/page/{}/wd/%E8%8B%8F%E5%B0%8F%E6%B6%B5.html')

    url = base_url.format(page)
    print(f"\n正在采集第 {page} 页: {url}")

    playlist = get_playlist(url)
    print(f"第 {page} 页 - 当前采集网址明细 playlist: {playlist}")

    # 如果当前页没有内容，结束采集
    if not playlist:
        print(f"第 {page} 页无内容，所有页面采集完毕，程序结束。")

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
    page += 1

    # 建议保留延时，防止请求过快被网站屏蔽
    # time.sleep(2)  # 可根据实际情况调整为 1~5 秒


def get_playlist(url):
    # 发起请求并获取网页内容
    response = requests.get(url)
    html_content = response.text
    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(html_content, 'html.parser')
    div_element = soup.find('div', class_='detail_right_div')
    video_list = []
    tag_list = div_element.contents[3]
    for tag in tag_list.contents:
        if not isinstance(tag, Tag):
            continue

        # 视频标题 处理 <p class="img"> 标签中包含 <img> 标签的情况
        title = ''
        for p in tag.contents:

            if not isinstance(p, Tag):
                continue
            else:
                if isinstance(p, Tag) and p.name == 'p':
                    # print("处理 <p class='img'> 标签中的 <img> 标签")
                    if p.find('img') is not None and p.get('class') == ['img']:
                        img_tag = p.find('img')
                        if 'title' in img_tag.attrs:
                            title = img_tag['title']

                    # print("处理 <p class='img'> 标签中的 <a> 标签")
                    if p.find('a', href=True) is not None:
                        href_links = p.find_all(href=re.compile('.*'))
                        if len(href_links) > 0:
                            href_values = [link.get('href') for link in href_links if link.get('href')]
                            video_list.append(title + '+' + url_head + href_values[0])

    return video_list


def create_m3u8_list(playlist):
    res_list = []
    for i, url in enumerate(playlist):
        print(i + 1, " 开始获取m3u8链接 ", url)
        tmp = url.split('+')
        title = tmp[0]
        # sleep(2)  # 如果需要可以保留
        m3u8 = get_old_video_m3u8(tmp[1])

        if m3u8:  # 如果 m3u8 不为 None 且不为空字符串
            res_list.append(m3u8 + ',' + title)
        else:
            print(f"警告: 获取失败，跳过视频 - {title} ({tmp[1]})")

    print(f"m3u8_list: {res_list}")
    return res_list


def get_old_video_m3u8(url):
    # 发起请求并获取网页内容
    m3u8_url = None  # 先初始化为 None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://91md.me/",  # 可选，增加真实性
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    response = requests.get(url, headers=headers, verify=False, timeout=30)
    response.encoding = 'utf-8'  # 或根据实际编码调整
    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找 <script type="text/javascript"> 部分
    script_tags = soup.find_all('script', type='text/javascript')
    for script_tag in script_tags:
        script_content = script_tag.string
        # 提取 m3u8 链接 检查脚本内容是否包含字符串 'player_aaaa'，如果包含则执行后续代码
        if script_content and 'player_aaaa' in script_content:
            m3u8_url = parse_m3u8(script_content)
            break
            # m3u8_urls.append(m3u8_url)
    return m3u8_url


# 从script解析m3u8
def parse_m3u8(script_content):
    # script_content = 'var player_aaaa={"flag":"play","encrypt":0,"trysee":0,"points":0,"link":"\\/index.php\\/vod\\/play\\/id\\/8630\\/sid\\/1\\/nid\\/1.html","link_next":"","link_pre":"","vod_data":{"vod_name":"\\u8f9b\\u5c24\\u91cc\\u7c97\\u7206\\u6027\\u4ea4\\u5f81\\u670d\\u574f\\u5973\\u4ec6","vod_actor":"\\u8f9b\\u5c24\\u91cc","vod_director":"","vod_class":""},"url":"https:\\/\\/t21.cdn2020.com\\/video\\/m3u8\\/2023\\/04\\/18\\/b934fd55\\/index.m3u8","url_next":"","from":"mahua","server":"no","note":"","id":"8630","sid":1,"nid":1}'
    start_index = script_content.find('{')
    end_index = script_content.rfind('}')
    json_str = script_content[start_index:end_index + 1]
    # 解析为对象
    script_obj = json.loads(json_str)
    return script_obj.get('url')


# # 获取完整字符串中目标字符串之前的字符串
# def get_before_string(full_string, target_string):
#     index = full_string.find(target_string)  # 查找目标字符串在完整字符串中的索引
#     if index != -1:  # 如果目标字符串存在于完整字符串中
#         before_string = full_string[:index]  # 提取目标字符串之前的部分
#         return before_string
#     else:
#         return None  # 目标字符串不存在于完整字符串中


if __name__ == '__main__':
    # main(1)
    get_old_video_m3u8('https://cn.pornhub.com/view_video.php?viewkey=680d282cc8610')
