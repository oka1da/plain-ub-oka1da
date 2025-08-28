import asyncio
import html
from pyrogram.types import Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
    """
    Asynchronously runs a shell command and captures its output, error, and return code.
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


@bot.add_cmd(cmd="neofetch")
async def neofetch_handler(bot: BOT, message: Message):
    """
    CMD: NEOFETCH
    INFO: Runs the neofetch command and displays the output with additional disk and IP info.
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Running neofetch...</code>")
    
    try:
        # Executa o neofetch
        stdout, stderr, returncode = await run_command("neofetch --stdout")
        
        if returncode != 0:
            error_details = stderr or stdout or "Unknown error."
            raise RuntimeError(error_details)
        
        # Coleta informações adicionais de disk e IP
        disk_cmd = "df -h / | awk 'NR==2{print $3\"/\"$2 \" (\"$5\")\"}'"
        ip_local_cmd = "hostname -I | awk '{print $1}'"
        ip_public_cmd = "curl -s ifconfig.me"
        
        disk_info, _, _ = await run_command(disk_cmd)
        ip_local, _, _ = await run_command(ip_local_cmd)
        ip_public, _, _ = await run_command(ip_public_cmd)
        
        # Processa a saída do neofetch para inserir as informações no lugar certo
        lines = stdout.split('\n')
        
        # Encontra a linha da Memory para inserir Disk depois
        memory_line_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('Memory:'):
                memory_line_index = i
                break
        
        # Adiciona a linha do Disk após a Memory
        if memory_line_index != -1:
            lines.insert(memory_line_index + 1, f"Disk: {disk_info if disk_info else 'N/A'}")
        
        # Encontra o final das informações do sistema para adicionar IPs
        # Geralmente após a linha GPU ou Resolution
        end_of_system_info = -1
        for i, line in enumerate(lines):
            if any(x in line for x in ['Resolution:', 'GPU:', 'Uptime:']):
                end_of_system_info = i
        
        # Adiciona linhas de IP após as informações do sistema
        if end_of_system_info != -1:
            lines.insert(end_of_system_info + 1, f"IP Local: {ip_local if ip_local else 'N/A'}")
            lines.insert(end_of_system_info + 2, f"IP Public: {ip_public if ip_public else 'N/A'}")
        
        # Reconstroi o texto
        modified_output = '\n'.join(lines)
        
        # Formata a mensagem final
        final_text = f"<b>Host Info:</b>\n\n<pre>{html.escape(modified_output)}</pre>\n\n"
        final_text += "<b>COPIAR CÓDIGO</b>"
        
        await progress_message.edit_text(final_text)
        await message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not run neofetch.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass 
