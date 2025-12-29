# -*- coding: utf-8 -*-
import random
from time import sleep

import requests
from bs4 import BeautifulSoup, Tag
import re
import json
import time  # 用于延时，避免请求过快
from model_download.m3u8Download import download_list
from urllib3.exceptions import InsecureRequestWarning

url_head = 'https://91md.me'
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

# def main():
#     m3u8_list = ['https://t21.cdn2020.com/video/m3u8/2023/01/10/2ab0b007/index.m3u8,糖心Vlog.淫荡女仆随时供给主人中出-米胡桃']
#     download_list(m3u8_list)
# %E8%8B%8F%E5%B0%8F%E6%B6%B5.html  苏小涵
# %E8%89%BE%E7%86%99 艾熙
# %E6%9D%8E%E8%93%89%E8%93%89.html 李蓉蓉
def main(page):
    model_name = '李蓉蓉'
    base_url = (url_head + '/index.php/vod/search/page/{}/wd/%E6%9D%8E%E8%93%89%E8%93%89.html')

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
    print(f"开始获取m3u8链接，共 {len(playlist)} 个视频")
    for i, url in enumerate(playlist):
        print(i + 1, " 开始获取m3u8链接 ", url)
        tmp = url.split('+')
        title = tmp[0]
        sleep(5)  # 如果需要可以保留
        m3u8 = get_old_video_m3u8(tmp[1])
        # m3u8 = new_get_video_m3u8(tmp[1])
        if m3u8:  # 如果 m3u8 不为 None 且不为空字符串
            res_list.append(m3u8 + ',' + title)
            print(f"第 {i + 1} 个视频 - {title} 的m3u8 获取成功：{m3u8}")
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
    sleep(5)  # 如果需要可以保留
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
    list = ['制服诱惑想要好成绩只好跟老师-李蓉蓉+https://91md.me/index.php/vod/play/id/29802/sid/1/nid/1.html', '性感兔女郎服装真实的高潮呈现-李蓉蓉+https://91md.me/index.php/vod/play/id/29750/sid/1/nid/1.html', '红色性感睡衣御姐风-李蓉蓉+https://91md.me/index.php/vod/play/id/29730/sid/1/nid/1.html', '蓉蓉我準备好一起过圣诞节了-李蓉蓉+https://91md.me/index.php/vod/play/id/29692/sid/1/nid/1.html', '喜欢一早有人吃吃吗-李蓉蓉+https://91md.me/index.php/vod/play/id/29658/sid/1/nid/1.html', '居家蕩妇超薄纱透视旗袍-李蓉蓉+https://91md.me/index.php/vod/play/id/29576/sid/1/nid/1.html', '鱿鱼游戏COSPLAY稍息立正没有我的允许不准射-李蓉蓉+https://91md.me/index.php/vod/play/id/29538/sid/1/nid/1.html', '温泉泡汤爱爱-李蓉蓉+https://91md.me/index.php/vod/play/id/29496/sid/1/nid/1.html', '居家系列眼镜御姐跳蛋玩弄无套内射-李蓉蓉+https://91md.me/index.php/vod/play/id/29456/sid/1/nid/1.html', '激烈到坠落床底-李蓉蓉+https://91md.me/index.php/vod/play/id/29412/sid/1/nid/1.html', '刚洗完澡被站着后入坏坏了-李蓉蓉+https://91md.me/index.php/vod/play/id/29392/sid/1/nid/1.html', '特别企划圣诞快乐Fcup巨乳姊姊口爆吞精-李蓉蓉+https://91md.me/index.php/vod/play/id/29322/sid/1/nid/1.html', '参加完表妹的婚礼回家被男友内射-李蓉蓉+https://91md.me/index.php/vod/play/id/29281/sid/1/nid/1.html', '使用玩具阴蒂和阴道双重刺激受不了身体自己扭动连续高潮-李蓉蓉+https://91md.me/index.php/vod/play/id/29241/sid/1/nid/1.html', '天使的诱惑性感睡衣无套内射-李蓉蓉+https://91md.me/index.php/vod/play/id/29221/sid/1/nid/1.html', '发春警告有时候突然就很湿很湿好想要想要塞满灌满阿-李蓉蓉+https://91md.me/index.php/vod/play/id/29177/sid/1/nid/1.html', '喝醉了被硬上你会特别兴奋吗-李蓉蓉+https://91md.me/index.php/vod/play/id/29109/sid/1/nid/1.html', 'POV居家系列特写内射露出-李蓉蓉+https://91md.me/index.php/vod/play/id/29077/sid/1/nid/1.html', '豹纹主题性爱含第一人称视角-李蓉蓉+https://91md.me/index.php/vod/play/id/29034/sid/1/nid/1.html', '阴蒂一直被玩弄真的很舒服第一人称视角无套内射-李蓉蓉+https://91md.me/index.php/vod/play/id/28991/sid/1/nid/1.html', 'CK的诱惑眼镜御姐色吗-李蓉蓉+https://91md.me/index.php/vod/play/id/28977/sid/1/nid/1.html', 'OL下班自慰个不停想要棒棒-李蓉蓉+https://91md.me/index.php/vod/play/id/28913/sid/1/nid/1.html', '明明只是约跑减肥怎么还是跑到床上了啦但是他真的好大被塞得好满最后又被内射到最深处-李蓉蓉+https://91md.me/index.php/vod/play/id/28892/sid/1/nid/1.html', '好色叔叔对我伸出魔爪来一炮吧-李蓉蓉+https://91md.me/index.php/vod/play/id/28839/sid/1/nid/1.html']
    create_m3u8_list(list)
    # get_old_video_m3u8('https://cn.pornhub.com/view_video.php?viewkey=680d282cc8610')
