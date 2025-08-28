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
    INFO: Runs the neofetch command and displays the output.
    USAGE: .neofetch
    """
    
    progress_message = await message.reply("<code>Running neofetch...</code>")
    
    try:
        stdout, stderr, returncode = await run_command("neofetch --stdout")
        
        if returncode == 0:
            neofetch_logo = """
HOST: OptiPlex 3070
OS: Debian GNU/Linux 12 (bookworm) x86_64
Kernel: 6.15.10-200.fc42.x86_64
Uptime: 15h 28m
Packages: 417 (dpkg)
Shell: bash 5.2.15

CPU: Intel i3-9100T (4) @ 3.70GHz
GPU: Intel UHD Graphics 630
RAM: 3977MiB / 15791MiB
Disk: 122GB / 500GB (24%)

IP (local): xxx.xxx.x.xx
IP (public): xxx.xxx.xxx.xxx
Net: ↑ 25 Mbps | ↓ 930 Mbps

Processes: 214
Load Avg: 0.21, 0.36, 0.42

CPU [■■■■■■□□]  35%
RAM [■■■□□□□□]  25%
DISK[■■■■■□□□]  60%
NET [↑ 25Mbps ↓ 930Mbps]
"""
    
            final_text = f"<b>Host Info:</b>\n<pre>{html.escape(stdout)}</pre>\n{neofetch_logo}"
    
            await progress_message.edit(final_text)
            await message.delete()

        else:
            error_details = stderr or stdout or "Unknown error."
            raise RuntimeError(error_details)

    except Exception as e:
        error_text = f"<b>Error:</b> Could not run neofetch.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
