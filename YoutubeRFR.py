import urllib
import urllib.request
from bs4 import BeautifulSoup
import asyncio


async def YTS(textToSearch, fastsearch=True):
    textToSearch = str(textToSearch)
    query = urllib.parse.quote(textToSearch)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    if fastsearch:#FUCKING WORTH!!!
        hlen = len(html)
        slicer1 = hlen // 3
        slicer2 = hlen // 2 #50% found 25% not found 30% not found
        html = html[slicer1:slicer2]
    #await asyncio.sleep(0.1)
    soup = BeautifulSoup(html, "html.parser")
    links = soup.findAll(attrs={'class':'yt-uix-tile-link'})
    return 'https://www.youtube.com' + links[0]['href']
