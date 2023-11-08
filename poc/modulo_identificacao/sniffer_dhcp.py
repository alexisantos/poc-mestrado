from include_sniffer_dhcp_classes import BPF, BPF_DHCP, Ethernet, IPv4, UDP, DHCP_Protocol, DHCP
import sys
import os
import socket
import argparse
import time
import netifaces
import psycopg2
from psycopg2 import OperationalError


'''
sudo apt update
sudo apt install python3-pip
sudo apt install python3-psycopg2
sudo pip install psycopg2-binary
sudo pip install psycopg2

Para atualizar banco cockroachlabs.cloud...
  Baixar certificado para o banco em cockroachlabs.cloud
  Como esse o sniffer precisa rodar como sudo fazer:
  $ sudo su
  $ curl --create-dirs -o $HOME/.postgresql/root.crt 'https://url_do_cockroach...'
  $ exit

rodar em modo admin ou root:
   > sudo python3 sniffer_dhcp.py

No windows, pode ser necessário utilizar Microsoft C++ Build Tools para importar a biblioteca netifaces
'''

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          ex: 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    print(f"DATABASE_URL={DATABASE_URL}")
    sys.exit()

simple_dhcp_type = ['DHCPREQUEST']


def lista_interfaces_rede():
    interfaces = netifaces.interfaces()
    lista = []

    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses and not interface.startswith('lo'):
            ip = addresses[netifaces.AF_INET][0]['addr']
            lista.append([interface, ip])
    return lista


def convert_hex_str_to_int_str(hexstr):
    pool = []
    for x,y in zip(hexstr[0::2], hexstr[1::2]):
        pool.append(str(int(x+y, 16)))
    return ','.join(pool)

def convert_hex_str_to_mac(hexstr):
    pool = []
    for x,y in zip(hexstr[0::2], hexstr[1::2]):
        pool.append(x+y)
    return ':'.join(pool)

def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime())


def adicionar_dispositivo(mac, hostname, ip, fingerprint_dhcp):

    try:
        # Tente estabelecer a conexão
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Verificar se o MAC já existe no banco de dados
        cursor.execute("SELECT mac FROM devices WHERE mac = '%s'" %mac)
        mac_existente = cursor.fetchone() is not None


        cursor.execute("SELECT hostname FROM devices WHERE mac = '%s'" %mac)
        hostname_existente = cursor.fetchone()
        if hostname_existente is not None:
            hostname_existente = hostname_existente[0]

        if mac_existente:
            # Atualizar dados se mac já for existente
            cursor.execute("UPDATE devices SET ip = %s WHERE mac = %s", (ip, mac))
            cursor.execute("UPDATE devices SET fingerprint_dhcp = %s WHERE mac = %s", (fingerprint_dhcp, mac))
            if hostname_existente is None or hostname_existente =="":
                cursor.execute("UPDATE devices SET hostname = %s WHERE mac = %s", (hostname, mac))
        else:
            # Inserir as informações do novo dispositivo no banco de dados
            cursor.execute("INSERT INTO devices (mac, hostname, ip, fingerprint_dhcp) VALUES (%s, %s, %s, %s)",
                        (mac, hostname, ip, fingerprint_dhcp))
        conn.commit()
        cursor.close()
        conn.close()
    
    except OperationalError as e:
        # Capturou uma exceção OperationalError
        print(f"Erro ao conectar ao banco de dados. Erro: \n{e}")
        if "root certificate file" in str(e):
            print("Certificado do servidor não encontrado.\nCertificado obrigatório. Baixar Download CA Cert em https://cockroachlabs.cloud/clusters \n")
        else:
            print("Erro ao conectar ao banco. Verificar acesso a internet e permissões ao banco.")





if __name__ == '__main__':

    print("--"*30)
    print(f"   Uso: python3 dhcp_sniffer_main.py -i <interface>")
    print(f"   Por padrão, a interface para escaneamento é a primeira interface.\n   As interfaces neste dispositivo são: ")
    interfaces = lista_interfaces_rede()
    for interface in interfaces:
        print(f"      Nome da interface: {interface[0]} | IP: {interface[1]}")
    print("--"*30)
    print(f"   (Para encerrar, finalize a aplicação com ctrl + C)")

    interface_padrao = interfaces[0][0]

    # argument parse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', default=interface_padrao, help='sniffer interface to get DHCP packets. default is eth0')
    parser.add_argument('-d', '--detail', action='store_true', help='show more detail packet information. if not set, only {} show.'.format(' '.join(simple_dhcp_type)))
    args = parser.parse_args()

    # bind raw_socket
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 0x0800)

    # use BPF to filter DHCP packet
    BPF_DHCP().set_dhcp_filter(sock)

    sock.bind((args.interface, 0x0800))

    # print setting
    print('bind interface: {}'.format(args.interface))
    if args.detail:
        print('capture type: all DHCP broadcast packets')
    else:
        print('capture type: {}'.format(' '.join(simple_dhcp_type)))
        print("{:30}{:20}{:20}{:20}{:20}{:20}".format('Local Time', 'Message Type', 'Host Name', 'MAC', 'IPv4', 'Option 55'))
        print('-' * 130)

    # only get DHCP packets: 
    #     format: IPv4(EtherType: 0x0800) + UDP(port: 67, 68)
    while True:
        packet = sock.recv(2048)

        # get Ethernet Frame
        ethernet_frame = Ethernet(packet)
        source_mac = ethernet_frame.get_source_mac()
        dest_mac = ethernet_frame.get_dest_mac()
        ether_type = ethernet_frame.get_ether_type()

        # get IPv4 packet
        ip_packet = IPv4(packet)
        protocol = ip_packet.get_protocol()
        source_ip = ip_packet.get_source_ip()
        dest_ip = ip_packet.get_dest_ip()

        # get UDP datagram
        udp = UDP(packet)
        source_port = udp.get_source_port()
        dest_port = udp.get_dest_port()
        udp_length = udp.get_length()

        # get DHCP
        dhcp = DHCP(packet, udp_length - 8)
        dhcp.parse_options()
        dhcp.parse_payload()
        chaddr       = dhcp.chaddr
        ciaddr       = dhcp.ciaddr
        message_type = dhcp.option_53
        request_list = dhcp.option_55
        host_name    = dhcp.option_12
        # there is no option50 (request IP) when DHCP client rebinds lease. Should use ciaddr as IP address in this condition.
        request_ip   = dhcp.option_50 if '' != dhcp.option_50 else ciaddr
        server_id    = dhcp.option_54

        # get now
        now = get_time()

        if args.detail:
            print("message type  : {}".format(message_type))
            print("local time    : {}".format(now))
            print("host name     : {}".format(host_name))
            print("request ip    : {}".format(request_ip))
            print("server id     : {}".format(server_id))
            print("source MAC    : {}".format(convert_hex_str_to_mac(chaddr)))
            print("dest   MAC    : {}".format(convert_hex_str_to_mac(dest_mac)))
            print("source IP     : {}:{}".format(source_ip, source_port))
            print("dest   IP     : {}:{}".format(dest_ip, dest_port))
            print("UDP length    : {}".format(udp_length))
            print("option 55     : {}".format(convert_hex_str_to_int_str(request_list)))
            print("")
        else:
            if message_type not in simple_dhcp_type:
                continue

            request_mac = convert_hex_str_to_mac(chaddr)
            fingerprint_dhcp = convert_hex_str_to_int_str(request_list)
            
            
            print("{:30}{:20}{:20}{:20}{:20}{:20}".format(now, message_type, host_name, request_mac, request_ip, fingerprint_dhcp))
            #print(f"{host_name}{request_mac}{request_ip}{fingerprint_dhcp}")

            adicionar_dispositivo(str(request_mac).lower(), host_name, request_ip, fingerprint_dhcp)
            
