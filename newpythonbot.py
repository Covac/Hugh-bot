import discord
import youtube_dl
import asyncio
from YoutubeRFR import YTS

def deleteSongs():
    import os
    folder = os.listdir(os.getcwd())
    counter = 0
    for file in folder:
        if file.endswith('.py'):#useless line :)
            pass
        elif file.endswith('webm'):
            counter += 1
            os.unlink(file)
        elif file.endswith('m4a'):
            counter += 1
            os.unlink(file)

    print('Deleted {} downloaded files'.format(counter))


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MyClient(discord.Client):
    #rewrite if shit :)
    def __init__(self, *args, **kwargs):
        super(MyClient, self).__init__(*args, **kwargs)
        self.guildQ = {}#potential overflow after billion hours of combined non-stop playing
        self.guildVCs = {}#Enables skipping and pausing of audio
    
    async def on_ready(self):
        deleteSongs()
        print(discord.opus.is_loaded())
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        
        guild = str(message.guild.id)
        
        if not (message.author.bot) :
            print('Message from {0.author} on {0.guild}: {0.content}'.format(message))
            #guildid = message.guild.id
            
        if message.content.startswith('!!play'):
            link = message.content.strip('!!play')
            if (not('http' in link) or not('www.' in link) or not('.com' in link)):
                try:#maybe handle it a different way ************FIX TO BE CONFIRMED****************************
                    link = await YTS(link)#maybe test it without await after lag fix
                except:
                    print("Error trying to find a song... Probably a 'index out of range'")
                    print("Trying to prevent it first")
                    try:
                        link = await YTS(link)#if it fails do the expensive one
                    except:
                        print("Failed to prevent it")
                        await message.channel.send('Error occured while trying to find the song! Try adding it with a link or try again.')

            if not (guild in self.guildQ):
                self.guildQ[guild] = []
                self.guildQ[guild].append(link)
                print(self.guildQ)
                
            elif guild in self.guildQ:
                self.guildQ[guild].append(link)
                print(self.guildQ)
                return None
            
            async with message.channel.typing():
                queuepointer = 0 ###plus 1
                self.guildVCs[guild] = await message.author.voice.channel.connect()
                while True:
                    
                    player = await YTDLSource.from_url(self.guildQ[guild][queuepointer])
                    await message.channel.send('Now playing: {}'.format(player.title))#add duration
                    self.guildVCs[guild].play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                    
                    while self.guildVCs[guild].is_playing():#might be expensive but makes skip work
                        await asyncio.sleep(2)
                        
                    queuepointer += 1
                    if len(self.guildQ[guild]) <= queuepointer:
                        break
                        
                await self.guildVCs[guild].disconnect()
                del self.guildQ[guild]

        if message.content.startswith('!!skip'):
            if self.guildVCs[guild].is_playing():
                self.guildVCs[guild].stop()
                
            else:
                print('There is nothing to skip!')

                                
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
TOKEN = os.environ['CLIENT_TOKEN']
client = MyClient()
client.run(TOKEN)
