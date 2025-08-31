import asyncio
import html
from pyrogram.types import Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
    """
    Executa um comando shell de forma assíncrona e captura a saída.
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    return (
        stdout.decode('utf-8', errors='replace').strip(),
        stderr.decode('utf-8', errors='replace').strip(),
        process.returncode
    )

@bot.add_cmd(cmd="fastf")
async def fastfetch_handler(bot: BOT, message: Message):
    """
    CMD: FASTFETCH
    INFO: Executa o fastfetch e exibe as informações do sistema
    USAGE: .fastf
    """
    
    progress_message = await message.reply("<code>🔄 Executando FastFetch...</code>")
    
    try:
        # Executa o fastfetch
        stdout, stderr, returncode = await run_command("fastfetch")
        
        if returncode != 0:
            # Tenta método alternativo se o primeiro falhar
            stdout, stderr, returncode = await run_command("fastfetch --load-config false")
            if returncode != 0:
                error_details = stderr or stdout or "FastFetch não encontrado ou falhou ao executar."
                raise RuntimeError(error_details)
        
        # Formata a saída para o Telegram
        if stdout:
            # Limita o tamanho da saída se for muito grande
            if len(stdout) > 2000:
                stdout = stdout[:2000] + "\n[...] (output truncado)"
            
            final_text = f"<b>🚀 FastFetch - System Info</b>\n\n<pre>{html.escape(stdout)}</pre>"
            await progress_message.edit_text(final_text)
        else:
            await progress_message.edit_text("<code>❌ Nenhuma saída do FastFetch.</code>")
        
        await message.delete()

    except Exception as e:
        error_text = f"<b>❌ Erro:</b> Não foi possível executar o FastFetch.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
