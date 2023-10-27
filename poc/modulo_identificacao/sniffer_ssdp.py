import os
import sys
import psycopg2


import json
import requests
import time
from ssdpy import SSDPClient #https://pypi.org/project/ssdpy/
from scapy.all import srp, Ether, ARP  # para obter o mac
import xml.etree.ElementTree as ET



DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          ex: 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    print(f"DATABASE_URL={DATABASE_URL}")
    sys.exit()


def get_mac_address(ip):
    # Cria um pacote ARP para enviar ao dispositivo
    arp = ARP(pdst=ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    # Envia o pacote ARP e recebe a resposta
    result = srp(packet, timeout=3, verbose=False)[0]

    # Extrai o endereço MAC da resposta
    if result:
        return result[0][1].hwsrc

    return None

def adicionar_dispositivo(mac, ip, hostname=None, upnp_server_strings=None, ssdp_url=None, manufacturer=None, modeldescription=None):
    # Estabelecer conexão com o banco de dados
    #conn = sqlite3.connect(db_dispositivos_sqlite)
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Verificar se o MAC já existe no banco de dados
    cursor.execute("SELECT mac FROM devices WHERE mac = %s", (mac,))
    mac_existente = cursor.fetchone() is not None

    if mac_existente:
        # Atualizar o IP do dispositivo existente
        cursor.execute("UPDATE devices SET ip = %s WHERE mac = %s", (ip, mac))
        cursor.execute("UPDATE devices SET hostname = %s WHERE mac = %s", (hostname, mac))
        cursor.execute("UPDATE devices SET upnp_server_strings = %s WHERE mac = %s", (upnp_server_strings, mac))
        cursor.execute("UPDATE devices SET ssdp_url = %s WHERE mac = %s", (ssdp_url, mac))
        cursor.execute("UPDATE devices SET manufacturer = %s WHERE mac = %s", (manufacturer, mac))
        cursor.execute("UPDATE devices SET modeldescription = %s WHERE mac = %s", (modeldescription, mac))
        print(f"O dispositivo {mac} já é existente, apenas atualizando características")
    else:
        # Inserir as informações do novo dispositivo no banco de dados
        print(f"{mac} é um dispositivo inédito, criando dispositivo na base.")
        cursor.execute("INSERT INTO devices (mac, hostname, ip, upnp_server_strings, ssdp_url, manufacturer, modeldescription) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (mac, hostname, ip, upnp_server_strings, ssdp_url, manufacturer, modeldescription))
        print(f"Dispositivo adicionado. ")
     

    # Salvar as alterações e fechar a conexão com o banco de dados
    conn.commit()
    cursor.close()
    conn.close()


seen_ips = set()
ssdp_parametros = []

print("Mantenha os dispositivos SSDP ligados. Os dispositivos compatíveis com SSDP geralmente trabalham com mídia.")
print("Aguardando um tempo por mensagens SSDP...")

conn = psycopg2.connect(DATABASE_URL)


client = SSDPClient()
devices = client.m_search("ssdp:all")

dados_brutos = json.dumps(devices, indent=2)

#print(dados_brutos)

for device in devices:
    ip = device.get("location", "").split("//")[1].split(":")[0]  # Extrair o IP do 'location'
    # Verificar se o IP já foi adicionado anteriormente
    if ip in seen_ips:
        continue
    seen_ips.add(ip)  # Adicionar o IP ao conjunto de IPs já vistos

    upnp_server_strings = device.get("server", "")  # Obter a string do servidor UPnP
    ssdp_url = device.get("location", "")  # Obter a URL SSDP

    # Criar um dicionário com as propriedades extraídas
    device_info = {
        "mac": str(get_mac_address(ip)).lower(),
        "ip": ip,
        "upnp_server_strings": upnp_server_strings,
        "ssdp_url": ssdp_url
    }

    # Acessar a ssdp_url e extrair informações do XML
    try:
        response = requests.get(ssdp_url)  # Fazer uma requisição GET à ssdp_url
        xml_content = response.text

        # Verificar se o conteúdo XML é válido
        if not xml_content.startswith("<"):
            print(f"Conteúdo XML inválido na ssdp_url: {ssdp_url}. Desconsiderado.")
            continue

        # Analisar o conteúdo XML
        root = ET.fromstring(xml_content)

        # Extrair as informações desejadas do XML
        friendly_name_elem = root.find(".//{urn:schemas-upnp-org:device-1-0}friendlyName")
        if friendly_name_elem is not None:
            friendly_name = friendly_name_elem.text
            device_info["hostname"] = friendly_name
        else:
            device_info["hostname"] = None

        manufacturer_elem = root.find(".//{urn:schemas-upnp-org:device-1-0}manufacturer")
        if manufacturer_elem is not None:
            manufacturer = manufacturer_elem.text
            device_info["manufacturer"] = manufacturer
        else:
            device_info["manufacturer"] = None
        
        model_description_elem = root.find(".//{urn:schemas-upnp-org:device-1-0}modelDescription")
        if model_description_elem is not None:
            model_description = model_description_elem.text
            device_info["modeldescription"] = model_description
        else:
            device_info["modeldescription"] = None

    except Exception as e:
        print(f"Erro ao acessar a ssdp_url: {e}")

    ssdp_parametros.append(device_info)


    if "none" not in device_info["mac"]:
        adicionar_dispositivo(device_info["mac"], device_info["ip"], device_info["hostname"], device_info["upnp_server_strings"], device_info["ssdp_url"], device_info["manufacturer"], device_info["modeldescription"])
        time.sleep(1.1)
    
# Converter a saída para uma string JSON formatada
output_json = json.dumps(ssdp_parametros, indent=2)


print(output_json)