# encoding: utf-8
from scapy.all import sniff, wrpcap, random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import config
from os import path
from urllib.parse import urlparse
from threading import Thread
from time import sleep


configs = config.configs


def capTraffic(website_name, tag):
    """
    macOS11当前存在问题，导致不能使用filter
    see: https://github.com/home-assistant/core/issues/45846

    虽然stop_filter可以设置抓包停止条件，但是由于是browser和sniff是串行的，所以无法在中间执行点击命令
    """
    print(7777777)
    pcap_path = configs.get('path') + website_name + str(tag) + ".pcap"
    dpkt = sniff(iface=configs.get('iface'), filter='tcp', timeout=configs.get('capture_timeout'))
    # 抓包 # prn=lambda x: x.show(),
    # pkts = sniff(prn=lambda x : x.sprintf("{IP:%IP.src% -> %IP.dst%\n}{Raw:%Raw.load%\n}"))
    wrpcap(pcap_path, dpkt)
    print("网页 " + website_name + " 抓包结束结束，pcap地址为：" + pcap_path + "\n")


def handleSelenium(url: str, tag):
    """
    chromedriver下载地址 http://npm.taobao.org/mirrors/chromedriver/
    当下版本为91.0.4472.114，用chrome://version查看版本
    """
    print('123123')
    driver_path = path.join(path.dirname(path.abspath(__file__)), 'resources/chromedriver')
    if configs.get('use_ip_poll') is True:
        chrome_options = Options()
        proxy = random.choice(config.proxy_arr)
        chrome_options.add_argument(proxy)
        browser = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    else:
        browser = webdriver.Chrome(executable_path=driver_path)

    if not url.startswith("http"):
        url = "http://" + url
    try:
        browser.set_window_size(800, 800)
        browser.get(url)

        # 不需要点击事件的话可以单进程顺序执行
        # capTraffic(urlparse(url)[1], str(tag))

        # 10s之后进行点击
        sleep_time = configs.get('capture_timeout') / 3
        sleep(sleep_time)
        # 点击(400,600)的位置，不一定准确
        ActionChains(browser).move_by_offset(200, 100).click().perform()
        sleep(sleep_time)
    except Exception as e:
        print(url + " 不能访问")
        print(e)
    finally:
        browser.close()
    print("模拟访问 " + url + " 结束")


def start_cap():
    urls = []
    with open('./resources/video_urls.txt', 'r') as f:
        for line in f.readlines():
            urls.append(line.strip())

    for i in range(configs.get('wrap_count')):
        for each_url in urls:
            # handleSelenium(each_url, i)
            # 多进程搞一搞
            t1 = Thread(target=handleSelenium, args=(each_url, i))
            t2 = Thread(target=capTraffic, args=(urlparse(each_url)[1], i))
            t1.start()
            t2.start()
            sleep(5)


if __name__ == '__main__':
    """
    基本思路：
    从配置文件中读取网卡信息，每次抓包持续的时间，读取每一个音视频页面avList的url
    开始scapy抓包，调用selenium访问url，保存为pcap文件，关闭当前访问页面
    avList循环10轮
    
    防爬虫：设置代理IP池；
    播放视频：10s后用selenium模拟点击中心
    要么开多进程，要么换tcpdump后台执行
    """
    start_cap()
