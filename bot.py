import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# IDs dos seus amigos que o bot responde
allowed_friends = [
    1195842056917094421,  # substitua pelos IDs reais dos seus amigos
    348568791023747083,
    604071914004021258,
    259706171114389513,
    497145088015728650,
    1183105491501588541,
]

# Para controlar se o amigo já respondeu ou não
last_messages = {}

@bot.event
async def on_ready():
    print(f'Bot Conectado como {bot.user}')

@bot.event
async def on_message(message):
    # Ignorar mensagens do próprio bot
    if message.author == bot.user:
        return

    # Só responder DM de amigos permitidos
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id in allowed_friends:
            # Atualiza o registro da última mensagem recebida
            last_messages[message.author.id] = asyncio.get_event_loop().time()

            # Exemplo simples: responder com "Oi, amigo!"
            await message.channel.send("Oi, amigo! Recebi sua mensagem.")

    # Permite que comandos ainda funcionem normalmente
    await bot.process_commands(message)

async def check_inactivity():
    await bot.wait_until_ready()
    while not bot.is_closed():
        current_time = asyncio.get_event_loop().time()
        to_remove = []

        for user_id, last_time in last_messages.items():
            # Se passaram mais de 120 segundos (2 minutos) da última mensagem
            if current_time - last_time > 120:
                user = bot.get_user(user_id)
                if user is not None:
                    try:
                        await user.send("Não estou no computador, assim que puder te retorno.")
                    except Exception:
                        pass  # Pode falhar se o usuário bloqueou o bot, etc.

                to_remove.append(user_id)

        # Remove os usuários que já receberam a mensagem para não repetir
        for user_id in to_remove:
            last_messages.pop(user_id)

        await asyncio.sleep(30)  # Verifica a cada 30 segundos

# Roda a tarefa de verificação da inatividade junto com o bot
bot.loop.create_task(check_inactivity())

bot.run(TOKEN)



