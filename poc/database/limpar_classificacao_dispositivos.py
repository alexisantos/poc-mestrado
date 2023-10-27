import sys
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          DATABASE_URL = 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    sys.exit()

try:
  conn = psycopg2.connect(DATABASE_URL)
  cursor = conn.cursor()
  cursor.execute("UPDATE devices SET category_id = NULL;") 
  conn.commit()
  cursor.close()
  conn.close()
  print('A classificacao foi limpa na tabela devices')
except psycopg2.Error as erro:
  print(f"Deu um erro: {erro}")