import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID
import database

rekognition = boto3.client('rekognition', region_name=AWS_REGION)

def cadastrar_face_rekognition(id_funcionario, caminho_imagem):
    print(f"\n[PASSO 2 de 3] Enviando face para o Amazon Rekognition...")
    try:
        with open(caminho_imagem, 'rb') as imagem:
            response = rekognition.index_faces(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={'Bytes': imagem.read()},
                ExternalImageId=str(id_funcionario),
                MaxFaces=1,
                QualityFilter="AUTO"
            )
        if response['FaceRecords']:
            return response['FaceRecords'][0]['Face']['FaceId']
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
        foto_path = input("Digite o caminho completo para a foto do funcionário (ex: C:\\Users\\...\\foto.jpg): ")

        print(f"\n[PASSO 1 de 3] Inserindo dados no banco...")
        novo_id_funcionario = database.inserir_novo_funcionario(nome_completo, departamento, cargo)

        if novo_id_funcionario:
            face_id_gerado = cadastrar_face_rekognition(novo_id_funcionario, foto_path)
            
            if face_id_gerado:
                print(f"\n[PASSO 3 de 3] Associando ID da face no banco...")
                database.associar_face_id(novo_id_funcionario, face_id_gerado)
                print("\nSUCESSO! Funcionário cadastrado completamente.")
                print(f"ID: {novo_id_funcionario} | Nome: {nome_completo}")
            else:
                print("\nERRO CRÍTICO: Cadastro facial falhou. Remova o funcionário e tente novamente.")
    except FileNotFoundError:
        print(f"\nERRO: O arquivo de imagem não foi encontrado no caminho especificado.")
    except Exception as e:
        print(f"\nOcorreu um erro geral durante o cadastro: {e}")

if __name__ == "__main__":
    executar_cadastro_interativo()