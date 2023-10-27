import sys
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          DATABASE_URL = 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    sys.exit()


# Dados a serem inseridos no banco de dados a partir do JSON
json_servicos = [
  {
    "name": "internet",
    "direction": "output",
    "udp_ports": "53",
    "tcp_ports": "80,443",
    "synonyms": ["internet", "net"]
  },
  {
    "name": "fifa",
    "direction": "input",
    "udp_ports": "3659,4500,5000",
    "tcp_ports": "1935,3074,3659",
    "synonyms": ["fifa","fifa 23","jogo fifa","EA SPORTS FC","EA Sports FC 24","jogo EA Sports FC"]
  },
  {
    "name": "eFootball",
    "direction": "input",
    "udp_ports": "88,500,3074,3544,4500,27015,27031,27032,27033,27034,27035,27036",
    "tcp_ports": "3074,3478,3479,3480",
    "synonyms": ["eFootball", "PES"]
  },
  {
    "name": "ssh",
    "direction": "output",
    "udp_ports": None,
    "tcp_ports": "22",
    "synonyms": ["ssh","porta 22"]
  },
  {
    "name": "telnet",
    "direction": "output",
    "udp_ports": None,
    "tcp_ports": "23",
    "synonyms": ["telnet", "porta 23"]
  },
  {
    "name": "redirecionamento externo as cameras",
    "direction": "input",
    "udp_ports": None,
    "tcp_ports": "8080",
    "synonyms": ["redirecionamento externo as cameras", "acesso externo as cameras"]
  }
]

# Limpeza da tabela  

try:
  conn = psycopg2.connect(DATABASE_URL)
  cursor = conn.cursor()
  delete_query = "DELETE FROM services;"
  cursor.execute(delete_query)
  print('Limpando registros da tabela services...')
  # Inserção dos dados no banco de dados

  for servico in json_servicos:
    cursor.execute(
        "INSERT INTO public.services (name, direction, tcp_ports, udp_ports, synonyms) VALUES (%s, %s, %s, %s, %s)",
        (servico["name"], servico["direction"], servico["tcp_ports"], servico["udp_ports"], servico["synonyms"])
    )
    
  print("pronto")
    
  # Commit e encerramento da conexão
  conn.commit()
  cursor.close()
  conn.close()
except psycopg2.Error as erro:
  print(f"Erro: {erro}")





