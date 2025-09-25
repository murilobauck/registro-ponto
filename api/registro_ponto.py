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

    id_func = dados_funcionario['id']
    nome_func = dados_funcionario['nome']
    
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    timestamp_atual = datetime.now(sao_paulo_tz)
    
    data_atual = timestamp_atual.date()
    
    print(f"\nOlá, {nome_func}! Processando seu registro de ponto...")
    print(f"Horário local (São Paulo): {timestamp_atual.strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        contagem_eventos_dia = database.contar_eventos_do_dia(id_func, data_atual)
        
        if contagem_eventos_dia % 2 == 0:
            tipo_evento = 'ENTRADA'
        else:
            tipo_evento = 'SAIDA'
            
        print(f"Este é o seu {contagem_eventos_dia + 1}º registro do dia. Tipo definido como: {tipo_evento}")

        novo_evento_id = database.inserir_evento_ponto(id_func, timestamp_atual, tipo_evento)

        if tipo_evento == 'ENTRADA':
            database.criar_periodo_de_trabalho(id_func, data_atual, novo_evento_id)
        
        elif tipo_evento == 'SAIDA':
            periodo_aberto = database.buscar_periodo_aberto(id_func, data_atual)
            
            if periodo_aberto:
                periodo_id, timestamp_entrada = periodo_aberto
                
                duracao = timestamp_atual - timestamp_entrada
                duracao_em_minutos = int(duracao.total_seconds() / 60)
                
                database.fechar_periodo_de_trabalho(periodo_id, novo_evento_id, duracao_em_minutos)
            else:
                print(f"AVISO: Registro de SAÍDA (ID {novo_evento_id}) sem um período de trabalho aberto correspondente hoje.")

        return True

    except Exception as e:
        print(f"Ocorreu um erro ao processar a jornada de trabalho: {e}")
        return False