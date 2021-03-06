import requests
from bs4 import BeautifulSoup as BS
from tqdm import tqdm
from threading import Lock, Thread
import time
from queue import Queue
import random
from fake_useragent import UserAgent
# from easy_json import Json

HTTP = "https://"

random.seed()
sleep = lambda: time.sleep(random.uniform(1., 5.))

class Requests:
    user_agent = UserAgent()

    @classmethod
    def get(cls, url, headers={}, params=None, proxies=False, cookies=None, stream=False):
        # 添加隨機的使用者代理
        headers['User-Agent'] = cls.user_agent.random

        if proxies:
            # 使用代理（記得打開docker的proxypool），不然會造成[WinError] 10061
            proxy = requests.get('http://localhost:5555/random').text.strip()
            proxies = {
                'http': 'http://' + proxy,
                'https': 'https://' + proxy,
            }
        else:
            proxies = None

        try:
            # NOTE: 報錯400是因為urllib3版本太高
            return requests.get(url, headers=headers, params=params, proxies=proxies, cookies=cookies, stream=stream)
        except ConnectionError:
            print("Connection error")
            return None

    @classmethod
    def post(cls, url, headers=None):
        pass

class UrlCatcher:
    def __init__(self, url, thread_count=1):
        self.__url = HTTP + url
        self.__videos = {}
        # self.__config = Json("./config.json")
        self.__task_count = 0
        self.__threads = []  # 防止download先於thread前執行，因此要把thread存入並使用.join()來等待
        self.__thread_count = thread_count
        self.__lock = Lock()
        self.__queue = Queue()
        self.__headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
            "Accept-Encoding": "gzip, deflate, br", 
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7", 
            "Host": self.__url.replace('https://', ''), 
            "Upgrade-Insecure-Requests": "1", 
        }

    def searchAll(self, key=None, page_start=1, page_end=1):
        self.clear()

        # 獲取總頁數
        url, params = self.__changeUrlAndParams(key, page_start)
        max_page = self.__getMaxPage(Requests.get(url, headers=self.__headers, params=params))
        print(f'[{time.ctime()}] {key} has {max_page} pages.')

        self.__getVideoUrls(key, max(1,page_start), min(page_end, max_page))

        return True

    def __getMaxPage(self, rs):
        max_page = 0

        # NOTE: 設定 len(style) == 1 是因為要排除某些也使用greyButton但不是頁碼的DOM物件
        while len(buttons := [ele for ele in BS(rs.content.decode(), 'html.parser')('a') if (style := ele.get('class')) and len(style) == 1 and ('greyButton' in style)]) > 0:
            # NOTE: 因為ele是BeautifulSoup的Tag物件，可以直接用text取值
            if max_page < (page := int(buttons[-1].text)):
                max_page = page
                sleep()  # 太快響應會造成pornhub鎖ip
                rs = Requests.get(self.__url + buttons[-1].get('href'), headers=self.__headers, stream=True)
            else: break
        
        return max_page

    def __getVideoUrls(self, key, page_start, page_end):
        # NOTE: 不設定range(1, max) = [1, max - 1]，所以要設定 +1 讓它到最後一頁
        for i in range(page_start, page_end + 1):
            # NOTE: 因為dict是傳址，所以要用copy函數解決page都是一樣的問題。
            self.__queue.put(self.__changeUrlAndParams(key, i))

        # 新增進度條
        self.__task_count = 0
        for i in range(self.__thread_count):
            t = Thread(target=self.__getVideoUrl)
            t.start()
            self.__threads.append(t)

        t = time.time()
        while self.__task_count != (page := page_end - page_start + 1):
            # NOTE: 解決所有thread都還在執行時，剩餘時間估算錯誤的問題
            if self.__task_count == 0:
                cost_time = "??:??:??"
            else:
                cost_time = time.strftime("%H:%M:%S", time.gmtime((time.time() - t) / self.__task_count * (page - self.__task_count)))

            print(f"[{time.ctime()}] copy link: {self.__task_count}/{page}({(self.__task_count) / page:.2%}) - remain=" + cost_time)
            time.sleep(1)

        # NOTE: 等待所有copy link都完成才能做寫入的動作，不然download都會早於thread前寫入
        for i in range(len(self.__threads)):
            self.__threads[i].join()

        print(f"[{time.ctime()}] copy link: {page}/{page}(100%) - total=" + time.strftime("%H:%M:%S", time.gmtime(time.time() - t)))

    def search(self, key=None, page=1):
        self.clear()

        # NOTE: 為了不破壞原本的平行處理機制，因此還是把 url 跟 params 存入queue裡面，
        #       然後 getVideoUrl從queue裡面撈值進行處理
        self.__queue.put(self.__changeUrlAndParams(key, page))
        self.__getVideoUrl()

        return True

    def clear(self):
        self.__videos = {}
        self.__threads = []

    def __changeUrlAndParams(self, key, page):
        url = self.__url + '/video/search' if key else self.__url
        params = {'search' : key} if key else {}

        if page > 1:
            params['page'] = page

            # NOTE: 處理pornhub第一頁和第二頁的網址多一個/video的問題。
            url += "/video" if url == self.__url else ""

        return url, params

    def __getVideoUrl(self):
        while self.__queue.qsize() != 0:
            sleep()  # 太快響應會造成pornhub鎖ip
            args = self.__queue.get_nowait()
            rs = Requests.get(args[0], params=args[1], headers=self.__headers)
            videos = {}

            # 讀取網頁所有影片的DOM物件
            for i, v in enumerate(tqdm([ele for ele in BS(rs.content.decode(), 'html.parser')('a') if (href := ele.get('href')) and href.find('viewkey') != -1], desc='catch links')):
                # 網址統一
                # NOTE: 要放在搜尋標題之前，不然Requese會因為href不正確而發生[Errno 11001] getaddrinfo failed'的錯誤
                v['href'] = (self.__url if v.get('href').find(self.__url) == -1 else "") + v.get('href')

                if v.get('title') is None:
                    # NOTE: 根據href開啟影片網址然後去抓title
                    sleep()  # 太快響應會造成pornhub鎖ip
                    video = [ele for ele in BS(Requests.get(v.get('href'), headers=self.__headers).content.decode(), 'html.parser')('span') if (style := ele.get('class')) and 'inlineFree' in style]

                    # NOTE: 如果找不到標題就命名unknown
                    v['title'] = video[0].text if len(video) > 0 else f"unknown{i}"

                # NOTE: 利用字典的特性來排除重複的網址
                if v.get('href') not in videos:
                    # NOTE: 網址統一加前綴
                    videos[v.get('href')] = v.get('title')

            # NOTE: 因為__videos對thread來說是global，所以要用lock處理，不然可能會有資料遺失的問題
            self.__lock.acquire()
            self.__videos |= videos
            self.__task_count += 1
            self.__lock.release()

            self.__queue.task_done()

    def download(self, filename):
        with open(filename + ".txt", 'w', encoding='UTF-8') as f:
            for url, title in tqdm(self.__videos.items(), total=len(self.__videos), desc="download to file"):
                f.write(title + "(" + url + ')\n')
                
        return True

if __name__ == "__main__":
    obj = UrlCatcher('www.youtube.com', thread_count=5)
    obj.searchAll('music', page_end=5)
    obj.download(filename="test")