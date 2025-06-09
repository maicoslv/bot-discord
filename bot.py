import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from discord.utils import get
import yt_dlp
from collections import defaultdict, deque
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

allowed_friends = [
    1195842056917094421,
    348568791023747083,
    604071914004021258,
    259706171114389513,
    497145088015728650,
    1183105491501588541,
    1379972116417609758,
    396790961633493012,
    220517671660290048,
]

last_message_time = {}

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(check_inactivity())

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("digitando mensagens automáticas 💬")
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel) and message.author.id in allowed_friends:
        now = datetime.now(timezone.utc)
        last_message_time[message.author.id] = now
        print(f"Mensagem recebida de {message.author} às {now}")

    await bot.process_commands(message)

async def check_inactivity():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now(timezone.utc)
        for user_id, last_time in list(last_message_time.items()):
            if now - last_time > timedelta(minutes=2):
                user = await bot.fetch_user(user_id)
                try:
                    await user.send("Não estou no computador, mas assim que estiver te retorno!")
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {user}: {e}")
                del last_message_time[user_id]
        await asyncio.sleep(30)

@bot.command(name="ajuda")
async def ajuda(ctx):
    await ctx.send(
        "📜 Comandos disponíveis:\n"
        "- `!ajuda`: Mostra esta mensagem\n"
        "- `!ola`: Te cumprimento\n"
        "- `!piada`: Envia uma piada aleatória\n"
        "- `!tocar <url>`: Toca música do YouTube\n"
        "- `!fila`: Mostra a fila de músicas\n"
        "- `!pular`: Pula a música atual"
    )

@bot.command(name="ola")
async def ola(ctx):
    await ctx.send(f"Olá {ctx.author.name}! 👋")

@bot.command(name="piada")
async def piada(ctx):
    piadas = [
        "Por que o JavaScript foi ao terapeuta? Porque ele tinha problemas com 'escopo'. 😂",
        "O que o Python disse ao programador triste? 'print(\"Vai ficar tudo bem\")' 🐍",
        "Qual é o café mais perigoso do mundo? O *ex-presso*! ☕💣"
    ]
    await ctx.send(random.choice(piadas))

# Música
AUDIO_DIR = "musicas"
os.makedirs(AUDIO_DIR, exist_ok=True)

queues = defaultdict(deque)
is_playing = {}

# Caminho para o FFmpeg
ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"

def get_yt_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(AUDIO_DIR, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': ffmpeg_path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        return filename, info.get('title', 'Música')

async def tocar_proxima(ctx, guild_id):
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if not queues[guild_id]:
        is_playing[guild_id] = False
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        return

    next_audio = queues[guild_id].popleft()
    filename, title = next_audio

    await ctx.send(f"🎶 Tocando: **{title}**")

    def after_playing(error=None):
        fut = tocar_proxima(ctx, guild_id)
        asyncio.run_coroutine_threadsafe(fut, bot.loop)

    if voice_client:
        voice_client.play(
            discord.FFmpegPCMAudio(executable=ffmpeg_path, source=filename),
            after=after_playing
        )

@bot.command(name="tocar")
async def tocar(ctx, *, url):
    if ctx.author.voice is None:
        await ctx.send("Você precisa estar em um canal de voz! 🎧")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    filename, title = get_yt_audio(url)
    queues[ctx.guild.id].append((filename, title))

    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    if not is_playing.get(ctx.guild.id, False):
        is_playing[ctx.guild.id] = True
        await tocar_proxima(ctx, ctx.guild.id)
    else:
        await ctx.send(f"📥 Adicionado à fila: **{title}**")

@bot.command(name="fila")
async def fila(ctx):
    fila = queues[ctx.guild.id]
    if not fila:
        await ctx.send("📭 A fila está vazia.")
    else:
        lista = "\n".join(f"{i+1}. {title}" for i, (_, title) in enumerate(fila))
        await ctx.send(f"📜 Fila atual:\n{lista}")

@bot.command(name="pular")
async def pular(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected() and voice_client.is_playing():
        await ctx.send("⏭️ Pulando para a próxima música.")
        voice_client.stop()  # Aciona after_playing
    else:
        await ctx.send("❌ Nenhuma música está tocando no momento.")

bot.run(TOKEN)








