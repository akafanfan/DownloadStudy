import os
import re
import requests
from bs4 import BeautifulSoup
import yt_dlp
from typing import Optional, Tuple

def get_chinese_title(page_url: str) -> str:
    """
    通过 requests + BeautifulSoup 直接从页面 <title> 提取中文标题
    适用于 Pornhub、91 系列等站点，标题几乎总是中文
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/143.0.0.0 Safari/537.36',
        'Referer': 'https://cn.pornhub.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')

        if title_tag and title_tag.text.strip():
            raw_title = title_tag.text.strip()
            # 去掉常见的后缀，如 " - Pornhub.com"
            title = re.sub(r'\s*[-–—]\s*Pornhub\.com.*$', '', raw_title)
            title = title.strip()
            # 清理非法文件名字符，但保留中文、表情符号、字母数字
            title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', title)
            title = title[:150]  # 防止文件名过长
            return title

    except Exception as e:
        print(f"请求页面获取标题失败: {e}")

    return "未知视频标题"


def get_1_video_m3u8(page_url: str) -> Optional[Tuple[str, str]]:
    """
    1. 先用 requests 提取纯正中文标题
    2. 再用 yt-dlp 提取 480p（或以下）画质的 m3u8 / 直链
    返回 (video_url, title) 或 None
    """
    # 第一步：获取中文标题
    title = get_chinese_title(page_url)
    print(f"提取到标题: {title}")

    # 第二步：用 yt-dlp 提取 480p 视频链接
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # 优先 480p 或以下画质，优先 m3u8
        'format': 'bestvideo[height<=480][protocol*=m3u8]/bestvideo[height<=480]/best[height<=480]',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/143.0.0.0 Safari/537.36',
            'Referer': page_url.rsplit('/', 1)[0] + '/',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(page_url, download=False)
            if not info:
                print("yt-dlp 未提取到任何信息")
                return None

            # 遍历 formats 找符合条件的链接
            best_url = None
            best_height = 0

            for fmt in info.get('formats', []):
                height = fmt.get('height') or 0
                url = fmt.get('url')
                protocol = fmt.get('protocol', '')

                if height <= 720 and url:
                    if 'm3u8' in protocol or 'm3u8' in url:  # 优先 m3u8
                        best_url = url
                        best_height = height
                        break
                    elif best_url is None or height > best_height:
                        best_url = url
                        best_height = height

            # 备选：直接的 url（部分站点）
            if not best_url:
                direct = info.get('url')
                direct_height = info.get('height', 0)
                if direct and direct_height <= 720:
                    best_url = direct
                    best_height = direct_height

            if best_url:
                print(f"成功提取 {best_height}p 视频链接（{'m3u8' if 'm3u8' in best_url else '直链'}）")
                return best_url+','+title
            else:
                print("未找到 480p 或以下画质（可能只有更高画质可用）")
                return None

    except Exception as e:
        print(f"yt-dlp 提取视频链接失败: {e}")
        return None


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 替换成你要处理的视频页面地址
    page_url = "https://cn.pornhub.com/view_video.php?viewkey=682f2c6e887cf"
    result = get_1_video_m3u8(page_url)
    if result:
        print(f"获取m3u8: {result}")
    else:
        print("获取失败，请检查链接或网络")