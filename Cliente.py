import time
import wmi
import requests
import psutil
import socket
from datetime import datetime

# Endpoints do servidor
SERVIDOR_LISTA = "http://192.168.1.200:5010/lista"  # lista de palavras bloqueadas
SERVIDOR_LOG = "http://192.168.1.200:5010/log"      # envio de logs


def enviar_log(nome_proc):
    """Envia log para o servidor Flask"""
    try:
        requests.post(SERVIDOR_LOG, json={
            "computador": socket.gethostname(),
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processo": nome_proc
        }, timeout=3)
    except Exception as e:
        print("[ERRO] Falha ao enviar log:", e)


def encerrar_processos_proibidos(palavras_bloqueadas):
    """Varre todos os processos abertos e encerra os proibidos."""
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            nome = (proc.info['name'] or "").lower()
            if any(p in nome for p in palavras_bloqueadas):
                psutil.Process(proc.info['pid']).kill()
                print(f"[Bloqueado] {nome}")
                enviar_log(nome)  # 🔹 registra no servidor
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


print("[Iniciando Cliente] 🚫 Bloqueio de processos via servidor central...")

# Conexão WMI e criação do watcher
c = wmi.WMI()
watcher = c.Win32_Process.watch_for("creation")

# Checagem inicial de processos
try:
    palavras_bloqueadas = requests.get(SERVIDOR_LISTA, timeout=5).json()
except Exception as e:
    print("[ERRO] Não foi possível conectar ao servidor na checagem inicial:", e)
    palavras_bloqueadas = []

encerrar_processos_proibidos(palavras_bloqueadas)

# Loop principal
while True:
    try:
        # aguarda novo processo
        novo_proc = watcher()
        nome_novo = (novo_proc.Caption or "").lower()

        # atualiza lista de bloqueios
        try:
            palavras_bloqueadas = requests.get(SERVIDOR_LISTA, timeout=5).json()
        except Exception as e:
            print("[ERRO] Não foi possível conectar ao servidor:", e)
            palavras_bloqueadas = []

        # verifica processo recém-criado
        if any(p in nome_novo for p in palavras_bloqueadas):
            try:
                psutil.Process(novo_proc.ProcessId).kill()
                print(f"[Bloqueado - Novo] {nome_novo}")
                enviar_log(nome_novo)  # 🔹 registra no servidor
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # varre todos para garantir bloqueio
        encerrar_processos_proibidos(palavras_bloqueadas)

    except Exception as e:
        print("[ERRO LOOP]", e)
        time.sleep(1)
