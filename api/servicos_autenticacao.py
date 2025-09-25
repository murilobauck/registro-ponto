import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, REKOGNITION_COLLECTION_ID, FACE_MATCH_THRESHOLD
import database

rekognition = boto3.client('rekognition', region_name=AWS_REGION)

def buscar_face_na_colecao(caminho_imagem):
    print("Buscando face na coleção de funcionários...")
    try:
        with open(caminho_imagem, 'rb') as imagem:
            response = rekognition.search_faces_by_image(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={'Bytes': imagem.read()},
                FaceMatchThreshold=FACE_MATCH_THRESHOLD,
                MaxFaces=1
            )
        
        if response['FaceMatches']:
            match = response['FaceMatches'][0]
            id_funcionario_encontrado = int(match['Face']['ExternalImageId'])
            similaridade = match['Similarity']
            nome_funcionario = database.buscar_nome_funcionario_por_id(id_funcionario_encontrado)
            
            print(f" -> Sucesso! Funcionário reconhecido: ID {id_funcionario_encontrado} - {nome_funcionario} (Similaridade: {similaridade:.2f}%)")
            return {'id': id_funcionario_encontrado, 'nome': nome_funcionario, 'sucesso': True}
        else:
            return {'error': 'Rosto não reconhecido. Verifique se você está cadastrado.', 'sucesso': False}
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidParameterException':
            return {'error': 'Nenhum rosto detectado na imagem. Aproxime-se e garanta boa iluminação.', 'sucesso': False}
        else:
            return {'error': 'Erro de comunicação com o serviço de reconhecimento.', 'sucesso': False}
    except FileNotFoundError:
        return {'error': 'Erro interno: arquivo de imagem temporário não encontrado.', 'sucesso': False}
    except Exception as e:
        return {'error': f'Erro interno ao processar reconhecimento: {e}', 'sucesso': False}