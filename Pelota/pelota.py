import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    voice_clients = {}

    yt_dl_options = {
        "format": "bestaudio/best",
        "cookiesfrombrowser": ("chromium",), 
        "noplaylist": True,        
        "quiet": True,             
    }
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',  
    }

    @client.event
    async def on_ready():
        print(f'{client.user} carregou!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!go'):
            try:
                if not message.author.voice:
                    await message.channel.send("Você precisa estar em um canal de voz!")
                    return

                voice_channel = message.author.voice.channel
                voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
                if not voice_client:
                    voice_client = await voice_channel.connect()
                    voice_clients[message.guild.id] = voice_client
                elif voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)

                try:
                    url = message.content.split()[1]
                    loop = asyncio.get_event_loop()
                    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                    
                    song = data['url']
                    title = data.get('title', 'Desconhecido')

                    player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                    voice_clients[message.guild.id].play(player, after=lambda e: print(f"Terminou de tocar: {e}"))
                    await message.channel.send(f"Tocando agora: **{title}**")

                except IndexError:
                    await message.channel.send("Por favor, forneça um URL após o comando! Exemplo: `!go https://youtube.com/...`")
                except Exception as e:
                    await message.channel.send(f"Erro ao reproduzir: {str(e)}")
                    print(f"Erro no yt-dlp: {e}")

            except Exception as e:
                await message.channel.send("Erro ao conectar ao canal de voz!")
                print(f"Erro na conexão: {e}")

        if message.content.startswith('!stop'):
            if message.guild.id in voice_clients:
                voice_client = voice_clients[message.guild.id]
                if voice_client.is_playing():
                    voice_client.stop()
                await voice_client.disconnect()
                del voice_clients[message.guild.id]
                await message.channel.send("Desconectado do canal de voz!")
            else:
                await message.channel.send("Não estou em nenhum canal de voz!")

    client.run(TOKEN)