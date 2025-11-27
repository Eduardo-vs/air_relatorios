"""
API Client - Integração com endpoints externos
"""

import requests
from typing import List, Dict, Optional
import streamlit as st

# URLs dos endpoints
ENDPOINT_GET_PROFILE_ID = "https://n8n.air.com.vc/webhook/2e7956e8-2f15-497d-9a10-efb21038d5e5"
ENDPOINT_GET_PROFILE = "https://n8n.air.com.vc/webhook-test/5246e807-0d6a-44aa-935a-88a26d831428"

def buscar_profile_id(username: str, network: str) -> Dict:
    """
    Busca o ID do perfil baseado no username e rede social
    
    Args:
        username: Nome de usuário (sem @)
        network: Rede social (instagram, tiktok, youtube)
    
    Returns:
        Dados do perfil incluindo profile_id
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
            return data[0]
        return data
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def buscar_profiles_batch(usernames: List[Dict[str, str]]) -> List[Dict]:
    """
    Busca múltiplos perfis de uma vez
    
    Args:
        usernames: Lista de dicts com 'username' e 'network'
    
    Returns:
        Lista de resultados
    """
    results = []
    
    for item in usernames:
        result = buscar_profile_id(item['username'], item['network'])
        results.append({
            'username': item['username'],
            'network': item['network'],
            'result': result
        })
    
    return results


def buscar_perfil_completo(profile_ids: List[str]) -> Dict:
    """
    Busca dados completos de perfis pelo ID
    
    Args:
        profile_ids: Lista de IDs de perfil
    
    Returns:
        Dados completos dos perfis
    """
    try:
        payload = {"profiles": profile_ids}
        
        response = requests.post(ENDPOINT_GET_PROFILE, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "items": []}
    except Exception as e:
        return {"error": str(e), "items": []}


def processar_dados_influenciador(api_data: Dict) -> Dict:
    """
    Processa dados da API para formato interno do sistema
    
    Args:
        api_data: Dados brutos da API
    
    Returns:
        Dados formatados para o sistema
    """
    if not api_data or 'extra_information' not in api_data:
        return None
    
    extra = api_data.get('extra_information', {})
    profile = extra.get('profile', {})
    
    # Converter seguidores para formato legível
    followers = profile.get('followers', 0)
    if followers >= 1000000:
        base_seguidores = f"{followers/1000000:.1f}M"
    elif followers >= 1000:
        base_seguidores = f"{followers/1000:.0f}K"
    else:
        base_seguidores = str(followers)
    
    # Calcular taxa de engajamento
    means = profile.get('means', {})
    engagement_rate = profile.get('engagement_rate', 0)
    
    return {
        'profile_id': extra.get('profile_id'),
        'nome': profile.get('name', ''),
        'usuario': f"@{profile.get('username', '')}",
        'redes_sociais': [profile.get('network', 'instagram').capitalize()],
        'base_seguidores': base_seguidores,
        'seguidores_num': followers,
        'perfil_link': '',  # Construir baseado na rede
        'taxa_engajamento': round(engagement_rate * 100, 2) if engagement_rate < 1 else round(engagement_rate, 2),
        'cidade': '',
        'endereco': '',
        'foto': profile.get('picture', ''),
        'score': profile.get('score', 0),
        'means': means,
        'hashtags': profile.get('hashtags', [])
    }


def processar_perfil_completo(api_data: Dict) -> Dict:
    """
    Processa dados completos do perfil
    
    Args:
        api_data: Dados brutos da API de perfil completo
    
    Returns:
        Dados formatados
    """
    items = api_data.get('items', [])
    
    if not items:
        return None
    
    profile = items[0]
    
    followers = profile.get('counters', {}).get('followers', 0)
    if followers >= 1000000:
        base_seguidores = f"{followers/1000000:.1f}M"
    elif followers >= 1000:
        base_seguidores = f"{followers/1000:.0f}K"
    else:
        base_seguidores = str(followers)
    
    counters = profile.get('counters', {})
    
    return {
        'profile_id': profile.get('id'),
        'nome': profile.get('name', ''),
        'usuario': f"@{profile.get('username', '')}",
        'foto': profile.get('picture', ''),
        'bio': profile.get('bio', ''),
        'redes_sociais': [profile.get('network', 'instagram').capitalize()],
        'base_seguidores': base_seguidores,
        'seguidores_num': followers,
        'engagement_rate': profile.get('engagement_rate', 0),
        'reach_rate': profile.get('reach_rate', 0),
        'score': profile.get('score', 0),
        'counters': counters,
        'network': profile.get('network', 'instagram')
    }
