# app/services/yampi_service.py

import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class YampiService:
    """Serviço para integração com API da Yampi"""
    
    def __init__(self):
        # Credenciais da Yampi
        self.token = 'WnUywC0wcNGFWFlSn6UelW1VqNBOnnfidkczUhkw'
        self.secret = 'sk_shYPIoIJ6qasmxlnykpxJsROJwTU8aMZ1jzee'
        self.alias = 'plataforma-launcher-shop'
        self.base_url = f'https://api.yampi.io/v2/merchant/{self.alias}'
        
        self.headers = {
            'User-Token': self.token,
            'User-Secret-Key': self.secret,
            'Content-Type': 'application/json'
        }
    
    def gerar_link_checkout(self, produto_sku, percentual_desconto, user_email, purchase_url=None):
        """
        Gera link de checkout da Yampi com desconto.
        
        IMPORTANTE: Prioriza o uso do purchase_url que já vem da API da Yampi.
        Apenas tenta criar carrinho via API se o purchase_url não existir.
        
        Args:
            produto_sku: SKU do produto na Yampi
            percentual_desconto: Percentual de desconto (ex: 50 para 50%)
            user_email: Email do usuário
            purchase_url: URL de compra direto da Yampi (PREFERENCIAL)
            
        Returns:
            str: URL de checkout da Yampi (formato: https://alias.pay.yampi.com.br/r/XXXXXX)
        """
        try:
            logger.info(f"🔗 Gerando link checkout Yampi para SKU: {produto_sku}")
            
            # ===== MÉTODO 0: USAR PURCHASE_URL SE DISPONÍVEL (MAIS SIMPLES E CONFIÁVEL) =====
            if purchase_url and purchase_url.strip():
                logger.info(f"✅ Usando purchase_url direto da Yampi: {purchase_url}")
                return purchase_url
            
            # ===== MÉTODO 1: Criar pedido via API e obter link de pagamento =====
            logger.info("⚠️ Purchase URL não disponível, tentando criar via API...")
            
            payload = {
                "customer": {
                    "email": user_email
                },
                "items": [
                    {
                        "sku_code": produto_sku,
                        "quantity": 1
                    }
                ]
            }
            
            # Se houver desconto, adicionar cupom
            if percentual_desconto and percentual_desconto > 0:
                payload["coupon_code"] = f"LAUNCHER{percentual_desconto}"
            
            # Fazer request para criar o pedido/carrinho
            response = requests.post(
                f"{self.base_url}/carts",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Verificar se tem o link de pagamento no response
                if 'data' in data and 'payment_url' in data['data']:
                    payment_url = data['data']['payment_url']
                    logger.info(f"✅ Link Yampi gerado via API: {payment_url}")
                    return payment_url
                
                # Se não tiver payment_url, tentar shortlink
                if 'data' in data and 'shortlink' in data['data']:
                    shortlink = data['data']['shortlink']
                    logger.info(f"✅ Shortlink Yampi gerado via API: {shortlink}")
                    return shortlink
                
                # Fallback: construir URL manualmente se tiver o token
                if 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    fallback_url = f"https://{self.alias}.pay.yampi.com.br/r/{token}"
                    logger.info(f"✅ URL Yampi construída via API: {fallback_url}")
                    return fallback_url
            
            # Se a API falhar, usar método alternativo: URL direta com parâmetros
            logger.warning(f"⚠️ API Yampi retornou {response.status_code}, usando URL direta")
            
            # ===== MÉTODO 2: URL direta com parâmetros (fallback) =====
            params = {
                'sku': produto_sku,
                'quantity': 1
            }
            
            if user_email:
                params['email'] = user_email
            
            if percentual_desconto and percentual_desconto > 0:
                params['discount'] = percentual_desconto
            
            url_direta = f"https://{self.alias}.pay.yampi.com.br/checkout?{urlencode(params)}"
            logger.info(f"✅ URL direta Yampi: {url_direta}")
            return url_direta
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao chamar API Yampi: {e}")
            
            # Em caso de erro, retornar URL direta básica
            url_basica = f"https://{self.alias}.pay.yampi.com.br/checkout?sku={produto_sku}&quantity=1"
            if percentual_desconto:
                url_basica += f"&discount={percentual_desconto}"
            
            logger.warning(f"⚠️ Usando URL básica: {url_basica}")
            return url_basica
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar link: {e}")
            
            # Última tentativa: URL mais simples possível
            url_emergencia = f"https://{self.alias}.pay.yampi.com.br"
            logger.error(f"⚠️ Usando URL de emergência: {url_emergencia}")
            return url_emergencia
    
    def validar_cupom(self, codigo_cupom):
        """Valida se um cupom existe e está ativo"""
        try:
            response = requests.get(
                f"{self.base_url}/coupons/{codigo_cupom}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('active', False)
            
            return False
        except Exception as e:
            logger.error(f"Erro ao validar cupom: {e}")
            return False
    
    def buscar_produto(self, sku):
        """Busca informações de um produto pelo SKU"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                params={'sku': sku},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                produtos = data.get('data', [])
                if produtos:
                    return produtos[0]
            
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar produto: {e}")
            return None


# Instância singleton do serviço
_yampi_service_instance = None

def get_yampi_service():
    """Retorna instância singleton do serviço Yampi"""
    global _yampi_service_instance
    
    if _yampi_service_instance is None:
        _yampi_service_instance = YampiService()
        logger.info("✅ YampiService inicializado")
    
    return _yampi_service_instance
