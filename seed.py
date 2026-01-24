# shop_seed.py
from app import create_app, db
from app.models.shop import Produto, Categoria, Resgate
import json
from datetime import datetime, timedelta
import random

def popular_shop():
    """
    Popula o banco de dados com categorias e produtos iniciais para a loja.
    Execute este script para criar os dados iniciais da loja.
    """
    app = create_app()
    
    with app.app_context():
        # Verificar se já existem categorias cadastradas
        if Categoria.query.count() > 0:
            print("Categorias já existem, pulando criação.")
            return
        
        print("[+] Criando categorias para a loja...")
        
        # Criar categorias
        categorias = [
            {
                'nome': 'Vestuário',
                'slug': 'vestuario',
                'descricao': 'Camisetas, moletons e outros itens de vestuário da Plataforma Launcher.'
            },
            {
                'nome': 'Acessórios',
                'slug': 'acessorios',
                'descricao': 'Acessórios diversos como canecas, garrafas, cadernos e mais.'
            },
            {
                'nome': 'Eletrônicos',
                'slug': 'eletronicos',
                'descricao': 'Gadgets e acessórios eletrônicos para otimizar seus estudos.'
            },
            {
                'nome': 'Edição Limitada',
                'slug': 'limitado',
                'descricao': 'Itens exclusivos disponíveis por tempo limitado. Não perca!'
            }
        ]
        
        # Inserir categorias no banco
        categorias_obj = {}
        for cat_data in categorias:
            categoria = Categoria(
                nome=cat_data['nome'],
                slug=cat_data['slug'],
                descricao=cat_data['descricao']
            )
            db.session.add(categoria)
            categorias_obj[cat_data['slug']] = categoria
        
        db.session.commit()
        print(f"[+] {len(categorias)} categorias criadas com sucesso!")
        
        print("[+] Criando produtos para a loja...")
        
        # Criar produtos
        produtos = [
            {
                'nome': 'Camisa Launcher',
                'descricao': 'Camisa oficial da Plataforma Launcher. Perfeita para mostrar seu compromisso com os estudos.',
                'descricao_detalhada': '''
                # Camisa Oficial Launcher
                
                A Camisa Launcher é perfeita para quem quer mostrar seu compromisso com os estudos e com a comunidade Launcher. Produzida com tecido de alta qualidade (100% algodão), proporciona conforto durante todo o dia.
                
                ## Características:
                
                - Material: 100% algodão
                - Estampa oficial da Plataforma Launcher
                - Disponível em vários tamanhos
                - Lavagem: Lavar à mão ou na máquina em água fria
                - Cor: Preto com detalhes em azul
                
                ## Instruções de Cuidado:
                
                1. Lave com cores semelhantes
                2. Não use alvejante
                3. Seque na sombra
                4. Passe em temperatura média
                
                Ao vestir esta camisa, você não só mostra seu estilo, mas também seu compromisso com a excelência acadêmica!
                ''',
                'imagem': 'camisa.jpg',
                'imagens_adicionais': json.dumps(['camisa_frente.jpg', 'camisa_costas.jpg', 'camisa_detalhe.jpg']),
                'preco_xp': 3000,
                'estoque': 50,
                'disponivel': True,
                'destaque': True,
                'limitado': False,
                'categorias': ['vestuario']
            },
            {
                'nome': 'Garrafa Launcher',
                'descricao': 'Garrafa térmica de aço inoxidável com logo da Launcher. Mantém bebidas quentes ou frias por horas.',
                'descricao_detalhada': '''
                # Garrafa Térmica Launcher
                
                A Garrafa Launcher é essencial para manter a hidratação durante suas sessões de estudo. Produzida em aço inoxidável de alta qualidade, mantém suas bebidas na temperatura ideal por horas.
                
                ## Características:
                
                - Capacidade: 500ml
                - Material: Aço inoxidável dupla camada
                - Mantém bebidas quentes por até 12 horas
                - Mantém bebidas frias por até 24 horas
                - Gravação a laser do logo Launcher
                - Tampa hermética anti-vazamentos
                
                ## Benefícios:
                
                - Ecológica: substitui centenas de garrafas plásticas descartáveis
                - Prática: cabe facilmente em mochilas e bolsas
                - Durável: construção robusta resistente a impactos
                
                Mantenha-se hidratado enquanto se prepara para decolar rumo à aprovação!
                ''',
                'imagem': 'garrafa.jpg',
                'imagens_adicionais': json.dumps(['garrafa_aberta.jpg', 'garrafa_detalhe.jpg']),
                'preco_xp': 2000,
                'estoque': 75,
                'disponivel': True,
                'destaque': False,
                'limitado': False,
                'categorias': ['acessorios']
            },
            {
                'nome': 'Caneca Launcher',
                'descricao': 'Caneca de cerâmica com logo da Launcher. Ideal para seu café durante as sessões de estudo.',
                'descricao_detalhada': '''
                # Caneca Launcher
                
                A Caneca Launcher é o parceiro perfeito para suas maratonas de estudo. Feita de cerâmica de alta qualidade, é ideal para seu café, chá ou bebida favorita enquanto você se prepara para o ENEM.
                
                ## Características:
                
                - Capacidade: 350ml
                - Material: Cerâmica premium
                - Acabamento brilhante
                - Design exclusivo com logo e slogan da Launcher
                - Segura para micro-ondas e lava-louças
                
                ## Dica de Uso:
                
                Combine com a técnica Pomodoro: um café a cada pausa de estudo para maximizar sua produtividade!
                
                Esta caneca não é apenas um item funcional, mas também um lembrete diário do seu compromisso com o sucesso acadêmico.
                ''',
                'imagem': 'caneca.jpg',
                'imagens_adicionais': json.dumps(['caneca_lado.jpg', 'caneca_frente.jpg']),
                'preco_xp': 1500,
                'estoque': 100,
                'disponivel': True,
                'destaque': False,
                'limitado': False,
                'categorias': ['acessorios']
            },
            {
                'nome': 'Fone Bluetooth',
                'descricao': 'Fone de ouvido sem fio com cancelamento de ruído. Ideal para se concentrar nos estudos.',
                'descricao_detalhada': '''
                # Fone de Ouvido Bluetooth Launcher
                
                Maximize sua concentração nos estudos com o Fone Bluetooth Launcher. Com tecnologia de cancelamento de ruído, você consegue criar o ambiente perfeito para absorver conteúdo sem distrações.
                
                ## Características Técnicas:
                
                - Bluetooth 5.0 com alcance de até 10m
                - Bateria com duração de até 20 horas
                - Cancelamento ativo de ruído
                - Microfone integrado para chamadas
                - Controles touch para volume e troca de músicas
                - Carregamento rápido: 10 minutos de carga = 2 horas de uso
                - Logo Launcher em relevo discreto
                
                ## Conteúdo da Embalagem:
                
                - Fone de ouvido Bluetooth
                - Cabo de carregamento USB-C
                - Estojo de transporte
                - Manual do usuário
                
                Transforme qualquer ambiente em uma sala de estudos ideal com este fone de alta qualidade!
                ''',
                'imagem': 'fone.jpg',
                'imagens_adicionais': json.dumps(['fone_estojo.jpg', 'fone_detalhes.jpg', 'fone_em_uso.jpg']),
                'preco_xp': 4000,
                'estoque': 30,
                'disponivel': True,
                'destaque': True,
                'limitado': False,
                'categorias': ['eletronicos']
            },
            {
                'nome': 'Mochila Launcher Pro',
                'descricao': 'Mochila com compartimentos para laptop, tablet e livros. Design exclusivo e resistente.',
                'descricao_detalhada': '''
                # Mochila Launcher Pro
                
                A Mochila Launcher Pro foi projetada especialmente para estudantes. Com diversos compartimentos e design ergonômico, é perfeita para organizar todos os seus materiais de estudo com praticidade.
                
                ## Características:
                
                - Compartimento acolchoado para laptop de até 15.6"
                - Bolso específico para tablet
                - Múltiplos compartimentos internos para melhor organização
                - Porta carregador USB externo (powerbank não incluso)
                - Material resistente à água
                - Alças acolchoadas para maior conforto
                - Capacidade: 25 litros
                - Dimensões: 45 x 30 x 20 cm
                
                ## Compartimentos Especiais:
                
                - Bolso lateral para garrafa
                - Compartimento seguro para documentos
                - Bolso frontal de acesso rápido
                
                Carregue tudo o que precisa para seus estudos com estilo e organização!
                ''',
                'imagem': 'mochila.jpg',
                'imagens_adicionais': json.dumps(['mochila_aberta.jpg', 'mochila_costas.jpg', 'mochila_lateral.jpg']),
                'preco_xp': 4800,
                'estoque': 20,
                'disponivel': True,
                'destaque': True,
                'limitado': True,
                'categorias': ['acessorios', 'limitado']
            },
            {
                'nome': 'Kit Cadernos Launcher',
                'descricao': 'Conjunto com 5 cadernos temáticos das principais áreas do ENEM. Ótimo para organizar seus estudos por disciplina.',
                'descricao_detalhada': '''
                # Kit Cadernos Launcher
                
                Organize seus estudos por área de conhecimento com este kit exclusivo de cadernos Launcher. Cada caderno é tematizado de acordo com uma área do ENEM, facilitando a organização do seu material.
                
                ## Conteúdo do Kit:
                
                - Caderno Linguagens (96 folhas): Capa azul
                - Caderno Matemática (96 folhas): Capa laranja
                - Caderno Ciências da Natureza (96 folhas): Capa verde
                - Caderno Ciências Humanas (96 folhas): Capa roxa
                - Caderno Redação (48 folhas): Capa vermelha
                
                ## Características:
                
                - Papel de alta qualidade 90g/m²
                - Pautado com margens
                - Encadernação em espiral resistente
                - Capa dura personalizada com dicas de estudo
                - Páginas destacáveis
                
                Cada caderno inclui na contracapa um resumo das principais competências avaliadas na respectiva área, além de dicas de estudo.
                ''',
                'imagem': 'cadernos.jpg',
                'imagens_adicionais': json.dumps(['cadernos_aberto.jpg', 'cadernos_conjunto.jpg']),
                'preco_xp': 2500,
                'estoque': 40,
                'disponivel': True,
                'destaque': False,
                'limitado': False,
                'categorias': ['acessorios']
            },
            {
                'nome': 'Moletom Launcher Edição ENEM 2025',
                'descricao': 'Moletom exclusivo da edição limitada ENEM 2025. Quentinho e estiloso para suas sessões de estudo.',
                'descricao_detalhada': '''
                # Moletom Launcher Edição ENEM 2025
                
                Um item de colecionador! Este moletom de edição limitada celebra sua jornada rumo ao ENEM 2025. Confortável e estiloso, perfeito para te aquecer durante as maratonas de estudo.
                
                ## Características:
                
                - Material: 80% algodão, 20% poliéster
                - Forro interno macio e quentinho
                - Capuz ajustável com cordão
                - Estampa exclusiva ENEM 2025 na frente
                - Logo Launcher bordado na manga
                - Bolso canguru frontal
                - Cós e punhos elásticos
                
                ## Disponível nos tamanhos:
                
                - P, M, G e GG
                
                *Produto de edição limitada. Disponível apenas enquanto durarem os estoques.*
                
                Quando você for aprovado no ENEM, este moletom será uma lembrança especial da sua jornada de sucesso!
                ''',
                'imagem': 'moletom.jpg',
                'imagens_adicionais': json.dumps(['moletom_costas.jpg', 'moletom_detalhe.jpg']),
                'preco_xp': 3500,
                'estoque': 15,
                'disponivel': True,
                'destaque': False,
                'limitado': True,
                'categorias': ['vestuario', 'limitado']
            }
        ]
        
        # Inserir produtos no banco
        for prod_data in produtos:
            # Extrair as categorias do produto
            cats = prod_data.pop('categorias')
            
            # Criar o produto
            produto = Produto(**prod_data)
            
            # Associar as categorias
            for cat_slug in cats:
                if cat_slug in categorias_obj:
                    produto.adicionar_categoria(categorias_obj[cat_slug])
            
            db.session.add(produto)
        
        db.session.commit()
        print(f"[+] {len(produtos)} produtos criados com sucesso!")
        
        # Criar alguns resgates de exemplo para demonstração
        if Resgate.query.count() == 0 and 'user_id' in locals():
            print("[+] Criando resgates de exemplo...")
            
            # Obter alguns produtos aleatórios
            produtos_db = Produto.query.all()
            
            # Criar resgates com diferentes status
            resgates_exemplo = [
                {
                    'produto': random.choice(produtos_db),
                    'status': 'Pendente',
                    'endereco_entrega': 'Rua Exemplo, 123 - Centro, São Paulo/SP, CEP: 01234-567',
                    'data_resgate': datetime.utcnow() - timedelta(days=2)
                },
                {
                    'produto': random.choice(produtos_db),
                    'status': 'Enviado',
                    'codigo_rastreio': 'BR123456789XX',
                    'transportadora': 'Correios - SEDEX',
                    'endereco_entrega': 'Av. Teste, 456 - Bairro, Rio de Janeiro/RJ, CEP: 20000-000',
                    'data_resgate': datetime.utcnow() - timedelta(days=5),
                    'data_envio': datetime.utcnow() - timedelta(days=3)
                },
                {
                    'produto': random.choice(produtos_db),
                    'status': 'Entregue',
                    'codigo_rastreio': 'BR987654321XX',
                    'transportadora': 'Transportadora Rápida',
                    'endereco_entrega': 'Rua das Flores, 789 - Jardim, Belo Horizonte/MG, CEP: 30000-000',
                    'data_resgate': datetime.utcnow() - timedelta(days=15),
                    'data_envio': datetime.utcnow() - timedelta(days=12),
                    'data_entrega': datetime.utcnow() - timedelta(days=8)
                }
            ]
            
            # Inserir resgates de exemplo
            for i, resgate_data in enumerate(resgates_exemplo):
                produto = resgate_data.pop('produto')
                resgate = Resgate(
                    produto_id=produto.id,
                    user_id=user_id,  # Use o ID do usuário de exemplo criado anteriormente
                    **resgate_data
                )
                db.session.add(resgate)
            
            db.session.commit()
            print(f"[+] {len(resgates_exemplo)} resgates de exemplo criados com sucesso!")
        
        print("[+] Povoamento da loja concluído com sucesso!")

if __name__ == "__main__":
    popular_shop()