import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

# 配置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s')

# 创建一个缓存字典来存储请求结果
request_cache = {}
img_url_list = []
href_list = []

def get_html(url):
    if url in request_cache:
        return request_cache[url]
    response = requests.get(url)
    response.raise_for_status()
    request_cache[url] = response.text
    return response.text


def find_img_url(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    lrg_pc_element = soup.select_one('div.lrg-pc')
    if lrg_pc_element is None:
        logging.warning("未找到class='lrg-pc'的元素。")
        return None
    img_tag = lrg_pc_element.find('img')
    img_url = img_tag['src']
    img_url_list.append(img_url)


def get_div_styles_and_links(url, base_url):

    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    l_cnt_element = soup.select_one('div.l-cnt')
    if l_cnt_element is None:
        logging.warning("未找到class='l-cnt'的元素。")
        return href_list

    shrt_blk_elements = l_cnt_element.find_all('div', class_='shrt-blk')
    for div in shrt_blk_elements:
        a_tags = div.find_all('a')
        for a in a_tags:
            if 'href' in a.attrs:
                href = a['href']
                if href.endswith('.html'):
                    full_href = urljoin(base_url, href)
                    logging.info(f"找到的图片地址:{full_href}")
                    href_list.append(full_href)

    nv_blk_element = soup.select_one('div.nv-blk')
    if nv_blk_element:
        next_page = nv_blk_element.select_one('li:nth-of-type(3) a')
        if next_page and 'href' in next_page.attrs:
            next_page_url = urljoin(base_url, next_page['href'])
            logging.info("下一页的URL:" + next_page_url)
            href_list.extend(get_div_styles_and_links(next_page_url, base_url))
        else:
            logging.info("没下一页了~")

    return href_list


def download_images(href_list, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(find_img_url, href_list)


# 示例用法
if __name__ == "__main__":
    base_url = "https://fapopedia.net/kermitmeji-nude-leaks/#photos"
    href_list = get_div_styles_and_links(base_url, base_url)
    logging.info(f"总数:{str(len(href_list))}")
    logging.info(f"总数:{str(len(img_url_list))}")

    # download_images(href_list)
