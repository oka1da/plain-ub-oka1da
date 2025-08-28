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
    Example: 192.168.1.100 → 192.168.***.***
    """
    if not ip_address or ip_address == "N/A":
        return "N/A"
    
    parts = ip_address.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
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
            "cpu_temp": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000}' || echo 'N/A'",
            "network_rx": "cat /proc/net/dev | grep eth0 | awk '{print $2/1024/1024}' || echo '0'",
            "network_tx": "cat /proc/net/dev | grep eth0 | awk '{print $10/1024/1024}' || echo '0'",
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
        
        # Processa a saída do neofetch
        lines = stdout.split('\n')
        
        # Remove linhas desnecessárias do neofetch para reorganizar
        filtered_lines = []
        for line in lines:
            if not any(x in line for x in ['Memory:', 'Disk:']):
                filtered_lines.append(line)
        
        # Encontra a linha da CPU para agrupar informações de CPU
        cpu_line_index = -1
        for i, line in enumerate(filtered_lines):
            if line.strip().startswith('CPU:'):
                cpu_line_index = i
                break
        
        # Adiciona informações de CPU agrupadas
        if cpu_line_index != -1:
            cpu_info = [
                f"CPU: {filtered_lines[cpu_line_index].split('CPU:')[1].strip()}",
                f"Cores: {info['cpu_cores']}",
                f"Freq: {cpu_freq}",
                f"Temp: {cpu_temp}",
                f"Load: {info['load_avg']}"
            ]
            # Remove a linha original da CPU e insere o grupo
            del filtered_lines[cpu_line_index]
            for j, cpu_line in enumerate(reversed(cpu_info)):
                filtered_lines.insert(cpu_line_index, cpu_line)
        
        # Encontra a linha de Memory para agrupar informações de armazenamento
        memory_line_index = -1
        for i, line in enumerate(filtered_lines):
            if line.strip().startswith('Memory:'):
                memory_line_index = i
                break
        
        # Adiciona informações de memória e armazenamento agrupadas
        if memory_line_index != -1:
            storage_info = [
                f"Memory: {filtered_lines[memory_line_index].split('Memory:')[1].strip()}",
                f"Disk: {info['disk']}"
            ]
            # Remove a linha original da Memory e insere o grupo
            del filtered_lines[memory_line_index]
            for j, storage_line in enumerate(reversed(storage_info)):
                filtered_lines.insert(memory_line_index, storage_line)
        
        # Encontra o final das informações do sistema para adicionar rede
        end_of_system_info = -1
        for i, line in enumerate(filtered_lines):
            if any(x in line for x in ['Resolution:', 'GPU:']):
                end_of_system_info = i
                break
        
        # Adiciona informações de rede agrupadas
        if end_of_system_info != -1:
            network_info = [
                "--- Network ---",
                f"Traffic: ↑{float(info['network_tx']):.1f}MB ↓{float(info['network_rx']):.1f}MB",
                f"Local IP: {masked_ip_local}",
                f"Public IP: {masked_ip_public}"
            ]
            
            for j, network_line in enumerate(reversed(network_info)):
                filtered_lines.insert(end_of_system_info + 1, network_line)
        
        # Reconstroi o texto
        modified_output = '\n'.join(filtered_lines)
        
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
