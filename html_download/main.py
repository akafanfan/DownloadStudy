import requests
from bs4 import BeautifulSoup
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# 设置日志记录配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s')

# 存储所有href属性的列表
href_list = []
img_url_list = []
number = 0
# 指定保存图片的文件夹路径
folder_path = "./download"
# 添加前缀
prefix = "kermitmeji_"
# 初始化计数器
download_count = 0
download_count_lock = threading.Lock()


def download_photos_concurrently(href_list):
    global download_count
    download_count = 0  # 重置计数器
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(download_photo, href_list)

    logging.info(f"下载完成！下载总数：{download_count} 文件路径为：{folder_path}")


def download_photo(href_url):
    global download_count
    try:
        img_url = find_img_url(href_url)

        logging.info(f">>>>>开始下载图片<<<<<<：{img_url}")
        # 解析图片URL以获取文件名
        file_name = os.path.basename(img_url)
        new_file_name = prefix + file_name
        # 检查文件夹是否存在，如果不存在则创建
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # 完整的文件路径
        full_file_path = os.path.join(folder_path, new_file_name)
        # 使用requests库下载图片
        response = requests.get(img_url)
        # 检查请求是否成功
        if response.status_code == 200:
            # 将图片保存到指定文件夹
            with open(full_file_path, 'wb') as f:
                f.write(response.content)
            logging.info(f">>>>>图片下载成功文件位置：{folder_path}/{new_file_name}<<<<<<")
            with download_count_lock:
                download_count += 1
        else:
            logging.error(f">>>>>图片url:{img_url}下载失败<<<<<<")

    except requests.RequestException as e:
        logging.error(f">>>>>请求失败: {e}<<<<<<")


def find_img_url(url):
    # 发送HTTP GET请求
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    # 使用BeautifulSoup解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')
    # 查找body标签
    body_tag = soup.find('body')
    # 查找class为wrp的元素
    wrp_element = body_tag.find('div', class_='wrp')
    # 查找class为cnt的元素
    cnt_element = wrp_element.find('div', class_='cnt')
    # 查找class为1-cnt的元素
    l_cnt_element = cnt_element.find('div', class_='l-cnt')
    if l_cnt_element is None:
        logging.warning("未找到class='1-cnt'的元素。")
        return None
    # 查找class为lrg-pc-blk的div元素
    lrg_pc_element = l_cnt_element.find('div', class_='lrg-pc')
    # 查找img标签
    img_tag = lrg_pc_element.find('img')
    # 获取img标签的src属性
    img_url = img_tag['src']
    return img_url


def get_div_styles_and_links(url):
    try:
        # 发送HTTP GET请求
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找body标签
        body_tag = soup.find('body')
        # 查找class为wrp的元素
        wrp_element = body_tag.find('div', class_='wrp')
        # 查找class为cnt的元素
        cnt_element = wrp_element.find('div', class_='cnt')
        # 查找class为1-cnt的元素
        l_cnt_element = cnt_element.find('div', class_='l-cnt')
        if l_cnt_element is None:
            logging.warning("未找到class='1-cnt'的元素。")
            return []

        # 查找class为shrt-blk的div元素
        shrt_blk_element = l_cnt_element.find_all('div', class_='shrt-blk')
        # 提取并打印每个div的样式信息，并提取href属性
        for div in shrt_blk_element:
            # 查找div中的所有a标签
            a_tags = div.find_all('a')
            for a in a_tags:
                if 'href' in a.attrs:
                    href = a['href']
                    # 筛选出以.html结尾的href属性
                    if href.endswith('.html'):
                        # 进去找图的url
                        logging.info(f"找到的图片地址:{href}")
                        href_list.append(href)

        # 判断是否存在下一页
        # 查找class为nv-blk的元素
        nv_blk_element = body_tag.find('div', class_='nv-blk')
        # 查找标签值为Next的元素
        li_list = nv_blk_element.find_all('li')
        a_tag = li_list[2].find('a')
        if a_tag and 'href' in a_tag.attrs:
            logging.info("下一页的URL:" + a_tag['href'])
            # 递归下一页
            get_div_styles_and_links(a_tag['href'])
        else:
            logging.info("没下一页了~")

        return href_list

    except requests.RequestException as e:
        logging.error(f"请求失败: {e}")
        return []


def main():
    # 提示用户输入网址
    # url = input("请输入网址: ")
    url = "https://fapopedia.net/kermitmeji-nude-leaks/#photos"
    href_list = get_div_styles_and_links(url)
    # 打印总数
    logging.info(f"获取图片url的总数: {str(len(href_list))}")
    # 打印所有提取到的href属性
    # logging.info("所有提取到的a标签href属性:")
    for href in href_list:
        logging.info(href)

    # 多线程下载图片
    download_photos_concurrently(href_list)


def main2():
    url = "https://fapopedia.net/kermitmeji-nude-leaks/10693066.html"
    download_photo(url)


if __name__ == "__main__":
    main()
