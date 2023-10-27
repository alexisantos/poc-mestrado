import sys
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          DATABASE_URL = 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    sys.exit()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Dados a serem inseridos no banco de dados a partir do JSON
json_classificacao = {
  "rede": {
  "class": "0.",
  "name": "ativos de gestão de rede",
  "synonyms": ["ativos de gestão de rede", "ativo de gestão de rede", "roteadores", "roteador", "gateway", "gateways", "equipamentos de rede"],
  "fingerbank_ids": [4, 8136]
  },
  "todos dispositivos": {
    "class": "1.",
    "name": "todos dispositivos",
    "synonyms": ["todos", "todas", "todes", "todis", "todis", "tudim", "todos eles", "todas elas"],
    "fingerbank_ids": []
  },
  "computadores": {
    "class": "1.1",
    "name": "computadores",
    "synonyms": ["computadores", "computador", "laptop", "laptops", "desktop", "desktops", "notebook", "notebooks", "PCs", "pcs", "pc"],
    "fingerbank_ids": [1, 14, 21, 38, 117, 119, 120, 121, 123, 124, 130, 286, 247, 249, 5772, 5850, 79947, 79950, 79951, 79952, 79953, 79954, 79955, 91833, 76576, 76577, 111085, 39676]
  },
  "smartphones": {
    "class": "1.2",
    "name": "smartphones",
    "synonyms": ["smartphones", "smartphone", "telefone", "telefones", "celular", "celulares", "telemóvel", "telemóveis", "iphone", "iphones"],
    "fingerbank_ids": [11, 191, 192, 193, 264, 1312, 3724, 9891, 33449, 33453, 33507, 44740]
  },
  "consoles": {
    "class": "1.3",
    "name": "consoles",
    "synonyms": ["consoles", "console", "xbox", "xboxs", "playstation", "playstations", "play station", "play stations", "ps4", "ps5", "videogame", "videogames", "videogames", "video games"],
    "fingerbank_ids": [6, 134, 135, 139, 5584, 5585, 5586]
  },
  "tvs": {
    "class": "1.4",
    "name": "TVs",
    "synonyms": ["tvs", "TV", "smarttvs", "smart tvs", "smarttv", "smart tv", "tv box", "televisão", "televisores", "televisões", "tvs smart", "tv smart"],
    "fingerbank_ids": [142, 148, 5588, 7175, 9961, 33481, 33640, 33874, 39923, 39937, 40622, 41617, 68739, 78590, 78592, 78604, 78676, 78853, 79963, 80419, 105992]
  },
  "dispositivos IoT": {
    "class": "1.5",
    "name": "dispositivos IoT",
    "synonyms": ["dispositivos IoT", "dispositivo IoT", "iot", "IoTs", "dispositivos inteligentes", "dispositivo inteligente"],
    "fingerbank_ids": [15, 78269]
  },
  "sensores": {
    "class": "1.5.1",
    "name": "sensores",
    "synonyms": ["sensores", "sensor"],
    "fingerbank_ids": [78282, 78283]
  },
  "smart lights": {
    "class": "1.5.2",
    "name": "smart lights",
    "synonyms": ["smart lights", "smart light", "smartlights", "smartlight", "luzes inteligentes", "lampadas", "lampadas inteligentes", "lampadas iot"],
    "fingerbank_ids": [78274]
  },
  "smart plugs": {
    "class": "1.5.2",
    "name": "smart plugs",
    "synonyms": ["smart plugs", "smart plug", "smartplugs", "smartplug", "tomadas inteligentes", "tomada inteligente", "tomadas iots"],
    "fingerbank_ids": [78280]
  },
  "ares condicionados": {
    "class": "1.5.4",
    "name": "ares condicionados",
    "synonyms": ["ares condicionados", "ar condicionado", "ar condicionados", "aparelhos de ar condicionado"],
    "fingerbank_ids": [33770, 38470, 49730, 50800, 75156, 78369, 78674, 83465, 83749, 85930, 90208, 93212, 94810, 95958, 97499, 103645, 103655, 121115, 121399, 121536, 123892]
  },
  "assistentes virtuais": {
    "class": "1.5.5",
    "name": "assistentes virtuais",
    "synonyms": ["assistentes virtuais", "assistente virtual", "alexa", "alexas", "echo", "echos"],
    "fingerbank_ids": [9417, 15669, 78271]
  },
  "smartlocks": {
    "class": "1.5.5",
    "name": "smart locks",
    "synonyms": ["smart locks", "smart lock", "smartlocks", "fechaduras", "fechadura", "trancas"],
    "fingerbank_ids": [22, 78273]
  },
  "dispositivos de monitoramento": {
    "class": "1.6",
    "name": "dispositivos de videomonitoramento",
    "synonyms": ["dispositivos de videomonitoramento", "dispositivo de videomonitoramento", "dispositivos de segurança", "DVR", "DVRs", "videomonitoramento", "NVR", "NVRs"],
    "fingerbank_ids": [78593, 78603, 89954, 106917]
  },
    "cameras": {
    "class": "1.6.1",
    "name": "cameras",
    "synonyms": ["cameras", "camera", "cameras de segurança", "camera de segurança"],
    "fingerbank_ids": [152, 8147, 78370, 85240]
  },
  "impressoras": {
    "class": "1.7",
    "name": "impressoras",
    "synonyms": ["impressoras", "impresora", "multifuncional", "multifuncionais"],
    "fingerbank_ids": [8]
  },
  "outros": {
    "class": "1.8",
    "name": "outros",
    "synonyms": ["outros", "corporativos", "voip", "voips", "storage", "storages"],
    "fingerbank_ids": [3, 9, 10, 12, 13, 17, 20, 23, 24, 8238, 16842, 16861, 33738, 73235]
  },
  "dispositivos não classificados": {
    "class": "1.8.1",
    "name": "dispositivos não classificado",
    "synonyms": ["dispositivos não classificados", "dispositivo não classificado", "não classificados", "desconhecidos", "não identificados"],
    "fingerbank_ids": []
  }
}

# Limpeza da tabela  

try:
  insert_query = "DELETE FROM categories;"
  cursor.execute(insert_query)
  print('Limpando registros da tabela categorias...')
  # Inserção dos dados no banco de dados
  for key, value in json_classificacao.items():
      class_id = value["class"]
      name = value["name"]
      synonyms = value["synonyms"]
      fingerbank_ids = value["fingerbank_ids"]
      
      insert_query = "INSERT INTO categories (name, classification_id, synonyms, fingerbank_ids) VALUES (%s, %s, %s, %s) RETURNING id;"
      cursor.execute(insert_query, (name, class_id, synonyms, fingerbank_ids))
      inserted_id = cursor.fetchone()[0]
      
      print(f"Inserted: {name} with ID: {inserted_id}")
      
  # Commit e encerramento da conexão
  conn.commit()
  cursor.close()
  conn.close()
  print(f"\nPronto...\nExecute o app para atualizar as categorias e dispositivos no dialogflow")
except psycopg2.Error as erro:
  print(f"Erro ao limpar registros da tabela categorias. \nConsidere limpar a classificacao de dispositivos antes.\nErro: {erro}")





