import yaml
import sys
from pathlib import Path
from yt_dlp import YoutubeDL


def load_config():
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ 未找到 config.yaml 文件！")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    models = config.get("models", [])

    if not models:
        print("❌ config.yaml 中没有配置 models")
        sys.exit(1)

    output_template = str(
        Path(config.get("output_dir", "./Downloads")) / "%(uploader)s" / config.get("filename_template")
    )

    ydl_opts = {
        'format': config.get('format', 'bestvideo[height<=720]+bestaudio/best[height<=720]'),
        'outtmpl': output_template,
        'download_archive': 'downloaded.txt',
        'concurrent_fragment_downloads': config.get('concurrent_fragments', 4),
        'sleep_interval': config.get('sleep_interval', 10),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'playlistreverse': config.get('playlist_reverse', False),
        'restrictfilenames': True,

        # Cookie
        'cookiefile': config.get('cookies'),

        # 关键防封参数（必须和命令行一致）
        'impersonate': config.get('impersonate', 'chrome'),
        'referer': 'https://www.pornhub.com/',
        'user_agent': config.get('user_agent',
                                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'),

        'extractor_retries': config.get('extractor_retries', 10),
        'retry_sleep': config.get('retry_sleep', 12),
        'force_ipv4': config.get('force_ipv4', True),
    }

    # 代理
    if config.get('proxy'):
        ydl_opts['proxy'] = config.get('proxy')

    # 时间过滤
    if config.get('date_after'):
        ydl_opts['dateafter'] = config.get('date_after')
    if config.get('date_before'):
        ydl_opts['datebefore'] = config.get('date_before')

    print(f"🚀 开始下载 {len(models)} 个 Model 的视频...\n")

    with YoutubeDL(ydl_opts) as ydl:
        for url in models:
            print(f"\n📌 正在处理 Model: {url}")
            try:
                ydl.download([url])
                print(f"✅ {url} 处理完成")
            except Exception as e:
                print(f"❌ 下载出错 {url}: {e}")

    print("\n🎉 全部任务完成！")


if __name__ == "__main__":
    main()