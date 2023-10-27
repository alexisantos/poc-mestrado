import sys
import os
import requests
import time
import json
import netifaces    # para descobrir o gateway da rede
import socket       # para descobrir o ip do dispositivo que está executando este código
from jsonpath_ng import jsonpath, parse
import psycopg2
from random import randint

DATABASE_URL = os.getenv('DATABASE_URL')
api_key = os.getenv('FINGERBANK_API_KEY')


if (DATABASE_URL is None) or (api_key is None):
    print("Error: You must define a DATABASE_URL and FINGERBANK_API_KEY environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          ex: 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    print(f"DATABASE_URL={DATABASE_URL}\napi_key = {api_key}")
    sys.exit()

conn = psycopg2.connect(DATABASE_URL)

def consulta_fingerbank(api_key, dhcp_fingerprint, mac, hostname, upnp_server_strings, destination_hosts):
    url = "https://api.fingerbank.org/api/v2/combinations/interrogate"

    # Parâmetro dhcp_fingerprint
    #destination_hosts = "amoeba.roku.com"
    params = {
        "dhcp_fingerprint": dhcp_fingerprint,
        "mac": mac,
        "hostname": hostname,
        "upnp_server_strings": [upnp_server_strings],
        "destination_hosts": [destination_hosts]
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }

    response = requests.post(url, headers=headers, json=params)
    print(f"\nEnviando parametros para fingerbank: {params}")

    if response.status_code == 200:
        retorno_fingerbank = response.json()
        # print(retorno_fingerbank)

        id_fingerbank = retorno_fingerbank['device']['id']
        name_fingerbank = retorno_fingerbank['device']['name']
        jsonpath_parents_id =      parse("$.device.parents.[*].id")                                 # Criar o JSONPath
        jsonpath_parents_id_name = parse("$.device.parents.[*].name")                               # Criar o JSONPath
        parent_ids    = [match.value for match in jsonpath_parents_id.find(retorno_fingerbank)]      # Aplicar o JSONPath no objeto de dados
        parent_names  = [match.value for match in jsonpath_parents_id_name.find(retorno_fingerbank)] # Aplicar o JSONPath no objeto de dados
        #print(f"\nO ID é {id_fingerbank} e os parentes são: {parent_ids} ({parent_names})")

        return id_fingerbank, name_fingerbank, parent_ids, parent_names
    else:
        #print("Erro na consulta a API fingerbank:", response.status_code)
        return None, None, None, None

def get_gateway_ip():
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET]
    return default_gateway[0]


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))  # Conecta a um endereço IP externo (no exemplo, o servidor DNS do Google)
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


if __name__ == '__main__':

    inicio_timer = time.time()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute("SELECT id from categories WHERE classification_id='1.8.1'")
            reg = cursor.fetchall()
            category_id = reg[0][0]
        with conn.cursor() as cursor:           # Buscar por todos os dispositivos não classificados
            cursor.execute("SELECT id, hostname, mac, ip, fingerprint_dhcp, upnp_server_strings, top5_dest_hosts_fqdn FROM devices WHERE category_id IS NULL OR category_id = %s" %category_id)
            dispositivos = cursor.fetchall()    # Dispositivos não classificados estão aqui
        
        
        #print(f"Dispositivos da base:")
        #print(json.dumps(dispositivos, indent=2))
        #print(dispositivos, end='\n\n')

        print("\033[34m\nIniciando a classificação de dispositivos. Serão analisados todos \nos dispositivos registrados que estejam não classificados.\n\033[0m")

        for dispositivo in dispositivos:
            device_id, hostname, mac, ip, dhcp_fingerprint, upnp_server_strings, top5_dest_hosts_fqdn = dispositivo

            print(f"Dispostivo para classificar: {mac} (hostname: {hostname})")
            fingerbank_data = consulta_fingerbank(api_key, dhcp_fingerprint, mac, hostname, upnp_server_strings, top5_dest_hosts_fqdn)
            #time.sleep(1)
            fingerbank_dev_id, fingerbank_dev_name, fingerbank_parents_id, fingerbank_parents_name = fingerbank_data
            # Mostra dados fingerbank de cada dispositivo
            print(f"\nDevolução API fingerbank para o dispositivo de hostname '{hostname}': ")
            if fingerbank_dev_id is not None: 
                print(f"  --> ID do dispositivo no fingerbank: {fingerbank_dev_name} (ID#: {fingerbank_dev_id})")
                print(f"  --> IDs das classes parentes no fingerbank: {fingerbank_parents_id}")
                print(f"  --> Nomes das classes parentes no fingerbank: {fingerbank_parents_name}")

            # Classificação
            # Primeiro procura consulta se o fingerbank_device_id está presente no banco (ganhar tempo), caso negativo verifica se seu pai está     
            categoria = False
            if fingerbank_dev_id:
                with conn.cursor() as cursor:
                    # Buscar se existe a ID fingerbank na base de dados do classificador
                    cursor.execute("SELECT classification_id, name FROM categories WHERE %s = ANY(fingerbank_ids)" %fingerbank_dev_id)
                    categoria = cursor.fetchall()

            if not categoria:
                # Neste caso, o fingerbank_device_id não foi localizado na lista de ids mapeados na tabela categories, verifica se seus ancestrais estão na lista e pára se encontrar.
                if fingerbank_parents_id:
                    for parent_id in fingerbank_parents_id:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT classification_id, name FROM categories WHERE %s = ANY(fingerbank_ids )" %parent_id)
                            categoria = cursor.fetchone()
                        if categoria:
                            break

            # Atualizando a tabela dispositivos com a classificação do dispositivo.
            if categoria:
                if type(categoria) is list:
                    print(f"\033[32mClassificação de categoria na hierarquia: {categoria[0]}\033[0m")
                    classe_dispositivo     = categoria[0][0]
                    classe_dipositivo_nome = categoria[0][1]
                else:
                    print(f"\033[32mClassificação de categoria na hierarquia: {categoria}\033[0m")
                    classe_dispositivo     = categoria[0]
                    classe_dipositivo_nome = categoria[1]
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM categories WHERE classification_id = '%s'" %classe_dispositivo)
                    reg = cursor.fetchone()
                    classe_id = reg[0]
                    #print(f"O id de registro no banco é {classe_id}")
                    cursor.execute("UPDATE devices SET category_id = %s WHERE id = %s",  (classe_id, device_id))  
                    cursor.execute("UPDATE devices SET fingerbank_id = %s WHERE id = %s",  (fingerbank_dev_id, device_id))
                    cursor.execute("UPDATE devices SET fingerbank_name = %s WHERE id = %s",  (fingerbank_dev_name, device_id))
                    cursor.execute("UPDATE devices SET fingerbank_parents_id = %s WHERE id = %s",  (fingerbank_parents_id, device_id))
                if hostname == "":
                    sufixo_hostname = randint(1, 200)
                    cursor = conn.cursor()
                    cursor.execute("SELECT synonyms FROM categories WHERE name = '%s'" %classe_dipositivo_nome) 
                    categoria_singular = cursor.fetchone()
                    categoria_singular = categoria_singular[0][1] #as categorias estao no plural, o objetivo aqui é pegar o nome no singular
                    print(f"\033[32mNa falta de um hostname, o dispositivo se chamará agora: {categoria_singular}{sufixo_hostname}\033[0m")
                    #print(f"Na falta de um hostname, o dispositivo se chamará agora: {classe_dispositivo}{sufixo_hostname}")
            else:
                #print("Nenhuma correspondência encontrada. Dispositivo marcado para nova classificação.")
                print("\033[31mNenhuma correspondência encontrada. Dispositivo marcado para nova classificação.\033[0m")

                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM categories WHERE classification_id = '1.8.1'")
                    reg = cursor.fetchone()
                    classe_id = reg[0]
                    cursor.execute("UPDATE devices SET category_id = %s WHERE id = %s",  (classe_id, device_id))  
                    cursor.execute("UPDATE devices SET fingerbank_id = %s WHERE id = %s",  (fingerbank_dev_id, device_id))
                    cursor.execute("UPDATE devices SET fingerbank_name = %s WHERE id = %s",  (fingerbank_dev_name, device_id))
                    cursor.execute("UPDATE devices SET fingerbank_parents_id = %s WHERE id = %s",  (fingerbank_parents_id, device_id))
            print("---"*40, end='\n\n')
         
        conn.commit()
        cursor.close()
        conn.close()


    except psycopg2.Error as erro:
        # Exibir mensagem de erro
        print("Erro ao acessar o banco de dados:", erro)

    fim_timer = time.time()
    tempo_execucao = fim_timer - inicio_timer

    print(f"Tempo de execução: {tempo_execucao} segundos")






