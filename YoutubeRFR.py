import urllib
import urllib.request
from bs4 import BeautifulSoup
import asyncio
import json
import re
from time import time
import requests

async def YTS(textToSearch,alternative=False):
    start = time()
    textToSearch = str(textToSearch)
    query = urllib.parse.quote(textToSearch)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    #await asyncio.sleep(0.1)
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all('script',text=re.compile('var ytInitialData ='))#find correct script tag
    data = re.search(r'ytInitialData = ({.*?});',
                      str(links), flags=re.DOTALL | re.MULTILINE).group(1)#extract JSON
    data = json.loads(data)
    url = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0+int(alternative)]["videoRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    print("Time spent searching: {0} seconds".format(round(time()-start),3))
    return 'https://www.youtube.com' + url

async def YTSFast(q,token):
    start = time()
    params = {'q':q,
              'key':token}
    r = requests.get("https://youtube.googleapis.com/youtube/v3/search", params=params)#"https://youtube.googleapis.com/youtube/v3/search?part=snippet&q={0}&key={}"
    if r.status_code == 200:
        for i in range(0,5):
            if r.json()["items"][0]["id"]["kind"] == "youtube#video":
                print("API took: {0} seconds".format(round(time()-start),4))
                return 'https://www.youtube.com/watch?v=' + r.json()["items"][0]["id"]["videoId"]
    else:
        print(r.status_code)
        print("Doing slow search!!!")
        await YTS(q)
