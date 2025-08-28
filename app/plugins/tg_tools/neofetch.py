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
            fedora_logo = r"""
       .',;::::;,'.
   .';:cccccccccc:;,.
 .;cccccccccccccccccc;.
.:cccccccccccccccccccc:.
;cccccccccccccccccccccc;
:cccccccccccccccccccccc:
:cccccccccccccccccccccc:
:cccccccccccccccccccccc:
:cccccccccccccccccccccc:
;cccccccccccccccccccccc;
.:cccccccccccccccccccc:.
 .;cccccccccccccccccc;.
   .;:cccccccccc:;'.
       '.,;::::;,'
"""

    final_output = fedora_logo + "\n" + stdout

    final_text = f"<b>Host Info:</b>\n<pre>{html.escape(final_output)}</pre>"

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
