import os
import requests
import mysql.connector
import logging
from mysql.connector import errorcode
from dotenv import load_dotenv

# === Configuração de ambiente e logs ===
load_dotenv()

logging.basicConfig(
    filename='logs/apontamentos.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

API_URL_APONTAMENTOS = os.getenv("API_URL_APONTAMENTOS")
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
CREATE TABLE IF NOT EXISTS apontamentos (
    requestUUID VARCHAR(100) PRIMARY KEY,
    apontamentoKey INT,
    ticketKey INT,
    organizacaoDoTicketKey INT,
    organizacaoDoTicketNome VARCHAR(255),
    usuarioKey INT,
    usuarioNomeAbreviado VARCHAR(255),
    descricao TEXT,
    dataDeCriacao VARCHAR(50),
    dataDeAlteracao VARCHAR(50),
    dataDoLancamentoFormatada VARCHAR(50),
    dataDoLancamento VARCHAR(50),
    horaDoLancamento VARCHAR(20),
    quantidade DECIMAL(10,2),
    quantidadeFormatada VARCHAR(20),
    valorPorQuantidade DECIMAL(10,2),
    bonificado BOOLEAN,
    tipoDeApontamentoKey INT,
    permiteEditarApontamentosDeOutrosUsuarios BOOLEAN,
    valorTotal DECIMAL(10,2),
    valorCredito DECIMAL(10,2),
    ativo BOOLEAN,
    moderado BOOLEAN,
    kanbanStatusDescricaoAtuacao VARCHAR(255),
    excedeuTempoEstimado BOOLEAN,
    semSaldoTempoEstimado BOOLEAN,
    link_href TEXT
);
"""

INSERT_SQL = """
REPLACE INTO apontamentos (
    requestUUID, apontamentoKey, ticketKey, organizacaoDoTicketKey, organizacaoDoTicketNome,
    usuarioKey, usuarioNomeAbreviado, descricao, dataDeCriacao, dataDeAlteracao,
    dataDoLancamentoFormatada, dataDoLancamento, horaDoLancamento, quantidade,
    quantidadeFormatada, valorPorQuantidade, bonificado, tipoDeApontamentoKey,
    permiteEditarApontamentosDeOutrosUsuarios, valorTotal, valorCredito,
    ativo, moderado, kanbanStatusDescricaoAtuacao, excedeuTempoEstimado,
    semSaldoTempoEstimado, link_href
)
VALUES (
    %(requestUUID)s, %(apontamentoKey)s, %(ticketKey)s, %(organizacaoDoTicketKey)s, %(organizacaoDoTicketNome)s,
    %(usuarioKey)s, %(usuarioNomeAbreviado)s, %(descricao)s, %(dataDeCriacao)s, %(dataDeAlteracao)s,
    %(dataDoLancamentoFormatada)s, %(dataDoLancamento)s, %(horaDoLancamento)s, %(quantidade)s,
    %(quantidadeFormatada)s, %(valorPorQuantidade)s, %(bonificado)s, %(tipoDeApontamentoKey)s,
    %(permiteEditarApontamentosDeOutrosUsuarios)s, %(valorTotal)s, %(valorCredito)s,
    %(ativo)s, %(moderado)s, %(kanbanStatusDescricaoAtuacao)s, %(excedeuTempoEstimado)s,
    %(semSaldoTempoEstimado)s, %(link_href)s
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
    resultados_por_pagina = '50'
    data_inicial = '01/04/2025'
    headers = {"Content-Type": "application/json"}
    auth = (API_EMAIL, API_TOKEN)

    while True:
        params = {"pagina": current_page, "resultadosPorPagina": resultados_por_pagina, "dataInicial": data_inicial}
        response = requests.get(API_URL_APONTAMENTOS, auth=auth, headers=headers, params=params)

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
            tickets = data.get("content", [])
        else:
            logging.warning(f"Formato de resposta inesperado na página {current_page}")
            break

        if not tickets:
            logging.info(f"Nenhum apontamento encontrado na página {current_page}. Encerrando.")
            break

        all_tickets.extend(tickets)
        logging.info(f"Página {current_page} processada com {len(tickets)} apontamentos.")

        # Controle de paginação
        if limit_pages and current_page >= limit_pages:
            break

        # Caso a API não tenha metadado de próxima página, apenas itera até a próxima página manualmente
        current_page += 1

    return all_tickets

def insert_tickets(conn, tickets):
    cursor = conn.cursor()

    for t in tickets:
        # Alguns apontamentos podem nao ter 'links' ou 'href'
        link_href = None
        if isinstance(t.get("links"), list) and len(t["links"]) > 0:
            link_href = t["links"][0].get("href")

        ticket_data = {
            "requestUUID": t.get("requestUUID"),
            "apontamentoKey": t.get("apontamentoKey"),
            "ticketKey": t.get("ticketKey"),
            "organizacaoDoTicketKey": t.get("organizacaoDoTicketKey"),
            "organizacaoDoTicketNome": t.get("organizacaoDoTicketNome"),
            "usuarioKey": t.get("usuarioKey"),
            "usuarioNomeAbreviado": t.get("usuarioNomeAbreviado"),
            "descricao": t.get("descricao"),
            "dataDeCriacao": t.get("dataDeCriacao"),
            "dataDeAlteracao": t.get("dataDeAlteracao"),
            "dataDoLancamentoFormatada": t.get("dataDoLancamentoFormatada"),
            "dataDoLancamento": t.get("dataDoLancamento"),
            "horaDoLancamento": t.get("horaDoLancamento"),
            "quantidade": t.get("quantidade"),
            "quantidadeFormatada": t.get("quantidadeFormatada"),
            "valorPorQuantidade": t.get("valorPorQuantidade"),
            "bonificado": t.get("bonificado"),
            "tipoDeApontamentoKey": t.get("tipoDeApontamentoKey"),
            "permiteEditarApontamentosDeOutrosUsuarios": t.get("permiteEditarApontamentosDeOutrosUsuarios"),
            "valorTotal": t.get("valorTotal"),
            "valorCredito": t.get("valorCredito"),
            "ativo": t.get("ativo"),
            "moderado": t.get("moderado"),
            "kanbanStatusDescricaoAtuacao": t.get("kanbanStatusDescricaoAtuacao"),
            "excedeuTempoEstimado": t.get("excedeuTempoEstimado"),
            "semSaldoTempoEstimado": t.get("semSaldoTempoEstimado"),
            "link_href": link_href
        }

        try:
            cursor.execute(INSERT_SQL, ticket_data)
        except mysql.connector.Error as err:
            logging.error(f"Erro ao inserir ticket: {err}")

    conn.commit()
    cursor.close()
    logging.info(f"{len(tickets)} apontamentos inseridos/atualizados no banco.")

def main(limit_pages=None):
    logging.info("=== Iniciando sincronização com API Acelerato ===")
    conn = connect_db()
    ensure_table_exists(conn)

    tickets = fetch_tickets(limit_pages=limit_pages)
    if tickets:
        conn.ping(reconnect=True, attempts=3, delay=2)
        insert_tickets(conn, tickets)
    else:
        logging.warning("Nenhum apontamento encontrado para sincronizar.")

    conn.close()
    logging.info("=== Sincronização concluída ===")

if __name__ == "__main__":
    # limite de páginas para testes
    main(limit_pages=500)