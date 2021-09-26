import requests
from pyquery import PyQuery as pq
from tqdm import tqdm
from collections import OrderedDict

# TODO: 優化程式碼
class PornSearcher:
    def __init__(self, key_word=None):
        self.__web = "https://www.pornhub.com"
        self.__videos = []
        if key_word:
            self.__res = requests.get(self.__web + '/video/search', params={'search': key_word})
            self.__suffix = '/&page='
        else:
            self.__res = requests.get(self.__web)
            self.__suffix = "/video?page="

        if self.__res.status_code != 200:
            exit

        self.__max_page = self.__getMaxPage()
        self.getVideoUrl()

    def __getMaxPage(self):
        rs = self.__res
        max_page = 0
        while rs.status_code == requests.codes.ok:
            buttons = [self.__web + button.attr['href'] for button in pq(rs.content.decode())('a').items() if (class_ := button.attr['class']) and class_ == 'greyButton']

            if len(buttons) > 0 and max_page < (new_max := int(buttons[-1][(buttons[-1].find('page=')+5):])):
                rs = requests.get(buttons[-1])
                max_page = new_max
            else:
                return max_page

    def getVideoUrl(self):
        # TODO: 使用thread同步下載
        rs = self.__res
        for i in tqdm(range(self.__max_page), desc="copy link"):
            videos = [href for element in pq(rs.content.decode())('a').items() if (href := element.attr['href']) and href.find('viewkey') != -1]

            # 網址統一
            for i, url in enumerate(videos):
                if url.find(self.__web) == -1:
                    videos[i] = self.__web + url

            self.__videos += list(OrderedDict.fromkeys(videos))

            if i < self.__max_page:
                rs = requests.get(self.__res.url + self.__suffix + str(i))

    def getVideos(self):
        return self.__videos

    def download(self, filename="pornhub_url"):
        with open(filename + ".txt", 'w', encoding='UTF-8') as f:
            for url in tqdm(self.__videos, desc="download to file"):
                f.write(url + '\n')
                
        return True

if __name__ == "__main__":
    obj = PornSearcher('lesbian')
    videos = obj.getVideos()
    obj.download()
