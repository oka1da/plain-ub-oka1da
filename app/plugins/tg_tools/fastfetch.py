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

async def install_fastfetch():
    """
    Tenta instalar o FastFetch automaticamente.
    """
    install_commands = [
        "curl -Lo /tmp/fastfetch.deb https://github.com/fastfetch-cli/fastfetch/releases/download/2.22.2/fastfetch-linux-amd64.deb",
        "dpkg -i /tmp/fastfetch.deb || apt-get install -f -y",
        "rm /tmp/fastfetch.deb"
    ]
    
    for cmd in install_commands:
        stdout, stderr, returncode = await run_command(cmd)
        if returncode != 0:
            return False, stderr
    
    # Verifica se a instalação foi bem-sucedida
    stdout, stderr, returncode = await run_command("fastfetch --version")
    return returncode == 0, stdout if returncode == 0 else stderr

async def is_fastfetch_installed():
    """
    Verifica se o FastFetch está instalado.
    """
    stdout, stderr, returncode = await run_command("which fastfetch || command -v fastfetch")
    return returncode == 0

@bot.add_cmd(cmd="fastf")
async def fastfetch_handler(bot: BOT, message: Message):
    """
    CMD: FASTFETCH
    INFO: Executa o fastfetch e exibe as informações do sistema
    USAGE: .fastf
    """
    
    progress_message = await message.reply("<code>🔄 Verificando FastFetch...</code>")
    
    try:
        # Verifica se o FastFetch está instalado
        if not await is_fastfetch_installed():
            await progress_message.edit_text("<code>📦 FastFetch não encontrado. Tentando instalar...</code>")
            
            success, output = await install_fastfetch()
            if not success:
                error_msg = f"❌ Falha na instalação:\n<code>{html.escape(output)}</code>"
                await progress_message.edit_text(error_msg)
                await asyncio.sleep(ERROR_VISIBLE_DURATION)
                await progress_message.delete()
                return
        
        # Agora executa o FastFetch
        await progress_message.edit_text("<code>🔄 Executando FastFetch...</code>")
        
        stdout, stderr, returncode = await run_command("fastfetch")
        
        if returncode != 0:
            # Tenta método alternativo
            stdout, stderr, returncode = await run_command("fastfetch --load-config false")
            if returncode != 0:
                raise RuntimeError(stderr or stdout or "Erro ao executar FastFetch")
        
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

@bot.add_cmd(cmd="fastf_install")
async def fastfetch_install_handler(bot: BOT, message: Message):
    """
    CMD: FASTFETCH_INSTALL
    INFO: Instala o FastFetch manualmente
    USAGE: .fastf_install
    """
    
    progress_message = await message.reply("<code>📦 Instalando FastFetch...</code>")
    
    try:
        success, output = await install_fastfetch()
        
        if success:
            await progress_message.edit_text(f"<b>✅ FastFetch instalado com sucesso!</b>\n<code>Versão: {html.escape(output)}</code>")
        else:
            await progress_message.edit_text(f"<b>❌ Falha na instalação:</b>\n<code>{html.escape(output)}</code>")
        
        await message.delete()

    except Exception as e:
        error_text = f"<b>❌ Erro na instalação:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
