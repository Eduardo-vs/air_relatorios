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
        
        # DEBUG: Salvar resposta bruta
        debug_info = {
            'endpoint': ENDPOINT_GET_POSTS,
            'payload': payload,
            'status_code': response.status_code,
            'response_type': type(data).__name__,
            'response_keys': list(data.keys()) if isinstance(data, dict) else f'list com {len(data)} itens' if isinstance(data, list) else 'outro',
            'response_raw': data if not isinstance(data, list) or len(data) < 3 else data[:2]
        }
        
        if isinstance(data, list) and len(data) > 0:
            return {"success": True, "data": data[0], "debug": debug_info}
        return {"success": True, "data": data, "debug": debug_info}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "debug": {"error_type": "request", "endpoint": ENDPOINT_GET_POSTS}}
    except Exception as e:
        return {"success": False, "error": str(e), "debug": {"error_type": "exception"}}


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
    Estrutura da API:
    {
        "id": "...",
        "name": "...",
        "username": "...",
        "picture": "...",
        "bio": "...",
        "engagement_rate": 105,  # Já em formato x100 (1.05%)
        "reach_rate": 633,  # Já em formato x100 (6.33%)
        "score": 0.41,
        "counters": {
            "followers": 331544,
            "posts": 0,
            "likes": 162499,
            "views": 2812620,
            "comments": 3645,
            ...
        },
        "network": "instagram"
    }
    """
    if not api_data:
        return None
    
    # A API retorna os dados diretamente no objeto, não em extra_information
    # Mas pode vir em diferentes formatos dependendo do endpoint
    
    # Tentar extrair de extra_information se existir (formato antigo)
    if api_data.get('extra_information'):
        extra = api_data.get('extra_information', {})
        profile = extra.get('profile', api_data)
    else:
        profile = api_data
    
    # Counters contém followers e outras métricas
    counters = profile.get('counters', {})
    
    # Seguidores está dentro de counters
    seguidores = counters.get('followers', 0) or profile.get('followers', 0) or 0
    
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
    
    # Taxas já vêm multiplicadas por 100 da API (ex: 105 = 1.05%)
    # Dividir por 100 para armazenar como percentual real
    engagement_rate_raw = profile.get('engagement_rate', 0) or 0
    reach_rate_raw = profile.get('reach_rate', 0) or 0
    
    # Se o valor for muito alto (>100), provavelmente está em formato x100
    engagement_rate = engagement_rate_raw / 100 if engagement_rate_raw > 100 else engagement_rate_raw
    reach_rate = reach_rate_raw / 100 if reach_rate_raw > 100 else reach_rate_raw
    
    return {
        'profile_id': profile.get('id', ''),
        'nome': profile.get('name', ''),
        'usuario': profile.get('username', ''),
        'network': profile.get('network', 'instagram'),
        'seguidores': seguidores,
        'foto': profile.get('picture', ''),
        'bio': profile.get('bio', ''),
        'engagement_rate': engagement_rate,
        'air_score': profile.get('score', 0) or 0,
        'reach_rate': reach_rate,
        'means': profile.get('means', {}),
        'hashtags': profile.get('hashtags', []),
        'classificacao': classificacao,
        # Counters
        'total_posts': counters.get('posts', 0) or counters.get('last_posts', 0) or 0,
        'total_likes': counters.get('likes', 0) or 0,
        'total_views': counters.get('views', 0) or 0,
        'total_comments': counters.get('comments', 0) or 0,
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
        Dict com success e data (ja processado com campos nome, usuario, etc)
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
                # Processar dados para formato padrao do sistema
                dados_processados = processar_dados_api(items[0])
                return {"success": True, "data": dados_processados}
        
        # Se não encontrou, retornar erro
        return {"success": False, "error": resultado.get('error', 'Perfil não encontrado na API')}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def buscar_posts_influenciador(profile_id: str, limite: int = 100, hashtags: List[str] = None, mentions: List[str] = None, start_date: str = None, end_date: str = None) -> Dict:
    """
    Busca posts de um influenciador, paginando todas as páginas disponíveis
    
    Args:
        profile_id: ID do perfil no AIR
        limite: Número máximo de posts a buscar (total)
        hashtags: Lista de hashtags para filtrar via parâmetro text
        mentions: Lista de menções para filtrar via parâmetro text
        start_date: Data início no formato YYYY-MM-DD (obrigatório)
        end_date: Data fim no formato YYYY-MM-DD (obrigatório)
    
    Returns:
        Dict com success e posts
    """
    from datetime import datetime, timedelta
    
    if not start_date or not end_date:
        return {"success": False, "posts": [], "error": "Datas de início e fim são obrigatórias"}
    
    try:
        # Montar lista de termos para filtro (hashtags + mentions)
        termos_filtro = []
        if hashtags:
            for h in hashtags:
                # Limpar hashtag
                h_clean = h.strip().replace('#', '')
                if h_clean:
                    termos_filtro.append(h_clean)
        
        if mentions:
            for m in mentions:
                # Limpar mention
                m_clean = m.strip().replace('@', '')
                if m_clean:
                    termos_filtro.append(m_clean)
        
        todos_posts = []
        page = 0
        max_pages = 50  # Limite de segurança
        api_debug = []  # DEBUG: Guardar info de cada chamada
        
        while len(todos_posts) < limite and page < max_pages:
            # Buscar com os termos de filtro
            if termos_filtro:
                # Junta todos os termos para busca
                texto_busca = ' '.join(termos_filtro[:10])  # Limita a 10 termos
                
                resultado = buscar_posts(
                    profile_id=profile_id,
                    start_date=start_date,
                    end_date=end_date,
                    text=texto_busca,
                    page=page
                )
            else:
                resultado = buscar_posts(
                    profile_id=profile_id,
                    start_date=start_date,
                    end_date=end_date,
                    page=page
                )
            
            if not resultado.get('success'):
                # DEBUG: Capturar erro
                api_debug.append({
                    'page': page,
                    'success': False,
                    'error': resultado.get('error'),
                    'debug': resultado.get('debug')
                })
                break
            
            # DEBUG: Capturar resposta
            api_debug.append({
                'page': page,
                'success': True,
                'debug': resultado.get('debug'),
                'data_type': type(resultado.get('data')).__name__
            })
            
            data = resultado.get('data', {})
            
            # DEBUG: Capturar estrutura do data
            if page == 0:  # So na primeira pagina
                api_debug.append({
                    'page': page,
                    'data_type': type(data).__name__,
                    'data_keys': list(data.keys()) if isinstance(data, dict) else 'nao e dict',
                    'posts_key_exists': 'posts' in data if isinstance(data, dict) else False,
                    'posts_count': len(data.get('posts', [])) if isinstance(data, dict) else 0,
                    'count_field': data.get('count') if isinstance(data, dict) else None,
                    'pages_field': data.get('pages') if isinstance(data, dict) else None
                })
            
            # Extrair posts e info de paginacao
            # API pode retornar em 'items' ou 'posts'
            posts_pagina = []
            total_pages = 1
            
            if isinstance(data, dict):
                # Tentar 'items' primeiro (formato atual da API), depois 'posts'
                posts_pagina = data.get('items', []) or data.get('posts', [])
                total_pages = data.get('pages', 1)
            elif isinstance(data, list):
                # Se data ainda e uma lista, tentar extrair o primeiro item
                if len(data) > 0 and isinstance(data[0], dict):
                    posts_pagina = data[0].get('items', []) or data[0].get('posts', [])
                    total_pages = data[0].get('pages', 1)
                else:
                    posts_pagina = data
            
            if not posts_pagina:
                break
            
            todos_posts.extend(posts_pagina)
            
            # Verificar se há mais páginas
            page += 1
            if page >= total_pages:
                break
        
        # Processar todos os posts coletados
        posts_processados = []
        for post_raw in todos_posts[:limite]:
            # Extrair counters
            counters = post_raw.get('counters', {})
            
            # Extrair dados do post
            caption = post_raw.get('caption', '') or ''
            post_type = post_raw.get('type', 'post') or 'post'
            permalink = post_raw.get('permalink', '') or post_raw.get('link', '') or post_raw.get('url', '') or ''
            thumbnail = post_raw.get('thumbnail', '') or post_raw.get('image', '') or ''
            short_code = post_raw.get('short_code', '') or post_raw.get('shortcode', '') or post_raw.get('code', '') or ''
            network = post_raw.get('network', 'instagram') or 'instagram'
            post_id = post_raw.get('id', '') or post_raw.get('post_id', '') or ''
            username = post_raw.get('username', '') or post_raw.get('user', '') or ''
            
            # Se nao tem permalink, tentar construir de varias formas
            if not permalink and short_code:
                if network == 'instagram':
                    permalink = f"https://www.instagram.com/p/{short_code}/"
                elif network == 'tiktok':
                    permalink = f"https://www.tiktok.com/@{username}/video/{short_code}"
            
            # Se ainda nao tem permalink, tentar extrair do thumbnail (instagram CDN as vezes tem o shortcode)
            if not permalink and post_id and network == 'instagram':
                # Tentar usar o post_id como shortcode
                permalink = f"https://www.instagram.com/p/{post_id}/"
            
            # Se ainda nao tem, tentar extrair shortcode da URL do thumbnail
            if not permalink and thumbnail and 'instagram' in thumbnail:
                import re as _re
                match = _re.search(r'/p/([A-Za-z0-9_-]+)/', thumbnail)
                if match:
                    permalink = f"https://www.instagram.com/p/{match.group(1)}/"
            
            # Mapear tipo para formato
            formato_map = {
                'post': 'Feed',
                'reel': 'Reels',
                'reels': 'Reels',
                'story': 'Stories',
                'stories': 'Stories',
                'carousel': 'Carrossel',
                'video': 'Video',
                'image': 'Feed'
            }
            formato = formato_map.get(post_type.lower(), 'Feed')
            
            # Data de publicação
            posted_at = post_raw.get('posted_at', '')
            data_pub = ''
            if posted_at:
                try:
                    dt = datetime.fromisoformat(posted_at.replace('Z', ''))
                    data_pub = dt.strftime('%d/%m/%Y')
                except:
                    data_pub = posted_at[:10] if len(posted_at) >= 10 else ''
            
            # Montar post processado
            post_processado = {
                'type': formato,
                'formato': formato,
                'permalink': permalink,
                'link': permalink,
                'date': data_pub,
                'data_publicacao': data_pub,
                'caption': caption,
                'thumbnail': thumbnail,
                'views': counters.get('views', 0) or 0,
                'reach': counters.get('reach', 0) or 0,
                'alcance': counters.get('reach', 0) or 0,
                'impressions': counters.get('impressions', 0) or 0,
                'impressoes': counters.get('impressions', 0) or 0,
                'engagement': counters.get('interactions', 0) or 0,
                'interacoes': counters.get('interactions', 0) or 0,
                'likes': counters.get('likes', 0) or 0,
                'curtidas': counters.get('likes', 0) or 0,
                'comments': counters.get('comments', 0) or 0,
                'comentarios_qtd': counters.get('comments', 0) or 0,
                'shares': counters.get('shares', 0) or 0,
                'compartilhamentos': counters.get('shares', 0) or 0,
                'saves': counters.get('saved', 0) or 0,
                'hashtags': post_raw.get('hashtags', [])
            }
            
            posts_processados.append(post_processado)
        
        return {
            "success": True, 
            "posts": posts_processados, 
            "total_encontrados": len(todos_posts),
            "raw_data": todos_posts[:3],  # Primeiros 3 para debug
            "raw_keys": list(todos_posts[0].keys()) if todos_posts else [],
            "first_post_link_fields": {
                'permalink': todos_posts[0].get('permalink', 'VAZIO') if todos_posts else 'SEM POSTS',
                'link': todos_posts[0].get('link', 'VAZIO') if todos_posts else 'SEM POSTS',
                'url': todos_posts[0].get('url', 'VAZIO') if todos_posts else 'SEM POSTS',
                'short_code': todos_posts[0].get('short_code', 'VAZIO') if todos_posts else 'SEM POSTS',
                'shortcode': todos_posts[0].get('shortcode', 'VAZIO') if todos_posts else 'SEM POSTS',
                'code': todos_posts[0].get('code', 'VAZIO') if todos_posts else 'SEM POSTS',
                'id': todos_posts[0].get('id', 'VAZIO') if todos_posts else 'SEM POSTS',
            } if todos_posts else {},
            "api_debug": api_debug
        }
        
    except Exception as e:
        return {"success": False, "posts": [], "error": str(e), "api_debug": api_debug if 'api_debug' in dir() else []}
