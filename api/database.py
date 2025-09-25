import psycopg2
import os

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def inserir_novo_funcionario(nome, departamento, cargo):
    sql = """INSERT INTO funcionarios (nome_completo, departamento, cargo, status) 
             VALUES (%s, %s, %s, 'Inativo') RETURNING id;"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (nome, departamento, cargo))
            novo_id = cur.fetchone()[0]
            conn.commit()
            return novo_id
    finally:
        conn.close()

def atualizar_status_funcionario(id_funcionario, novo_status):
    """Atualiza o status de um funcionário (Ativo/Inativo)."""
    sql = "UPDATE funcionarios SET status = %s WHERE id = %s;"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (novo_status, id_funcionario))
            conn.commit()
    finally:
        conn.close()

def buscar_estatisticas():
    stats = {}
    sql_total = "SELECT COUNT(*) FROM funcionarios;"
    sql_ativos = "SELECT COUNT(*) FROM funcionarios WHERE status = 'Ativo';"
    sql_inativos = "SELECT COUNT(*) FROM funcionarios WHERE status = 'Inativo';"
    sql_deptos = "SELECT COUNT(DISTINCT departamento) FROM funcionarios;"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_total)
            stats['total'] = cur.fetchone()[0]
            cur.execute(sql_ativos)
            stats['ativos'] = cur.fetchone()[0]
            cur.execute(sql_inativos)
            stats['inativos'] = cur.fetchone()[0]
            cur.execute(sql_deptos)
            stats['departamentos'] = cur.fetchone()[0]
    finally:
        conn.close()
    return stats

def associar_face_id(id_funcionario, rekognition_face_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE funcionarios SET rekognition_face_id = %s WHERE id = %s", (rekognition_face_id, id_funcionario))
    print(f"FaceID associado ao funcionário ID: {id_funcionario}.")

def buscar_todos_funcionarios():
    sql = "SELECT id, nome_completo, departamento, cargo, status, to_char(criado_em, 'DD/MM/YYYY') as data_admissao FROM funcionarios ORDER BY nome_completo;"
    funcionarios = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            for row in cur.fetchall():
                funcionarios.append({"id": row[0], "nome": row[1], "departamento": row[2], "cargo": row[3], "status": row[4], "admissao": row[5]})
    return funcionarios

def buscar_dados_funcionario(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nome_completo, rekognition_face_id FROM funcionarios WHERE id = %s", (id_funcionario,))
            return cur.fetchone()

def remover_funcionario_por_id(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM funcionarios WHERE id = %s", (id_funcionario,))
    print(f"Funcionário ID {id_funcionario} removido do banco de dados com sucesso.")

def buscar_nome_funcionario_por_id(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nome_completo FROM funcionarios WHERE id = %s", (id_funcionario,))
            resultado = cur.fetchone()
            return resultado[0] if resultado else None


def contar_eventos_do_dia(id_funcionario, data_evento):
    sql = "SELECT COUNT(id) FROM eventos_ponto WHERE id_funcionario = %s AND (timestamp_evento AT TIME ZONE 'America/Sao_Paulo')::date = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_funcionario, data_evento))
            return cur.fetchone()[0]

def inserir_evento_ponto(id_funcionario, timestamp_evento, tipo_evento, dispositivo_id="Terminal-01"):
    sql = "INSERT INTO eventos_ponto (id_funcionario, timestamp_evento, tipo_evento, dispositivo_id) VALUES (%s, %s, %s, %s) RETURNING id;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_funcionario, timestamp_evento, tipo_evento, dispositivo_id))
            return cur.fetchone()[0]

def criar_periodo_de_trabalho(id_funcionario, data_referencia, evento_entrada_id):
    sql = "INSERT INTO periodos_trabalhados (id_funcionario, data_referencia, evento_entrada_id, status) VALUES (%s, %s, %s, 'ABERTO');"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_funcionario, data_referencia, evento_entrada_id))
    print(f"Período de trabalho aberto para o funcionário {id_funcionario}.")

def buscar_periodo_aberto(id_funcionario, data_referencia):
    sql = "SELECT pt.id, ep.timestamp_evento FROM periodos_trabalhados pt JOIN eventos_ponto ep ON pt.evento_entrada_id = ep.id WHERE pt.id_funcionario = %s AND pt.data_referencia = %s AND pt.status = 'ABERTO' ORDER BY ep.timestamp_evento DESC LIMIT 1;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_funcionario, data_referencia))
            return cur.fetchone()

def fechar_periodo_de_trabalho(periodo_id, evento_saida_id, duracao_minutos):
    sql = "UPDATE periodos_trabalhados SET evento_saida_id = %s, duracao_minutos = %s, status = 'FECHADO' WHERE id = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (evento_saida_id, duracao_minutos, periodo_id))
    print(f"Período de trabalho ID {periodo_id} fechado. Duração: {duracao_minutos} minutos.")