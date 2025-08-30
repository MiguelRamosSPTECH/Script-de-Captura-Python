import pandas as pd
import psutil
import time
import os
from datetime import datetime
import pytz #ajusta fuso horário

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')

dados = {
    "timestamp": [],
    "uso_cpu_total_%":[], #dados_cpu
    "uso_ram_total_%":[], #uso_ram
    "swap_rate_mbs": [], #pegar_swap_rate
    # "tempo_cpu_ociosa": [], #dados_cpu
    # "cpu_io_wait_%":[],#dados_cpu
    "uso_disco_total_%":[], #uso_disco
    "disco_iops_total": [], #pegar_iops_e_latencia
    "disco_throughput_mbs": [], #pegar_throughput
    "disco_read_count":[], #pegar_iops_e_latencia
    "disco_write_count":[], #pegar_iops_e_latencia
    "disco_latencia_ms": [] #pegar_iops_e_latencia
}

#Throughput de um disco só
def to_mb(x): #funcao para transformar em mb
    return round((x / (1024**2)),2)

def uso_ram():
    uso_ram = psutil.virtual_memory().percent
    return uso_ram

def pegar_swap_rate():
    swap_rate = []
    swap_rate.append(psutil.swap_memory())
    time.sleep(1)
    swap_rate.append(psutil.swap_memory())

    sout_rate = (swap_rate[1].sout - swap_rate[0].sout)
    sin_rate = (swap_rate[1].sin - swap_rate[0].sin)
    return [to_mb(sout_rate), to_mb(sin_rate), (to_mb(sout_rate) + to_mb(sin_rate))]


def pegar_throughput():
    data = []
    data.append(psutil.disk_io_counters())
    time.sleep(1)
    data.append(psutil.disk_io_counters())

    readPerSecond = data[1].read_bytes - data[0].read_bytes
    writePerSecond = data[1].write_bytes - data[0].write_bytes
    return (to_mb(readPerSecond+writePerSecond))


def pegar_iops_e_latencia():
    tempo_inicio = time.perf_counter()
    io1 = psutil.disk_io_counters()
    time.sleep(1)
    tempo_final = time.perf_counter()
    io2 = psutil.disk_io_counters()

    readIOPS = io2.read_count - io1.read_count
    writeIOPS = io2.write_count - io1.write_count
    iops = readIOPS+writeIOPS

    total_ms = (tempo_final - tempo_inicio) *1000
    latencia_ms = 0
    if iops > 0:
        latencia_ms = round(total_ms / iops,2)
    return [iops, readIOPS, writeIOPS, latencia_ms]

def pegar_dados_cpu():
    # só com linux o io_wait
    cpu_dados = psutil.cpu_times_percent(interval=0.1)
    # cpu_iowait = cpu_dados.iowait
    cpu_idle = cpu_dados.idle
    cpu_uso_usuarios = cpu_dados.user
    cpu_uso_sistema = cpu_dados.system
    return [cpu_idle, cpu_uso_usuarios, cpu_uso_sistema]

def uso_disco():
    dados_disco = psutil.disk_usage('/').percent
    return dados_disco    


print("Iniciando captura de dados...",datetime.now())
print("------------------------------------------------------------------------------")
max_barra = 25
while True:
    horario_agora = datetime.now()
    trata_data = datetime.strftime(horario_agora, "%d-%m-%Y %H:%M:%S")
    dados_cpu = pegar_dados_cpu()
    uso_ram_porcentagem = uso_ram()
    swap_rate = pegar_swap_rate()
    uso_disco_porcentagem = uso_disco()
    dados_disco = pegar_iops_e_latencia()
    throughput = pegar_throughput()
    dados_disco.append(throughput)

    dados["timestamp"].append(trata_data)
    dados["uso_cpu_total_%"].append(dados_cpu[2])
    dados["uso_ram_total_%"].append(uso_ram_porcentagem)
    dados["swap_rate_mbs"].append(swap_rate[2])
    # dados["tempo_cpu_ociosa"].append(dados[0])
    # dados["cpu_io_wait_%"].append(dados[0])
    dados["uso_disco_total_%"].append(uso_disco_porcentagem)
    dados["disco_iops_total"].append(dados_disco[0])
    dados["disco_throughput_mbs"].append(dados_disco[len(dados_disco)-1])
    dados["disco_read_count"].append(dados_disco[1])
    dados["disco_write_count"].append(dados_disco[2])
    dados["disco_latencia_ms"].append(dados_disco[3])

    print("Uso da CPU (%) =", "|" * (int(max_barra * ((dados_cpu[2]/100)))),f"{dados_cpu[2]}%")
    print("Uso da RAM (%) =", "|" * (int(max_barra * ((uso_ram_porcentagem/100)))),f"{uso_ram_porcentagem}%")
    print("Swap Rate (MB/s) =", "|" * (int(max_barra * ((swap_rate[2]/100)))),f"{swap_rate[2]} MB/s")
    print("Tempo de CPU Ociosa (s) =", "|" * (int(dados_cpu[0]* ((dados_cpu[0]/100)))),f"{dados_cpu[0]} s")
    # print("Tempo de CPU I/O Ociosa (s) =", "|" * (int(dados_cpu[0]* ((dados_cpu[0]/100)))),f"{dados_cpu[0]} s")
    print("Uso do Disco (%) =", "|" * (int(max_barra* ((uso_disco_porcentagem/100)))),f"{uso_disco_porcentagem} GB")
    print("IOPS =", "|" * (int(max_barra* ((dados_disco[0]/100)))),f"{dados_disco[0]} MB/s")
    print("Throughput do disco =", "|" * (int(max_barra* ((dados_disco[len(dados_disco)-1]/100)))),f"{dados_disco[len(dados_disco)-1]} MB/s")
    print("Dados lidos no disco =", "|" * (int(max_barra* ((dados_disco[1]/100)))),f"{dados_disco[1]} MB/s")
    print("Dados escritos no disco =", "|" * (int(max_barra* ((dados_disco[2]/100)))),f"{dados_disco[2]} MB/s")
    print("Latência do disco =", "|" * (int(max_barra* ((dados_disco[3]/100)))),f"{dados_disco[3]} ms")

    df = pd.DataFrame(dados)
    df.to_csv("dados-mainframe.csv", encoding="utf-8", sep=";", index=False)
    
    print("\n------------------------------------------------------------------------------\n")