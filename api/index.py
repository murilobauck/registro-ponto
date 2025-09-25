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

@app.route("/funcionarios", methods=["GET"])
def get_funcionarios():
    try:
        lista_funcionarios = database.buscar_todos_funcionarios()
        return jsonify(lista_funcionarios), 200
    except Exception as e:
        print(f"ERRO AO BUSCAR FUNCIONÁRIOS: {e}")
        return jsonify({"erro": "Erro interno ao buscar funcionários."}), 500

@app.route("/cadastrar", methods=["POST"])
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


@app.route("/remover-funcionario/<int:id_funcionario>", methods=["DELETE"])
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

@app.route("/stats", methods=["GET"])
def get_stats():
    try:
        estatisticas = database.buscar_estatisticas()
        return jsonify(estatisticas), 200
    except Exception as e:
        print(f"ERRO AO BUSCAR ESTATÍSTICAS: {e}")
        return jsonify({"erro": "Erro interno ao buscar estatísticas."}), 500