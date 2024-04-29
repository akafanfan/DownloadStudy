import requests
import json
import pymysql
import time
import datetime

cook =  headers=douyin_headers
# 定义获取视频列表的URL地址
URL = "https://www.douyin.com/aweme/v1/web/aweme/post/?"
HEADERS = {
    "referer": 'https://www.douyin.com/user/MS4wLjABAAAAHem01myZ0J6SCouppAy6Tk9rueMJuTy4sbe6ptfQwVc',
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    "cookie": cook
}
# 设置请求参数
params = {
    'device_platform': 'webapp',
    'sec_user_id': 'MS4wLjABAAAAj6beq4yBLdA3cTB7P-9cYKP1WU8h-L3aBT0Xfun30h_pXkTeaVKF1hnMUmCLA603',
    'count': '18',
    'max_cursor': '0',
    'aid': '6383',
    'webid': '7250374762605479424',
    'cookie_enabled': True
}

config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'rootpassword',
    'db': 'Tiktok',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
# 连接数据库
# conn = pymysql.connect(**config)
# table_name = 'qzbk'
# # 插入数据到数据库中
# cursor = conn.cursor()
# create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (aweme_id VARCHAR(255), group_id VARCHAR(255), create_time DATETIME, api_max_cursor VARCHAR(255), video_desc TEXT, admire_count INT, collect_count INT, comment_count INT, digg_count INT, play_count INT, share_count INT, videos_play_addr1 TEXT, videos_play_addr2 TEXT, videos_play_addr3 TEXT)"
# cursor.execute(create_table_query)
#
# sql = "INSERT INTO `qzbk`(`aweme_id`, `group_id`, `create_time`, `api_max_cursor`, `video_desc`, `admire_count`, `collect_count`, `comment_count`, `digg_count`, `play_count`, `share_count`, `videos_play_addr1`, `videos_play_addr2`, `videos_play_addr3`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

video_list = []
# 循环获取所有视频信息
while True:
    print(params)
    max_cursor_in = params['max_cursor']

    # 发送请求并获取响应结果
    response = requests.get(URL, headers=HEADERS, params=params, verify=False)
    # 将响应结果转换为JSON格式
    data = json.loads(response.text)
    # 获取视频列表
    aweme_list = data['aweme_list']
    # print(aweme_list)
    # 将视频信息添加到视频列表中
    video_list.extend(aweme_list)

    # 将视频信息写入数据库中
    for item in aweme_list:
        aweme_id = item['aweme_id']
        group_id = item['group_id']
        create_time_timestamp = item['create_time']  # timestamp
        create_time = datetime.datetime.fromtimestamp(create_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        video_desc = item['desc']

        admire_count = item['statistics']['admire_count']
        collect_count = item['statistics']['collect_count']
        comment_count = item['statistics']['comment_count']
        digg_count = item['statistics']['digg_count']
        play_count = item['statistics']['play_count']
        share_count = item['statistics']['share_count']

        video = item['video']
        videos_play_addr1 = video['play_addr']['url_list'][0]
        videos_play_addr2 = video['play_addr']['url_list'][1]
        videos_play_addr3 = video['play_addr']['url_list'][2]
        print(aweme_id, group_id, create_time, video_desc)
        print(item['statistics'])
        print(videos_play_addr1, videos_play_addr2, videos_play_addr3)
        cursor.execute(sql, (
        aweme_id, group_id, create_time, max_cursor_in, video_desc, admire_count, collect_count, comment_count,
        digg_count, play_count, share_count, videos_play_addr1, videos_play_addr2, videos_play_addr3))
    print("数据插入成功")

    # 判断是否还有下一页
    if data['has_more']:
        params['max_cursor'] = data['max_cursor']  # 更新max_cursor参数
        time.sleep(1)
    else:  # 如果没有下一页，则退出循环
        break

# 提交更改并关闭连接
conn.commit()
conn.close()