from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import pytz
import database
import servicos_autenticacao
from cadastro_funcionarios import cadastrar_face_rekognition
from remover_funcionario import remover_face_rekognition

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/api/funcionarios", methods=["GET"])
def get_funcionarios():
    try:
        lista_funcionarios = database.buscar_todos_funcionarios()
        return jsonify(lista_funcionarios), 200
    except Exception as e:
        print(f"ERRO AO BUSCAR FUNCIONÁRIOS: {e}")
        return jsonify({"erro": "Erro interno ao buscar funcionários."}), 500


@app.route("/api/cadastrar", methods=["POST"])
def endpoint_cadastrar():
    nome = request.form.get("nome")
    departamento = request.form.get("departamento")
    cargo = request.form.get("cargo")

    if not all([nome, departamento, cargo, "imagem" in request.files]):
        return jsonify({"erro": "Dados incompletos"}), 400

    imagem = request.files["imagem"]
    nome_arquivo_temp = os.path.join(app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}.jpg")
    imagem.save(nome_arquivo_temp)

    try:
        novo_id = database.inserir_novo_funcionario(nome, departamento, cargo)
        face_id = cadastrar_face_rekognition(novo_id, nome_arquivo_temp)

        if face_id:
            database.associar_face_id(novo_id, face_id)
            os.remove(nome_arquivo_temp)
            return (
                jsonify(
                    {
                        "sucesso": True,
                        "mensagem": f"Funcionário {nome} cadastrado com sucesso!",
                        "id_gerado": novo_id,
                    }
                ),
                201,
            )
        else:
            os.remove(nome_arquivo_temp)
            return (
                jsonify(
                    {
                        "sucesso": False,
                        "mensagem": "Funcionário criado no banco, mas falha ao cadastrar face no Rekognition.",
                    }
                ),
                500,
            )
    except Exception as e:
        if os.path.exists(nome_arquivo_temp):
            os.remove(nome_arquivo_temp)
        return jsonify({"sucesso": False, "erro": f"Ocorreu um erro interno: {e}"}), 500


@app.route("/api/remover-funcionario/<int:id_funcionario>", methods=["DELETE"])
def endpoint_remover_funcionario(id_funcionario):
    try:
        dados_funcionario = database.buscar_dados_funcionario(id_funcionario)
        if not dados_funcionario:
            return (
                jsonify(
                    {
                        "sucesso": False,
                        "mensagem": f"Funcionário com ID {id_funcionario} não encontrado.",
                    }
                ),
                404,
            )

        nome_funcionario, face_id = dados_funcionario
        sucesso_aws = remover_face_rekognition(face_id)

        if not sucesso_aws and face_id:
            return (
                jsonify(
                    {
                        "sucesso": False,
                        "mensagem": f"Falha ao remover face do Rekognition.",
                    }
                ),
                500,
            )

        database.remover_funcionario_por_id(id_funcionario)
        return (
            jsonify(
                {
                    "sucesso": True,
                    "mensagem": f"Funcionário {nome_funcionario} (ID: {id_funcionario}) removido.",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"sucesso": False, "erro": f"Ocorreu um erro interno: {e}"}), 500


@app.route("/registrar-ponto", methods=["POST"])
def endpoint_registrar_ponto():
    if "imagem" not in request.files:
        return jsonify({"sucesso": False, "mensagem": "Nenhuma imagem enviada"}), 400

    imagem = request.files["imagem"]
    nome_arquivo_temp = os.path.join(app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}.jpg")
    imagem.save(nome_arquivo_temp)

    dados_autenticacao = servicos_autenticacao.autenticar_funcionario(nome_arquivo_temp)
    os.remove(nome_arquivo_temp)

    if not dados_autenticacao or not dados_autenticacao.get("sucesso"):
        mensagem_erro = dados_autenticacao.get("error", "Falha na autenticação.")
        return jsonify({"sucesso": False, "mensagem": mensagem_erro}), 401

    try:
        id_func = dados_autenticacao["id"]
        nome_func = dados_autenticacao["nome"]

        sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
        timestamp_atual = datetime.now(sao_paulo_tz)
        data_atual = timestamp_atual.date()

        contagem_eventos_dia = database.contar_eventos_do_dia(id_func, data_atual)
        tipo_evento = "ENTRADA" if contagem_eventos_dia % 2 == 0 else "SAIDA"
        novo_evento_id = database.inserir_evento_ponto(
            id_func, timestamp_atual, tipo_evento
        )

        mensagem_final = f"Ponto de '{tipo_evento}' registrado para {nome_func}."

        if tipo_evento == "ENTRADA":
            database.criar_periodo_de_trabalho(id_func, data_atual, novo_evento_id)
        elif tipo_evento == "SAIDA":
            periodo_aberto = database.buscar_periodo_aberto(id_func, data_atual)
            if periodo_aberto:
                periodo_id, timestamp_entrada = periodo_aberto
                duracao = timestamp_atual - timestamp_entrada
                duracao_em_minutos = int(duracao.total_seconds() / 60)
                database.fechar_periodo_de_trabalho(
                    periodo_id, novo_evento_id, duracao_em_minutos
                )
                mensagem_final += f" Duração do período: {duracao_em_minutos} minutos."

        novo_status = "Ativo" if tipo_evento == "ENTRADA" else "Inativo"
        database.atualizar_status_funcionario(id_func, novo_status)

        return jsonify({"sucesso": True, "mensagem": mensagem_final}), 200
    except Exception as e:
        print(f"ERRO INTERNO NO SERVIDOR: {e}")
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": "Ocorreu um erro interno ao processar a jornada de trabalho.",
                }
            ),
            500,
        )


@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        estatisticas = database.buscar_estatisticas()
        return jsonify(estatisticas), 200
    except Exception as e:
        print(f"ERRO AO BUSCAR ESTATÍSTICAS: {e}")
        return jsonify({"erro": "Erro interno ao buscar estatísticas."}), 500


import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID
import database

rekognition = boto3.client("rekognition", region_name=AWS_REGION)


def cadastrar_face_rekognition(id_funcionario, caminho_imagem):
    print(f"\n[PASSO 2 de 3] Enviando face para o Amazon Rekognition...")
    try:
        with open(caminho_imagem, "rb") as imagem:
            response = rekognition.index_faces(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={"Bytes": imagem.read()},
                ExternalImageId=str(id_funcionario),
                MaxFaces=1,
                QualityFilter="AUTO",
            )
        if response["FaceRecords"]:
            return response["FaceRecords"][0]["Face"]["FaceId"]
        print("ERRO: Nenhum rosto detectado na imagem pelo Rekognition.")
        return None
    except Exception as e:
        print(f"ERRO ao indexar face no Rekognition: {e}")
        return None


def executar_cadastro_interativo():
    print("\n--- Cadastro de Novo Funcionário ---")

    try:
        nome_completo = input("Digite o nome completo do funcionário: ")
        departamento = input("Digite o departamento: ")
        cargo = input("Digite o cargo: ")
        foto_path = input(
            "Digite o caminho completo para a foto do funcionário (ex: C:\\Users\\...\\foto.jpg): "
        )

        print(f"\n[PASSO 1 de 3] Inserindo dados no banco...")
        novo_id_funcionario = database.inserir_novo_funcionario(
            nome_completo, departamento, cargo
        )

        if novo_id_funcionario:
            face_id_gerado = cadastrar_face_rekognition(novo_id_funcionario, foto_path)

            if face_id_gerado:
                print(f"\n[PASSO 3 de 3] Associando ID da face no banco...")
                database.associar_face_id(novo_id_funcionario, face_id_gerado)
                print("\nSUCESSO! Funcionário cadastrado completamente.")
                print(f"ID: {novo_id_funcionario} | Nome: {nome_completo}")
            else:
                print(
                    "\nERRO CRÍTICO: Cadastro facial falhou. Remova o funcionário e tente novamente."
                )
    except FileNotFoundError:
        print(
            f"\nERRO: O arquivo de imagem não foi encontrado no caminho especificado."
        )
    except Exception as e:
        print(f"\nOcorreu um erro geral durante o cadastro: {e}")

    AWS_REGION = "us-east-1"


REKOGNITION_COLLECTION_ID = "funcionarios_empresa"
FACE_MATCH_THRESHOLD = 90.0

import psycopg2
import os


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
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
            stats["total"] = cur.fetchone()[0]
            cur.execute(sql_ativos)
            stats["ativos"] = cur.fetchone()[0]
            cur.execute(sql_inativos)
            stats["inativos"] = cur.fetchone()[0]
            cur.execute(sql_deptos)
            stats["departamentos"] = cur.fetchone()[0]
    finally:
        conn.close()
    return stats


def associar_face_id(id_funcionario, rekognition_face_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE funcionarios SET rekognition_face_id = %s WHERE id = %s",
                (rekognition_face_id, id_funcionario),
            )
    print(f"FaceID associado ao funcionário ID: {id_funcionario}.")


def buscar_todos_funcionarios():
    sql = "SELECT id, nome_completo, departamento, cargo, status, to_char(criado_em, 'DD/MM/YYYY') as data_admissao FROM funcionarios ORDER BY nome_completo;"
    funcionarios = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            for row in cur.fetchall():
                funcionarios.append(
                    {
                        "id": row[0],
                        "nome": row[1],
                        "departamento": row[2],
                        "cargo": row[3],
                        "status": row[4],
                        "admissao": row[5],
                    }
                )
    return funcionarios


def buscar_dados_funcionario(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome_completo, rekognition_face_id FROM funcionarios WHERE id = %s",
                (id_funcionario,),
            )
            return cur.fetchone()


def remover_funcionario_por_id(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM funcionarios WHERE id = %s", (id_funcionario,))
    print(f"Funcionário ID {id_funcionario} removido do banco de dados com sucesso.")


def buscar_nome_funcionario_por_id(id_funcionario):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome_completo FROM funcionarios WHERE id = %s",
                (id_funcionario,),
            )
            resultado = cur.fetchone()
            return resultado[0] if resultado else None


def contar_eventos_do_dia(id_funcionario, data_evento):
    sql = "SELECT COUNT(id) FROM eventos_ponto WHERE id_funcionario = %s AND (timestamp_evento AT TIME ZONE 'America/Sao_Paulo')::date = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_funcionario, data_evento))
            return cur.fetchone()[0]


def inserir_evento_ponto(
    id_funcionario, timestamp_evento, tipo_evento, dispositivo_id="Terminal-01"
):
    sql = "INSERT INTO eventos_ponto (id_funcionario, timestamp_evento, tipo_evento, dispositivo_id) VALUES (%s, %s, %s, %s) RETURNING id;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql, (id_funcionario, timestamp_evento, tipo_evento, dispositivo_id)
            )
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
    print(
        f"Período de trabalho ID {periodo_id} fechado. Duração: {duracao_minutos} minutos."
    )

    import servicos_autenticacao


import database
from datetime import datetime
import pytz


def registrar_ponto(caminho_imagem):
    print(f"\nIniciando tentativa de registro de ponto...")

    dados_funcionario = servicos_autenticacao.autenticar_funcionario(caminho_imagem)

    if not dados_funcionario:
        print("Registro de ponto falhou: autenticação mal sucedida.")
        return False

    id_func = dados_funcionario["id"]
    nome_func = dados_funcionario["nome"]

    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    timestamp_atual = datetime.now(sao_paulo_tz)

    data_atual = timestamp_atual.date()

    print(f"\nOlá, {nome_func}! Processando seu registro de ponto...")
    print(f"Horário local (São Paulo): {timestamp_atual.strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        contagem_eventos_dia = database.contar_eventos_do_dia(id_func, data_atual)

        if contagem_eventos_dia % 2 == 0:
            tipo_evento = "ENTRADA"
        else:
            tipo_evento = "SAIDA"

        print(
            f"Este é o seu {contagem_eventos_dia + 1}º registro do dia. Tipo definido como: {tipo_evento}"
        )

        novo_evento_id = database.inserir_evento_ponto(
            id_func, timestamp_atual, tipo_evento
        )

        if tipo_evento == "ENTRADA":
            database.criar_periodo_de_trabalho(id_func, data_atual, novo_evento_id)

        elif tipo_evento == "SAIDA":
            periodo_aberto = database.buscar_periodo_aberto(id_func, data_atual)

            if periodo_aberto:
                periodo_id, timestamp_entrada = periodo_aberto

                duracao = timestamp_atual - timestamp_entrada
                duracao_em_minutos = int(duracao.total_seconds() / 60)

                database.fechar_periodo_de_trabalho(
                    periodo_id, novo_evento_id, duracao_em_minutos
                )
            else:
                print(
                    f"AVISO: Registro de SAÍDA (ID {novo_evento_id}) sem um período de trabalho aberto correspondente hoje."
                )

        return True

    except Exception as e:
        print(f"Ocorreu um erro ao processar a jornada de trabalho: {e}")
        return False


from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID
import database

rekognition = boto3.client("rekognition", region_name=AWS_REGION)


def remover_face_rekognition(face_id_para_remover):
    if not face_id_para_remover:
        print("AVISO: Nenhum FaceID do Rekognition associado. Pulando remoção da AWS.")
        return True
    print(f"Removendo FaceID {face_id_para_remover} da coleção...")
    try:
        response = rekognition.delete_faces(
            CollectionId=REKOGNITION_COLLECTION_ID, FaceIds=[face_id_para_remover]
        )
        if response["DeletedFaces"]:
            print(" -> Face removida da AWS com sucesso.")
            return True
        else:
            print(
                " -> A AWS informou que a face não foi encontrada ou não pôde ser removida."
            )
            return False
    except ClientError as e:
        print(f"ERRO na API da AWS ao tentar remover a face: {e}")
        return False


def executar_remocao_interativa():
    print("\n--- Remoção de Funcionário ---")
    try:
        id_para_remover_str = input("Digite o ID do funcionário que deseja remover: ")
        id_para_remover = int(id_para_remover_str)

        dados_funcionario = database.buscar_dados_funcionario(id_para_remover)

        if not dados_funcionario:
            print(f"\nERRO: Nenhum funcionário encontrado com o ID {id_para_remover}.")
        else:
            nome_funcionario, face_id = dados_funcionario

            print(
                f"\nFuncionário encontrado: {nome_funcionario} (ID: {id_para_remover})"
            )
            confirmacao = (
                input(
                    f"Tem certeza que deseja remover PERMANENTEMENTE este funcionário? [S/N]: "
                )
                .strip()
                .upper()
            )

            if confirmacao == "S":
                print("\nIniciando processo de remoção...")
                sucesso_aws = remover_face_rekognition(face_id)
                if sucesso_aws:
                    database.remover_funcionario_por_id(id_para_remover)
                    print("\nSUCESSO! Funcionário removido completamente.")
                else:
                    print(
                        "\nERRO CRÍTICO: Falha na remoção da AWS. A remoção do banco foi abortada."
                    )
            else:
                print("\nOperação cancelada.")
    except ValueError:
        print("\nERRO: O ID deve ser um número inteiro.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")


from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID, FACE_MATCH_THRESHOLD
import database

rekognition = boto3.client("rekognition", region_name=AWS_REGION)


def buscar_face_na_colecao(caminho_imagem):
    print("Buscando face na coleção de funcionários...")
    try:
        with open(caminho_imagem, "rb") as imagem:
            response = rekognition.search_faces_by_image(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={"Bytes": imagem.read()},
                FaceMatchThreshold=FACE_MATCH_THRESHOLD,
                MaxFaces=1,
            )

        if response["FaceMatches"]:
            match = response["FaceMatches"][0]
            id_funcionario_encontrado = int(match["Face"]["ExternalImageId"])
            similaridade = match["Similarity"]
            nome_funcionario = database.buscar_nome_funcionario_por_id(
                id_funcionario_encontrado
            )

            print(
                f" -> Sucesso! Funcionário reconhecido: ID {id_funcionario_encontrado} - {nome_funcionario} (Similaridade: {similaridade:.2f}%)"
            )
            return {
                "id": id_funcionario_encontrado,
                "nome": nome_funcionario,
                "sucesso": True,
            }
        else:
            return {
                "error": "Rosto não reconhecido. Verifique se você está cadastrado.",
                "sucesso": False,
            }

    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidParameterException":
            return {
                "error": "Nenhum rosto detectado na imagem. Aproxime-se e garanta boa iluminação.",
                "sucesso": False,
            }
        else:
            return {
                "error": "Erro de comunicação com o serviço de reconhecimento.",
                "sucesso": False,
            }
    except FileNotFoundError:
        return {
            "error": "Erro interno: arquivo de imagem temporário não encontrado.",
            "sucesso": False,
        }
    except Exception as e:
        return {
            "error": f"Erro interno ao processar reconhecimento: {e}",
            "sucesso": False,
        }
