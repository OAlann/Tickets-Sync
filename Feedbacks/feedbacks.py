import os
import requests
import mysql.connector
import logging
from mysql.connector import errorcode
from dotenv import load_dotenv

# === Configuração de ambiente e logs ===
load_dotenv()

logging.basicConfig(
    filename='logs/feedbacks.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

API_URL_FEEDBACKS = os.getenv("API_URL_FEEDBACKS")
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
CREATE TABLE IF NOT EXISTS feedbacks (
    ticketId INT PRIMARY KEY,
    pesquisaId INT,
    pesquisaNome VARCHAR(255),
    dataDeProntoTicket VARCHAR(50),
    agenteId VARCHAR(50),
    agenteNome VARCHAR(255),
    comentarios TEXT,
    avaliacaoMedia DECIMAL(5,2),
    status VARCHAR(50),
    pergunta TEXT,
    nota DECIMAL(5,2),
    usuarioAvaliacaoId INT,
    usuarioAvaliacaoNome VARCHAR(255),
    dataDeAvaliacao VARCHAR(50),
    statusPergunta VARCHAR(50)
);
"""

INSERT_SQL = """
REPLACE INTO feedbacks (
    ticketId, pesquisaId, pesquisaNome, dataDeProntoTicket, agenteId, agenteNome,
    comentarios, avaliacaoMedia, status, pergunta, nota, usuarioAvaliacaoId,
    usuarioAvaliacaoNome, dataDeAvaliacao, statusPergunta
)
VALUES (
    %(ticketId)s, %(pesquisaId)s, %(pesquisaNome)s, %(dataDeProntoTicket)s, %(agenteId)s, %(agenteNome)s,
    %(comentarios)s, %(avaliacaoMedia)s, %(status)s, %(pergunta)s, %(nota)s, %(usuarioAvaliacaoId)s,
    %(usuarioAvaliacaoNome)s, %(dataDeAvaliacao)s, %(statusPergunta)s
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
        response = requests.get(API_URL_FEEDBACKS, auth=auth, headers=headers, params=params)

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
        pergunta = None
        nota = None
        usuarioAvaliacaoId = None
        usuarioAvaliacaoNome = None
        dataDeAvaliacao = None
        statusPergunta = None

        # Caso o JSON tenha perguntas, pegamos a primeira
        if isinstance(t.get("perguntas"), list) and len(t["perguntas"]) > 0:
            p = t["perguntas"][0]
            pergunta = p.get("pergunta")
            nota = p.get("nota")
            usuarioAvaliacaoId = p.get("usuarioAvaliacaoId")
            usuarioAvaliacaoNome = p.get("usuarioAvaliacaoNome")
            dataDeAvaliacao = p.get("dataDeAvaliacao")
            statusPergunta = p.get("status")

        ticket_data = {
            "ticketId": t.get("ticketId"),
            "pesquisaId": t.get("pesquisaId"),
            "pesquisaNome": t.get("pesquisaNome"),
            "dataDeProntoTicket": t.get("dataDeProntoTicket"),
            "agenteId": t.get("agenteId"),
            "agenteNome": t.get("agenteNome"),
            "comentarios": t.get("comentarios"),
            "avaliacaoMedia": t.get("avaliacaoMedia"),
            "status": t.get("status"),
            "pergunta": pergunta,
            "nota": nota,
            "usuarioAvaliacaoId": usuarioAvaliacaoId,
            "usuarioAvaliacaoNome": usuarioAvaliacaoNome,
            "dataDeAvaliacao": dataDeAvaliacao,
            "statusPergunta": statusPergunta
        }

        try:
            cursor.execute(INSERT_SQL, ticket_data)
        except mysql.connector.Error as err:
            logging.error(f"Erro ao inserir avaliação do ticket {t.get('ticketId')}: {err}")

    conn.commit()
    cursor.close()
    logging.info(f"{len(tickets)} avaliações inseridas/atualizadas no banco.")

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
    main(limit_pages=30)