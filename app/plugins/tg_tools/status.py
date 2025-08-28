import subprocess
from app import BOT, bot, Message

@bot.add_cmd(cmd="status")
async def status_function(bot: BOT, message: Message):
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Health.Status}}", "userbot"],
            capture_output=True, text=True
        )
        status = result.stdout.strip()
        await message.reply(f"Status do container: {status}")
    except Exception as e:
        await message.reply(f"Erro ao verificar status: {e}")
