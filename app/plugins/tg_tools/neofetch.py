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
    INFO: Runs a neofetch-like system info panel and displays the output.
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Gathering system info...</code>")
    
    try:
        # Informações básicas do sistema
        host, _, _ = await run_command("hostname")
        os_info, _, _ = await run_command("lsb_release -ds || cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'")
        kernel, _, _ = await run_command("uname -r")
        uptime, _, _ = await run_command("uptime -p")
        packages, _, _ = await run_command("dpkg -l | wc -l")
        shell, _, _ = await run_command("echo $SHELL")
        cpu, _, _ = await run_command("lscpu | grep 'Model name' | cut -d':' -f2 | xargs")
        memory, _, _ = await run_command("free -m | awk '/Mem:/ {print $3 \"MiB /\" $2 \"MiB\"}'")
        
        # Informações extras
        ip_local, _, _ = await run_command("hostname -I | awk '{print $1}'")
        ip_public, _, _ = await run_command("curl -s ifconfig.me")
        disk_usage, _, _ = await run_command("df -h / | awk 'NR==2 {print $3 \" / \" $2 \" (\" $5 \")\"}'")
        load_avg, _, _ = await run_command("uptime | awk -F'load average:' '{print $2}'")
        processes, _, _ = await run_command("ps -e --no-headers | wc -l")
        gpu, _, _ = await run_command("lspci | grep VGA | cut -d':' -f3 | xargs")
        top_processes, _, _ = await run_command("ps -eo pid,comm,%cpu --sort=-%cpu | head -n 5")
        
        # Montando painel completo
        system_info = f"""
HOST: {host}
OS: {os_info}
Kernel: {kernel}
Uptime: {uptime}
Packages: {packages} (dpkg)
Shell: {shell}

CPU: {cpu}
Memory: {memory}
GPU: {gpu}
Disk: {disk_usage}

IP Local: {ip_local}
IP Público: {ip_public}
Load Average: {load_avg}
Processos: {processes}

Top Processos (PID, CMD, CPU%):
{top_processes}
"""

        # Rodando neofetch para a arte ASCII (opcional)
        stdout, stderr, returncode = await run_command("neofetch --stdout")
        
        if returncode == 0:
            final_text = f"<b>Host Info:</b>\n<pre>{html.escape(stdout)}</pre>\n<pre>{html.escape(system_info)}</pre>"
        else:
            # Caso neofetch falhe, só mostrar painel
            final_text = f"<b>Host Info:</b>\n<pre>{html.escape(system_info)}</pre>"

        await progress_message.edit(final_text)
        await message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not retrieve system info.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
