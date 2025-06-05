import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone  # IMPORTA timezone AQUI

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
        now = datetime.now(timezone.utc)  # Agora timezone-aware
        last_message_time[message.author.id] = now
        print(f"Mensagem recebida de {message.author} às {now}")

    await bot.process_commands(message)

async def check_inactivity():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now(timezone.utc)  # timezone-aware
        for user_id, last_time in list(last_message_time.items()):
            if now - last_time > timedelta(minutes=2):
                user = await bot.fetch_user(user_id)
                try:
                    await user.send("Não estou no computador, mas assim que estiver te retorno!")
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {user}: {e}")
                del last_message_time[user_id]
        await asyncio.sleep(30)

bot.run(TOKEN)





