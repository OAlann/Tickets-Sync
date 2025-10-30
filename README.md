# Projeto de Extração e Integração de Dados Acelerato para BI

Este projeto consiste em um conjunto de scripts Python desenvolvidos para extrair dados da API do Acelerato Tickets e integrá-los a um banco de dados MySQL, facilitando a análise e o tratamento em ferramentas de Business Intelligence (BI).

## Componentes do Projeto

O projeto é composto por três scripts principais, cada um responsável pela sincronização de um tipo específico de dado:

| Script | Descrição da Extração | Tabela no Banco de Dados | Chave Primária |
| :--- | :--- | :--- | :--- |
| `chamados.py` | Extrai dados de **Chamados** (Tickets) do Acelerato. | `chamados` | `ticketKey` |
| `apontamentos.py` | Extrai dados de **Apontamentos de Tempo** (Time Tracking) associados aos tickets. | `apontamentos` | `requestUUID` |
| `feedbacks.py` | Extrai dados de **Feedbacks/Avaliações** de tickets. | `feedbacks` | `ticketId` |

## Pré-requisitos

Para executar os scripts, você precisará ter instalado:

1.  **Python 3.x**
2.  **MySQL ou MariaDB** (servidor de banco de dados)

### Dependências Python

As seguintes bibliotecas Python são necessárias e podem ser instaladas via `pip`:

```bash
pip install requests mysql-connector-python python-dotenv
```

## Configuração do Ambiente

Os scripts utilizam variáveis de ambiente para gerenciar credenciais de API e de banco de dados de forma segura.

Crie um arquivo chamado `.env` na raiz do projeto com as seguintes variáveis:

```ini
# --- Configurações da API Acelerato ---
# Seu e-mail de acesso ao Acelerato
API_EMAIL="seu_email@dominio.com"
# Seu token de acesso à API Acelerato
API_TOKEN="seu_token_api"

# URLs específicas para cada endpoint
API_URL_TICKETS="https://{seu_dominio}.acelerato.com/api/v1/tickets"
API_URL_APONTAMENTOS="https://{seu_dominio}.acelerato.com/api/v1/apontamentos"
API_URL_FEEDBACKS="https://{seu_dominio}.acelerato.com/api/v1/feedbacks"

# --- Configurações do Banco de Dados MySQL ---
DB_HOST="localhost"
DB_USER="seu_usuario_mysql"
DB_PASSWORD="sua_senha_mysql"
DB_NAME="nome_do_banco_de_dados"
```

**Atenção**: Substitua os valores entre chaves `{}` e os exemplos (`seu_email@dominio.com`, `seu_token_api`, etc.) pelas suas credenciais reais.

## Estrutura de Logs

Os scripts estão configurados para salvar logs de execução individuais em um diretório dedicado.

Crie o diretório `logs` na raiz do projeto:

```bash
mkdir logs
```

Os logs serão gerados automaticamente com os seguintes nomes:

*   **`apontamentos.log`**: Logs de execução do `apontamentos.py`.
*   **`chamados.log`**: Logs de execução do `chamados.py`.
*   **`feedbacks.log`**: Logs de execução do `feedbacks.py`.

## Execução dos Scripts

Para sincronizar os dados, execute cada script Python individualmente:

```bash
# Sincroniza os Chamados (Tickets)
python chamados.py

# Sincroniza os Apontamentos de Tempo
python apontamentos.py

# Sincroniza os Feedbacks/Avaliações
python feedbacks.py
```

**Nota sobre Paginação**: Os scripts implementam um loop de paginação para buscar todos os dados disponíveis na API, a partir de uma data mínima definida internamente (`dataDeCriacaoMinima` ou `dataInicial`). Por padrão, eles buscam até 500 páginas (limit_pages=500) para evitar loops infinitos em caso de erro na API, mas você pode ajustar isso no bloco `if __name__ == "__main__":` de cada script.

## Detalhes Técnicos e Estrutura das Tabelas

Cada script garante que sua tabela correspondente seja criada no banco de dados, caso ainda não exista. A inserção de dados utiliza a instrução `REPLACE INTO`, o que significa que se um registro com a mesma chave primária já existir, ele será **atualizado** com os novos dados da API.

### 1. Tabela `chamados` (Script `chamados.py`)

Armazena os dados principais dos tickets.

| Coluna | Tipo MySQL | Descrição |
| :--- | :--- | :--- |
| `ticketKey` | `INT` | **Chave Primária**. Identificador único do chamado. |
| `titulo` | `VARCHAR(255)` | Título do chamado. |
| `kanbanStatusdescricao` | `VARCHAR(100)` | Status atual do chamado no Kanban. |
| `organizacaonome` | `VARCHAR(150)` | Nome da Organização/Cliente. |
| `agenteNome` | `VARCHAR(150)` | Nome do Agente (Atendente) responsável. |
| `dataDeCriacao` | `DATETIME` | Data e hora de criação do chamado. |
| `dataDaUltimaAlteracao` | `DATETIME` | Data e hora da última alteração. |
| `url` | `VARCHAR(300)` | URL direta para o chamado no Acelerato. |
| *Outras Colunas* | *Diversos* | Inclui chaves de relacionamento (`kanbanStatusKey`, `organizacaoKey`, etc.) e flags booleanas (`arquivado`, `lixeira`, etc.). |

### 2. Tabela `apontamentos` (Script `apontamentos.py`)

Armazena os registros de tempo e atividades.

| Coluna | Tipo MySQL | Descrição |
| :--- | :--- | :--- |
| `requestUUID` | `VARCHAR(100)` | **Chave Primária**. Identificador único do apontamento. |
| `ticketKey` | `INT` | Chave estrangeira para a tabela `chamados`. |
| `usuarioNomeAbreviado` | `VARCHAR(255)` | Usuário que realizou o apontamento. |
| `descricao` | `TEXT` | Descrição da atividade realizada. |
| `dataDoLancamento` | `VARCHAR(50)` | Data do lançamento do apontamento. |
| `quantidade` | `DECIMAL(10,2)` | Quantidade de tempo apontada (em horas ou unidades). |
| `valorTotal` | `DECIMAL(10,2)` | Valor total (se aplicável). |
| *Outras Colunas* | *Diversos* | Inclui metadados como datas de criação/alteração, tipo de apontamento e status. |

### 3. Tabela `feedbacks` (Script `feedbacks.py`)

Armazena as avaliações de satisfação.

| Coluna | Tipo MySQL | Descrição |
| :--- | :--- | :--- |
| `ticketId` | `INT` | **Chave Primária**. Identificador do ticket avaliado. |
| `pesquisaNome` | `VARCHAR(255)` | Nome da pesquisa de satisfação. |
| `agenteNome` | `VARCHAR(255)` | Nome do Agente avaliado. |
| `comentarios` | `TEXT` | Comentários deixados pelo cliente. |
| `avaliacaoMedia` | `DECIMAL(5,2)` | Média geral da avaliação. |
| `nota` | `DECIMAL(5,2)` | Nota específica da primeira pergunta (se houver). |
| `usuarioAvaliacaoNome` | `VARCHAR(255)` | Nome do usuário que realizou a avaliação. |
| `dataDeAvaliacao` | `VARCHAR(50)` | Data da avaliação. |
| *Outras Colunas* | *Diversos* | Inclui IDs de pesquisa, status e a pergunta da pesquisa. |

## Estrutura de Código Comum

Todos os scripts seguem uma estrutura modular para facilitar a manutenção:

*   **`connect_db()`**: Estabelece a conexão com o MySQL.
*   **`ensure_table_exists(conn)`**: Executa o `CREATE TABLE IF NOT EXISTS`.
*   **`fetch_tickets(page=1, limit_pages=None)`**: Realiza as chamadas paginadas à API Acelerato, tratando a autenticação e a estrutura da resposta JSON.
*   **`insert_tickets(conn, tickets)`**: Itera sobre os dados extraídos e insere/atualiza os registros no banco de dados usando `REPLACE INTO`.
*   **`main(limit_pages=None)`**: Função principal que orquestra a conexão, a busca e a inserção.

Esta documentação fornece o ponto de partida para a utilização e integração dos dados do Acelerato com suas ferramentas de BI.
