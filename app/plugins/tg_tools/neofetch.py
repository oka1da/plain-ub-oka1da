import asyncio
import html
from pyrogram.types import Message
from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
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
    progress_message = await message.reply("<code>Collecting system information...</code>")
    
    try:
        # Comandos específicos para o formato desejado
        commands = {
            "hostname": "hostname",
            "os": "cat /etc/os-release | grep PRETTY_NAME | cut -d=' -f2 | tr -d '\"'",
            "kernel": "uname -r",
            "uptime": "uptime -p | sed 's/up //'",
            "packages": "dpkg --list | wc -l",
            "shell": "echo $SHELL | xargs basename",
            "cpu": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | sed 's/^ //'",
            "memory_total": "free -b | grep Mem | awk '{print $2}'",
            "memory_used": "free -b | grep Mem | awk '{print $3}'",
            "disk_used": "df -h / | awk 'NR==2{print $3}'",
            "disk_total": "df -h / | awk 'NR==2{print $2}'",
            "disk_percent": "df / | awk 'NR==2{print $5}'",
            "ip_local": "hostname -I | awk '{print $1}'",
            "ip_public": "curl -s ifconfig.me",
            "load_avg": "cat /proc/loadavg | awk '{print $1\", \"$2\", \"$3}'",
            "process_count": "ps aux | wc -l",
            "top_processes": "ps aux --sort=-%cpu | head -6 | awk '{if(NR>1) printf \"%s, %s, %s%%\\n\", $2, $11, $3}'"
        }
        
        info = {}
        for key, cmd in commands.items():
            stdout, stderr, returncode = await run_command(cmd)
            if returncode == 0 and stdout:
                info[key] = stdout
            else:
                info[key] = ""
        
        # Formatação EXATA da segunda imagem
        final_message = "<code>"
        final_message += f"HOST: {info['hostname']}\n"
        final_message += f"OS: {info['os']}\n"
        final_message += f"Kernel: {info['kernel']}\n"
        final_message += f"Uptime: {info['uptime']}\n"
        final_message += f"Packages: {info['packages']} (dpkg)\n"
        final_message += f"Shell: {info['shell']}\n\n"
        
        final_message += f"CPU: {info['cpu']}\n"
        
        # Memória formatada como na imagem (vazio se não disponível)
        if info['memory_used'] and info['memory_total']:
            mem_used_mb = int(int(info['memory_used']) / 1024 / 1024)
            mem_total_mb = int(int(info['memory_total']) / 1024 / 1024)
            final_message += f"Memory: {mem_used_mb}MiB / {mem_total_mb}MiB\n"
        else:
            final_message += f"Memory: \n"
        
        final_message += f"GPU: \n"  # Vazio como na imagem
        
        # Disk formatado exatamente como na imagem
        if info['disk_used'] and info['disk_total'] and info['disk_percent']:
            final_message += f"Disk: {info['disk_used']} / {info['disk_total']} ({info['disk_percent']})\n\n"
        else:
            final_message += f"Disk: \n\n"
        
        final_message += f"IP Local: {info['ip_local']}\n"
        final_message += f"IP Público: {info['ip_public']}\n"
        final_message += f"Load Average: {info['load_avg']}\n"
        final_message += f"Processos: {info['process_count']}\n\n"
        
        final_message += "Top Processos (PID, CMD, CPU%):\n"
        if info['top_processes']:
            final_message += f"{info['top_processes']}\n"
        else:
            final_message += f"\n"  # Vazio como na imagem
        
        final_message += "</code>"
        
        # Adiciona o "COPIAR CÓDIGO" igual na imagem
        final_message += "\n---\n<b>COPIAR CÓDIGO</b>"
        
        await progress_message.edit_text(final_message)
        
    except Exception as e:
        error_msg = f"<b>❌ Error:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_msg)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
