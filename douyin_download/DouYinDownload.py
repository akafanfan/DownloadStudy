#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import json
import yaml
import time
import threading
import queue

from douyin_download.apiproxy.common import utils
from douyin_download.apiproxy.douyin import douyin_headers
from douyin_download.apiproxy.douyin.douyin import Douyin
from douyin_download.apiproxy.douyin.download import Download

configModel = {
    "link": [],
    "path": os.getcwd(),
    "music": True,
    "cover": True,
    "avatar": True,
    "json": True,
    "folderstyle": True,
    "mode": ["post"],
    "number": {
        "post": 0,
        "like": 0,
        "allmix": 0,
        "mix": 0,
        "music": 0,
    },
    'database': True,
    "increase": {
        "post": False,
        "like": False,
        "allmix": False,
        "mix": False,
        "music": False,
    },
    "thread": 5,
    "cookie": None

}


def argument():
    parser = argparse.ArgumentParser(description='抖音批量下载工具 使用帮助')
    parser.add_argument("--cmd", "-C", help="使用命令行(True)或者配置文件(False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--link", "-l",
                        help="作品(视频或图集)、直播、合集、音乐集合、个人主页的分享链接或者电脑浏览器网址, 可以设置多个链接(删除文案, 保证只有URL, https://v.douyin.com/kcvMpuN/ 或者 https://www.douyin.com/开头的)",
                        type=str, required=False, default=[], action="append")
    parser.add_argument("--path", "-p", help="下载保存位置, 默认当前文件位置",
                        type=str, required=False, default=os.getcwd())
    parser.add_argument("--music", "-m", help="是否下载视频中的音乐(True/False), 默认为True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--cover", "-c", help="是否下载视频的封面(True/False), 默认为True, 当下载视频时有效",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--avatar", "-a", help="是否下载作者的头像(True/False), 默认为True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--json", "-j", help="是否保存获取到的数据(True/False), 默认为True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--folderstyle", "-fs", help="文件保存风格, 默认为True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--mode", "-M",
                        help="link是个人主页时, 设置下载发布的作品(post)或喜欢的作品(like)或者用户所有合集(mix), 默认为post, 可以设置多种模式",
                        type=str, required=False, default=[], action="append")
    parser.add_argument("--postnumber", help="主页下作品下载个数设置, 默认为0 全部下载",
                        type=int, required=False, default=0)
    parser.add_argument("--likenumber", help="主页下喜欢下载个数设置, 默认为0 全部下载",
                        type=int, required=False, default=0)
    parser.add_argument("--allmixnumber", help="主页下合集下载个数设置, 默认为0 全部下载",
                        type=int, required=False, default=0)
    parser.add_argument("--mixnumber", help="单个合集下作品下载个数设置, 默认为0 全部下载",
                        type=int, required=False, default=0)
    parser.add_argument("--musicnumber", help="音乐(原声)下作品下载个数设置, 默认为0 全部下载",
                        type=int, required=False, default=0)
    parser.add_argument("--database", "-d",
                        help="是否使用数据库, 默认为True 使用数据库; 如果不使用数据库, 增量更新不可用",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--postincrease", help="是否开启主页作品增量下载(True/False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--likeincrease", help="是否开启主页喜欢增量下载(True/False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--allmixincrease", help="是否开启主页合集增量下载(True/False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--mixincrease", help="是否开启单个合集下作品增量下载(True/False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--musicincrease", help="是否开启音乐(原声)下作品增量下载(True/False), 默认为False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--thread", "-t",
                        help="设置线程数, 默认5个线程",
                        type=int, required=False, default=5)
    parser.add_argument("--cookie", help="设置cookie, 格式: \"name1=value1; name2=value2;\" 注意要加冒号",
                        type=str, required=False, default='')
    args = parser.parse_args()
    if args.thread <= 0:
        args.thread = 5

    return args


def yamlConfig():
    curPath = os.path.dirname(os.path.realpath(sys.argv[0]))
    yamlPath = os.path.join(curPath, "config.yml")
    f = open(yamlPath, 'r', encoding='utf-8')
    cfg = f.read()
    configDict = yaml.load(stream=cfg, Loader=yaml.FullLoader)

    try:
        if configDict["link"] != None:
            configModel["link"] = configDict["link"]
    except Exception as e:
        print("[  警告  ]:link未设置, 程序退出...\r\n")
    try:
        if configDict["path"] != None:
            configModel["path"] = configDict["path"]
    except Exception as e:
        print("[  警告  ]:path未设置, 使用当前路径...\r\n")
    try:
        if configDict["music"] != None:
            configModel["music"] = configDict["music"]
    except Exception as e:
        print("[  警告  ]:music未设置, 使用默认值True...\r\n")
    try:
        if configDict["cover"] != None:
            configModel["cover"] = configDict["cover"]
    except Exception as e:
        print("[  警告  ]:cover未设置, 使用默认值True...\r\n")
    try:
        if configDict["avatar"] != None:
            configModel["avatar"] = configDict["avatar"]
    except Exception as e:
        print("[  警告  ]:avatar未设置, 使用默认值True...\r\n")
    try:
        if configDict["json"] != None:
            configModel["json"] = configDict["json"]
    except Exception as e:
        print("[  警告  ]:json未设置, 使用默认值True...\r\n")
    try:
        if configDict["folderstyle"] != None:
            configModel["folderstyle"] = configDict["folderstyle"]
    except Exception as e:
        print("[  警告  ]:folderstyle未设置, 使用默认值True...\r\n")
    try:
        if configDict["mode"] != None:
            configModel["mode"] = configDict["mode"]
    except Exception as e:
        print("[  警告  ]:mode未设置, 使用默认值post...\r\n")
    try:
        if configDict["number"]["post"] != None:
            configModel["number"]["post"] = configDict["number"]["post"]
    except Exception as e:
        print("[  警告  ]:post number未设置, 使用默认值0...\r\n")
    try:
        if configDict["number"]["like"] != None:
            configModel["number"]["like"] = configDict["number"]["like"]
    except Exception as e:
        print("[  警告  ]:like number未设置, 使用默认值0...\r\n")
    try:
        if configDict["number"]["allmix"] != None:
            configModel["number"]["allmix"] = configDict["number"]["allmix"]
    except Exception as e:
        print("[  警告  ]:allmix number未设置, 使用默认值0...\r\n")
    try:
        if configDict["number"]["mix"] != None:
            configModel["number"]["mix"] = configDict["number"]["mix"]
    except Exception as e:
        print("[  警告  ]:mix number未设置, 使用默认值0...\r\n")
    try:
        if configDict["number"]["music"] != None:
            configModel["number"]["music"] = configDict["number"]["music"]
    except Exception as e:
        print("[  警告  ]:music number未设置, 使用默认值0...\r\n")
    try:
        if configDict["database"] != None:
            configModel["database"] = configDict["database"]
    except Exception as e:
        print("[  警告  ]:database未设置, 使用默认值False...\r\n")
    try:
        if configDict["increase"]["post"] != None:
            configModel["increase"]["post"] = configDict["increase"]["post"]
    except Exception as e:
        print("[  警告  ]:post 增量更新未设置, 使用默认值False...\r\n")
    try:
        if configDict["increase"]["like"] != None:
            configModel["increase"]["like"] = configDict["increase"]["like"]
    except Exception as e:
        print("[  警告  ]:like 增量更新未设置, 使用默认值False...\r\n")
    try:
        if configDict["increase"]["allmix"] != None:
            configModel["increase"]["allmix"] = configDict["increase"]["allmix"]
    except Exception as e:
        print("[  警告  ]:allmix 增量更新未设置, 使用默认值False...\r\n")
    try:
        if configDict["increase"]["mix"] != None:
            configModel["increase"]["mix"] = configDict["increase"]["mix"]
    except Exception as e:
        print("[  警告  ]:mix 增量更新未设置, 使用默认值False...\r\n")
    try:
        if configDict["increase"]["music"] != None:
            configModel["increase"]["music"] = configDict["increase"]["music"]
    except Exception as e:
        print("[  警告  ]:music 增量更新未设置, 使用默认值False...\r\n")
    try:
        if configDict["thread"] != None:
            configModel["thread"] = configDict["thread"]
    except Exception as e:
        print("[  警告  ]:thread未设置, 使用默认值5...\r\n")
    try:
        if configDict["cookies"] != None:
            cookiekey = configDict["cookies"].keys()
            cookieStr = ""
            for i in cookiekey:
                cookieStr = cookieStr + i + "=" + configDict["cookies"][i] + "; "
            configModel["cookie"] = cookieStr
    except Exception as e:
        pass
    try:
        if configDict["cookie"] != None:
            configModel["cookie"] = configDict["cookie"]
    except Exception as e:
        pass


# 定义全局变量来存储线程运行结果
global thread_result_list

# 定义全局变量来存储颜色代码
global COLOR_GREEN
global COLOR_BLUE
global COLOR_YELLOW
global COLOR_RED
global COLOR_RESET

COLOR_GREEN = "\033[32m"
COLOR_BLUE = "\033[34m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[m"


def main():
    # args = argument()

    # if args.cmd:
    #     configModel["link"] = args.link
    #     configModel["path"] = args.path
    #     configModel["music"] = args.music
    #     configModel["cover"] = args.cover
    #     configModel["avatar"] = args.avatar
    #     configModel["json"] = args.json
    #     configModel["folderstyle"] = args.folderstyle
    #     if args.mode == None or args.mode == []:
    #         args.mode = []
    #         args.mode.append("post")
    #     configModel["mode"] = list(set(args.mode))
    #     configModel["number"]["post"] = args.postnumber
    #     configModel["number"]["like"] = args.likenumber
    #     configModel["number"]["allmix"] = args.allmixnumber
    #     configModel["number"]["mix"] = args.mixnumber
    #     configModel["number"]["music"] = args.musicnumber
    #     configModel["database"] = args.database
    #     configModel["increase"]["post"] = args.postincrease
    #     configModel["increase"]["like"] = args.likeincrease
    #     configModel["increase"]["allmix"] = args.allmixincrease
    #     configModel["increase"]["mix"] = args.mixincrease
    #     configModel["increase"]["music"] = args.musicincrease
    #     configModel["thread"] = args.thread
    #     configModel["cookie"] = args.cookie
    # else:
    yamlConfig()

    if not configModel["link"]:
        return

    if configModel["cookie"] is not None and configModel["cookie"] != "":
        douyin_headers["Cookie"] = configModel["cookie"]

    configModel["path"] = os.path.abspath(configModel["path"])
    print("[  提示  ]:数据保存路径 " + configModel["path"])
    if not os.path.exists(configModel["path"]):
        os.mkdir(configModel["path"])

    dl = Download(thread=configModel["thread"], music=configModel["music"], cover=configModel["cover"],
                  avatar=configModel["avatar"], resjson=configModel["json"],
                  folderstyle=configModel["folderstyle"])
    print("[  提示  ]:准备开始多线程下载 ")
    # 开启多线程下载
    global thread_result_list
    thread_result_list = queue.Queue()
    tasks = []
    for _ in configModel["link"]:
        task_name = _.split(',')[1]
        # 加入线程池
        tasks.append(threading.Thread(target=ready_download, args=(_, dl), name=task_name))
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()
    # 收集节点检查子线程运行结果
    # 输出子线程运行结果
    # 结果集
    result = []
    while not thread_result_list.empty():
        result.append(thread_result_list.get())

    print("[  提示  ]:多线程下载结束 ")
    # 输出 result 中的数据
    for value in result:
        print(f'{COLOR_BLUE}{value}{COLOR_RESET}')


def ready_download(_, dl):
    db = Douyin(database=configModel["database"])
    current_thread = threading.current_thread()
    print(f"Thread {current_thread.name} is downloading")

    # 开始时间
    start = time.time()
    # 主页链接地址
    link = _.split(',')[0]
    # 固定昵称
    name = _.split(',')[1]
    print("--------------------------------------------------------------------------------")
    print(f"[  提示 {current_thread.name}]:正在请求的链接: " + link + "\r\n")
    url = db.getShareLink(link)
    key_type, key = db.getKey(url)
    if key_type == "user":
        user_path = os.path.join(configModel["path"], name)
        if not os.path.exists(user_path):
            os.mkdir(user_path)

        print("--------------------------------------------------------------------------------")
        print(f"[  提示 {current_thread.name}]:正在请求用户主页模式: " + " 昵称：" + name + "\r\n")
        # increase 是否开启主页作品增量下载
        # datalist = db.getUserInfo(key, mode, 18, configModel["number"][mode], configModel["increase"][mode])
        datalist = db.get_user_info(key, name)
        if datalist is not None and datalist != []:
            mode_path = os.path.join(user_path, 'post')
            if not os.path.exists(mode_path):
                os.mkdir(mode_path)
            dl.userDownload(awemeList=datalist, savePath=mode_path)
    end = time.time()  # 结束时间

    print('\n[' + current_thread.name + '下载完成]:总耗时: %d分钟%d秒\n' % (
        int((end - start) / 60), ((end - start) % 60)))  # 输出下载用时时间
    global thread_result_list
    thread_result_list.put(f'下载{name}作品成功')


if __name__ == "__main__":
    main()
