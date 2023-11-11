## Arquitetura de suporte à configuração de redes de computadores baseada em  linguagem natural e descoberta de dispositivos


### Recursos da prova de conceito: 

Este repositório disponibiliza o código fonte do protótipo utilizado como prova de conceito da arquitetura e da interface de comunicação e tradução **MAJU-NC** (*Management Assistance with Json Usage for Network Configuration*).

#### 🎥 Vídeo de demostração: [▶️Abrir demostração em vídeo](https://www.youtube.com/watch?v=3OuJ5BpLvpg)

As seguintes camadas estão implementadas no protótipo, entre parênteses estão presentes as tecnologias ou métodos utilizados como facilitadores:

 - Interface com usuário (MAJU-NC / Dialogflow)
 - Conversão (Dialogflow UI)
 - Tradução (Dialogflow UI / Componente Tradutor [MAJU-NC])
 - Identificação (Componente Sniffer DHCP / Componente Sniffer SSDP / Componente ICMP / Crockroach DB)
 - Classificação (Fingerbank API)
	 - Alinhamento entre a identificação de dispositivos e interface com o usuário (Crockroach DB, Dialogflow API)
 - Interface com rede gerenciável (Paramiko [SSH])
 - Rede gerenciada (DD-WRT)
---
### Orientações:

- *Backend*: Estará ativo ao executar `run.py`. É necessário verificar requisitos de bibliotecas ao executar.
- *Database*: É requerido um banco de dados compatível com psycopg2. Foi utilizado [Crockroach
   DB](https://cockroachlabs.cloud/) em nuvem. O esquema de tabelas do banco pode ser encontrado em `poc/database`.
- *Componentes Sniffer SSDP/ICMP*: Poderá rodar no Windows e Linux.
- *Componente Sniffer DHCP*: Só irá rodar no Linux, sudo é necessário.  
- *Componente Classificador*:
   - Para importar a biblioteca *netifaces* no Windows é necessário instalar o Microsoft C++ Build Tools.
   - Fingerbank: Necessário gerar uma chave API no [Fingerbank](https://www.fingerbank.org)
   - Google API: Necessário criar uma conta de serviço no IAM admin do Google Cloud e registrar uma credencial JSON. [Pode seguir essas etapas](https://support.woztell.com/portal/en/kb/articles/how-to-get-the-json-key-file-from-dialogflow)