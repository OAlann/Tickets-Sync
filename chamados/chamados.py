import os
import requests
import mysql.connector
import logging
from mysql.connector import errorcode
from dotenv import load_dotenv

# === Configuração de ambiente e logs ===
load_dotenv()

logging.basicConfig(
    filename='logs/chamados.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

API_URL_TICKETS = os.getenv("API_URL_TICKETS")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

# === Criação da tabela ===
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chamados (
    ticketKey INT PRIMARY KEY,
    titulo VARCHAR(255),
    arquivado BOOLEAN,
    lixeira BOOLEAN,
    suspenso BOOLEAN,
    impedido BOOLEAN,
    alvoDeSpam BOOLEAN,
    tempoDeVidaEmDias INT,
    tempoCiclicoEmDias INT,
    kanbanStatusKey INT,
    kanbanStatusdescricao VARCHAR(100),
    kanbanStatusinicio BOOLEAN,
    kanbanStatusfim BOOLEAN,
    kanbanStatusfila BOOLEAN,
    organizacaoKey INT,
    organizacaonome VARCHAR(150),
    organizacaoativo BOOLEAN,
    equipeDeAtendimentoequipeKey INT,
    equipeDeAtendimentonome VARCHAR(150),
    agenteUsuarioKey INT,
    agenteNome VARCHAR(150),
    agenteEmail VARCHAR(255),
    agenteUltimoAcessoEm DATETIME,
    categoriaKey INT,
    categoriadescricao VARCHAR(150),
    tipoDeTicketKey INT,
    tipoDeTicketDescricao VARCHAR(150),
    tipoDePrioridadeKey INT,
    tipoDePrioridadeDescricao VARCHAR(150),
    dataDeCriacao DATETIME,
    dataDaUltimaAlteracao DATETIME,
    reporterUsuarioKey INT,
    reporterNome VARCHAR(150),
    reporterEmail VARCHAR(255),
    origem VARCHAR(100),
    url VARCHAR(300)
);
"""

INSERT_SQL = """
REPLACE INTO chamados (
    ticketKey, titulo, arquivado, lixeira, suspenso, impedido, alvoDeSpam, tempoDeVidaEmDias, 
    tempoCiclicoEmDias, kanbanStatusKey, kanbanStatusdescricao, kanbanStatusinicio, kanbanStatusfim, kanbanStatusfila,
    organizacaoKey, organizacaonome, organizacaoativo, equipeDeAtendimentoequipeKey, equipeDeAtendimentonome, agenteUsuarioKey,
    agenteNome, agenteEmail, agenteUltimoAcessoEm, categoriaKey, categoriadescricao, tipoDeTicketKey, tipoDeTicketdescricao, 
    tipoDePrioridadeKey, tipoDePrioridadedescricao, dataDeCriacao, dataDaUltimaAlteracao, reporterUsuarioKey, reporterNome, 
    reporterEmail, origem, url
)
VALUES (
    %(ticketKey)s, %(titulo)s, %(arquivado)s, %(lixeira)s, %(suspenso)s, %(impedido)s, %(alvoDeSpam)s, %(tempoDeVidaEmDias)s, 
    %(tempoCiclicoEmDias)s, %(kanbanStatusKey)s, %(kanbanStatusdescricao)s, %(kanbanStatusinicio)s, %(kanbanStatusfim)s, %(kanbanStatusfila)s,
    %(organizacaoKey)s, %(organizacaonome)s, %(organizacaoativo)s, %(equipeDeAtendimentoequipeKey)s, %(equipeDeAtendimentonome)s, %(agenteUsuarioKey)s,
    %(agenteNome)s, %(agenteEmail)s, %(agenteUltimoAcessoEm)s, %(categoriaKey)s, %(categoriadescricao)s, %(tipoDeTicketKey)s, %(tipoDeTicketDescricao)s, 
    %(tipoDePrioridadeKey)s, %(tipoDePrioridadedescricao)s, %(dataDeCriacao)s, %(dataDaUltimaAlteracao)s, %(reporterUsuarioKey)s, %(reporterNome)s, 
    %(reporterEmail)s, %(origem)s, %(url)s
);
"""

def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Erro ao conectar ao banco: {err}")
        raise

def ensure_table_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
        cursor.close()
        logging.info("Tabela verificada/criada com sucesso.")
    except mysql.connector.Error as err:
        logging.error(f"Erro ao criar tabela: {err}")
        raise

def fetch_tickets(page=1, limit_pages=None):
    all_tickets = []
    current_page = page
    itens_por_pagina = '100'
    status_do_ticket = 'TODOS'
    data_de_criacao_minima = "02/04/2025"
    headers = {"Content-Type": "application/json"}
    auth = (API_EMAIL, API_TOKEN)

    while True:
        params = {"page": current_page, "size": itens_por_pagina, "status": status_do_ticket, "dataDeCriacaoMinima": data_de_criacao_minima}
        response = requests.get(API_URL_TICKETS, auth=auth, headers=headers, params=params)

        if response.status_code != 200:
            logging.error(f"Erro ao buscar página {current_page}: {response.status_code} - {response.text}")
            break

        try:
            data = response.json()
        except Exception as e:
            logging.error(f"Erro ao decodificar JSON da página {current_page}: {e}")
            break

        # Detecta se o retorno é lista ou dicionário
        if isinstance(data, list):
            tickets = data
        elif isinstance(data, dict):
            tickets = data.get("data", data)
        else:
            logging.warning(f"Formato de resposta inesperado na página {current_page}")
            break

        if not tickets:
            logging.info(f"Nenhum ticket encontrado na página {current_page}. Encerrando.")
            break

        all_tickets.extend(tickets)
        logging.info(f"Página {current_page} processada com {len(tickets)} tickets.")

        # Controle de paginação
        if limit_pages and current_page >= limit_pages:
            break

        # Caso a API não tenha metadado de próxima página, apenas itera até a próxima página manualmente
        current_page += 1

    return all_tickets

def insert_tickets(conn, tickets):
    cursor = conn.cursor()
    for t in tickets:
        ticket_data = {
            "ticketKey": t.get("ticketKey"),
            "titulo": t.get("titulo"),
            "arquivado": t.get("arquivado"),
            "lixeira": t.get("lixeira"),
            "suspenso": t.get("suspenso"),
            "impedido": t.get("impedido"),
            "alvoDeSpam": t.get("alvoDeSpam"),
            "tempoDeVidaEmDias": t.get("tempoDeVidaEmDias"),
            "tempoCiclicoEmDias": t.get("tempoCiclicoEmDias"),
            "kanbanStatusKey": (t.get("kanbanStatus") or {}).get("kanbanStatusKey"),
            "kanbanStatusdescricao": (t.get("kanbanStatus") or {}).get("descricao"),
            "kanbanStatusinicio": (t.get("kanbanStatus") or {}).get("inicio"),
            "kanbanStatusfim": (t.get("kanbanStatus") or {}).get("fim"),
            "kanbanStatusfila": (t.get("kanbanStatus") or {}).get("fila"),
            "organizacaoKey": (t.get("organizacao") or {}).get("organizacaoKey"),
            "organizacaonome": (t.get("organizacao") or {}).get("nome"),
            "organizacaoativo": (t.get("organizacao") or {}).get("ativo"),
            "equipeDeAtendimentoequipeKey": (t.get("equipeDeAtendimento") or {}).get("equipeKey"),
            "equipeDeAtendimentonome": (t.get("equipeDeAtendimento") or {}).get("nome"),
            "agenteUsuarioKey": (t.get("agente") or {}).get("usuarioKey"),
            "agenteNome": (t.get("agente") or {}).get("nome"),
            "agenteEmail": (t.get("agente") or {}).get("email"),
            "agenteUltimoAcessoEm": (t.get("agente") or {}).get("ultimoAcessoEm"),
            "categoriaKey": (t.get("categoria") or{}).get("categoriaKey"),
            "categoriadescricao": (t.get("categoria") or{}).get("descricao"),
            "tipoDeTicketKey": (t.get("tipoDeTicket") or{}).get("tipoDeTicketKey"),
            "tipoDeTicketDescricao": (t.get("tipoDeTicket") or{}).get("descricao"),
            "tipoDePrioridadeKey": (t.get("tipoDePrioridade") or {}).get("tipoDePrioridadeKey"),
            "tipoDePrioridadedescricao": (t.get("tipoDePrioridade") or {}).get("descricao"),
            "dataDeCriacao": t.get("dataDeCriacao"),
            "dataDaUltimaAlteracao": t.get("dataDaUltimaAlteracao"),
            "reporterUsuarioKey": (t.get("reporter") or {}).get("usuarioKey"),
            "reporterNome": (t.get("reporter") or {}).get("nome"),
            "reporterEmail": (t.get("reporter") or {}).get("email"),
            "origem": t.get("origem"),
            "url": t.get("url"),
        }
        # logging.info(f"Inserindo ticketKey={ticket_data['ticketKey']}")
        try:
            cursor.execute(INSERT_SQL, ticket_data)
        except mysql.connector.Error as err:
            logging.error(f"Erro ao inserir ticket {t.get('id')}: {err}")

    conn.commit()
    cursor.close()
    logging.info(f"{len(tickets)} tickets inseridos/atualizados no banco.")

def main(limit_pages=None):
    logging.info("=== Iniciando sincronização com API Acelerato ===")
    conn = connect_db()
    ensure_table_exists(conn)

    tickets = fetch_tickets(limit_pages=limit_pages)
    if tickets:
        conn.ping(reconnect=True, attempts=3, delay=2)
        insert_tickets(conn, tickets)
    else:
        logging.warning("Nenhum ticket encontrado para sincronizar.")

    conn.close()
    logging.info("=== Sincronização concluída ===")

if __name__ == "__main__":
    # limite de páginas para testes
    main(limit_pages=500)