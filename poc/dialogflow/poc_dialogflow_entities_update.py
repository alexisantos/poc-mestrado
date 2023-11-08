# Method: projects.agent.entityTypes.list

import sys
import os
import requests
import psycopg2

#import google.cloud
from google.oauth2 import service_account
from google.auth.transport.requests import Request

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          DATABASE_URL = 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    sys.exit()


endpoint = 'https://dialogflow.googleapis.com'
project  = 'poc-smjo'                               # nome do projeto no google cloud
google_json_patch = os.getenv('Google_json_patch')  # caminho do arquivo de chave json da nuvem google
serviceaccount_json_key = google_json_patch
scopes = ['https://www.googleapis.com/auth/dialogflow']

def credential_renew():
    request = Request()
    credentials.refresh(request)
    if credentials.token:
        print("Autenticado.")
        #print(f"{credentials.token}")
    else:
        print("Autenticação falhou")

def get_dialogflow_entity_list():
    # GET request para https://{endpoint}/v2/{parent=projects/*/agent}/entityTypes
    parent = f'projects/{project}/agent'  # Valor do parâmetro parent
    api_path = f'/v2/{parent}/entityTypes'
    url = f'{endpoint}{api_path}'
 
    params = {'languageCode': 'pt-br'}
        
    response = requests.get(url, headers={
        'Authorization': f'Bearer {credentials.token}',
    }, params=params)

    entity_list = []
    if response.status_code == 200:
        entity_list = response.json()
        #print(entity_list)     
    else:
        print(f"Erro na solicitação HTTP: {response.status_code} - {response.text}")
    return entity_list
    
def get_dialogflow_entity_info(displayName, entity_list):
    if entity_list:
        # displayName deve ser a entidade escolhida para atualizacao ,por exemplo alvo
        for entity in entity_list['entityTypes']:
            # Verificar se o valor da chave 'displayName' é igual a 'alvo'
            if entity['displayName'] == displayName:
                name_path = entity['name']
                name_id = name_path.split("/")
                name_id = name_id[-1]
                entity_info = {
                    'name_path': name_path,
                    'name_id': name_id,
                    'displayName': entity['displayName'],
                    'kind': entity['kind'],
                    'entities': entity['entities']
                }
                return entity_info
        print(f"Não encontrado nenhuma entidade com o nome {displayName} no projeto {project}")
    else:
        print(f"entity_list está vazio")    
    return False

def select_db_table(table, columns, column):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        query = f"SELECT {columns} FROM {table} WHERE {column} !='';"
        cursor.execute(query)
        table_lines = cursor.fetchall() 
        # Inserção dos dados no banco de dados
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as erro:
        print(f"Erro\nErro: {erro}")
        table_lines = False
    return table_lines
        

def update_dialogflow_entity_path_categories(entity):
    #PATCH https://{endpoint}/v2/{entityType.name=projects/*/agent/entityTypes/*}
    entitytype_name = entity['name_path']  # Valor do parâmetro entityType.name
    api_path = f'/v2/{entitytype_name}'
    url = f'{endpoint}{api_path}'
    
    params = {
        "languageCode": "pt-br",
        "displayName": entity['displayName'],
        "name": entity['name_id'],
        "kind": entity['kind'],
        "entities": []
    }
    categories_name = select_db_table("categories", "name, synonyms", "name")
    for category in categories_name:
        entity_dict = {
            "value":    category[0],    # Nome da categoria
            "synonyms": category[1]     # Sinônimos da categoria
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params

    response = requests.patch(url, headers={
        'Authorization': f'Bearer {credentials.token}',
    }, json=params)

    data = []
    if response.status_code == 200:
        data = response.json()
        #print(entity_list)     
    else:
        print(f"Erro na solicitação HTTP: {response.status_code} - {response.text}")
    
    return data

def update_dialogflow_entity_path_target(entity):
    #PATCH https://{endpoint}/v2/{entityType.name=projects/*/agent/entityTypes/*}
    entitytype_name = entity['name_path']  # Valor do parâmetro entityType.name
    api_path = f'/v2/{entitytype_name}'
    url = f'{endpoint}{api_path}'
    
    params = {
        "languageCode": "pt-br",
        "displayName": entity['displayName'],
        "name": entity['name_id'],
        "kind": entity['kind'],
        "entities": []
    }
    devices_names   = select_db_table("devices", "hostname, ip", "hostname")
    categories_name = select_db_table("categories", "name, synonyms", "name")

    for device in devices_names:
        entity_dict = {
            "value":    device[0],               # Nome do dispositivo
            "synonyms": [device[0],device[1]]    # Sinonimo do dispositivo (ele mesmo)
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params


    for category in categories_name:
        entity_dict = {
            "value":    category[0],    # Nome da categoria
            "synonyms": category[1]     # Sinônimos da categoria
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params

    response = requests.patch(url, headers={
        'Authorization': f'Bearer {credentials.token}',
    }, json=params)

    data = []
    if response.status_code == 200:
        data = response.json()
        #print(entity_list)     
    else:
        print(f"Erro na solicitação HTTP: {response.status_code} - {response.text}")
    
    return data

def update_dialogflow_entity_path_services(entity):
    #PATCH https://{endpoint}/v2/{entityType.name=projects/*/agent/entityTypes/*}
    entitytype_name = entity['name_path']  # Valor do parâmetro entityType.name
    api_path = f'/v2/{entitytype_name}'
    url = f'{endpoint}{api_path}'
    
    params = {
        "languageCode": "pt-br",
        "displayName": entity['displayName'],
        "name": entity['name_id'],
        "kind": entity['kind'],
        "entities": []
    }
    services_name = select_db_table("services", "name, synonyms", "name")
    for service in services_name:
        entity_dict = {
            "value":    service[0],    # Nome da categoria
            "synonyms": service[1]     # Sinônimos da categoria
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params

    response = requests.patch(url, headers={
        'Authorization': f'Bearer {credentials.token}',
    }, json=params)

    data = []
    if response.status_code == 200:
        data = response.json()
        #print(entity_list)     
    else:
        print(f"Erro na solicitação HTTP: {response.status_code} - {response.text}")
    
    return data


def update_dialogflow_entity_path_host(entity):
    #PATCH https://{endpoint}/v2/{entityType.name=projects/*/agent/entityTypes/*}
    entitytype_name = entity['name_path']  # Valor do parâmetro entityType.name
    api_path = f'/v2/{entitytype_name}'
    url = f'{endpoint}{api_path}'
    
    params = {
        "languageCode": "pt-br",
        "displayName": entity['displayName'],
        "name": entity['name_id'],
        "kind": entity['kind'],
        "entities": []
    }

    devices  = select_db_table("devices", "hostname, ip", "hostname")

    for device in devices:
        entity_dict = {
            "value":    device[0],    # Nome do dispositivo
            "synonyms": device[0]     # Sinonimo do dispositivo (ele mesmo)
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params
        entity_dict = {
            "value":    device[1],    # Nome do dispositivo
            "synonyms": device[1]     # Sinonimo do dispositivo (ele mesmo)
        }
        params["entities"].append(entity_dict) # Adiciona a entidade à lista de entidades em params

    response = requests.patch(url, headers={
        'Authorization': f'Bearer {credentials.token}',
    }, json=params)

    data = []
    if response.status_code == 200:
        data = response.json()
        #print(entity_list)     
    else:
        print(f"Erro na solicitação HTTP: {response.status_code} - {response.text}")
    
    return data



##################################


if __name__ == '__main__':
    # Informações da conta de serviço e escopo    
    credentials = service_account.Credentials.from_service_account_file(
        serviceaccount_json_key,
        scopes = scopes
    )
    
    print("Contando ao Google clould...")
    if not credentials.token:
        print("Renovando token google...")
        credential_renew()

    entitylist = get_dialogflow_entity_list()
    entityinfo_categoria = get_dialogflow_entity_info('categoria', entitylist) # retorna um objeto
    entityinfo_alvo      = get_dialogflow_entity_info('alvo', entitylist) # retorna um objeto
    entityinfo_servicos  = get_dialogflow_entity_info('servico', entitylist) # retorna um objeto
    entityinfo_host  = get_dialogflow_entity_info('host', entitylist) # retorna um objeto
    # print(entityinfo)
    entity_categoria_update = update_dialogflow_entity_path_categories(entityinfo_categoria)
    entity_alvo_update      = update_dialogflow_entity_path_target(entityinfo_alvo)
    entity_servico_update   = update_dialogflow_entity_path_services(entityinfo_servicos)
    entity_host_update      = update_dialogflow_entity_path_host(entityinfo_host)

    v  = '\033[32m'
    vv = '\033[0m'

    print(f"{v}Atualizando entidade 'categoria': {vv}")
    print(entity_categoria_update)
    print(f"{v}Atualizando entidade 'alvo': {vv}")
    print(entity_alvo_update)
    print(f"{v}Atualizando entidade 'servicos': {vv}")
    print(entity_servico_update)
    print(f"{v}Atualizando entidade 'host': {vv}")
    print(entity_host_update)
    

