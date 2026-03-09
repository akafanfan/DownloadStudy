import re
import subprocess
import os
from pathlib import Path
import time

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, DownloadColumn, TransferSpeedColumn
from rich.panel import Panel
from rich import print as rprint  # rich 的 print，支持样式

from tai_download.DownloadWithNoMd import get_taiav_m3u8

console = Console()

def print_rich_ffmpeg_output(process, show_progress: bool = True):
    """
    解析 ffmpeg -progress pipe:1 的多行键值对格式，并用 rich 美化显示
    """
    if not show_progress:
        for line in iter(process.stdout.readline, ''):
            console.print(line.strip())
        return

    # 用于暂存当前进度组的字段
    current_progress = {}
    last_displayed_time = ""  # 避免重复打印相同时间点

    with Progress(
        TextColumn("[bold cyan]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeElapsedColumn(),
        transient=True
    ) as progress:

        task = progress.add_task("[cyan]下载视频中...", total=None)

        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue

            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                current_progress[key] = value

            # 当遇到 progress=continue 或 progress=end 时，认为一组完成
            if line.startswith('progress='):
                # 提取关键信息
                frame = current_progress.get('frame', 'N/A')
                fps = current_progress.get('fps', 'N/A')
                time_str = current_progress.get('out_time', 'N/A')
                size_str = current_progress.get('total_size', current_progress.get('size', 'N/A'))
                bitrate = current_progress.get('bitrate', 'N/A')
                speed = current_progress.get('speed', 'N/A')

                # 只在时间变化时更新（避免刷屏）
                if time_str != last_displayed_time:
                    last_displayed_time = time_str

                    desc = f"[cyan]正在下载  [magenta]{size_str}[/magenta]  已用 [yellow]{time_str}[/yellow]"
                    if speed != 'N/A':
                        desc += f"  速度 [green]{speed}[/green]"
                    if fps != 'N/A':
                        desc += f"  fps [blue]{fps}[/blue]"

                    progress.update(task, description=desc)

                    # 同时打印简洁一行总结（可选）
                    console.print(
                        f"[dim]帧: {frame} | 时间: {time_str} | 速度: {speed} | 大小: {size_str}[/dim]"
                    )

                # 清空当前组，准备下一组
                current_progress.clear()

            # 处理其他非进度行
            elif 'Opening' in line:
                console.print(f"[blue]↳ {line}[/blue]")

            elif any(word in line.lower() for word in ['error', 'failed', 'cannot', 'invalid']):
                console.print(Panel(
                    f"[bold red]{line}[/bold red]",
                    title="⚠️  出现问题",
                    border_style="red",
                    expand=False
                ))

            elif 'hls @' in line:
                console.print(f"[dim]{line}[/dim]")

            elif any(word in line for word in ['Input #', 'Stream #', 'Metadata:']):
                console.print(f"[light_blue]{line}[/light_blue]")

            else:
                # 其他行直接打印（比如初始的 Opening crypto+...）
                console.print(line)
def download_taiav_video(
    m3u8_url: str,
    output_file: str,
    quality: str = "1280",
    ffmpeg_path: str = "ffmpeg",
    extra_ffmpeg_args: list = None,
    timeout_get_m3u8: int = 15,
    show_progress: bool = True,
    http_proxy: str = "http://127.0.0.1:7897",
    https_proxy: str = "http://127.0.0.1:7897"
) -> bool:
    """
    下载 m3u8 视频，使用 rich 美化实时日志
    """
    if not output_file.lower().endswith(('.mp4', '.mkv', '.ts')):
        console.print("[yellow]警告：建议输出文件以 .mp4 结尾[/yellow]")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]目标保存路径:[/bold] {output_path.absolute()}")

    # 构建 ffmpeg 命令
    cmd = [
        ffmpeg_path,
        "-headers", f"Referer: {m3u8_url}\r\n"
                    f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36\r\n",
        "-i", m3u8_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-progress", "pipe:1",          # 启用进度输出
        "-y"
    ]

    if extra_ffmpeg_args:
        cmd.extend(extra_ffmpeg_args)

    cmd.append(str(output_path))

    if show_progress:
        console.print("[bold yellow]即将执行的 ffmpeg 命令：[/bold yellow]")
        console.print(" ".join(cmd))
        console.print("\n[bold cyan]═" * 60 + "[/bold cyan]")
        console.print("[bold green]开始下载...（进度将实时显示）[/bold green]\n")

    try:
        start_time = time.time()

        env = os.environ.copy()
        if http_proxy:
            env["http_proxy"] = http_proxy
            env["HTTP_PROXY"] = http_proxy
        if https_proxy:
            env["https_proxy"] = https_proxy
            env["HTTPS_PROXY"] = https_proxy

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # 使用 rich 美化实时输出
        print_rich_ffmpeg_output(process, show_progress=show_progress)

        return_code = process.wait()

        elapsed = time.time() - start_time

        if return_code == 0:
            console.print("\n" + "[bold cyan]═" * 60 + "[/bold cyan]")
            console.print(f"[bold green]✓ 下载完成！用时 {elapsed:.1f} 秒[/bold green]")
            console.print(f"[bold]文件已保存至:[/bold] {output_path.absolute()}")
            return True
        else:
            console.print(f"\n[bold red]ffmpeg 异常结束，返回码: {return_code}[/bold red]")
            return False

    except FileNotFoundError:
        console.print(f"\n[bold red]错误：找不到 ffmpeg → {ffmpeg_path}[/bold red]")
        return False

    except Exception as e:
        console.print(f"\n[bold red]意外错误: {e}[/bold red]")
        return False


# ────────────────────────────────────────────────
# 使用示例
# ────────────────────────────────────────────────

if __name__ == "__main__":
    url = "https://taiav.com/cn/movie/683d16c08bb62c0d8cc5b5aa"
    m3u8 = get_taiav_m3u8(url, quality="1280")
    if m3u8:
        print("当前 m3u8:", m3u8)
        # 示例输出可能像：
        # https://taiav
    download_taiav_video(
        m3u8_url=m3u8,
        output_file=r"D:\Documents\GitHub\DownloadStudy\tai_download\model\姚宛儿_浴室尿失禁.mp4",
        http_proxy="http://127.0.0.1:7897",
        https_proxy="http://127.0.0.1:7897"
    )