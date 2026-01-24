# helpzone_setup.py

from app import create_app, db
from app.models.helpzone import Badge, Duvida, Resposta, DuvidaVoto, RespostaVoto, Notificacao
from app.models.user import User
from datetime import datetime, timedelta
import random

# Importar a função de inicialização de badges
from app.routes.helpzone import initialize_badges

app = create_app()

def setup_helpzone():
    with app.app_context():
        print("[+] Configurando Help Zone...")
        
        # 1. Inicializar Badges
        print("[+] Criando badges padrão...")
        initialize_badges()
        
        # 2. Verificar se já existem dados
        if Duvida.query.count() > 0:
            print("[+] Dados de Help Zone já existem. Pulando criação de exemplos.")
            return
        
        # 3. Criar alguns usuários para testes, se necessário
        if User.query.count() < 3:
            print("[+] Criando usuários de exemplo para o Help Zone...")
            users = [
                {
                    "username": "professor_matematica",
                    "email": "prof.mat@example.com",
                    "nome_completo": "Professor de Matemática",
                    "password": "senha123"
                },
                {
                    "username": "estudante_biologia",
                    "email": "bio.estudante@example.com",
                    "nome_completo": "Estudante de Biologia",
                    "password": "senha123"
                },
                {
                    "username": "mestre_quimica",
                    "email": "quimica@example.com",
                    "nome_completo": "Mestre da Química",
                    "password": "senha123"
                }
            ]
            
            for user_data in users:
                user = User.query.filter_by(username=user_data["username"]).first()
                if not user:
                    user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        nome_completo=user_data["nome_completo"]
                    )
                    user.set_password(user_data["password"])
                    db.session.add(user)
            
            db.session.commit()
        
        # 4. Criar dúvidas de exemplo
        print("[+] Criando dúvidas e respostas de exemplo...")
        areas = ["matematica", "portugues", "quimica", "fisica", "biologia", "historia", "geografia", "redacao"]
        duvidas_exemplos = [
            {
                "titulo": "Como calcular o limite de uma função?",
                "conteudo": "Estou com dificuldades em entender o conceito de limite e como calcular limites de funções. Alguém poderia me ajudar com um passo a passo?",
                "area": "matematica"
            },
            {
                "titulo": "Dúvida sobre crase",
                "conteudo": "Quando devo usar crase? Sempre confundo as regras, principalmente quando tem 'a' antes de palavras femininas.",
                "area": "portugues"
            },
            {
                "titulo": "Como balancear equações químicas?",
                "conteudo": "Tenho dificuldade em balancear equações químicas mais complexas. Existe alguma técnica ou método mais eficiente?",
                "area": "quimica"
            },
            {
                "titulo": "Explicação sobre Movimento Uniformemente Variado",
                "conteudo": "Alguém poderia me explicar o MUV de uma forma mais simples? Não estou conseguindo entender a relação entre aceleração, velocidade e tempo.",
                "area": "fisica"
            },
            {
                "titulo": "Diferença entre mitose e meiose",
                "conteudo": "Qual a principal diferença entre mitose e meiose? E em quais situações cada uma ocorre?",
                "area": "biologia"
            }
        ]
        
        # Obter usuários para atribuir dúvidas e respostas
        users = User.query.all()
        
        for i, duvida_data in enumerate(duvidas_exemplos):
            # Escolher um usuário aleatório como autor da dúvida
            user = random.choice(users)
            
            # Criar a dúvida
            duvida = Duvida(
                titulo=duvida_data["titulo"],
                conteudo=duvida_data["conteudo"],
                area=duvida_data["area"],
                user_id=user.id,
                data_criacao=datetime.utcnow() - timedelta(days=random.randint(1, 10))
            )
            db.session.add(duvida)
            db.session.flush()  # Para obter o ID da dúvida
            
            # Criar entre 1 e 3 respostas para cada dúvida
            for j in range(random.randint(1, 3)):
                # Escolher um usuário diferente para responder
                resposta_user = random.choice([u for u in users if u.id != user.id])
                
                resposta = Resposta(
                    conteudo=f"Esta é uma resposta de exemplo {j+1} para a dúvida sobre {duvida_data['area']}. "
                             f"Explicando de forma {random.choice(['simples', 'detalhada', 'clara'])}, "
                             f"o conceito principal é {random.choice(['fundamental', 'importante', 'essencial'])} "
                             f"para compreender este tema.",
                    duvida_id=duvida.id,
                    user_id=resposta_user.id,
                    data_criacao=duvida.data_criacao + timedelta(hours=random.randint(1, 24))
                )
                db.session.add(resposta)
                
                # Adicionar alguns votos aleatórios
                for k in range(random.randint(0, 5)):
                    # Escolher um usuário aleatório para votar
                    vote_user = random.choice([u for u in users if u.id != resposta_user.id])
                    
                    voto = RespostaVoto(
                        resposta_id=resposta.id,
                        user_id=vote_user.id,
                        valor=random.choice([1, 1, 1, -1])  # Maior probabilidade de votos positivos
                    )
                    db.session.add(voto)
            
            # Marcar aleatoriamente algumas dúvidas como resolvidas
            if random.random() < 0.6:  # 60% de chance de estar resolvida
                duvida.resolvida = True
                
                # Selecionar uma resposta aleatória para ser a solução
                respostas = Resposta.query.filter_by(duvida_id=duvida.id).all()
                if respostas:
                    solucao = random.choice(respostas)
                    solucao.solucao = True
        
        # 5. Commit das alterações
        db.session.commit()
        print("[+] Configuração do Help Zone concluída com sucesso!")


if __name__ == "__main__":
    setup_helpzone()