"""
Script para popular o banco de dados com 15 questões do formulário ENEM
Execute: python seed_forms_questoes.py
"""

from app import create_app, db
from app.models.forms import FormsQuestao, FormsAlternativa

app = create_app()

# Lista de 15 questões variadas
QUESTOES = [
    {
        'texto': '<p>A charge abaixo critica qual problema social brasileiro?</p><p><em>(Imagine uma charge sobre desigualdade social)</em></p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'A falta de investimento em educação básica'},
            {'letra': 'B', 'texto': 'A concentração de renda e desigualdade social'},
            {'letra': 'C', 'texto': 'O desemprego estrutural'},
            {'letra': 'D', 'texto': 'A inflação crescente'},
            {'letra': 'E', 'texto': 'A corrupção política'}
        ],
        'resposta_correta': 'B',
        'explicacao': 'A concentração de renda é um dos principais problemas sociais do Brasil, com grande parte da riqueza nas mãos de poucos, gerando desigualdade social profunda.'
    },
    {
        'texto': '<p>Qual foi o principal objetivo da criação da ONU (Organização das Nações Unidas) em 1945?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Promover o comércio internacional'},
            {'letra': 'B', 'texto': 'Estabelecer uma moeda única mundial'},
            {'letra': 'C', 'texto': 'Manter a paz e segurança internacional'},
            {'letra': 'D', 'texto': 'Unificar todos os países em um governo global'},
            {'letra': 'E', 'texto': 'Controlar a economia mundial'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'A ONU foi criada após a Segunda Guerra Mundial com o objetivo principal de manter a paz e segurança internacional, promovendo cooperação entre as nações.'
    },
    {
        'texto': '<p>O efeito estufa é um fenômeno natural essencial para a vida na Terra. No entanto, a intensificação desse efeito tem causado preocupação. Qual gás é o principal responsável pelo aquecimento global?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Oxigênio (O₂)'},
            {'letra': 'B', 'texto': 'Nitrogênio (N₂)'},
            {'letra': 'C', 'texto': 'Dióxido de carbono (CO₂)'},
            {'letra': 'D', 'texto': 'Hélio (He)'},
            {'letra': 'E', 'texto': 'Argônio (Ar)'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'O dióxido de carbono (CO₂) é o principal gás do efeito estufa emitido por atividades humanas, como queima de combustíveis fósseis e desmatamento, intensificando o aquecimento global.'
    },
    {
        'texto': '<p>Na função f(x) = 2x + 3, qual é o valor de f(5)?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': '8'},
            {'letra': 'B', 'texto': '10'},
            {'letra': 'C', 'texto': '11'},
            {'letra': 'D', 'texto': '13'},
            {'letra': 'E', 'texto': '15'}
        ],
        'resposta_correta': 'D',
        'explicacao': 'Para calcular f(5), substituímos x por 5 na função: f(5) = 2(5) + 3 = 10 + 3 = 13.'
    },
    {
        'texto': '<p>Qual movimento literário brasileiro valorizava a linguagem coloquial, o humor e a liberdade formal, rompendo com as normas acadêmicas?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Romantismo'},
            {'letra': 'B', 'texto': 'Realismo'},
            {'letra': 'C', 'texto': 'Modernismo'},
            {'letra': 'D', 'texto': 'Parnasianismo'},
            {'letra': 'E', 'texto': 'Simbolismo'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'O Modernismo brasileiro, iniciado com a Semana de Arte Moderna de 1922, rompeu com padrões acadêmicos, valorizando a linguagem coloquial e a liberdade formal.'
    },
    {
        'texto': '<p>Qual destas fontes de energia é considerada renovável?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Petróleo'},
            {'letra': 'B', 'texto': 'Carvão mineral'},
            {'letra': 'C', 'texto': 'Gás natural'},
            {'letra': 'D', 'texto': 'Energia solar'},
            {'letra': 'E', 'texto': 'Urânio'}
        ],
        'resposta_correta': 'D',
        'explicacao': 'A energia solar é renovável porque provém do sol, uma fonte inesgotável em escala humana, ao contrário dos combustíveis fósseis que são finitos.'
    },
    {
        'texto': '<p>Em qual século ocorreu o Descobrimento do Brasil por Pedro Álvares Cabral?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Século XIV'},
            {'letra': 'B', 'texto': 'Século XV'},
            {'letra': 'C', 'texto': 'Século XVI'},
            {'letra': 'D', 'texto': 'Século XVII'},
            {'letra': 'E', 'texto': 'Século XVIII'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'O Brasil foi descoberto em 1500, que pertence ao século XVI. Pedro Álvares Cabral chegou ao território brasileiro em 22 de abril de 1500.'
    },
    {
        'texto': '<p>Qual organela celular é responsável pela produção de energia na célula?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Núcleo'},
            {'letra': 'B', 'texto': 'Ribossomo'},
            {'letra': 'C', 'texto': 'Mitocôndria'},
            {'letra': 'D', 'texto': 'Lisossomo'},
            {'letra': 'E', 'texto': 'Complexo de Golgi'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'A mitocôndria é conhecida como a "usina de energia" da célula, pois realiza a respiração celular, produzindo ATP (energia) a partir de nutrientes.'
    },
    {
        'texto': '<p>Qual é a lei da física que afirma: "Para toda ação há uma reação de igual intensidade e sentido contrário"?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Primeira Lei de Newton (Lei da Inércia)'},
            {'letra': 'B', 'texto': 'Segunda Lei de Newton (F = m.a)'},
            {'letra': 'C', 'texto': 'Terceira Lei de Newton (Ação e Reação)'},
            {'letra': 'D', 'texto': 'Lei da Gravitação Universal'},
            {'letra': 'E', 'texto': 'Lei de Hooke'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'A Terceira Lei de Newton, também chamada de Lei da Ação e Reação, estabelece que forças sempre ocorrem aos pares: para cada ação há uma reação de mesma intensidade e direção oposta.'
    },
    {
        'texto': '<p>Qual bioma brasileiro é conhecido como "berço das águas" por abrigar nascentes de importantes rios brasileiros?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Amazônia'},
            {'letra': 'B', 'texto': 'Mata Atlântica'},
            {'letra': 'C', 'texto': 'Cerrado'},
            {'letra': 'D', 'texto': 'Caatinga'},
            {'letra': 'E', 'texto': 'Pantanal'}
        ],
        'resposta_correta': 'C',
        'explicacao': 'O Cerrado é chamado de "berço das águas" porque abriga nascentes de rios das três principais bacias hidrográficas da América do Sul: Amazônica, Tocantins-Araguaia e Platina.'
    },
    {
        'texto': '<p>Qual acontecimento histórico marcou o fim da Idade Média e início da Idade Moderna?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Queda do Império Romano do Ocidente'},
            {'letra': 'B', 'texto': 'Tomada de Constantinopla pelos turcos otomanos'},
            {'letra': 'C', 'texto': 'Descobrimento da América'},
            {'letra': 'D', 'texto': 'Revolução Francesa'},
            {'letra': 'E', 'texto': 'Reforma Protestante'}
        ],
        'resposta_correta': 'B',
        'explicacao': 'A Tomada de Constantinopla pelos turcos otomanos em 1453 é o marco histórico que convencionalmente delimita o fim da Idade Média e o início da Idade Moderna.'
    },
    {
        'texto': '<p>Qual tipo de figura de linguagem está presente na frase: "Aquela mulher é uma flor"?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Metonímia'},
            {'letra': 'B', 'texto': 'Metáfora'},
            {'letra': 'C', 'texto': 'Hipérbole'},
            {'letra': 'D', 'texto': 'Eufemismo'},
            {'letra': 'E', 'texto': 'Antítese'}
        ],
        'resposta_correta': 'B',
        'explicacao': 'A metáfora é uma figura de linguagem que estabelece uma comparação implícita entre dois termos. Na frase, a mulher é comparada a uma flor sem usar conectivos comparativos.'
    },
    {
        'texto': '<p>Qual é a fórmula química da água?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'H₂O'},
            {'letra': 'B', 'texto': 'CO₂'},
            {'letra': 'C', 'texto': 'O₂'},
            {'letra': 'D', 'texto': 'NaCl'},
            {'letra': 'E', 'texto': 'CH₄'}
        ],
        'resposta_correta': 'A',
        'explicacao': 'A água é composta por dois átomos de hidrogênio (H) e um átomo de oxigênio (O), formando a molécula H₂O.'
    },
    {
        'texto': '<p>Qual foi o regime político implantado no Brasil após o golpe militar de 1964?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'Monarquia'},
            {'letra': 'B', 'texto': 'Ditadura Militar'},
            {'letra': 'C', 'texto': 'República Parlamentarista'},
            {'letra': 'D', 'texto': 'Anarquia'},
            {'letra': 'E', 'texto': 'Teocracia'}
        ],
        'resposta_correta': 'B',
        'explicacao': 'O golpe militar de 1964 instaurou uma Ditadura Militar no Brasil, que durou até 1985, período marcado por censura, repressão e supressão de direitos civis.'
    },
    {
        'texto': '<p>Qual é o continente mais populoso do mundo?</p>',
        'alternativas': [
            {'letra': 'A', 'texto': 'América'},
            {'letra': 'B', 'texto': 'África'},
            {'letra': 'C', 'texto': 'Europa'},
            {'letra': 'D', 'texto': 'Ásia'},
            {'letra': 'E', 'texto': 'Oceania'}
        ],
        'resposta_correta': 'D',
        'explicacao': 'A Ásia é o continente mais populoso do mundo, abrigando mais de 4,5 bilhões de pessoas, incluindo países muito populosos como China e Índia.'
    }
]

def popular_questoes():
    """Popula o banco com as 15 questões"""
    
    with app.app_context():
        try:
            print("🚀 Iniciando população das questões...")
            
            # Limpar questões existentes (opcional - comentar se não quiser limpar)
            # FormsAlternativa.query.delete()
            # FormsQuestao.query.delete()
            # db.session.commit()
            
            for idx, q_data in enumerate(QUESTOES, 1):
                print(f"\n📝 Criando questão {idx}/15...")
                
                # Criar questão
                questao = FormsQuestao(
                    texto=q_data['texto'],
                    resposta_correta=q_data['resposta_correta'],
                    explicacao=q_data['explicacao'],
                    ativo=True
                )
                
                db.session.add(questao)
                db.session.flush()  # Para obter o ID
                
                # Criar alternativas
                for alt_data in q_data['alternativas']:
                    alternativa = FormsAlternativa(
                        questao_id=questao.id,
                        letra=alt_data['letra'],
                        texto=alt_data['texto']
                    )
                    db.session.add(alternativa)
                
                print(f"   ✅ Questão {idx} criada com sucesso!")
            
            # Commit final
            db.session.commit()
            
            print("\n" + "="*50)
            print("🎉 SUCESSO! Todas as 15 questões foram cadastradas!")
            print("="*50)
            
            # Mostrar resumo
            total_questoes = FormsQuestao.query.count()
            total_alternativas = FormsAlternativa.query.count()
            
            print(f"\n📊 Resumo do banco de dados:")
            print(f"   • Total de questões: {total_questoes}")
            print(f"   • Total de alternativas: {total_alternativas}")
            print("\n✨ O formulário está pronto para uso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao popular questões: {str(e)}")
            raise

if __name__ == '__main__':
    popular_questoes()
