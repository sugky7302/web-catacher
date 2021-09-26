import requests
from bs4 import BeautifulSoup as BS
from tqdm import tqdm
from threading import Lock, Thread
import time
from queue import Queue
# from easy_json import Json

class UrlCatcher:
    def __init__(self, url, thread_count=10):
        self.__url = url
        self.__videos = {}
        # self.__config = Json("./config.json")
        self.__threads = []  # 防止download先於thread前執行，因此要把thread存入並使用.join()來等待
        self.__thread_count = thread_count
        self.__lock = Lock()
        self.__queue = Queue()


    def search(self, key=None, page=0):
        url = self.__url + '/video/search' if key else self.__url
        params = {'search' : key} if key else {}
    
        if page < 1:
            self.__getVideoUrls(url, params, self.__getMaxPage(requests.get(url, params=params)))
        else:
            self.__getVideoUrls(url, params, page)

        return True


    def __getMaxPage(self, rs):
        max_page = 0

        # NOTE: 設定 len(style) == 1 是因為要排除某些也使用greyButton但不是頁碼的DOM物件
        while len(buttons := [ele for ele in BS(rs.content.decode(), 'html.parser')('a') if (style := ele.get('class')) and len(style) == 1 and ('greyButton' in style)]) > 0:
            # NOTE: 因為ele是BeautifulSoup的Tag物件，可以直接用text取值
            if max_page < (page := int(buttons[-1].text)):
                max_page = page
                rs = requests.get(self.__url + buttons[-1].get('href'), stream=True)
            else: break
        
        return max_page

    def __getVideoUrls(self, url, params, page):
        # NOTE: 不設定range(1, max) = [1, max - 1]，所以要設定 +1 讓它到最後一頁
        for i in range(1, page + 1):
            if page > 1:
                params['page'] = i

                # NOTE: 處理pornhub第一頁和第二頁的網址多一個/video的問題
                url += "/video" if url == self.__url else ""

            self.__queue.put((url, params))

        # 新增進度條
        for i in range(self.__thread_count):
            t = Thread(target=self.__getVideoUrl)
            t.start()
            self.__threads.append(t)

        t = time.time()
        while (size := self.__queue.qsize()) != 0:
            print(f"[{time.ctime()}] copy link: {(r:=page-size)}/{page}({(r) / page:.2%}) - remain=" + time.strftime("%H:%M:%S", time.gmtime((time.time() - t) / r * size)))
            time.sleep(1)

        print(f"[{time.ctime()}] copy link: {page}/{page}(100%) - total=" + time.strftime("%H:%M:%S", time.gmtime(time.time() - t)))

    def __getVideoUrl(self):
        while self.__queue.qsize() != 0:
            args = self.__queue.get_nowait()
            rs = requests.get(args[0], params=args[1])
            videos = {}

            # 讀取網頁所有影片的DOM物件
            for i, v in enumerate([ele for ele in BS(rs.content.decode(), 'html.parser')('a') if (href := ele.get('href')) and href.find('viewkey') != -1]):
                if v.get('title') is None:
                    # NOTE: 根據href開啟影片網址然後去抓title
                    video = [ele for ele in BS(requests.get(self.__url + v.get('href')).content.decode(), 'html.parser')('span') if (style := ele.get('class')) and 'inlineFree' in style]

                    # NOTE: 如果找不到標題就命名unknown
                    v['title'] = video[0].text if len(video) > 0 else f"unknown{i}"
                
                # NOTE: 利用字典的特性來排除重複的網址
                if v.get('title') not in videos:
                    # NOTE: 網址統一加前綴
                    videos[v.get('title')] = (self.__url if v.get('href').find(self.__url) == -1 else "") + v.get('href')

            # NOTE: 因為__videos對thread來說是global，所以要用lock處理，不然可能會有資料遺失的問題
            self.__lock.acquire()
            self.__videos |= videos
            self.__lock.release()

            self.__queue.task_done()


    def download(self, filename):
        # NOTE: 等待所有copy link都完成才能做寫入的動作，不然download都會早於thread前寫入
        for i in range(self.__thread_count):
            self.__threads[i].join()

        with open(filename + ".txt", 'w', encoding='UTF-8') as f:
            for title, url in tqdm(self.__videos.items(), total=len(self.__videos), desc="download to file"):
                f.write(title + "(" + url + ')\n')
                
        return True

if __name__ == "__main__":
    obj = UrlCatcher('https://www.pornhub.com', thread_count=1)
    obj.search("健身", page=1)
    obj.download(filename="pornhub")



