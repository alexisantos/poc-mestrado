import psycopg2
import sys
import os
from ping3 import ping

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          ex: 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    print(f"DATABASE_URL={DATABASE_URL}")
    sys.exit()

lista_ips = []

def ping_scan(ip_list):
    lista_status = []
    for ip in ip_list:
        response_time = ping(ip, timeout=0.5)
        if response_time is not None:
            lista_status.append((ip, True))
        else:
            lista_status.append((ip, False))
    return lista_status


try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT ip from devices") 
    ips = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()

    for ip in ips:
        lista_ips.append(ip[0])
    
    print("Buscando dispositivos na rede. Aguarde...")
    device_status_icmp = ping_scan(lista_ips)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("Buscando concluida. Atualizando banco...")
    for device in device_status_icmp:  
        cursor.execute("UPDATE devices SET is_enabled = %s WHERE ip = %s", (device[1], device[0]))
    print("Concluido")

    conn.commit()
    cursor.close()
    conn.close()
    
except psycopg2.Error as erro:
    print(f"Deu um erro: {erro}")



'''

def ping_scan(ip_list):
    for ip in ip_list:
        response_time = ping(ip, timeout=5)
        if response_time is not None:
            print(f"{ip} está online (tempo de resposta: {response_time} ms)")
        else:
            print(f"{ip} está offline")

if __name__ == "__main__":
    ping_scan(lista_ips)
'''