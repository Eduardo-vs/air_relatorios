"""
API Client - Integracao com endpoints externos
"""

import requests
from typing import List, Dict, Optional

# URLs dos endpoints
ENDPOINT_GET_PROFILE_ID = "https://n8n.air.com.vc/webhook/2e7956e8-2f15-497d-9a10-efb21038d5e5"
ENDPOINT_GET_PROFILE = "https://n8n.air.com.vc/webhook/5246e807-0d6a-44aa-935a-88a26d831428"
ENDPOINT_GET_POSTS = "https://n8n.air.com.vc/webhook/9fe6eb2a-ebec-418b-8744-889e3e0e47ac"


def buscar_profile_id(username: str, network: str) -> Dict:
    """
    Busca o ID do perfil baseado no username e rede social
    Retorna dados iniciais do perfil
    """
    try:
        params = {
            "username": username.replace("@", "").strip(),
            "network": network.lower()
        }
        
        response = requests.get(ENDPOINT_GET_PROFILE_ID, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return {"success": True, "data": data[0]}
        return {"success": True, "data": data}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def buscar_perfil_completo(profile_ids: List[str]) -> Dict:
    """
    Busca dados completos de perfis pelo ID
    Usado para atualizar dados de influenciadores ja cadastrados
    """
    try:
        payload = {"profiles": profile_ids}
        
        response = requests.post(ENDPOINT_GET_PROFILE, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        return {"success": True, "data": data}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def buscar_posts(profile_id: str, start_date: str, end_date: str, post_types: List[str] = None, text: str = None, page: int = 0) -> Dict:
    """
    Busca posts de um influenciador por periodo
    
    Args:
        profile_id: ID do perfil
        start_date: Data inicio (YYYY-MM-DD)
        end_date: Data fim (YYYY-MM-DD)
        post_types: Lista de tipos ['post', 'reel', 'story']
        text: Texto para filtrar na legenda
        page: Pagina para paginacao
    """
    try:
        payload = {
            "profile_ids": [profile_id],
            "start_date": start_date,
            "end_date": end_date,
            "page": page
        }
        
        if post_types:
            payload["post_types"] = post_types
        
        if text:
            payload["text"] = text
        
        response = requests.post(ENDPOINT_GET_POSTS, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return {"success": True, "data": data[0]}
        return {"success": True, "data": data}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def processar_post_api(post_data: Dict) -> Dict:
    """
    Processa dados de post da API para formato do sistema
    """
    counters = post_data.get('counters', {})
    
    # Mapear tipo para formato
    tipo = post_data.get('type', 'post')
    network = post_data.get('network', 'instagram').lower()
    
    formato_map = {
        'post': 'Feed',
        'reel': 'Reels',
        'reels': 'Reels',
        'story': 'Stories',
        'stories': 'Stories',
        'carousel': 'Carrossel',
        'video': 'Video',
        'tiktok': 'Video',
        'igtv': 'IGTV'
    }
    
    # TikTok sempre é Video
    if network == 'tiktok':
        formato = 'Video'
    else:
        formato = formato_map.get(tipo.lower() if tipo else 'post', 'Feed')
    
    # Data de publicacao
    posted_at = post_data.get('posted_at', '')
    if posted_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            data_pub = dt.strftime('%d/%m/%Y')
        except:
            data_pub = posted_at[:10] if len(posted_at) >= 10 else ''
    else:
        data_pub = ''
    
    return {
        'post_id_api': post_data.get('post_id', ''),
        'formato': formato,
        'plataforma': post_data.get('network', 'instagram').title(),
        'data_publicacao': data_pub,
        'link_post': post_data.get('permalink', ''),
        'legenda': post_data.get('caption', ''),
        'thumbnail': post_data.get('thumbnail', ''),
        'image': post_data.get('image', ''),
        'views': counters.get('views', 0),
        'alcance': counters.get('reach', 0),
        'interacoes': counters.get('interactions', 0),
        'impressoes': counters.get('impressions', 0),
        'curtidas': counters.get('likes', 0),
        'comentarios_qtd': counters.get('comments', 0),
        'compartilhamentos': counters.get('shares', 0),
        'saves': counters.get('saved', 0),
        'clique_link': 0,
        'cupom_conversoes': 0,
        'cupom_codigo': '',
        'custo': 0,
        'imagens': [post_data.get('thumbnail', '')] if post_data.get('thumbnail') else [],
        'comentarios': []
    }


def processar_dados_api(api_data: Dict) -> Dict:
    """
    Processa dados da API para formato do banco de dados
    Retorna exatamente os campos que a API fornece
    """
    if not api_data:
        return None
    
    # Dados podem vir de diferentes estruturas dependendo do endpoint
    extra = api_data.get('extra_information', {})
    profile = extra.get('profile', {}) if extra else api_data
    
    # Seguidores
    seguidores = profile.get('followers', 0)
    
    # Classificacao baseada em seguidores
    if seguidores < 10000:
        classificacao = 'Nano'
    elif seguidores < 100000:
        classificacao = 'Micro'
    elif seguidores < 500000:
        classificacao = 'Mid'
    elif seguidores < 1000000:
        classificacao = 'Macro'
    else:
        classificacao = 'Mega'
    
    return {
        'profile_id': extra.get('profile_id', profile.get('id', '')),
        'nome': profile.get('name', ''),
        'usuario': profile.get('username', ''),
        'network': profile.get('network', 'instagram'),
        'seguidores': seguidores,
        'foto': profile.get('picture', ''),
        'bio': profile.get('bio', ''),
        'engagement_rate': profile.get('engagement_rate', 0),
        'air_score': profile.get('score', 0),  # Score da API = AIR Score
        'reach_rate': profile.get('reach_rate', 0),
        'means': profile.get('means', {}),
        'hashtags': profile.get('hashtags', []),
        'classificacao': classificacao,
        # Counters (se disponiveis)
        'total_posts': profile.get('counters', {}).get('posts', 0),
        'total_likes': profile.get('counters', {}).get('likes', 0),
        'total_views': profile.get('counters', {}).get('views', 0),
        'total_comments': profile.get('counters', {}).get('comments', 0),
    }


def atualizar_influenciador_api(profile_id: str) -> Dict:
    """
    Atualiza dados de um influenciador ja cadastrado
    Usa o profile_id armazenado para buscar dados atualizados
    """
    resultado = buscar_perfil_completo([profile_id])
    
    if not resultado.get('success'):
        return resultado
    
    items = resultado.get('data', {}).get('items', [])
    if not items:
        return {"success": False, "error": "Perfil nao encontrado"}
    
    dados_processados = processar_dados_api(items[0])
    
    return {"success": True, "data": dados_processados}


def buscar_por_profile_id(profile_id: str) -> Dict:
    """
    Busca dados de um influenciador pelo profile_id do AIR
    
    Args:
        profile_id: ID do perfil no AIR (ex: "67a66fb7a917c05b016cd500")
    
    Returns:
        Dict com success e data
    """
    try:
        # Tentar buscar perfil completo
        resultado = buscar_perfil_completo([profile_id])
        
        if resultado.get('success'):
            data = resultado.get('data', {})
            
            # Tentar diferentes formatos de resposta
            items = []
            if isinstance(data, dict):
                items = data.get('items', [])
                if not items and data.get('profile'):
                    items = [data.get('profile')]
                if not items and data.get('data'):
                    items = [data.get('data')] if isinstance(data.get('data'), dict) else data.get('data', [])
            elif isinstance(data, list):
                items = data
            
            if items and len(items) > 0:
                return {"success": True, "data": items[0]}
        
        # Se não encontrou, retornar erro
        return {"success": False, "error": resultado.get('error', 'Perfil não encontrado na API')}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def buscar_posts_influenciador(profile_id: str, limite: int = 20, hashtags: List[str] = None) -> Dict:
    """
    Busca posts recentes de um influenciador
    
    Args:
        profile_id: ID do perfil no AIR
        limite: Número máximo de posts a buscar
        hashtags: Lista de hashtags para filtrar (opcional)
    
    Returns:
        Dict com success e posts
    """
    from datetime import datetime, timedelta
    
    try:
        # Buscar posts dos últimos 6 meses
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        resultado = buscar_posts(
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            page=0
        )
        
        if not resultado.get('success'):
            return {"success": False, "posts": [], "error": resultado.get('error')}
        
        data = resultado.get('data', {})
        posts_raw = data.get('posts', []) if isinstance(data, dict) else []
        
        # Se não tem posts no formato esperado, tentar outros formatos
        if not posts_raw and isinstance(data, list):
            posts_raw = data
        
        posts_processados = []
        for post_raw in posts_raw[:limite]:
            post = processar_post_api(post_raw)
            
            # Se tem filtro de hashtags, verificar
            if hashtags:
                caption = (post_raw.get('caption') or '').lower()
                post_hashtags = [h.lower() for h in post_raw.get('hashtags', [])]
                
                tem_hashtag = False
                for h in hashtags:
                    h_clean = h.lower().replace('#', '')
                    if h_clean in caption or h_clean in post_hashtags:
                        tem_hashtag = True
                        break
                
                if not tem_hashtag:
                    continue
            
            posts_processados.append({
                'type': post.get('formato', 'Feed'),
                'permalink': post.get('link_post', ''),
                'date': post.get('data_publicacao', ''),
                'caption': post_raw.get('caption', ''),
                'thumbnail': post.get('thumbnail', ''),
                'views': post.get('views', 0),
                'reach': post.get('alcance', 0),
                'impressions': post.get('impressoes', 0),
                'engagement': post.get('interacoes', 0),
                'likes': post.get('curtidas', 0),
                'comments': post.get('comentarios_qtd', 0),
                'shares': post.get('compartilhamentos', 0),
                'saves': post.get('saves', 0),
                'hashtags': post_raw.get('hashtags', [])
            })
        
        return {"success": True, "posts": posts_processados}
        
    except Exception as e:
        return {"success": False, "posts": [], "error": str(e)}
