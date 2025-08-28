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
        # Executa o neofetch
        stdout, stderr, returncode = await run_command("neofetch --stdout")
        
        if returncode != 0:
            error_details = stderr or stdout or "Unknown error."
            raise RuntimeError(error_details)
        
        # Coleta informações adicionais do sistema
        commands = {
            "disk": "df -h / | awk 'NR==2{print $3\"/\"$2 \" (\"$5\")\"}'",
            "ip_local": "hostname -I | awk '{print $1}'",
            "ip_public": "curl -s ifconfig.me",
            "load_avg": "cat /proc/loadavg | awk '{print $1\", \"$2\", \"$3}'",
            "cpu_temp": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | awk '{print $1/1000}' | head -1 || echo '27.8'",
            "network_rx": "cat /proc/net/dev | grep -E '(eth|enp|wlp)' | head -1 | awk '{print $2/1024/1024}' || echo '0'",
            "network_tx": "cat /proc/net/dev | grep -E '(eth|enp|wlp)' | head -1 | awk '{print $10/1024/1024}' || echo '0'",
            "cpu_cores": "nproc",
            "cpu_freq": "cat /proc/cpuinfo | grep 'cpu MHz' | head -1 | awk '{print $4}' | cut -d'.' -f1 || echo '3487'",
            "architecture": "uname -m",
            "memory": "free -h | grep Mem | awk '{print $3\"/\"$2}' || echo '4347MiB/15791MiB'",
            "cpu_model": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | sed 's/^ //' || echo 'Intel i3-9100T (4) @ 3.700GHz'"
        }
        
        info = {}
        for key, cmd in commands.items():
            try:
                stdout_cmd, stderr_cmd, returncode_cmd = await run_command(cmd)
                info[key] = stdout_cmd if returncode_cmd == 0 and stdout_cmd else "N/A"
            except:
                info[key] = "N/A"
        
        # Aplica máscara nos IPs por segurança
        masked_ip_local = mask_ip(info.get('ip_local', 'N/A'))
        masked_ip_public = mask_ip(info.get('ip_public', 'N/A'))
        
        # Formata temperatura da CPU com tratamento de erro
        cpu_temp = "27.8°C"  # Valor padrão
        temp_icon = "🌡️💚"
        if info.get('cpu_temp') != "N/A" and info.get('cpu_temp'):
            try:
                temp_value = float(info['cpu_temp'])
                cpu_temp = f"{temp_value}°C"
                temp_icon = get_temperature_icon(temp_value)
                cpu_temp = f"{temp_icon} {cpu_temp}"
            except (ValueError, TypeError):
                cpu_temp = f"{temp_icon} 27.8°C"  # Valor padrão com ícone
        
        # Formata frequência da CPU com tratamento de erro
        cpu_freq = "3487 MHz"  # Valor padrão
        if info.get('cpu_freq') != "N/A" and info.get('cpu_freq'):
            try:
                cpu_freq = f"{info['cpu_freq']} MHz"
            except:
                cpu_freq = "3487 MHz"  # Valor padrão
        
        # Processa a saída do neofetch
        lines = stdout.split('\n')
        
        # Substitui "OS:" por "OS Docker:" em todas as linhas
        modified_lines = []
        for line in lines:
            if line.strip().startswith('OS:'):
                modified_lines.append(line.replace('OS:', 'OS Docker:'))
                # Adiciona o OS Host logo abaixo do OS Docker
                modified_lines.append(f"OS Host: Fedora Server 42 {info.get('architecture', 'x86_64')}")
            else:
                modified_lines.append(line)
        
        lines = modified_lines
        
        # Remove linhas que serão substituídas/reorganizadas
        filtered_lines = []
        for line in lines:
            if not any(x in line for x in ['CPU:', 'Memory:']):
                filtered_lines.append(line)
        
        # Encontra a posição onde inserir os grupos (após as informações básicas)
        insert_position = -1
        for i, line in enumerate(filtered_lines):
            if any(x in line for x in ['Uptime:', 'Packages:', 'Shell:']):
                insert_position = i + 1
        
        # Se não encontrar, insere no final
        if insert_position == -1:
            insert_position = len(filtered_lines)
        
        # GRUPO CPU - Todas informações da CPU juntas
        cpu_group = [
            f"CPU: {info.get('cpu_model', 'Intel i3-9100T (4) @ 3.700GHz')}",
            f"Cores: {info.get('cpu_cores', '4')}",
            f"Freq: {cpu_freq}",
            f"Temp: {cpu_temp}",
            f"Load: {info.get('load_avg', '0.19, 0.17, 0.17')}"
        ]
        
        # GRUPO MEMÓRIA & ARMAZENAMENTO
        memory_group = [
            f"Memory: {info.get('memory', '4347MiB / 15791MiB')}",
            f"Disk: {info.get('disk', '7.3G/118G (7%)')}"
        ]
        
        # GRUPO REDE com tratamento de erro
        network_tx = 138.2
        network_rx = 333.2
        try:
            network_tx = float(info.get('network_tx', '138.2'))
            network_rx = float(info.get('network_rx', '333.2'))
        except (ValueError, TypeError):
            network_tx = 138.2
            network_rx = 333.2
        
        network_group = [
            f"Traffic: ↑{network_tx:.1f}MB ↓{network_rx:.1f}MB",
            f"Local: {masked_ip_local}",
            f"Public: {masked_ip_public}"
        ]
        
        # Insere todos os grupos na posição correta
        all_groups = [""] + cpu_group + [""] + memory_group + [""] + network_group
        
        for i, group_line in enumerate(reversed(all_groups)):
            filtered_lines.insert(insert_position, group_line)
        
        # Reconstroi o texto
        modified_output = '\n'.join(filtered_lines)
        
        # Formata a mensagem final
        final_text = f"<b>Host Info:</b>\n\n<pre>{html.escape(modified_output)}</pre>"
        
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
