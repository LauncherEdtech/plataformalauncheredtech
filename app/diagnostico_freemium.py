#!/usr/bin/env python3
"""
Diagnóstico Completo do Sistema Freemium
Verifica todos os arquivos, integrações e possíveis erros
"""

import os
import sys
from pathlib import Path

class FreemiumDiagnostico:
    def __init__(self, base_path="/home/launchercursos/launcheredit/launcher-app"):
        self.base_path = Path(base_path)
        self.erros = []
        self.avisos = []
        self.ok = []
        
    def print_header(self, texto):
        print(f"\n{'='*70}")
        print(f"  {texto}")
        print('='*70)
    
    def verificar_arquivo(self, caminho_relativo, obrigatorio=True):
        """Verifica se arquivo existe e retorna seu tamanho"""
        caminho = self.base_path / caminho_relativo
        
        if caminho.exists():
            tamanho = caminho.stat().st_size
            self.ok.append(f"✅ {caminho_relativo} ({tamanho} bytes)")
            return True, tamanho
        else:
            if obrigatorio:
                self.erros.append(f"❌ {caminho_relativo} NÃO EXISTE (obrigatório)")
            else:
                self.avisos.append(f"⚠️  {caminho_relativo} não existe (opcional)")
            return False, 0
    
    def verificar_conteudo(self, caminho_relativo, texto_busca, nome_verificacao):
        """Verifica se arquivo contém determinado texto"""
        caminho = self.base_path / caminho_relativo
        
        if not caminho.exists():
            return False
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            if texto_busca in conteudo:
                self.ok.append(f"✅ {nome_verificacao}: encontrado em {caminho_relativo}")
                return True
            else:
                self.erros.append(f"❌ {nome_verificacao}: NÃO encontrado em {caminho_relativo}")
                return False
        except Exception as e:
            self.erros.append(f"❌ Erro ao ler {caminho_relativo}: {e}")
            return False
    
    def verificar_sintaxe_js(self, caminho_relativo):
        """Verifica sintaxe básica do JavaScript"""
        caminho = self.base_path / caminho_relativo
        
        if not caminho.exists():
            return False
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Verificações básicas
            problemas = []
            
            # 1. Verificar se tem conteúdo
            if len(conteudo.strip()) == 0:
                problemas.append("Arquivo vazio")
            
            # 2. Verificar balanceamento de chaves
            if conteudo.count('{') != conteudo.count('}'):
                problemas.append(f"Chaves desbalanceadas: { conteudo.count('{') } {{ vs { conteudo.count('}') } }}")
            
            # 3. Verificar balanceamento de parênteses
            if conteudo.count('(') != conteudo.count(')'):
                problemas.append(f"Parênteses desbalanceados: { conteudo.count('(') } ( vs { conteudo.count(')') } )")
            
            # 4. Verificar se tem as funções essenciais
            funcoes_essenciais = [
                'FreemiumHandler',
                'init',
                'detectarFlashMessages',
                'checkSpecificLimit',
                'testarModal'
            ]
            
            for funcao in funcoes_essenciais:
                if funcao not in conteudo:
                    problemas.append(f"Função '{funcao}' não encontrada")
            
            if problemas:
                for p in problemas:
                    self.erros.append(f"❌ JS {caminho_relativo}: {p}")
                return False
            else:
                self.ok.append(f"✅ Sintaxe JS OK em {caminho_relativo}")
                return True
                
        except Exception as e:
            self.erros.append(f"❌ Erro ao verificar JS {caminho_relativo}: {e}")
            return False
    
    def verificar_modelo_user(self):
        """Verifica se User model tem campos freemium"""
        campos_necessarios = [
            'redacoes_gratuitas_restantes',
            'simulados_gratuitos_restantes',
            'aulas_gratuitas_restantes',
            'plano_ativo',
            'pode_fazer_redacao',
            'pode_fazer_simulado',
            'pode_assistir_aula'
        ]
        
        existe, _ = self.verificar_arquivo('app/models/user.py')
        if not existe:
            return False
        
        todos_ok = True
        for campo in campos_necessarios:
            if not self.verificar_conteudo('app/models/user.py', campo, f"Campo User.{campo}"):
                todos_ok = False
        
        return todos_ok
    
    def verificar_blueprint_registrado(self):
        """Verifica se blueprint da API está registrado"""
        return self.verificar_conteudo(
            'app/__init__.py',
            'api_freemium_bp',
            'Blueprint api_freemium_bp registrado'
        )
    
    def diagnostico_completo(self):
        """Executa diagnóstico completo"""
        
        self.print_header("🔍 DIAGNÓSTICO DO SISTEMA FREEMIUM")
        
        # 1. Arquivos essenciais
        print("\n1️⃣ Verificando arquivos essenciais...")
        self.verificar_arquivo('app/templates/components/freemium_modal.html', obrigatorio=True)
        self.verificar_arquivo('app/static/js/freemium-handler.js', obrigatorio=True)
        self.verificar_arquivo('app/routes/api_freemium.py', obrigatorio=True)
        self.verificar_arquivo('app/decorators/freemium.py', obrigatorio=True)
        self.verificar_arquivo('app/models/user.py', obrigatorio=True)
        
        # 2. Include no layout
        print("\n2️⃣ Verificando includes no layout.html...")
        self.verificar_conteudo(
            'app/templates/layout.html',
            'freemium_modal.html',
            'Include do modal'
        )
        self.verificar_conteudo(
            'app/templates/layout.html',
            'freemium-handler.js',
            'Script freemium-handler.js'
        )
        
        # 3. Sintaxe JavaScript
        print("\n3️⃣ Verificando sintaxe JavaScript...")
        self.verificar_sintaxe_js('app/static/js/freemium-handler.js')
        
        # 4. Modelo User
        print("\n4️⃣ Verificando modelo User...")
        self.verificar_modelo_user()
        
        # 5. Blueprint registrado
        print("\n5️⃣ Verificando registro de blueprints...")
        self.verificar_blueprint_registrado()
        
        # 6. API endpoints
        print("\n6️⃣ Verificando endpoints da API...")
        endpoints = [
            ('/status', 'Endpoint /api/freemium/status'),
            ('/verificar/<tipo>', 'Endpoint /api/freemium/verificar'),
        ]
        
        for endpoint, nome in endpoints:
            self.verificar_conteudo('app/routes/api_freemium.py', endpoint, nome)
        
        # 7. Verificar se freemium-handler.js tem window.testarModal
        print("\n7️⃣ Verificando função testarModal...")
        self.verificar_conteudo(
            'app/static/js/freemium-handler.js',
            'window.testarModal',
            'Função window.testarModal'
        )
        
        # 8. Verificar linha do script no layout
        print("\n8️⃣ Verificando caminho do script no layout...")
        caminho = self.base_path / 'app/templates/layout.html'
        if caminho.exists():
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            script_encontrado = False
            for i, linha in enumerate(linhas, 1):
                if 'freemium-handler.js' in linha:
                    script_encontrado = True
                    print(f"   Linha {i}: {linha.strip()}")
                    
                    # Verificar se está DEPOIS do modal
                    modal_antes = False
                    for j in range(max(0, i-20), i):
                        if 'freemium_modal.html' in linhas[j]:
                            modal_antes = True
                            break
                    
                    if modal_antes:
                        self.ok.append("✅ Script está DEPOIS do include do modal (correto)")
                    else:
                        self.erros.append("❌ Script está ANTES do include do modal (deve estar depois)")
            
            if not script_encontrado:
                self.erros.append("❌ Script freemium-handler.js não encontrado no layout.html")
        
        # RESULTADOS
        self.print_header("📊 RESULTADOS")
        
        print(f"\n✅ SUCESSOS ({len(self.ok)}):")
        for item in self.ok:
            print(f"  {item}")
        
        if self.avisos:
            print(f"\n⚠️  AVISOS ({len(self.avisos)}):")
            for item in self.avisos:
                print(f"  {item}")
        
        if self.erros:
            print(f"\n❌ ERROS ({len(self.erros)}):")
            for item in self.erros:
                print(f"  {item}")
            
            print("\n" + "="*70)
            print("🔧 AÇÕES NECESSÁRIAS:")
            print("="*70)
            
            if any('freemium-handler.js' in erro for erro in self.erros):
                print("\n1. Verificar freemium-handler.js:")
                print("   cd ~/launcheredit/launcher-app")
                print("   cat app/static/js/freemium-handler.js | head -20")
                print("   # Verificar se arquivo não está vazio/corrompido")
            
            if any('testarModal' in erro for erro in self.erros):
                print("\n2. Função testarModal faltando:")
                print("   # Substituir freemium-handler.js pelo arquivo correto")
            
            if any('Script está ANTES' in erro for erro in self.erros):
                print("\n3. Ordem incorreta no layout.html:")
                print("   # O script deve vir DEPOIS do include do modal")
                print("   # Correto:")
                print("   #   {% include 'components/freemium_modal.html' %}")
                print("   #   <script src='... freemium-handler.js'></script>")
            
            return False
        else:
            print("\n" + "="*70)
            print("🎉 TUDO OK! Sistema freemium configurado corretamente!")
            print("="*70)
            print("\n📝 Teste no navegador:")
            print("   1. Abrir Console (F12)")
            print("   2. Digite: testarModal('aula')")
            print("   3. Popup deve aparecer!")
            return True

if __name__ == '__main__':
    # Detectar base_path
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Tentar detectar automaticamente
        possiveis = [
            '/home/launchercursos/launcheredit/launcher-app',
            '~/launcheredit/launcher-app',
            './launcher-app',
            '.'
        ]
        
        base_path = None
        for caminho in possiveis:
            caminho_expandido = os.path.expanduser(caminho)
            if os.path.exists(os.path.join(caminho_expandido, 'app')):
                base_path = caminho_expandido
                break
        
        if not base_path:
            print("❌ Não foi possível detectar o diretório da aplicação")
            print("Use: python diagnostico_freemium.py /caminho/para/launcher-app")
            sys.exit(1)
    
    print(f"📂 Base path: {base_path}")
    
    diag = FreemiumDiagnostico(base_path)
    sucesso = diag.diagnostico_completo()
    
    sys.exit(0 if sucesso else 1)
