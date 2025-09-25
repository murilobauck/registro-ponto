import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID
import database

rekognition = boto3.client('rekognition', region_name=AWS_REGION)

def remover_face_rekognition(face_id_para_remover):
    if not face_id_para_remover:
        print("AVISO: Nenhum FaceID do Rekognition associado. Pulando remoção da AWS.")
        return True
    print(f"Removendo FaceID {face_id_para_remover} da coleção...")
    try:
        response = rekognition.delete_faces(
            CollectionId=REKOGNITION_COLLECTION_ID,
            FaceIds=[face_id_para_remover]
        )
        if response['DeletedFaces']:
            print(" -> Face removida da AWS com sucesso.")
            return True
        else:
            print(" -> A AWS informou que a face não foi encontrada ou não pôde ser removida.")
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
            
            print(f"\nFuncionário encontrado: {nome_funcionario} (ID: {id_para_remover})")
            confirmacao = input(f"Tem certeza que deseja remover PERMANENTEMENTE este funcionário? [S/N]: ").strip().upper()

            if confirmacao == 'S':
                print("\nIniciando processo de remoção...")
                sucesso_aws = remover_face_rekognition(face_id)
                if sucesso_aws:
                    database.remover_funcionario_por_id(id_para_remover)
                    print("\nSUCESSO! Funcionário removido completamente.")
                else:
                    print("\nERRO CRÍTICO: Falha na remoção da AWS. A remoção do banco foi abortada.")
            else:
                print("\nOperação cancelada.")
    except ValueError:
        print("\nERRO: O ID deve ser um número inteiro.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")