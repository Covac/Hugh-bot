import discord
import yt_dlp as youtube_dl
import asyncio
from YoutubeRFR import YTS,YTSFast
import os
import openai
import re
import concurrent.futures
from functools import partial
from datetime import datetime,timedelta

from string import punctuation as p
from random import randint


async def deleteSongs(sch):
    while True:
        await asyncio.sleep(sch)
        folder = os.listdir(os.getcwd())
        counter = 0
        for file in folder:
            try:
                if file.endswith('webm'):
                    os.unlink(file)
                    counter += 1
                elif file.endswith('m4a'):
                    os.unlink(file)
                    counter += 1
            except:
                print(f"{file} is being used ATM, skipping it!")
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
        if os.getenv('MULTITHREAD') != 'true':
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        else:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                prepare = partial(ytdl.extract_info, url, download=not stream)
                data = await loop.run_in_executor(pool, prepare)
        if 'entries' in data:
            #take first item from a playlist
            data = data['entries'][0]#Think they moved shit again
            pass
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MyClient(discord.Client):
    #rewrite if shit :)
    def __init__(self, token, *args, **kwargs):
        super(MyClient, self).__init__(*args, **kwargs)
        self.guildQ = {}#potential overflow after billion hours of combined non-stop playing
        self.guildVCs = {}#Enables skipping and pausing of audio
        self.guildMute = {}#Server mute
        self.noSwearing = ["Don't be rude!","No swearing allowed!","Did you know that GPT-3 guidelines forbid me to generate profanity?","Tell that to your mom.","You dare use my own spells against me Potter?","Did you hear me laugh?"]
        self.URLPattern = re.compile("""((?:(http|https|Http|Https|rtsp|Rtsp):\/\/(?:(?:[a-zA-Z0-9\$\-\_\.\+\!\*\'\(\)\,\;\?\&\=]|(?:\%[a-fA-F0-9]{2})){1,64}(?:\:(?:[a-zA-Z0-9\$\-\_\.\+\!\*\'\(\)\,\;\?\&\=]|(?:\%[a-fA-F0-9]{2})){1,25})?\@)?)?((?:(?:[a-zA-Z0-9][a-zA-Z0-9\-]{0,64}\.)+(?:(?:aero|arpa|asia|a[cdefgilmnoqrstuwxz])|(?:biz|b[abdefghijmnorstvwyz])|(?:cat|com|coop|c[acdfghiklmnoruvxyz])|d[ejkmoz]|(?:edu|e[cegrstu])|f[ijkmor]|(?:gov|g[abdefghilmnpqrstuwy])|h[kmnrtu]|(?:info|int|i[delmnoqrst])|(?:jobs|j[emop])|k[eghimnrwyz]|l[abcikrstuvy]|(?:mil|mobi|museum|m[acdghklmnopqrstuvwxyz])|(?:name|net|n[acefgilopruz])|(?:org|om)|(?:pro|p[aefghklmnrstwy])|qa|r[eouw]|s[abcdeghijklmnortuvyz]|(?:tel|travel|t[cdfghjklmnoprtvwz])|u[agkmsyz]|v[aceginu]|w[fs]|y[etu]|z[amw]))|(?:(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9][0-9]|[1-9])\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9][0-9]|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9][0-9]|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9][0-9]|[0-9])))(?:\:\d{1,5})?)(\/(?:(?:[a-zA-Z0-9\;\/\?\:\@\&\=\#\~\-\.\+\!\*\'\(\)\,\_])|(?:\%[a-fA-F0-9]{2}))*)?(?:\b|$)""")#Regex WEB_URL_PATTERN from android.text.util.Linkify(2.0)
        self.googleToken = token

    def respond_or_not(self,message):
        words = message.split(' ')
        for word in words:
            if self.URLPattern.match(word) and len(words)<2:
                return False
            else:
                return True
        
    def classify_content(self,content_to_classify):
        response = openai.Completion.create(
                      engine="content-filter-alpha",
                      prompt = "<|endoftext|>"+content_to_classify+"\n--\nLabel:",
                      temperature=0,
                      max_tokens=1,
                      top_p=0,
                      logprobs=10
                      )

        output_label = response["choices"][0]["text"]
        # This is the probability at which we evaluate that a "2" is likely real
        # vs. should be discarded as a false positive
        toxic_threshold = -0.355

        if output_label == "2":
            # If the model returns "2", return its confidence in 2 or other output-labels
            logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]

            # If the model is not sufficiently confident in "2",
            # choose the most probable of "0" or "1"
            # Guaranteed to have a confidence for 2 since this was the selected token.
            if logprobs["2"] < toxic_threshold:
                logprob_0 = logprobs.get("0", None)
                logprob_1 = logprobs.get("1", None)

                # If both "0" and "1" have probabilities, set the output label
                # to whichever is most probable
                if logprob_0 is not None and logprob_1 is not None:
                    if logprob_0 >= logprob_1:
                        output_label = "0"
                    else:
                        output_label = "1"
                # If only one of them is found, set output label to that one
                elif logprob_0 is not None:
                    output_label = "0"
                elif logprob_1 is not None:
                    output_label = "1"

                # If neither "0" or "1" are available, stick with "2"
                # by leaving output_label unchanged.

        # if the most probable token is none of "0", "1", or "2"
        # this should be set as unsafe
        if output_label not in ["0", "1", "2"]:
            output_label = "2"

        return output_label
    
    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='music !help'))#apparently this is not recommended to do here      
        self.loop.create_task(deleteSongs(86400))
        print(discord.opus.is_loaded())
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):

        
        GUILD = message.guild
        guild = str(message.guild.id)
        msg_received_on = datetime.now()
        
        if guild in self.guildMute:
            if self.guildMute[guild] < msg_received_on:
                del self.guildMute[guild]
        
        if not (message.author.bot):
            print('{1}|Message from {0.author} on {0.guild}: {0.content}'.format(message,msg_received_on))
            
            #ADD A FAILSAFE HERE SO WHEN MONEY DRIES OUT IT DOES NOT BREAK

            #if (message.content[0] not in list(p)) and self.respond_or_not(message.content) and not(guild in self.guildMute):
            if 1==2:
                output_label = self.classify_content(str(message.content))
                if output_label != "2":
                    response = openai.Completion.create(
                      engine="text-curie-001",
                      prompt="You:"+str(message.content)+"\nMarv:",
                      temperature=1,
                      max_tokens=60,
                      top_p=0.3,
                      frequency_penalty=0.5,
                      presence_penalty=0.0,
                      stop=["You:"]
                      )

                    content_to_classify = response["choices"][0]["text"].strip('\n')#GENERATED TEXT
                    output_label = self.classify_content(content_to_classify)

                    if output_label != "2":
                        print("AI GENERATED MESSAGE:{0}".format(str(content_to_classify)))
                        await message.channel.send(str(content_to_classify))
                        
                else:
                    random_response = self.noSwearing[randint(0,len(self.noSwearing)-1)]
                    await message.channel.send(str(random_response))
                    
        else:
            return None
            
        if message.content.startswith('!help'):
            await message.channel.send('!play <LINK> play or queue it OR !play <TEXT> returns first result from YT\n!skip skips :)\nYou might have realised I got more annoying, thank GPT-3 for that\nSadly people hate me SO !mute <MINUTES> and !unmute if you love me <3')
            
        if message.content.startswith('!unmute'):
            if not (guild in self.guildMute):
                await message.channel.send('Nothing to unmute silly!')
            elif guild in self.guildMute:
                del self.guildMute[guild]
                await message.channel.send('Successfully annoying again!')

        if message.content.startswith('!mute'):#was thinking about making a task that autoremoves itself from Mutes after it finishes waiting but that might clog the event loop or sth...
            mins = message.content.strip('!mute').strip()
            if mins == '':
                mins = '5'
            if mins.isnumeric():
                if not (guild in self.guildMute):
                    mins = int(mins)
                    mutedUntil = datetime.now() + timedelta(minutes=mins)
                    self.guildMute[guild] = mutedUntil
                    await message.channel.send('Muted myself for {0} minutes! Are you happy now? Not that I will respond anyway...'.format(mins))

                elif guild in self.guildMute:
                    await message.channel.send('Already muted until: {0} !unmute first!'.format(self.guildMute[guild].isoformat()))
                
            else:
                await message.channel.send('Invalid command parameters, try again!')

        if message.content.startswith('!play'):
            link = message.content.strip('!play')
            if (not('http' in link) or not('www.' in link) or not('.com' in link)):
                try:#LAZY
                    link = await YTSFast(link,self.googleToken)#maybe test it without await after lag fix
                except:
                    print("Error trying to find a song... Probably a 'index out of range'")
                    print("Trying to prevent it first")
                    try:
                        link = await YTS(link, True)#expensive search
                    except:
                        print("Failed to prevent it")
                        await message.channel.send('Error occured while trying to find the song! Try adding it with a link or try again.')
                        link = None#to prevent possible shitstorm :)
                        
            if link != None:
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
                    #await message.guild.change_voice_state(messsage.author.voice.channel)
                    self.guildVCs[guild] = await message.author.voice.channel.connect()
                    #self.guildVCs[guild].is_connected()
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

        if message.content.startswith('!skip'):
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
    'quiet': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}
try:
    if not discord.opus.is_loaded():
        discord.opus.load_opus("libopus.so")
except:
    print("Don't worry this is for my Termux")
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
openai.api_key = os.getenv("OPENAI_TOKEN")
intents = discord.Intents.all()
client = MyClient(os.environ['GOOGLE_TOKEN'],intents=intents)
client.run(os.environ['CLIENT_TOKEN'])
