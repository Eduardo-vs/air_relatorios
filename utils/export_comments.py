"""
Modulo de integracao com ExportComments.com API
Para extracao de comentarios do Instagram e outras plataformas
"""

import os
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime


class ExportCommentsClient:
    """Cliente para API do ExportComments.com"""
    
    BASE_URL = "https://exportcomments.com"
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o cliente
        
        Args:
            api_key: Token de API do ExportComments (ou usa variavel de ambiente)
        """
        self.api_key = api_key or os.getenv('EXPORTCOMMENTS_API_KEY', '')
        self.headers = {
            'X-AUTH-TOKEN': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def set_api_key(self, api_key: str):
        """Define o token de API"""
        self.api_key = api_key
        self.headers['X-AUTH-TOKEN'] = api_key
    
    def ping(self) -> Dict:
        """
        Verifica se a API esta funcionando e se o token e valido
        
        Returns:
            Dict com status da conexao
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v1/ping",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Conexao OK"}
            elif response.status_code == 401:
                return {"success": False, "error": "Token de API invalido"}
            else:
                return {"success": False, "error": f"Erro {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_user_info(self) -> Dict:
        """
        Retorna informacoes do usuario e creditos disponiveis
        
        Returns:
            Dict com dados do usuario
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v1/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Erro {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def create_export_job(self, url: str, instagram_session_id: str = None, 
                          replies: bool = True, options: Dict = None) -> Dict:
        """
        Cria um job de exportacao de comentarios
        
        Args:
            url: URL do post (Instagram, TikTok, YouTube, etc)
            instagram_session_id: Cookie sessionid do Instagram (opcional, para posts privados)
            replies: Se deve incluir respostas aos comentarios
            options: Opcoes adicionais (vpn, pool, etc)
        
        Returns:
            Dict com guid do job criado
        """
        try:
            payload = {
                "url": url,
                "replies": replies
            }
            
            # Adicionar cookie do Instagram se fornecido
            if instagram_session_id:
                payload["sessionid"] = instagram_session_id
            
            # Adicionar opcoes extras
            if options:
                payload["options"] = options
            
            response = requests.post(
                f"{self.BASE_URL}/api/v3/job",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True, 
                    "guid": data.get('guid') or data.get('id'),
                    "status": data.get('status', 'processing'),
                    "data": data
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token de API invalido"}
            elif response.status_code == 402:
                return {"success": False, "error": "Creditos insuficientes"}
            elif response.status_code == 422:
                return {"success": False, "error": "URL invalida ou nao suportada"}
            else:
                error_msg = response.text[:200] if response.text else f"Erro {response.status_code}"
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_job_status(self, guid: str) -> Dict:
        """
        Verifica o status de um job de exportacao
        
        Args:
            guid: ID do job
        
        Returns:
            Dict com status e dados do job
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v3/job/{guid}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get('status'),
                    "comments_count": data.get('comments_count', 0),
                    "download_url": data.get('download_url'),
                    "error_message": data.get('error_message'),
                    "data": data
                }
            elif response.status_code == 404:
                return {"success": False, "error": "Job nao encontrado"}
            else:
                return {"success": False, "error": f"Erro {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def wait_for_job(self, guid: str, timeout: int = 300, poll_interval: int = 5,
                     progress_callback=None) -> Dict:
        """
        Aguarda um job finalizar (polling)
        
        Args:
            guid: ID do job
            timeout: Tempo maximo de espera em segundos
            poll_interval: Intervalo entre verificacoes em segundos
            progress_callback: Funcao callback para reportar progresso (opcional)
        
        Returns:
            Dict com resultado final do job
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                return {"success": False, "error": "Timeout - job demorou demais"}
            
            status_result = self.get_job_status(guid)
            
            if not status_result.get('success'):
                return status_result
            
            status = status_result.get('status')
            
            if progress_callback:
                progress_callback(status, elapsed, status_result.get('comments_count', 0))
            
            if status == 'done':
                return status_result
            elif status == 'failed':
                return {
                    "success": False, 
                    "error": status_result.get('error_message', 'Job falhou'),
                    "data": status_result.get('data')
                }
            elif status in ['processing', 'queued', 'pending']:
                time.sleep(poll_interval)
            else:
                # Status desconhecido, continuar esperando
                time.sleep(poll_interval)
    
    def download_comments(self, download_url: str) -> Dict:
        """
        Baixa os comentarios de um job finalizado
        
        Args:
            download_url: URL de download retornada pelo job
        
        Returns:
            Dict com lista de comentarios
        """
        try:
            response = requests.get(download_url, timeout=60)
            
            if response.status_code == 200:
                # Tentar parsear como JSON
                try:
                    data = response.json()
                    
                    # Extrair comentarios do formato retornado
                    comentarios = []
                    
                    if isinstance(data, list):
                        comentarios = data
                    elif isinstance(data, dict):
                        comentarios = data.get('comments', []) or data.get('data', []) or []
                    
                    return {"success": True, "comentarios": comentarios, "total": len(comentarios)}
                    
                except ValueError:
                    # Se nao for JSON, pode ser CSV
                    return {"success": True, "raw_data": response.text, "format": "csv"}
            else:
                return {"success": False, "error": f"Erro ao baixar: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def extract_comments(self, url: str, instagram_session_id: str = None,
                        timeout: int = 300, progress_callback=None) -> Dict:
        """
        Metodo completo: cria job, aguarda e retorna comentarios
        
        Args:
            url: URL do post
            instagram_session_id: Cookie sessionid do Instagram (opcional)
            timeout: Tempo maximo de espera
            progress_callback: Callback para progresso
        
        Returns:
            Dict com lista de comentarios processados
        """
        # 1. Criar job
        job_result = self.create_export_job(url, instagram_session_id)
        
        if not job_result.get('success'):
            return job_result
        
        guid = job_result.get('guid')
        
        if not guid:
            return {"success": False, "error": "Job criado mas sem GUID"}
        
        # 2. Aguardar finalizacao
        wait_result = self.wait_for_job(guid, timeout, progress_callback=progress_callback)
        
        if not wait_result.get('success'):
            return wait_result
        
        download_url = wait_result.get('download_url')
        
        if not download_url:
            return {"success": False, "error": "Job finalizado mas sem URL de download"}
        
        # 3. Baixar comentarios
        download_result = self.download_comments(download_url)
        
        if not download_result.get('success'):
            return download_result
        
        # 4. Processar comentarios para formato padrao do sistema
        comentarios_raw = download_result.get('comentarios', [])
        comentarios_processados = []
        
        for c in comentarios_raw:
            # Usar nomes de campos compativeis com o sistema existente
            comentario = {
                'usuario': c.get('username') or c.get('author') or c.get('user', {}).get('username', 'Anonimo'),
                'autor': c.get('username') or c.get('author') or c.get('user', {}).get('username', 'Anonimo'),
                'texto': c.get('text') or c.get('comment') or c.get('content', ''),
                'data': c.get('date') or c.get('created_at') or c.get('timestamp', ''),
                'likes': c.get('likes') or c.get('like_count', 0),
                'respostas': c.get('replies_count') or c.get('reply_count', 0),
                'id': c.get('id') or c.get('comment_id', ''),
                'is_reply': c.get('is_reply', False) or c.get('parent_id') is not None,
                'raw': c  # Dados originais para debug
            }
            comentarios_processados.append(comentario)
        
        return {
            "success": True,
            "comentarios": comentarios_processados,
            "total": len(comentarios_processados),
            "job_guid": guid
        }
    
    def get_jobs_history(self, limit: int = 20) -> Dict:
        """
        Lista jobs anteriores
        
        Args:
            limit: Numero maximo de jobs a retornar
        
        Returns:
            Dict com lista de jobs
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v3/jobs",
                headers=self.headers,
                params={"limit": limit},
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "jobs": response.json()}
            else:
                return {"success": False, "error": f"Erro {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}


# Instancia global para uso facil
export_comments_client = ExportCommentsClient()


def extrair_comentarios_instagram(url: str, api_key: str = None, 
                                   session_id: str = None,
                                   progress_callback=None) -> Dict:
    """
    Funcao helper para extrair comentarios do Instagram
    
    Args:
        url: URL do post do Instagram
        api_key: Token da API (opcional se ja configurado)
        session_id: Cookie sessionid do Instagram (opcional)
        progress_callback: Callback para progresso
    
    Returns:
        Dict com comentarios
    """
    client = ExportCommentsClient(api_key) if api_key else export_comments_client
    
    return client.extract_comments(
        url=url,
        instagram_session_id=session_id,
        progress_callback=progress_callback
    )


def verificar_api_key(api_key: str) -> Dict:
    """
    Verifica se um token de API e valido
    
    Args:
        api_key: Token a verificar
    
    Returns:
        Dict com resultado da verificacao
    """
    client = ExportCommentsClient(api_key)
    
    # Primeiro testa o ping
    ping_result = client.ping()
    
    if not ping_result.get('success'):
        return ping_result
    
    # Depois busca info do usuario para confirmar
    user_result = client.get_user_info()
    
    if user_result.get('success'):
        user_data = user_result.get('data', {})
        return {
            "success": True,
            "message": "Token valido",
            "email": user_data.get('email'),
            "credits": user_data.get('credits', user_data.get('balance', 'N/A'))
        }
    
    return {"success": True, "message": "Token valido (sem info de usuario)"}
