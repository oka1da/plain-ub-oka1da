import asyncio
import json
import subprocess
import os
from pathlib import Path

class FastFetchPlugin:
    def __init__(self, userbot):
        self.userbot = userbot
        self.fastfetch_path = self._find_fastfetch()
        
    def _find_fastfetch(self):
        """Encontra o caminho do FastFetch"""
        try:
            # Tenta encontrar usando 'which' ou 'where'
            result = subprocess.run(['which', 'fastfetch'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Se não encontrar, tenta outros métodos
            possible_paths = [
                "/usr/bin/fastfetch",
                "/usr/local/bin/fastfetch",
                "/bin/fastfetch",
                os.path.expanduser("~/.local/bin/fastfetch"),
                "fastfetch"
            ]
            
            for path in possible_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
                    
        except Exception:
            pass
            
        return None
        
    async def get_system_info(self):
        """Executa o FastFetch e retorna as informações do sistema"""
        if not self.fastfetch_path:
            return {"error": "FastFetch não encontrado no sistema"}
        
        try:
            # Executa o FastFetch com saída em JSON
            process = await asyncio.create_subprocess_exec(
                self.fastfetch_path, "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Erro desconhecido"
                return {"error": f"Erro ao executar FastFetch: {error_msg}"}
            
            # Parse do JSON
            system_info = json.loads(stdout.decode())
            return system_info
            
        except json.JSONDecodeError as e:
            return {"error": f"Resposta do FastFetch não é um JSON válido: {str(e)}"}
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}
    
    async def format_system_info(self, system_info):
        """Formata as informações do sistema para exibição"""
        if "error" in system_info:
            return f"❌ Erro: {system_info['error']}"
        
        try:
            # Extrai informações relevantes com fallbacks
            os_info = system_info.get("os", {})
            host_info = system_info.get("host", {})
            cpu_info = system_info.get("cpu", {})
            gpu_info = system_info.get("gpu", {})
            memory_info = system_info.get("memory", {})
            disks = system_info.get("disk", [{}])
            disk_info = disks[0] if disks else {}
            
            # Constrói a mensagem formatada
            message = "🖥️ **Informações do Sistema**\n\n"
            message += f"**Sistema**: {os_info.get('name', 'N/A')} {os_info.get('version', '')}\n"
            message += f"**Kernel**: {os_info.get('kernel', 'N/A')}\n"
            message += f"**Host**: {host_info.get('name', 'N/A')} ({host_info.get('model', 'N/A')})\n"
            message += f"**CPU**: {cpu_info.get('name', 'N/A')} ({cpu_info.get('cores', 'N/A')} cores)\n"
            message += f"**GPU**: {gpu_info.get('name', 'N/A')}\n"
            
            # Memória
            if 'used' in memory_info and 'total' in memory_info:
                message += f"**Memória**: {memory_info['used']} / {memory_info['total']}\n"
            else:
                message += f"**Memória**: {memory_info.get('total', 'N/A')}\n"
            
            # Disco
            if 'used' in disk_info and 'total' in disk_info:
                message += f"**Disco**: {disk_info['used']} / {disk_info['total']}\n"
            else:
                message += f"**Disco**: {disk_info.get('total', 'N/A')}\n"
            
            # Tempo de atividade
            if 'uptime' in system_info:
                message += f"**Uptime**: {system_info['uptime']}\n"
                
            return message
            
        except Exception as e:
            return f"Erro ao formatar informações: {str(e)}"

    async def get_simple_info(self):
        """Método alternativo para obter informações simples"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.fastfetch_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode()
            else:
                return f"Erro: {stderr.decode()}"
                
        except Exception as e:
            return f"Erro ao executar FastFetch: {str(e)}"

# Função principal para o userbot
async def fastfetch_command(userbot, message):
    """Comando para exibir informações do sistema usando FastFetch"""
    plugin = FastFetchPlugin(userbot)
    
    # Envia mensagem de "processando"
    processing_msg = await message.reply("🔄 Coletando informações do sistema...")
    
    # Obtém informações
    system_info = await plugin.get_system_info()
    
    # Se falhar com JSON, tenta o método simples
    if "error" in system_info:
        simple_info = await plugin.get_simple_info()
        await processing_msg.edit_text(f"📋 **Informações do Sistema**\n```\n{simple_info}\n```")
    else:
        formatted_info = await plugin.format_system_info(system_info)
        await processing_msg.edit_text(formatted_info)

# Comando alternativo simples
async def sysinfo_command(userbot, message):
    """Comando simples de system info"""
    plugin = FastFetchPlugin(userbot)
    
    processing_msg = await message.reply("🔄 Coletando informações...")
    info = await plugin.get_simple_info()
    await processing_msg.edit_text(f"📋 **System Info**\n```\n{info}\n```")

# Registra os comandos no userbot
def register(userbot):
    userbot.add_command("systeminfo", fastfetch_command, "Exibe informações detalhadas do sistema")
    userbot.add_command("sysinfo", sysinfo_command, "Exibe informações simples do sistema")
