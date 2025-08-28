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
    INFO: Runs system commands to display comprehensive system information
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Collecting system information...</code>")
    
    try:
        # Comandos para coletar informações do sistema
        commands = {
            "HOST": "hostname",
            "OS": "cat /etc/os-release | grep PRETTY_NAME | cut -d=' -f2 | tr -d '\"'",
            "Kernel": "uname -r",
            "Uptime": "uptime -p",
            "Packages": "dpkg --list | wc -l",  # Para Debian/Ubuntu
            "Shell": "echo $SHELL",
            "CPU": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | sed 's/^ //'",
            "Memory": "free -h | grep Mem | awk '{print $3\"/\"$2}'",
            "GPU": "lspci | grep -i vga | head -1 | cut -d':' -f3- | sed 's/^ //'",
            "Disk": "df -h / | awk 'NR==2{print $3\"/\"$2 \" (\"$5\")\"}'",
            "IP Local": "hostname -I | awk '{print $1}'",
            "IP Público": "curl -s ifconfig.me || curl -s icanhazip.com",
            "Load Average": "cat /proc/loadavg | awk '{print $1\", \"$2\", \"$3}'",
            "Processos": "ps aux | wc -l",
            "Top Processos": "ps aux --sort=-%cpu | head -6 | awk '{if(NR>1) printf \"%s, %s, %s%%\\n\", $2, $11, $3}'"
        }
        
        system_info = {}
        
        # Executa todos os comandos
        for key, command in commands.items():
            try:
                stdout, stderr, returncode = await run_command(command)
                if returncode == 0 and stdout:
                    system_info[key] = stdout
                else:
                    system_info[key] = "N/A"
            except Exception as e:
                system_info[key] = f"Error: {str(e)}"
        
        # Constrói a mensagem formatada
        final_message = "<b>🖥️ System Information</b>\n\n<code>"
        
        # Informações principais
        main_info = ["HOST", "OS", "Kernel", "Uptime", "Packages", "Shell", "CPU", "Memory", "GPU", "Disk"]
        for key in main_info:
            final_message += f"{key}: {system_info[key]}\n"
        
        final_message += "\n--- Network ---\n"
        final_message += f"IP Local: {system_info['IP Local']}\n"
        final_message += f"IP Público: {system_info['IP Público']}\n"
        
        final_message += "\n--- System Status ---\n"
        final_message += f"Load Average: {system_info['Load Average']}\n"
        final_message += f"Processos: {system_info['Processos']}\n\n"
        
        final_message += "Top Processos (PID, CMD, CPU%):\n"
        final_message += f"{system_info['Top Processos']}</code>"
        
        await progress_message.edit_text(final_message)
        
    except Exception as e:
        error_msg = f"<b>❌ Error:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_msg)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
