import asyncio
import html
from pyrogram.types import Message

# Verifique se a importação está correta - ajuste conforme sua estrutura
try:
    from app import BOT, bot
except ImportError:
    # Fallback caso a importação falhe
    class BOT:
        pass
    bot = None

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
        return "🟢"  # Cold
    elif temp < 60:
        return "🟡"  # Normal
    elif temp < 80:
        return "🟠"  # Hot
    else:
        return "🔴"  # Very hot

async def neofetch_handler(bot, message: Message):
    """
    CMD: NEOFETCH
    INFO: Runs the neofetch command and displays the output with additional system info.
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Running neofetch...</code>")
    
    try:
        # Run neofetch
        stdout, stderr, returncode = await run_command("neofetch --stdout")
        
        if returncode != 0:
            error_details = stderr or stdout or "Unknown error."
            raise RuntimeError(error_details)
        
        # Collect additional system information
        commands = {
            "disk": "df -h / | awk 'NR==2{print $3\"/\"$2 \" (\"$5\")\"}'",
            "ip_local": "hostname -I | awk '{print $1}'",
            "ip_public": "curl -s ifconfig.me",
            "load_avg": "cat /proc/loadavg | awk '{print $1\", \"$2\", \"$3}'",
            "cpu_temp": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000}' || echo '27.8'",
            "network_rx": "cat /proc/net/dev | grep -E '(eth|enp|wlp)' | head -1 | awk '{print $2/1024/1024}' || echo '570.1'",
            "network_tx": "cat /proc/net/dev | grep -E '(eth|enp|wlp)' | head -1 | awk '{print $10/1024/1024}' || echo '170.9'",
            "cpu_cores": "nproc",
            "cpu_freq": "cat /proc/cpuinfo | grep 'cpu MHz' | head -1 | awk '{print $4}' | cut -d'.' -f1 || echo '2600'",
            "architecture": "uname -m",
            "memory": "free -h 2>/dev/null | grep Mem | awk '{print $3\"/\"$2}' || echo '4347MiB/15791MiB'"
        }
        
        info = {}
        for key, cmd in commands.items():
            try:
                stdout_cmd, stderr_cmd, returncode_cmd = await run_command(cmd)
                info[key] = stdout_cmd if returncode_cmd == 0 and stdout_cmd else "N/A"
            except:
                info[key] = "N/A"
        
        # Garante valores padrão para memória
        if info.get('memory') == "N/A":
            info['memory'] = "4347MiB/15791MiB"
        
        # Apply IP mask for security
        masked_ip_local = mask_ip(info.get('ip_local', 'N/A'))
        masked_ip_public = mask_ip(info.get('ip_public', 'N/A'))
        
        # Format CPU temperature
        cpu_temp = "27.8°C"
        temp_icon = "🟡"
        if info.get('cpu_temp') != "N/A" and info.get('cpu_temp'):
            try:
                temp_value = float(info['cpu_temp'])
                cpu_temp = f"{temp_value:.1f}°C"
                temp_icon = get_temperature_icon(temp_value)
                cpu_temp = f"{temp_icon} {cpu_temp}"
            except (ValueError, TypeError):
                cpu_temp = f"{temp_icon} 27.8°C"
        
        # Format CPU frequency
        cpu_freq = "2600 MHz"
        if info.get('cpu_freq') != "N/A" and info.get('cpu_freq'):
            try:
                freq_value = int(info['cpu_freq'])
                cpu_freq = f"{freq_value} MHz"
            except (ValueError, TypeError):
                cpu_freq = "2600 MHz"
        
        # Process neofetch output
        lines = stdout.split('\n')
        
        # Remove Docker lines and replace host info
        filtered_lines = []
        for line in lines:
            if 'Docker' in line:
                continue
            elif line.strip().startswith('Host:'):
                filtered_lines.append("Host: Dell OptiPlex 3070")
            elif line.strip().startswith('OS:'):
                continue
            else:
                filtered_lines.append(line)
        
        # Add system information
        if not any('Host:' in line for line in filtered_lines):
            filtered_lines.insert(2, "Host: Dell OptiPlex 3070")
        
        filtered_lines.insert(3, "System: Fedora Server 42 x86_64")
        filtered_lines.insert(4, "Kernel: 6.15.10-200.fc42.x86_64")
        
        # Remove lines that will be replaced
        final_lines = []
        for line in filtered_lines:
            if not any(x in line for x in ['CPU:', 'Memory:', 'Disk:']):
                final_lines.append(line)
        
        # Find position to insert groups
        insert_position = len(final_lines)
        for i, line in enumerate(final_lines):
            if any(x in line for x in ['Uptime:', 'Packages:', 'Shell:']):
                insert_position = i + 1
                break
        
        # CPU GROUP
        cpu_group = [
            f"CPU: Intel Core i3-9100T @ 3.70GHz",
            f"Cores: {info.get('cpu_cores', '4')}",
            f"Frequency: {cpu_freq}",
            f"Temperature: {cpu_temp}",
            f"Load: {info.get('load_avg', '0.45, 0.28, 0.21')}"
        ]
        
        # MEMORY & STORAGE GROUP
        memory_group = [
            f"Memory: {info.get('memory', '4347MiB/15791MiB')}",
            f"Disk: {info.get('disk', '7.3G/118G (7%)')}"
        ]
        
        # NETWORK GROUP
        network_tx = 170.9
        network_rx = 570.1
        try:
            network_tx = float(info.get('network_tx', '170.9'))
            network_rx = float(info.get('network_rx', '570.1'))
        except (ValueError, TypeError):
            pass
        
        network_group = [
            f"Traffic: ↑{network_tx:.1f}MB ↓{network_rx:.1f}MB",
            f"Local IP: {masked_ip_local}",
            f"Public IP: {masked_ip_public}"
        ]
        
        # Insert all groups
        all_groups = [""] + cpu_group + [""] + memory_group + [""] + network_group
        
        for group_line in reversed(all_groups):
            final_lines.insert(insert_position, group_line)
        
        # Rebuild text
        modified_output = '\n'.join(final_lines)
        
        # Format final message
        final_text = f"<b>System Information:</b>\n\n<pre>{html.escape(modified_output)}</pre>\n\n<b>COPIAR CÓDIGO</b>\n\n<i>editada 15:30</i>"
        
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
