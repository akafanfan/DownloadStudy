import requests
from bs4 import BeautifulSoup, Tag
import re
import json

from model_download.m3u8Download import download_list

url_head = 'https://91md.me'


# def main():
#     m3u8_list = ['https://t21.cdn2020.com/video/m3u8/2023/01/10/2ab0b007/index.m3u8,糖心Vlog.淫荡女仆随时供给主人中出-米胡桃']
#     download_list(m3u8_list)

def main():
    # play_list_url = 'https://91md.me/index.php/vod/search/page/2/wd/辛尤里.html'
    # url1 = 'https://91md.me/index.php/vod/play/id/8630/sid/1/nid/1'
    url2 = 'https://91md.me/index.php/vod/search/page/1/wd/%E8%BE%9B%E5%B0%A4%E9%87%8C.html'
    playlist = get_playlist(url2)
    m3u8_list = create_m3u8_list(playlist)
    print("m3u8_list:")
    for index, item in enumerate(m3u8_list, start=1):
        print(f"{index}. {item}")
    download_list(m3u8_list)

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
                            video_list.append(title + ',' + url_head + href_values[0])

    return video_list


def create_m3u8_list(playlist):
    res_list = []
    # 遍历列表中的每个URL
    for i, url in enumerate(playlist):
        # 打印当前获取的M3U8链接
        print(i + 1, " 当前前获取m3u8链接:", url)
        tmp = url.split(',')
        title = tmp[0]
        m3u8 = get_1_video_m3u8(tmp[1])
        res_list.append(m3u8 + ',' + title)
    return res_list


def get_1_video_m3u8(url):
    # 发起请求并获取网页内容
    m3u8_url = ''
    response = requests.get(url)
    html_content = response.text
    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(html_content, 'html.parser')
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
    main()
