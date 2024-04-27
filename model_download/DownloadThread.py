import os
import threading
import queue
import requests
from ffmpy import FFmpeg
class DownloadThread(threading.Thread):
    def __init__(self, queue, output_dir):
        threading.Thread.__init__(self)
        self.queue = queue
        self.output_dir = output_dir
    def run(self):
        while True:
            # Get the next URL from the queue
            url = self.queue.get()
            # Download the M3U8 file contents using Requests
            response = requests.get(url)
            m3u8_contents = response.text
            # Extract the video segment URLs from the M3U8 playlist and download them one by one using Requests
            urls = [line.strip() for line in m3u8_contents.split('\n') if line.endswith('.ts')]
            for i, ts_url in enumerate(urls):
                print(f'Downloading {ts_url} ({i+1}/{len(urls)})')
                response = requests.get(ts_url)
                # Save the downloaded video segment to a temporary file
                ts_filename = f'{i:04d}.ts'
                temp_filepath = os.path.join(self.output_dir, ts_filename)
                with open(temp_filepath, 'wb') as f:
                    f.write(response.content)
            # Use FFmpeg to concatenate the video segments and convert them to MP4 format
            print('Converting video segments to MP4')
            input_files = os.path.join(self.output_dir, '*.ts')
            output_file = os.path.join(self.output_dir, 'output.mp4')
            ff = FFmpeg(inputs={input_files: '-pattern_type glob'}, outputs={output_file: None})
            ff.run()
            # Mark the URL as done in the queue
            self.queue.task_done()


if __name__ == '__main__':

    # Define some constants
    NUM_THREADS = 4
    M3U8_URL = 'https://t25.cdn2020.com/video/m3u8/2024/04/19/a6e0e6b4/index.m3u8'
    OUTPUT_DIR = 'output'
    # Create the output directory if it doesn't already exist
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    # Create a queue to hold the download tasks
    queue = queue.Queue()
    # Add the M3U8 URL to the queue as the first task
    queue.put(M3U8_URL)
    # Create a pool of worker threads and start them
    threads = []
    for i in range(NUM_THREADS):
        t = DownloadThread(queue, OUTPUT_DIR)
        t.start()
        threads.append(t)
    # Wait for all tasks to complete before exiting
    queue.join()
    print('All done!')