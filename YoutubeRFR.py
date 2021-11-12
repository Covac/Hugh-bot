import urllib
import urllib.request
from bs4 import BeautifulSoup
import asyncio
import json
import re

async def YTS(textToSearch):
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
    url = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["videoRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    return 'https://www.youtube.com' + url
