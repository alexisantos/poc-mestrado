import sys
import os
import paramiko
import psycopg2
from time import sleep
import re

#iptables -t nat -vnL PREROUTING
#iptables -L -n -v


DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print("Error: You must define a DATABASE_URL environment variable. Windows users: reboot may be required.\n\
          This code uses the CockroachDB cloud database.\n\
          ex: 'postgresql://user:userpassword@crown-sponge-995.g8x.cockroachlabs.cloud:26257/db-name?sslmode=verify-full'")
    print(f"DATABASE_URL={DATABASE_URL}")
    sys.exit()

router_definition = {
    "gateway": "192.168.3.25",
    "username": "root",
    "password": "admin"
}

verde = "\033[32m"
endverde = "\033[0m"

def check_inputs_from_block_intent(action, target, service, userfeedback, devices_list, categories_list):
    target_status = False
    target_type = 'desconhecido'
    final_target = 'todos dispositivos'
   
    if not userfeedback: # se esta é a primeira interação com esta aplicação
        if type(target) is list:
            for t in target:
                if t in devices_list:
                    # print(f'Encontrei {t} na lista de dispositivos')
                    final_target = t
                    target_status = True
                    target_type = 'dispositivo'
                    break
            if not target_status:
                for t in target:
                    if t in categories_list:
                        # print(f'Encontrei {t} na lista de categorias')
                        final_target = t
                        target_status = True
                        target_type = 'categoria'
                        break

            if target_status is True:
                feedback_msg = '(ack request): '
                if target_type == 'categoria':
                    feedback_txt = f'Você deseja {action} o serviço {service} para todos dispositivos do tipo {final_target}?'
                else: # Solicita confirmação para apenas um dispositivo
                    feedback_txt = f'Você deseja {action} o serviço {service} para o dispositivo {final_target}?'
            else:
                if "todos dispositivos" in target or "todos os dispositivos" in target:
                    feedback_msg = '(ack request): '
                    feedback_txt = f'Você deseja {action} o serviço {service} para todos dispositivos?'
                    final_target = "todos dispositivos"
                else:
                    feedback_msg = '(unable): '
                    feedback_txt = f'Não consegui localizar nenhuma combinação para {target} na base de dispositivos nem na base de categorias. Você pode dizer "listar todos dispositivos" para exibir todos os dispositivos que já foram registrados na rede'
        else:
            if target in devices_list:
                target_status = True
                target_type = 'dispositivo'

            if not target_status:
                if target in categories_list:
                    target_status = True
                    target_type= 'categoria'    
            
            if target_status is True:
                feedback_msg = '(ack request): '
                if target_type == 'categoria':
                    feedback_txt = f'Você deseja {action} o serviço {service} para todos dispositivos do tipo {target}?'
                else: # Solicita confirmação para apenas um dispositivo
                    feedback_txt = f'Você deseja {action} o serviço {service} para o dispositivo {target}?'
            else:
                feedback_msg = '(unable): '
                feedback_txt = f'Não consegui localizar nenhuma combinação para {target} na base de dispositivos nem na base de categorias. Você pode dizer "listar todos dispositivos" para exibir todos os dispositivos que já foram registrados na rede'
    else:
        if userfeedback == "sim":
            feedback_msg = '(sucess): '
            feedback_txt = f'Certo, vou {action} agora mesmo.'

            if type(target) is list:
                for t in target:
                    if t in devices_list:
                        # print(f'Encontrei {t} na lista de dispositivos')
                        final_target = t
                        target_status = True
                        break
                if not target_status:
                    for t in target:
                        if t in categories_list:
                            # print(f'Encontrei {t} na lista de categorias')
                            final_target = t
                            target_status = True
                            break
            else:
                print("A entidade 'alvo' precisa ser uma lista no dialogflow")

            checked_intent = {
                'action' : action,
                'target' : final_target,
                'service': service
            }

            translated_intent = translate(checked_intent)
            instructions      = router_intructions(translated_intent)
            
            print(f"{verde}A intenção do usuário foi traduzida em: {endverde} {translated_intent}")
            print(f"{verde}As intruções a serem executadas são: {endverde}")
            # for instrucao in instructions:
            #     print (instrucao)
            print(f'{instructions}', end='\n')
            router_execution  = set_router_instructions(router_definition, translated_intent, instructions)
            #print(router_execution)
            feedback_txt = f'Certo, vou {action} agora mesmo....\n {router_execution}'

        else:
            feedback_msg = '(sucess): '
            feedback_txt = f'Tudo bem, vou ficar quietinha. Talvez eu não tenha compreendido direito.'
    feedback = f'{feedback_msg}{feedback_txt}'

    return feedback

def check_inputs_from_list_intent(action, list_options, category, status, userfeedback):

    if not userfeedback: # se esta é a primeira interação com esta aplicação
        if "dispositivos" in list_options:
            feedback_msg = '(ack request): '
            if category == "todos dispositivos":
                feedback_txt = f'Você deseja {action} todos os dispositivos {status} presentes na rede?'
            elif category == "ativos de gestão de rede":
                feedback_txt = f'Você deseja {action} todas os dispositivos dos {category} (roteadores e similares)? '
            else:
                feedback_txt = f'Você deseja ver uma lista dos dispositivos {status} da categoria {category}?'
        elif "regras" in list_options:
            feedback_msg = '(ack request): '
            if category == "todos dispositivos":
                feedback_txt = f'Você deseja {action} todas as regras de todos os dispositivos?'
            elif category == "ativos de gestão de rede":
                feedback_txt = f'Você deseja {action} todas as regras dos {category} (roteadores e similares)? '
            else:
                feedback_txt = f'Você deseja {action} as regras dos dispositivos da categoria {category}?'
        else:
            feedback_msg = '(unable): '
            feedback_txt = f'Não consegui entender pois não esperava receber em list_options apenas "dispositivos" ou "regras". No entanto recebi "{list_options}"'
    else:
        if "sim" in userfeedback:
            feedback_msg = '(sucess): '
            
            # Chama função de conexão ao banco aqui
            checked_intent = {
                'action' : action,
                'list_option': list_options,
                'category' : category,
                'status': status
            }
            translated_intent = translate(checked_intent)
            sql_response = sql_execution(translated_intent)
            feedback_txt = f'Certo, aqui está a listagem de {category}... \n{sql_response}'
            
        else:
            feedback_msg = '(sucess): '
            feedback_txt = f'Tudo bem meu jovem, acho que não fui capaz de entender o que queria.'

    feedback = f'{feedback_msg}{feedback_txt}'

    return feedback

def check_inputs_from_rename_intent(action, host, newname, userfeedback):
    if "sim" in userfeedback:
        # Chama função de conexão ao banco aqui
        checked_intent = {
            'action' : action,
            'host': host,
            'newname' : newname,
        }
        translated_intent = translate(checked_intent)
        sql_response = sql_execution(translated_intent)
        feedback_msg = sql_response[0]
        feedback_txt = sql_response[1]
    else:
        feedback_msg = '(sucess): '
        feedback_txt = f'Tudo bem. Acho que não fui capaz de entender o que queria.'

    feedback = f'{feedback_msg}{feedback_txt}'

    return feedback


def check_entity_inputs(intent):
    db_category_table = []   # lista de nomes de categorias
    db_devices_table  = []   # lista de nomes de dispositivos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Obtem a lista de hostnames dos dispositivos
    cursor.execute("SELECT hostname from devices where hostname != '';")
    hostnames_tuple = cursor.fetchall()
    for hostname in hostnames_tuple:
        db_devices_table.append(hostname[0])

    # Obtem a lista de nomes de categorias
    cursor.execute("SELECT name from categories WHERE name !='todos dispositivos';")
    categorys_name_tuple = cursor.fetchall()
     
    for category_name in categorys_name_tuple:
        db_category_table.append(category_name[0])
    
    conn.commit()
    cursor.close()
    conn.close()

    try:
        user_feedback = intent['feedback']
        if user_feedback == "":
            user_feedback = False
    except:
        user_feedback = False
    
    
    if intent['acao'] == "bloquear" or intent['acao'] == "liberar":
        try:
            check_feedback = check_inputs_from_block_intent(intent['acao'], intent['alvo'], intent['servico'], user_feedback, db_devices_table, db_category_table)
        except:
            print(f"Erro ao tentar executar a checagem no intent {intent['acao']}. Todas as entidades necessárias estão no dialogflow?")
            check_feedback = f"Erro ao tentar mapear uma ou mais entidades na intent {intent['acao']}"

    if intent['acao'] == "listar":
        try:
            check_feedback = check_inputs_from_list_intent(intent['acao'], intent['listar_opcoes'], intent['categoria'], intent['estado'] , user_feedback)
        except:
            print(f"Erro ao tentar mapear uma ou mais entidades no intent {intent['acao']}. Todas as entidades necessárias estão no dialogflow?")
            check_feedback = f"Erro ao tentar mapear uma ou mais entidades na intent {intent['acao']}"
    if intent['acao'] == 'renomear':
        try:
            check_feedback = check_inputs_from_rename_intent(intent['acao'], intent['host'], intent['any'], user_feedback)
        except:
            check_feedback = f"Erro ao tentar mapear uma ou mais entidades na intent {intent['acao']}"
            
    if intent['acao'] == 'reclassificar' or intent['acao'] == 'limitar':
        check_feedback = f"unable: A intenção {intent['acao']} não está implementada no protótipo"
    
    return check_feedback

def get_interface_wan():
    # comandoviassh = "ip route | grep default"
    output = "default via 192.168.3.1 dev eth0"
    parts = output.split()
    if len(parts) >= 2:
        interface_name = parts[-1]
        return interface_name
    else:
        return False

def translate(intent):
    hostnames = []
    ips = []
    categories = []
    device_status = []

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
  
    if intent['action'] == "bloquear" or intent['action'] == "liberar" :
        print(f"\nAlvo final identificado: {intent['target']}")
        if not intent['service']:
           intent['service'] = "internet"

        if intent['target'] == "todos dispositivos":
            where = ''
        else:
            where = f" WHERE hostname ='{intent['target']}'"      
    
        sql_consulta = f"SELECT hostname, ip FROM devices{where};"
        cursor.execute(sql_consulta)
        database_devices = cursor.fetchall()

        if not database_devices:
            # intent_alvo = remove_plural(intent_alvo)
            sql_consulta = f"SELECT devices.hostname, devices.ip \
            FROM devices INNER JOIN categories ON devices.category_id = categories.id \
            WHERE categories.name ='{intent['target']}';"
            cursor.execute(sql_consulta)
            database_devices = cursor.fetchall()

        for device_info in database_devices:
            hostnames.append(device_info[0]) # criando uma lista de ips
            ips.append(device_info[1]) # criando uma lista de ips


        cursor = conn.cursor()
        cursor.execute("SELECT name, direction, udp_ports, tcp_ports from services where name = '%s'" %intent['service'])
        service_result = cursor.fetchall()
        service = {
            "name": service_result[0][0],
            "direction": service_result[0][1],
            "udp_ports": service_result[0][2],
            "tcp_ports": service_result[0][3],
        }
    
        translate = {           # Devolvendo em Representação Intermediaia (RI)
            'intent': intent['action'],
            'category': intent['target'],
            'hostname': hostnames,
            'ip': ips,
            'service': service
        }
    elif intent['action'] == "listar":
        print(f"\nCategoria identificada: {intent['category']}")
        if intent['list_option'] == 'dispositivos':
            if intent['category'] == "todos dispositivos":
                sql_consulta = f"SELECT devices.hostname, devices.ip, categories.name, devices.is_enabled \
                FROM devices INNER JOIN categories ON devices.category_id = categories.id;"
                cursor.execute(sql_consulta)
                database_devices = cursor.fetchall()
            else: # Condição de o usuário definiu qual categoria deseja listar
                sql_consulta = f"SELECT devices.hostname, devices.ip, categories.name, devices.is_enabled \
                FROM devices INNER JOIN categories ON devices.category_id = categories.id \
                WHERE categories.name LIKE '%{intent['category']}%';"
                cursor.execute(sql_consulta)
                database_devices = cursor.fetchall()
            
            for device_info in database_devices:
                hostnames.append(device_info[0])  # criando uma lista de hostnames
                ips.append(device_info[1])        # criando uma lista de ips
                categories.append(device_info[2]) # criando uma lista de categorias
                device_status.append(device_info[3]) # criando uma lista de status de dispositivos

            translate = {              # Devolvendo em Representação Intermediaia (RI)
                'intent': intent['action'],
                'list_option': intent['list_option'],
                'chosen_category': intent['category'],
                'hostname': hostnames,
                'ip': ips,
                'category': categories,
                'status': device_status
            }
    elif intent['action'] == "renomear":
        hostname = False
        ip = False
        
        ipv4_regex = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        found_ipv4 = re.findall(ipv4_regex, intent['host'])
        if found_ipv4:
            ip = intent['host']
        else:
            hostname = intent['host']     
        translate = {              # Devolvendo em Representação Intermediaia (RI)
            'intent': intent['action'],
            'host': hostname,
            'ip': ip,
            'newname': intent['newname']
        }

    else:
        #demais intenções
        translate = {}
                      
    conn.commit()
    cursor.close()
    conn.close()

    # retorna as instruções a serem executadas
    return translate

def status_txt(status):
    if status == True:
        return 'ligado'
    else:
        return 'desligado'

def sql_execution(translated_intent):
    query_list = []
    print(translated_intent)
   
    if translated_intent['intent'] == 'listar':
        if translated_intent['list_option'] == 'dispositivos': # Execução de instrução
            for hostname, ip, category, status in zip(translated_intent['hostname'], translated_intent['ip'], translated_intent['category'], translated_intent['status']):
                if hostname != "":
                    if translated_intent['chosen_category'] != 'todos dispositivos':
                        string = f"{hostname} com IP {ip}."
                        query_list.append(string)
                    else:
                        string = f"{hostname} do tipo {category}."
                        query_list.append(string)
        return ('\n'.join(query_list))
    elif translated_intent['intent'] == 'renomear':
        rename_feedback = []
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        if translated_intent['host']:
            where = f"WHERE hostname = '{translated_intent['host']}'"
        else:
            where = f"WHERE ip = '{translated_intent['ip']}'"

        sql_update = f"UPDATE devices SET hostname = '{translated_intent['newname']}' {where};"
        try:
            cursor.execute(sql_update)
            num_rows_updated = cursor.rowcount
            print(f"numero de linhas afetadas: {num_rows_updated}")
            if num_rows_updated > 0:
                msg = f"A mudança de nome foi realizada com sucesso. {cursor.rowcount} dispositivo foi atualizado"
                print(msg)
                rename_feedback = ['(sucess): ', msg]
            else:
                msg = f"A mudança de nome não foi realizada. Nenhum dispositivo foi atualizado"
                print(msg)
                rename_feedback = ['(unable): ', msg]
        except psycopg2.Error as e:
            print("Ocorreu um erro durante a atualização:", e)
            msg = f"A mudança de nome não foi realizada. {e}"
            rename_feedback = ['(unable): ', msg]
        
        conn.commit()
        cursor.close()
        conn.close()

        return rename_feedback
    

def router_intructions(translated_intent):
    instructions = []
    wan_interface = get_interface_wan()
    
    service_direction = translated_intent["service"]["direction"]
    udp_ports = translated_intent["service"]["udp_ports"]
    tcp_ports = translated_intent["service"]["tcp_ports"]

    if translated_intent["intent"] == "bloquear":
        if service_direction == "output":           # Conexões de saida
            for ip in translated_intent["ip"]:
                if tcp_ports is not None:
                    iptables_instruction = f"iptables -I FORWARD -s {ip} -p tcp -m multiport --dports {tcp_ports} -j DROP"
                    instructions.append(iptables_instruction)
                if udp_ports is not None:
                    iptables_instruction = f"iptables -I FORWARD -s {ip} -p udp -m multiport --dports {udp_ports} -j DROP"
                    instructions.append(iptables_instruction)
        else:                                       # Conexões de entrada
            for ip in translated_intent["ip"]:
                if tcp_ports is not None:
                    tcp_ports_list = tcp_ports.split(',')  # Converte para lista usando ',' como separador
                    for port in tcp_ports_list:
                        iptables_instruction = f"iptables -t nat -D PREROUTING -i {wan_interface} -p tcp --dport {port} -j DNAT --to-destination {ip}:{port}"
                        instructions.append(iptables_instruction)
                if udp_ports is not None:
                    udp_ports_list = udp_ports.split(',')  # Converte para lista usando ',' como separador
                    for port in udp_ports_list:
                        iptables_instruction = f"iptables -t nat -D PREROUTING -i {wan_interface} -p tcp --dport {port} -j DNAT --to-destination {ip}:{port}"
                        instructions.append(iptables_instruction)
    elif translated_intent["intent"] == "liberar":
        if service_direction == "output":           # Conexões de saida
            for ip in translated_intent["ip"]:
                if tcp_ports is not None:
                    iptables_instruction = f"iptables -D FORWARD -s {ip} -p tcp -m multiport --dports {tcp_ports} -j DROP"
                    instructions.append(iptables_instruction)
                if udp_ports is not None:
                    iptables_instruction = f"iptables -D FORWARD -s {ip} -p udp -m multiport --dports {udp_ports} -j DROP"
                    instructions.append(iptables_instruction)
        else:                                       # Conexões de entrada
            for ip in translated_intent["ip"]:
                if tcp_ports is not None:
                    tcp_ports_list = tcp_ports.split(',')  # Converte para lista usando ',' como separador
                    for port in tcp_ports_list:
                        iptables_instruction = f"iptables -t nat -A PREROUTING -i {wan_interface} -p tcp --dport {port} -j DNAT --to-destination {ip}:{port}"
                        instructions.append(iptables_instruction)
                if udp_ports is not None:
                    udp_ports_list = udp_ports.split(',')  # Converte para lista usando ',' como separador
                    for port in udp_ports_list:
                        iptables_instruction = f"iptables -t nat -A PREROUTING -i {wan_interface} -p tcp --dport {port} -j DNAT --to-destination {ip}:{port}"
                        instructions.append(iptables_instruction)
    else:
        pass # condições para alterar velocidade (qos, etc)
    return instructions     

def set_router_instructions(router, translated_intent, instructions):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    msg = []
    #print(instructions)
    print(f"Há {len(instructions)} comandos para executar no roteador para {translated_intent['intent']} {len(translated_intent['ip'])} dispositivos. Conectando ao roteador...")

    msg.append(f"Há {len(instructions)} comandos para executar no roteador para {translated_intent['intent']} {len(translated_intent['ip'])} dispositivos. Conectando ao roteador...")

    try:
        ssh.connect(router['gateway'], username=router['username'], password=router['password'], timeout=2)
        print("Conexão SSH bem-sucedida!")

        for instruction in instructions:
            stdin, stdout, stderr = ssh.exec_command(instruction)
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            text = f"Executando instrução '{instruction}' "
            
            if not stderr_str:
                msg.append(f"{text} || Executado.{stdout_str}")
                print(f"{text} {verde}Executado.{stdout_str}{endverde}")
            else:
                msg.append(f"{text} // Erro: {stderr_str}")
                print(f"{text} Erro: {stderr_str}")
        ssh.close()
    except paramiko.AuthenticationException:
        msg.append("(unable): Falha na autenticação. Verificar as credenciais do roteador")
    except paramiko.SSHException as e:
        msg.append(f"(unable): Erro na conexão SSH: {str(e)}")
    except Exception as e:
        msg.append(f"(unable): Erro inesperado: {str(e)}")
    return ('\n'.join(msg))



