"""
Modulo para extracao de comentarios do Instagram via Instaloader
e classificacao via IA
"""

import instaloader
import requests
import time
import re
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable
import json


class ComentariosExtractor:
    """Classe para extrair e classificar comentarios do Instagram"""
    
    def __init__(self, webhook_url: str = None, username: str = None, password: str = None, session_file: str = None):
        """
        Inicializa o extrator
        
        Args:
            webhook_url: URL do webhook para classificacao via IA
            username: Usuario do Instagram para login (opcional)
            password: Senha do Instagram para login (opcional)
            session_file: Arquivo de sessao salva (opcional)
        """
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.webhook_url = webhook_url or "https://n8n.air.com.vc/webhook/classificar-comentarios"
        self.logged_in = False
        self.username = username
        
        # Tentar carregar sessao salva ou fazer login
        if session_file and os.path.exists(session_file):
            try:
                self.loader.load_session_from_file(username, session_file)
                self.logged_in = True
            except:
                pass
        elif username and password:
            self.login(username, password)
    
    def login(self, username: str, password: str, save_session: bool = True) -> Dict:
        """
        Faz login no Instagram
        
        Args:
            username: Usuario do Instagram
            password: Senha do Instagram
            save_session: Se deve salvar a sessao para uso futuro
            
        Returns:
            Dict com status do login
        """
        try:
            self.loader.login(username, password)
            self.logged_in = True
            self.username = username
            
            if save_session:
                # Salvar sessao em arquivo
                session_file = f".instaloader_session_{username}"
                self.loader.save_session_to_file(session_file)
            
            return {
                'sucesso': True,
                'mensagem': f'Login realizado com sucesso como @{username}'
            }
        except instaloader.exceptions.BadCredentialsException:
            return {
                'sucesso': False,
                'erro': 'Credenciais invalidas. Verifique usuario e senha.'
            }
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            return {
                'sucesso': False,
                'erro': 'Conta requer autenticacao de dois fatores. Desative temporariamente ou use uma conta sem 2FA.'
            }
        except instaloader.exceptions.ConnectionException as e:
            return {
                'sucesso': False,
                'erro': f'Erro de conexao: {str(e)}'
            }
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Erro ao fazer login: {str(e)}'
            }
    
    def logout(self):
        """Faz logout e limpa sessao"""
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True
        )
        self.logged_in = False
        self.username = None
    
    def carregar_sessao(self, username: str) -> Dict:
        """
        Carrega uma sessao salva anteriormente
        
        Args:
            username: Usuario da sessao salva
            
        Returns:
            Dict com status
        """
        session_file = f".instaloader_session_{username}"
        
        if not os.path.exists(session_file):
            return {
                'sucesso': False,
                'erro': f'Nenhuma sessao salva encontrada para @{username}'
            }
        
        try:
            self.loader.load_session_from_file(username, session_file)
            self.logged_in = True
            self.username = username
            return {
                'sucesso': True,
                'mensagem': f'Sessao carregada para @{username}'
            }
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Erro ao carregar sessao: {str(e)}'
            }
        
    def extrair_shortcode_do_link(self, link: str) -> Optional[str]:
        """
        Extrai o shortcode de um link do Instagram
        
        Exemplos de links suportados:
        - https://www.instagram.com/p/ABC123/
        - https://www.instagram.com/reel/ABC123/
        - https://instagram.com/p/ABC123/?utm_source=...
        
        Args:
            link: URL do post do Instagram
            
        Returns:
            Shortcode do post ou None se invalido
        """
        # Padroes para extrair shortcode
        patterns = [
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)
        
        return None
    
    def extrair_comentarios(self, link: str, limite: int = 100, 
                           progress_callback: Callable = None) -> Dict:
        """
        Extrai comentarios de um post do Instagram
        
        Args:
            link: URL do post
            limite: Numero maximo de comentarios a extrair
            progress_callback: Funcao chamada a cada comentario extraido
            
        Returns:
            Dict com informacoes do post e lista de comentarios
        """
        shortcode = self.extrair_shortcode_do_link(link)
        
        if not shortcode:
            return {
                'sucesso': False,
                'erro': 'Link invalido. Use um link de post do Instagram.',
                'comentarios': []
            }
        
        try:
            # Carregar o post
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Informacoes basicas do post
            resultado = {
                'sucesso': True,
                'shortcode': shortcode,
                'link': link,
                'owner': post.owner_username,
                'data_publicacao': post.date_utc.isoformat(),
                'caption': post.caption[:500] if post.caption else '',
                'likes': post.likes,
                'total_comentarios_post': post.comments,
                'logged_in': self.logged_in,
                'comentarios': []
            }
            
            # Extrair comentarios
            count = 0
            for comment in post.get_comments():
                if count >= limite:
                    break
                
                comentario = {
                    'id': str(comment.id),
                    'usuario': comment.owner.username,
                    'texto': comment.text,
                    'data': comment.created_at_utc.isoformat(),
                    'likes': comment.likes_count,
                    'respostas': []
                }
                
                # Extrair respostas (replies) se houver
                try:
                    for reply in comment.answers:
                        comentario['respostas'].append({
                            'id': str(reply.id),
                            'usuario': reply.owner.username,
                            'texto': reply.text,
                            'data': reply.created_at_utc.isoformat(),
                            'likes': reply.likes_count
                        })
                except:
                    pass  # Algumas contas podem nao permitir ver respostas
                
                resultado['comentarios'].append(comentario)
                count += 1
                
                if progress_callback:
                    progress_callback(count, limite)
                
                # Pequena pausa para evitar rate limit
                time.sleep(0.2)
            
            resultado['total_extraidos'] = len(resultado['comentarios'])
            return resultado
            
        except instaloader.exceptions.LoginRequiredException:
            return {
                'sucesso': False,
                'erro': 'Este perfil requer login. Configure uma conta do Instagram nas configuracoes.',
                'requer_login': True,
                'comentarios': []
            }
        except instaloader.exceptions.QueryReturnedNotFoundException:
            return {
                'sucesso': False,
                'erro': 'Post nao encontrado. Verifique o link.',
                'comentarios': []
            }
        except instaloader.exceptions.QueryReturnedBadRequestException:
            return {
                'sucesso': False,
                'erro': 'Requisicao bloqueada pelo Instagram. Aguarde alguns minutos ou faca login.',
                'comentarios': []
            }
        except instaloader.exceptions.ConnectionException as e:
            if "429" in str(e) or "rate" in str(e).lower():
                return {
                    'sucesso': False,
                    'erro': 'Limite de requisicoes atingido. Aguarde alguns minutos.',
                    'comentarios': []
                }
            return {
                'sucesso': False,
                'erro': f'Erro de conexao: {str(e)}',
                'comentarios': []
            }
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Erro ao extrair comentarios: {str(e)}',
                'comentarios': []
            }
    
    def classificar_comentarios(self, comentarios: List[Dict], 
                                categorias: List[str],
                                contexto_campanha: str = "",
                                progress_callback: Callable = None) -> List[Dict]:
        """
        Envia comentarios para classificacao via IA
        
        Args:
            comentarios: Lista de comentarios extraidos
            categorias: Lista de categorias para classificacao
            contexto_campanha: Contexto adicional sobre a campanha
            progress_callback: Funcao chamada a cada comentario classificado
            
        Returns:
            Lista de comentarios com classificacao adicionada
        """
        comentarios_classificados = []
        total = len(comentarios)
        
        for idx, comentario in enumerate(comentarios):
            try:
                payload = {
                    "acao": "classificar_comentario",
                    "comentario": {
                        "id": comentario.get('id'),
                        "texto": comentario.get('texto'),
                        "usuario": comentario.get('usuario'),
                        "likes": comentario.get('likes', 0)
                    },
                    "categorias": categorias,
                    "contexto": contexto_campanha,
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    resultado = response.json()
                    
                    # Extrair classificacao da resposta
                    classificacao = extrair_classificacao_resposta(resultado)
                    
                    comentario_classificado = {
                        **comentario,
                        'categoria': classificacao.get('categoria', 'Nao Classificado'),
                        'sentimento': classificacao.get('sentimento', 'neutro'),
                        'confianca': classificacao.get('confianca', 0),
                        'justificativa': classificacao.get('justificativa', '')
                    }
                else:
                    comentario_classificado = {
                        **comentario,
                        'categoria': 'Erro',
                        'sentimento': 'neutro',
                        'confianca': 0,
                        'justificativa': f'Erro HTTP {response.status_code}'
                    }
                    
            except requests.exceptions.Timeout:
                comentario_classificado = {
                    **comentario,
                    'categoria': 'Erro',
                    'sentimento': 'neutro',
                    'confianca': 0,
                    'justificativa': 'Timeout na requisicao'
                }
            except Exception as e:
                comentario_classificado = {
                    **comentario,
                    'categoria': 'Erro',
                    'sentimento': 'neutro',
                    'confianca': 0,
                    'justificativa': str(e)
                }
            
            comentarios_classificados.append(comentario_classificado)
            
            if progress_callback:
                progress_callback(idx + 1, total)
            
            # Pausa entre requisicoes
            time.sleep(0.5)
        
        return comentarios_classificados
    
    def classificar_lote(self, comentarios: List[Dict],
                         categorias: List[str],
                         contexto_campanha: str = "",
                         tamanho_lote: int = 10) -> Dict:
        """
        Classifica comentarios em lotes (mais eficiente)
        
        Args:
            comentarios: Lista de comentarios
            categorias: Categorias para classificacao
            contexto_campanha: Contexto da campanha
            tamanho_lote: Quantos comentarios por requisicao
            
        Returns:
            Dict com comentarios classificados e estatisticas
        """
        try:
            payload = {
                "acao": "classificar_lote",
                "comentarios": [
                    {
                        "id": c.get('id'),
                        "texto": c.get('texto'),
                        "usuario": c.get('usuario'),
                        "likes": c.get('likes', 0)
                    }
                    for c in comentarios[:tamanho_lote]
                ],
                "categorias": categorias,
                "contexto": contexto_campanha,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=120,  # Timeout maior para lote
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                resultado = response.json()
                return extrair_classificacoes_lote(resultado, comentarios)
            else:
                return {
                    'sucesso': False,
                    'erro': f'Erro HTTP {response.status_code}',
                    'comentarios': comentarios
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'comentarios': comentarios
            }


def extrair_classificacao_resposta(resultado) -> Dict:
    """Extrai classificacao da resposta do webhook"""
    # Formato esperado: [{"output": {"classificacao": {...}}}]
    # ou {"classificacao": {...}}
    
    try:
        if isinstance(resultado, list) and len(resultado) > 0:
            primeiro = resultado[0]
            if isinstance(primeiro, dict):
                if 'output' in primeiro:
                    return primeiro['output'].get('classificacao', {})
                elif 'classificacao' in primeiro:
                    return primeiro['classificacao']
        elif isinstance(resultado, dict):
            if 'output' in resultado:
                return resultado['output'].get('classificacao', {})
            elif 'classificacao' in resultado:
                return resultado['classificacao']
    except:
        pass
    
    return {}


def extrair_classificacoes_lote(resultado, comentarios_originais) -> Dict:
    """Extrai classificacoes de lote da resposta do webhook"""
    try:
        classificacoes = []
        
        if isinstance(resultado, list) and len(resultado) > 0:
            primeiro = resultado[0]
            if isinstance(primeiro, dict):
                if 'output' in primeiro and 'classificacoes' in primeiro['output']:
                    classificacoes = primeiro['output']['classificacoes']
                elif 'classificacoes' in primeiro:
                    classificacoes = primeiro['classificacoes']
        elif isinstance(resultado, dict):
            if 'output' in resultado and 'classificacoes' in resultado['output']:
                classificacoes = resultado['output']['classificacoes']
            elif 'classificacoes' in resultado:
                classificacoes = resultado['classificacoes']
        
        # Mesclar classificacoes com comentarios originais
        comentarios_classificados = []
        for i, comentario in enumerate(comentarios_originais):
            if i < len(classificacoes):
                classif = classificacoes[i]
                comentarios_classificados.append({
                    **comentario,
                    'categoria': classif.get('categoria', 'Nao Classificado'),
                    'sentimento': classif.get('sentimento', 'neutro'),
                    'confianca': classif.get('confianca', 0),
                    'justificativa': classif.get('justificativa', '')
                })
            else:
                comentarios_classificados.append({
                    **comentario,
                    'categoria': 'Nao Classificado',
                    'sentimento': 'neutro',
                    'confianca': 0,
                    'justificativa': ''
                })
        
        return {
            'sucesso': True,
            'comentarios': comentarios_classificados,
            'total': len(comentarios_classificados)
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'comentarios': comentarios_originais
        }


def gerar_estatisticas(comentarios_classificados: List[Dict]) -> Dict:
    """
    Gera estatisticas dos comentarios classificados
    
    Args:
        comentarios_classificados: Lista de comentarios com classificacao
        
    Returns:
        Dict com estatisticas por categoria e sentimento
    """
    total = len(comentarios_classificados)
    
    # Contagem por categoria
    por_categoria = {}
    for c in comentarios_classificados:
        cat = c.get('categoria', 'Nao Classificado')
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
    
    # Contagem por sentimento
    por_sentimento = {
        'positivo': 0,
        'neutro': 0,
        'negativo': 0
    }
    for c in comentarios_classificados:
        sent = c.get('sentimento', 'neutro')
        if sent in por_sentimento:
            por_sentimento[sent] += 1
    
    # Calcular percentuais
    estatisticas = {
        'total': total,
        'por_categoria': {
            cat: {
                'quantidade': qtd,
                'percentual': round(qtd / total * 100, 1) if total > 0 else 0
            }
            for cat, qtd in por_categoria.items()
        },
        'por_sentimento': {
            sent: {
                'quantidade': qtd,
                'percentual': round(qtd / total * 100, 1) if total > 0 else 0
            }
            for sent, qtd in por_sentimento.items()
        },
        'media_confianca': round(
            sum(c.get('confianca', 0) for c in comentarios_classificados) / total, 2
        ) if total > 0 else 0
    }
    
    return estatisticas
