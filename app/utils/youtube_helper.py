# app/utils/youtube_helper.py
"""
Funções auxiliares para trabalhar com URLs do YouTube
"""

import re
from urllib.parse import urlparse, parse_qs


def extrair_video_id(url):
    """
    Extrai o ID do vídeo de uma URL do YouTube.
    
    Suporta os seguintes formatos:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    
    Args:
        url (str): URL do YouTube
        
    Returns:
        str: ID do vídeo (11 caracteres) ou None se não encontrado
    
    Exemplos:
        >>> extrair_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extrair_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    if not url:
        return None
    
    # Padrão regex universal para capturar o video_id
    # Suporta: youtube.com, youtu.be, m.youtube.com, embed, etc.
    pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    # Fallback: tentar parse_qs para ?v=
    try:
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                if len(video_id) == 11:
                    return video_id
    except Exception:
        pass
    
    return None


def obter_thumbnail_url(video_id, qualidade='maxresdefault'):
    """
    Gera URL da thumbnail do YouTube.
    
    Args:
        video_id (str): ID do vídeo do YouTube
        qualidade (str): Qualidade da thumbnail
            - 'maxresdefault' (1920x1080) - melhor qualidade
            - 'sddefault' (640x480)
            - 'hqdefault' (480x360)
            - 'mqdefault' (320x180)
            - 'default' (120x90)
    
    Returns:
        str: URL da thumbnail
    """
    if not video_id:
        return None
    
    return f"https://img.youtube.com/vi/{video_id}/{qualidade}.jpg"


def obter_embed_url(video_id, autoplay=False, rel=False):
    """
    Gera URL de embed do YouTube.
    
    Args:
        video_id (str): ID do vídeo
        autoplay (bool): Se deve iniciar automaticamente
        rel (bool): Se deve mostrar vídeos relacionados
    
    Returns:
        str: URL de embed
    """
    if not video_id:
        return None
    
    params = []
    if autoplay:
        params.append('autoplay=1')
    if not rel:
        params.append('rel=0')
    
    param_string = '&'.join(params)
    if param_string:
        return f"https://www.youtube.com/embed/{video_id}?{param_string}"
    
    return f"https://www.youtube.com/embed/{video_id}"


# ========================================
# FILTROS JINJA2
# ========================================

def registrar_filtros_youtube(app):
    """
    Registra os filtros do YouTube no Jinja2.
    
    Uso no template:
        {{ aula.url_video | extrair_video_id }}
        {{ video_id | obter_thumbnail_url }}
        {{ video_id | obter_embed_url }}
    
    Args:
        app: Instância do Flask
    """
    app.jinja_env.filters['extrair_video_id'] = extrair_video_id
    app.jinja_env.filters['obter_thumbnail_url'] = obter_thumbnail_url
    app.jinja_env.filters['obter_embed_url'] = obter_embed_url
    
    # Adicionar também como função global do template
    app.jinja_env.globals['extrair_video_id'] = extrair_video_id
    app.jinja_env.globals['obter_thumbnail_url'] = obter_thumbnail_url
    app.jinja_env.globals['obter_embed_url'] = obter_embed_url


# ========================================
# TESTES
# ========================================

if __name__ == '__main__':
    # Testar diferentes formatos de URL
    urls_teste = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
        "https://www.youtube.com/watch?feature=youtu.be&v=dQw4w9WgXcQ",
    ]
    
    print("🧪 Testando extração de video_id:\n")
    for url in urls_teste:
        video_id = extrair_video_id(url)
        print(f"✅ {url}")
        print(f"   → video_id: {video_id}")
        if video_id:
            print(f"   → thumbnail: {obter_thumbnail_url(video_id)}")
            print(f"   → embed: {obter_embed_url(video_id)}")
        print()
