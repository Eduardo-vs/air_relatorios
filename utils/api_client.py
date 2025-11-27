"""
API Client - Integracao com endpoints externos
"""

import requests
from typing import List, Dict, Optional

# URLs dos endpoints
ENDPOINT_GET_PROFILE_ID = "https://n8n.air.com.vc/webhook/2e7956e8-2f15-497d-9a10-efb21038d5e5"
ENDPOINT_GET_PROFILE = "https://n8n.air.com.vc/webhook-test/5246e807-0d6a-44aa-935a-88a26d831428"


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
