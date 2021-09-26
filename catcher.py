import net
from pyquery import PyQuery as pq
from tqdm import tqdm
import json
from queue import Queue
from threading import Thread
import time
import m3u8

class Catcher:
    def __init__(self):
        self.net = net.Net()
        # self.m3u8 = m3u8.M3U8_Downloader(50)
        self.video_page_queue = Queue()
        self.video_page_scapre_thread_num = 50  # the max number of debug thread 
        self.video_page_thread_list = []
        self.video_page_links = []
        # self.scrape_all_video_page_link()
        # self.loading_video_page_links()  # load saved video page list

        self.video_download_links = []
        self.video_download_links_queue = Queue()
        self.video_download_links_queue_thread_num = 50
        # self.get_video_download_link_start_thread()
        # self.loading_video_download_link()  # load saved video download links

    def download_video(self,url):
        self.net.Download(url)
        print("finished!!")

    def loading_video_download_link(self):
        f = open("Video_Download_Link.txt", 'r')
        data = json.load(f)
        f.close()
        self.video_download_links = data

    def get_video_download_links(self, link):
        header = ""
        rs = self.net.Get(url=link, header_string=header)
        data = rs.content.decode()
        Get_3gp_link = self.net.preg_get_word('file: "(https://.+\.3gp)"', 1, data)
        return Get_3gp_link

    def thread_video_download_link(self):
        while self.video_download_links_queue.qsize() != 0:
            link = self.video_download_links_queue.get()
            download_link = self.get_video_download_links(link)
            self.video_download_links.append(download_link)

            time.sleep(0.2)

    def get_video_download_link_start_thread(self):
        for page_link in self.video_page_links[0:300]:
            self.video_download_links_queue.put(page_link)

        for n in range(self.video_download_links_queue_thread_num):
            t = Thread(target=self.thread_video_download_link)
            t.start()

        print("start to get video")
        total_mission = self.video_download_links_queue.qsize()

        while self.video_download_links_queue.qsize() != 0:
            print("link progress: {}/{}".format(self.video_download_links_queue.qsize(), total_mission))
            time.sleep(1)

        fp = open("Video_Download_Link.txt", "w+")
        fp.write(json.dumps(self.video_download_links))
        fp.close()
        print("work finished")

    def loading_video_page_links(self):
        file_name = "Video_Page_Link.txt"
        f = open(file_name, "r")
        data = f.read()
        f.close()
        self.video_page_links = json.loads(data)

    def get_page_max_number(self):
        url = "https://airav.cc/index.aspx?idx=1"
        header = "Host: airav.cc###Connection: keep-alive###Cache-Control: max-age=0###Upgrade-Insecure-Requests: 1###User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36###Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8###Accept-Encoding: gzip, deflate, br###Accept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        rs = self.net.Get(url =url, header_string =header)
        data = rs.content.decode()
        py_txt = pq(data).find(".nextback")
        last_page_num_element = py_txt.eq(len(py_txt) -1).html()
        last_page_num = pq(last_page_num_element).attr('href').replace("/index.aspx?idx=","")
        return int(last_page_num)

    def get_page_video(self,page_num):
        url = "https://airav.cc/index.aspx?idx="+format(page_num)
        header = "Host: airav.cc###Connection: keep-alive###Cache-Control: max-age=0###Upgrade-Insecure-Requests: 1###User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36###Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8###Accept-Encoding: gzip, deflate, br###Accept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        rs = self.net.Get(url=url, header_string=header)
        data = rs.content.decode()
        list_item = pq(data).find('.listItem')

        video_list = []
        for video_item in list_item:
            link = pq(video_item).find('.ga_click').attr('href')
            link = "https://airav.cc/" + link
            video_list.append(link)

        return video_list
    
    def thread_get_page_video(self):
        while self.video_page_queue.qsize() != 0:
            page_number = self.video_page_queue.get()
            links = self.get_page_video(page_number)
            for link in links:
                self.video_page_links.append(link)

            time.sleep(0.2)

    def scrape_all_video_page_link(self):
        page_max = self.video_page_queue.get()
        all_links = []
        for n in tqdm(range(1,page_max), desc="distributing task"):
            self.video_page_queue.put(n)

        for n in range(self.video_page_scapre_thread_num):
            t = Thread(target=self.thread_get_page_video)
            t.start()

            self.video_page_thread_list.append(t)

        total_mission = self.video_download_links_queue.qsize()
        while self.video_page_queue.qsize() != 0:
            print("debug progress: {}/{}".format(self.video_page_queue.qsize(), total_mission))
            time.sleep(1)

        f = open("Video_Page_Link.txt", 'w+')
        f.write(json.dumps(self.video_page_links))
        f.close()
    

if __name__ == "__main__":
    obj = Catcher()
    obj.get_video_download_link_start_thread()
    # obj.download_video(obj.video_download_links[0])