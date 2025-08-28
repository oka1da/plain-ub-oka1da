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

def mask_ip(ip_address: str) -> str:
    """
    Masks the IP address for security (shows only first half).
    Example: 192.168.1.100 → 192.168.*.*
    """
    if not ip_address or ip_address == "N/A":
        return "N/A"
    
    parts = ip_address.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    else:
        return ip_address

def get_temperature_icon(temp: float) -> str:
    """
    Returns a temperature icon based on CPU temperature.
    """
    if temp < 40:
        return "🌡️❄️"  # Frio
    elif temp < 60:
        return "🌡️💚"  # Normal
    elif temp < 80:
        return "🌡️💛"  # Quente
    else:
        return "🌡️🔥"  # Muito quente


@bot.add_cmd(cmd="neofetch")
async def neofetch_handler(bot: BOT, message: Message):
    """
    CMD: NEOFETCH
    INFO: Runs the neofetch command and displays the output with additional system info.
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Running neofetch...</code>")
    
    try:
        # Coleta informações do HOST (seu PC Fedora) em vez do container
        commands = {
            "os": "cat /etc/os-release | grep PRETTY_NAME | cut -d=' -f2 | tr -d '\"'",
            "host": "cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null || echo 'Unknown'",
            "kernel": "uname -r",
            "uptime": "uptime -p | sed 's/up //'",
            "shell": "echo $SHELL | xargs basename",
            "cpu": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | sed 's/^ //'",
            "memory_total": "free -b | grep Mem | awk '{print $2}'",
            "memory_used": "free -b | grep Mem | awk '{print $3}'",
            "disk": "df -h / | awk 'NR==2{print $3\"/\"$2 \" (\"$5\")\"}'",
            "ip_local": "hostname -I | awk '{print $1}'",
            "ip_public": "curl -s ifconfig.me",
            "load_avg": "cat /proc/loadavg | awk '{print $1\", \"$2\", \"$3}'",
            "cpu_temp": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000}' || echo 'N/A'",
            "network_rx": "cat /proc/net/dev | grep enp | head -1 | awk '{print $2/1024/1024}' || cat /proc/net/dev | grep wlp | head -1 | awk '{print $2/1024/1024}' || echo '0'",
            "network_tx": "cat /proc/net/dev | grep enp | head -1 | awk '{print $10/1024/1024}' || cat /proc/net/dev | grep wlp | head -1 | awk '{print $10/1024/1024}' || echo '0'",
            "cpu_cores": "nproc",
            "cpu_freq": "cat /proc/cpuinfo | grep 'cpu MHz' | head -1 | awk '{print $4}' | cut -d'.' -f1"
        }
        
        info = {}
        for key, cmd in commands.items():
            stdout_cmd, stderr_cmd, returncode_cmd = await run_command(cmd)
            info[key] = stdout_cmd if returncode_cmd == 0 and stdout_cmd else "N/A"
        
        # Aplica máscara nos IPs por segurança
        masked_ip_local = mask_ip(info['ip_local'])
        masked_ip_public = mask_ip(info['ip_public'])
        
        # Formata temperatura da CPU
        cpu_temp = f"{info['cpu_temp']}°C" if info['cpu_temp'] != "N/A" else "N/A"
        if info['cpu_temp'] != "N/A":
            temp_icon = get_temperature_icon(float(info['cpu_temp']))
            cpu_temp = f"{temp_icon} {cpu_temp}"
        
        # Formata frequência da CPU
        cpu_freq = f"{info['cpu_freq']} MHz" if info['cpu_freq'] != "N/A" else "N/A"
        
        # Formata memória
        if info['memory_used'] != "N/A" and info['memory_total'] != "N/A":
            mem_used_mb = int(int(info['memory_used']) / 1024 / 1024)
            mem_total_mb = int(int(info['memory_total']) / 1024 / 1024)
            memory_info = f"{mem_used_mb}MiB / {mem_total_mb}MiB"
        else:
            memory_info = "N/A"
        
        # Constrói a saída manualmente (não usa neofetch do container)
        lines = [
            f"Host: {info['host']}",
            f"OS: {info['os']}",
            f"Kernel: {info['kernel']}",
            f"Uptime: {info['uptime']}",
            f"Shell: {info['shell']}",
            "",
            # GRUPO CPU
            f"CPU: {info['cpu']}",
            f"Cores: {info['cpu_cores']}",
            f"Freq: {cpu_freq}",
            f"Temp: {cpu_temp}",
            f"Load: {info['load_avg']}",
            "",
            # GRUPO MEMÓRIA & ARMAZENAMENTO
            f"Memory: {memory_info}",
            f"Disk: {info['disk']}",
            "",
            # GRUPO REDE
            f"Traffic: ↑{float(info['network_tx']):.1f}MB ↓{float(info['network_rx']):.1f}MB",
            f"Local: {masked_ip_local}",
            f"Public: {masked_ip_public}"
        ]
        
        # Reconstroi o texto
        modified_output = '\n'.join(lines)
        
        # Formata a mensagem final
        final_text = f"<b>Host Info:</b>\n\n<pre>{html.escape(modified_output)}</pre>"
        
        await progress_message.edit_text(final_text)
        await message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not collect system info.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit_text(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
