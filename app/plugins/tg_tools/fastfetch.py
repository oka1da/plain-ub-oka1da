import asyncio
import json
import subprocess
import os
from pathlib import Path

class FastFetchPlugin:
    def __init__(self, userbot):
        self.userbot = userbot
        self.fastfetch_path = self._get_fastfetch_path()
        
    def _get_fastfetch_path(self):
        # Tenta encontrar o FastFetch em vários locais possíveis
        possible_paths = [
            "/usr/bin/fastfetch",
            "/usr/local/bin/fastfetch",
            "/bin/fastfetch",
            os.path.expanduser("~/.local/bin/fastfetch"),
            "fastfetch"  # Tenta usar o do PATH
        ]
        
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
                
        return None
        
    async def install_fastfetch(self):
        """Tenta instalar o FastFetch automaticamente"""
        install_commands = [
            ["apt-get", "update", "-y"],
            ["apt-get", "install", "-y", "fastfetch"]
        ]
        
        try:
            for cmd in install_commands:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return False, stderr.decode()
                    
            # Verifica se a instalação foi bem-sucedida
            self.fastfetch_path = self._get_fastfetch_path()
            if self.fastfetch_path:
                return True, "FastFetch instalado com sucesso!"
            else:
                return False, "Instalação concluída, mas fastfetch não foi encontrado."
                
        except Exception as e:
            return False, f"Erro durante a instalação: {str(e)}"
    
    async def get_system_info(self, format="json"):
        """Executa o FastFetch e retorna as informações do sistema"""
        if not self.fastfetch_path:
            success, message = await self.install_fastfetch()
            if not success:
                return {"error": f"FastFetch não encontrado e falha na instalação: {message}"}
        
        try:
            # Executa o FastFetch com saída em JSON
            cmd = [self.fastfetch_path, "--format", "json"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {"error": f"Erro ao executar FastFetch: {stderr.decode()}"}
            
            # Parse do JSON
            system_info = json.loads(stdout.decode())
            return system_info
            
        except json.JSONDecodeError:
            return {"error": "Resposta do FastFetch não é um JSON válido"}
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}
    
    async def format_system_info(self, system_info):
        """Formata as informações do sistema para exibição"""
        if "error" in system_info:
            return system_info["error"]
        
        try:
            # Extrai informações relevantes
            os_info = system_info.get("os", {})
            host_info = system_info.get("host", {})
            cpu_info = system_info.get("cpu", {})
            gpu_info = system_info.get("gpu", {})
            memory_info = system_info.get("memory", {})
            disk_info = system_info.get("disk", [{}])[0] if system_info.get("disk") else {}
            
            # Constrói a mensagem formatada
            message = "🖥️ **Informações do Sistema**\n\n"
            message += f"**Sistema**: {os_info.get('name', 'N/A')} {os_info.get('version', '')}\n"
            message += f"**Host**: {host_info.get('name', 'N/A')} ({host_info.get('model', 'N/A')})\n"
            message += f"**CPU**: {cpu_info.get('name', 'N/A')}\n"
            message += f"**GPU**: {gpu_info.get('name', 'N/A')}\n"
            message += f"**Memória**: {memory_info.get('total', 'N/A')}\n"
            message += f"**Disco**: {disk_info.get('total', 'N/A')} (Livre: {disk_info.get('available', 'N/A')})\n"
            
            # Adiciona tempo de atividade se disponível
            if 'uptime' in system_info:
                message += f"**Uptime**: {system_info['uptime']}\n"
                
            return message
            
        except Exception as e:
            return f"Erro ao formatar informações: {str(e)}"

# Função principal para o userbot
async def fastfetch_command(userbot, message):
    """Comando para exibir informações do sistema usando FastFetch"""
    plugin = FastFetchPlugin(userbot)
    
    # Envia mensagem de "processando"
    processing_msg = await message.reply("🔄 Coletando informações do sistema...")
    
    # Obtém informações
    system_info = await plugin.get_system_info()
    formatted_info = await plugin.format_system_info(system_info)
    
    # Edita a mensagem com os resultados
    await processing_msg.edit_text(formatted_info)

# Registra o comando no userbot
def register(userbot):
    userbot.add_command("systeminfo", fastfetch_command, "Exibe informações do sistema usando FastFetch")