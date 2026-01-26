"""
Serviço de integração com AWS S3 para armazenamento de mídias
Versão: 2.0 - HelpZone Media Storage
"""
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Configurações de mídias permitidas
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 20 * 1024 * 1024  # 20MB


def _cfg():
    """Carrega configurações do S3 das variáveis de ambiente"""
    region = os.getenv("AWS_REGION", "us-east-1")
    bucket = os.getenv("S3_BUCKET")
    prefix = os.getenv("S3_PREFIX", "helpzone")
    
    if not bucket:
        raise RuntimeError("S3_BUCKET não definido no ambiente")
    
    return region, bucket, prefix


def _get_s3_client():
    """Cria e retorna um cliente S3 configurado"""
    region, _, _ = _cfg()
    return boto3.client("s3", region_name=region)


def validate_file(file_obj, file_type: str) -> Tuple[bool, str]:
    """
    Valida arquivo antes do upload
    
    Args:
        file_obj: Objeto de arquivo do Flask (FileStorage)
        file_type: 'image' ou 'video'
    
    Returns:
        Tuple (válido, mensagem_erro)
    """
    if not file_obj or not hasattr(file_obj, 'filename'):
        return False, "Arquivo inválido"
    
    filename = file_obj.filename
    if not filename or '.' not in filename:
        return False, "Nome de arquivo inválido"
    
    ext = filename.rsplit('.', 1)[-1].lower()
    
    # Validar extensão
    if file_type == 'image':
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Formato de imagem não permitido. Use: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
    elif file_type == 'video':
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            return False, f"Formato de vídeo não permitido. Use: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
    else:
        return False, "Tipo de arquivo desconhecido"
    
    # Validar tamanho (seek para o final para obter o tamanho)
    file_obj.seek(0, 2)  # Seek to end
    size = file_obj.tell()
    file_obj.seek(0)  # Voltar ao início
    
    if file_type == 'image' and size > MAX_IMAGE_SIZE:
        return False, f"Imagem muito grande. Máximo: {MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB"
    elif file_type == 'video' and size > MAX_VIDEO_SIZE:
        return False, f"Vídeo muito grande. Máximo: {MAX_VIDEO_SIZE / 1024 / 1024:.0f}MB"
    
    return True, ""


def upload_helpzone_media(file_obj, user_id: int, media_type: str, folder: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Faz upload de mídia do HelpZone para o S3
    
    Args:
        file_obj: Objeto de arquivo do Flask
        user_id: ID do usuário
        media_type: 'image' ou 'video'
        folder: Subpasta opcional (padrão: helpzone/posts ou helpzone/stories)
    
    Returns:
        Tuple (key, error_message)
        key: Chave S3 do arquivo se sucesso, None se erro
        error_message: Mensagem de erro se falhou, None se sucesso
    """
    try:
        # Validar arquivo
        valid, error_msg = validate_file(file_obj, media_type)
        if not valid:
            return None, error_msg
        
        # Obter configurações
        region, bucket, prefix = _cfg()
        s3 = _get_s3_client()
        
        # Gerar extensão e key
        ext = ""
        if hasattr(file_obj, "filename") and "." in file_obj.filename:
            ext = "." + file_obj.filename.rsplit(".", 1)[-1].lower()
        
        # Determinar subpasta
        base_folder = folder if folder else f"{prefix}/posts"
        
        # Gerar key única
        unique_id = uuid.uuid4().hex
        key = f"{base_folder}/{user_id}/{unique_id}{ext}"
        
        # Determinar Content-Type correto
        content_type = file_obj.mimetype if hasattr(file_obj, 'mimetype') else None
        if not content_type:
            if media_type == 'image':
                content_type = f"image/{ext[1:]}" if ext else "image/jpeg"
            elif media_type == 'video':
                content_type = f"video/{ext[1:]}" if ext else "video/mp4"
            else:
                content_type = "application/octet-stream"
        
        # Upload para S3
        s3.upload_fileobj(
            file_obj,
            bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": "public, max-age=31536000",  # Cache por 1 ano
                "Metadata": {
                    "user-id": str(user_id),
                    "media-type": media_type,
                    "uploaded-by": "helpzone"
                }
            },
        )
        
        logger.info(f"Mídia enviada com sucesso: {key}")
        return key, None
        
    except ClientError as e:
        error_msg = f"Erro ao fazer upload para S3: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Erro inesperado no upload: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def presigned_get_url(key: str, expires: int = 3600) -> Optional[str]:
    """
    Gera URL presigned para acesso temporário ao arquivo
    
    Args:
        key: Chave S3 do arquivo
        expires: Tempo de expiração em segundos (padrão: 1 hora)
    
    Returns:
        URL presigned ou None em caso de erro
    """
    try:
        region, bucket, _ = _cfg()
        s3 = _get_s3_client()
        
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )
        
        return url
    except Exception as e:
        logger.error(f"Erro ao gerar URL presigned para {key}: {str(e)}")
        return None


def delete_media(key: str) -> Tuple[bool, Optional[str]]:
    """
    Remove mídia do S3
    
    Args:
        key: Chave S3 do arquivo
    
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        region, bucket, _ = _cfg()
        s3 = _get_s3_client()
        
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Mídia removida com sucesso: {key}")
        
        return True, None
    except ClientError as e:
        error_msg = f"Erro ao remover mídia do S3: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Erro inesperado ao remover mídia: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


# ===== FUNÇÕES LEGADAS (compatibilidade) =====
def upload_fileobj(file_obj, user_id: int, folder: str = None) -> str:
    """
    LEGADO: Função de upload básica mantida para compatibilidade
    Use upload_helpzone_media() para novos desenvolvimentos
    """
    region, bucket, prefix = _cfg()
    s3 = _get_s3_client()
    
    ext = ""
    if getattr(file_obj, "filename", None) and "." in file_obj.filename:
        ext = "." + file_obj.filename.rsplit(".", 1)[-1].lower()
    
    base_folder = folder or prefix
    key = f"{base_folder}/{user_id}/{uuid.uuid4().hex}{ext}"
    
    s3.upload_fileobj(
        file_obj,
        bucket,
        key,
        ExtraArgs={
            "ContentType": getattr(file_obj, "mimetype", None) or "application/octet-stream",
            "CacheControl": "public, max-age=31536000",
        },
    )
    
    return key
