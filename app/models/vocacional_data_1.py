# =============================================================================
# BANCO DE DADOS DO TESTE VOCACIONAL - LAUNCHER EDUCAÇÃO
# Baseado em: RIASEC (Holland), Big Five, Valores de Trabalho, Habilidades
# 72 questões + 52 carreiras brasileiras mapeadas
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 1 — INTERESSES VOCACIONAIS (RIASEC)
# 36 questões, 6 por dimensão. Escala Likert 1-5
# dimensao: R=Realista, I=Investigativo, A=Artístico, S=Social, E=Empreendedor, C=Convencional
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_RIASEC = [
    # ── REALISTA (R) ── trabalho prático, técnico, manual, natureza
    {"id": "R1", "dimensao": "R", "bloco": "riasec",
     "texto": "Consertar, montar ou construir coisas com as mãos",
     "emoji": "🔧"},
    {"id": "R2", "dimensao": "R", "bloco": "riasec",
     "texto": "Trabalhar com máquinas, ferramentas ou equipamentos",
     "emoji": "⚙️"},
    {"id": "R3", "dimensao": "R", "bloco": "riasec",
     "texto": "Estar em ambientes ao ar livre (campo, obras, natureza)",
     "emoji": "🌿"},
    {"id": "R4", "dimensao": "R", "bloco": "riasec",
     "texto": "Fazer atividades físicas como parte do trabalho",
     "emoji": "💪"},
    {"id": "R5", "dimensao": "R", "bloco": "riasec",
     "texto": "Trabalhar com plantas, animais ou recursos naturais",
     "emoji": "🌱"},
    {"id": "R6", "dimensao": "R", "bloco": "riasec",
     "texto": "Resolver problemas práticos do dia a dia com soluções concretas",
     "emoji": "🏗️"},

    # ── INVESTIGATIVO (I) ── pesquisa, análise, ciência, raciocínio
    {"id": "I1", "dimensao": "I", "bloco": "riasec",
     "texto": "Pesquisar e entender como as coisas funcionam por dentro",
     "emoji": "🔬"},
    {"id": "I2", "dimensao": "I", "bloco": "riasec",
     "texto": "Resolver problemas complexos que exigem raciocínio lógico",
     "emoji": "🧮"},
    {"id": "I3", "dimensao": "I", "bloco": "riasec",
     "texto": "Estudar ciências como biologia, química, física ou matemática",
     "emoji": "⚗️"},
    {"id": "I4", "dimensao": "I", "bloco": "riasec",
     "texto": "Analisar dados, gráficos e informações para tirar conclusões",
     "emoji": "📊"},
    {"id": "I5", "dimensao": "I", "bloco": "riasec",
     "texto": "Explorar temas profundamente até entender todos os detalhes",
     "emoji": "🔍"},
    {"id": "I6", "dimensao": "I", "bloco": "riasec",
     "texto": "Fazer experimentos ou testes para descobrir como algo funciona",
     "emoji": "🧪"},

    # ── ARTÍSTICO (A) ── criatividade, expressão, arte, inovação
    {"id": "A1", "dimensao": "A", "bloco": "riasec",
     "texto": "Criar coisas originais como textos, imagens ou músicas",
     "emoji": "🎨"},
    {"id": "A2", "dimensao": "A", "bloco": "riasec",
     "texto": "Expressar ideias e sentimentos de formas criativas",
     "emoji": "✍️"},
    {"id": "A3", "dimensao": "A", "bloco": "riasec",
     "texto": "Trabalhar com design, estética ou comunicação visual",
     "emoji": "🖌️"},
    {"id": "A4", "dimensao": "A", "bloco": "riasec",
     "texto": "Inventar histórias, roteiros, campanhas ou conceitos novos",
     "emoji": "💡"},
    {"id": "A5", "dimensao": "A", "bloco": "riasec",
     "texto": "Ambientes de trabalho que valorizam inovação e liberdade criativa",
     "emoji": "🌈"},
    {"id": "A6", "dimensao": "A", "bloco": "riasec",
     "texto": "Apreciar e analisar arte, literatura, cinema ou arquitetura",
     "emoji": "🎭"},

    # ── SOCIAL (S) ── ajudar, ensinar, cuidar, trabalho com pessoas
    {"id": "S1", "dimensao": "S", "bloco": "riasec",
     "texto": "Ajudar pessoas com seus problemas emocionais ou práticos",
     "emoji": "🤝"},
    {"id": "S2", "dimensao": "S", "bloco": "riasec",
     "texto": "Ensinar, explicar ou treinar outras pessoas",
     "emoji": "📚"},
    {"id": "S3", "dimensao": "S", "bloco": "riasec",
     "texto": "Trabalhar em equipe e construir relacionamentos",
     "emoji": "👥"},
    {"id": "S4", "dimensao": "S", "bloco": "riasec",
     "texto": "Atuar em áreas que fazem diferença na vida das pessoas",
     "emoji": "❤️"},
    {"id": "S5", "dimensao": "S", "bloco": "riasec",
     "texto": "Ouvir e entender o ponto de vista das outras pessoas",
     "emoji": "👂"},
    {"id": "S6", "dimensao": "S", "bloco": "riasec",
     "texto": "Trabalhar em saúde, educação ou assistência social",
     "emoji": "🏥"},

    # ── EMPREENDEDOR (E) ── liderança, negócios, persuasão, risco
    {"id": "E1", "dimensao": "E", "bloco": "riasec",
     "texto": "Liderar grupos, projetos ou times de pessoas",
     "emoji": "🚀"},
    {"id": "E2", "dimensao": "E", "bloco": "riasec",
     "texto": "Convencer e persuadir outras pessoas",
     "emoji": "🎯"},
    {"id": "E3", "dimensao": "E", "bloco": "riasec",
     "texto": "Iniciar projetos novos e assumir riscos calculados",
     "emoji": "💼"},
    {"id": "E4", "dimensao": "E", "bloco": "riasec",
     "texto": "Competir e superar metas e desafios",
     "emoji": "🏆"},
    {"id": "E5", "dimensao": "E", "bloco": "riasec",
     "texto": "Negociar, vender ideias ou produtos",
     "emoji": "🤑"},
    {"id": "E6", "dimensao": "E", "bloco": "riasec",
     "texto": "Ter poder de decisão e influenciar resultados",
     "emoji": "⚡"},

    # ── CONVENCIONAL (C) ── organização, dados, regras, processos
    {"id": "C1", "dimensao": "C", "bloco": "riasec",
     "texto": "Organizar informações, arquivos e processos com precisão",
     "emoji": "📋"},
    {"id": "C2", "dimensao": "C", "bloco": "riasec",
     "texto": "Trabalhar com números, planilhas e finanças",
     "emoji": "🔢"},
    {"id": "C3", "dimensao": "C", "bloco": "riasec",
     "texto": "Seguir procedimentos e garantir que as coisas sejam feitas corretamente",
     "emoji": "✅"},
    {"id": "C4", "dimensao": "C", "bloco": "riasec",
     "texto": "Ambientes de trabalho estruturados e com regras claras",
     "emoji": "🏛️"},
    {"id": "C5", "dimensao": "C", "bloco": "riasec",
     "texto": "Verificar detalhes e garantir a qualidade e exatidão do trabalho",
     "emoji": "🎯"},
    {"id": "C6", "dimensao": "C", "bloco": "riasec",
     "texto": "Trabalhar com registros, relatórios, auditorias ou controles",
     "emoji": "📊"},
]

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 2 — PERSONALIDADE (Big Five simplificado)
# 15 questões. Escala concordância 1-5
# Dimensões: O=Abertura, C=Conscienciosidade, E=Extroversão, A=Amabilidade, N=Neuroticismo(invertido=Estabilidade)
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_PERSONALIDADE = [
    {"id": "P1", "dimensao": "O", "bloco": "personalidade",
     "texto": "Gosto de explorar ideias novas e questionar o que já existe",
     "emoji": "🌍"},
    {"id": "P2", "dimensao": "C", "bloco": "personalidade",
     "texto": "Costumo planejar minhas tarefas com antecedência e cumpro prazos",
     "emoji": "📅"},
    {"id": "P3", "dimensao": "E", "bloco": "personalidade",
     "texto": "Prefiro trabalhar e estudar em grupo do que sozinho",
     "emoji": "🗣️"},
    {"id": "P4", "dimensao": "A", "bloco": "personalidade",
     "texto": "Me preocupo genuinamente com o bem-estar das pessoas ao meu redor",
     "emoji": "💛"},
    {"id": "P5", "dimensao": "N", "bloco": "personalidade",
     "texto": "Consigo manter a calma bem mesmo em situações de pressão",
     "emoji": "😌"},
    {"id": "P6", "dimensao": "O", "bloco": "personalidade",
     "texto": "Fico curioso com assuntos que nunca estudei antes",
     "emoji": "🔭"},
    {"id": "P7", "dimensao": "C", "bloco": "personalidade",
     "texto": "Quando começo algo, raramente desisto antes de terminar",
     "emoji": "🏁"},
    {"id": "P8", "dimensao": "E", "bloco": "personalidade",
     "texto": "Me sinto bem sendo o centro das atenções em situações sociais",
     "emoji": "🎤"},
    {"id": "P9", "dimensao": "A", "bloco": "personalidade",
     "texto": "Prefiro chegar a um acordo do que entrar em conflito",
     "emoji": "🕊️"},
    {"id": "P10", "dimensao": "N", "bloco": "personalidade",
     "texto": "Não me abalo muito com críticas ou opiniões negativas",
     "emoji": "🛡️"},
    {"id": "P11", "dimensao": "O", "bloco": "personalidade",
     "texto": "Gosto de rotinas previsíveis mais do que de surpresas constantes",
     "emoji": "🔄",
     "inverso": True},
    {"id": "P12", "dimensao": "C", "bloco": "personalidade",
     "texto": "Sou muito detalhista e me incomoda quando algo está impreciso",
     "emoji": "🔎"},
    {"id": "P13", "dimensao": "E", "bloco": "personalidade",
     "texto": "Prefiro tomar decisões rápidas a ficar analisando por muito tempo",
     "emoji": "⚡"},
    {"id": "P14", "dimensao": "A", "bloco": "personalidade",
     "texto": "Fico satisfeito quando contribuo para o sucesso de outra pessoa",
     "emoji": "🌟"},
    {"id": "P15", "dimensao": "N", "bloco": "personalidade",
     "texto": "Raramente me sinto sobrecarregado ou ansioso com minhas responsabilidades",
     "emoji": "⚖️"},
]

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 3 — VALORES DE TRABALHO
# 12 questões de escolha forçada entre dois valores.
# O aluno escolhe qual dos dois é MAIS importante para ele.
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_VALORES = [
    {"id": "V1", "bloco": "valores",
     "opcao_a": {"texto": "Ter estabilidade e segurança no emprego", "valor": "estabilidade", "emoji": "🏠"},
     "opcao_b": {"texto": "Ter liberdade e autonomia no meu trabalho", "valor": "autonomia", "emoji": "🦅"}},
    {"id": "V2", "bloco": "valores",
     "opcao_a": {"texto": "Ganhar bem financeiramente", "valor": "remuneracao", "emoji": "💰"},
     "opcao_b": {"texto": "Ter impacto positivo na sociedade", "valor": "impacto_social", "emoji": "🌍"}},
    {"id": "V3", "bloco": "valores",
     "opcao_a": {"texto": "Crescer e ser reconhecido na carreira", "valor": "reconhecimento", "emoji": "🏆"},
     "opcao_b": {"texto": "Ter equilíbrio entre trabalho e vida pessoal", "valor": "equilibrio", "emoji": "⚖️"}},
    {"id": "V4", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar em algo que me desafia intelectualmente", "valor": "desafio_intelectual", "emoji": "🧠"},
     "opcao_b": {"texto": "Trabalhar em algo que me permita ajudar pessoas diretamente", "valor": "ajudar_pessoas", "emoji": "🤝"}},
    {"id": "V5", "bloco": "valores",
     "opcao_a": {"texto": "Inovar e criar coisas novas", "valor": "inovacao", "emoji": "💡"},
     "opcao_b": {"texto": "Aperfeiçoar e melhorar o que já existe", "valor": "melhoria", "emoji": "🔧"}},
    {"id": "V6", "bloco": "valores",
     "opcao_a": {"texto": "Liderar e tomar decisões importantes", "valor": "lideranca", "emoji": "👑"},
     "opcao_b": {"texto": "Trabalhar em colaboração sem pressão hierárquica", "valor": "colaboracao", "emoji": "👥"}},
    {"id": "V7", "bloco": "valores",
     "opcao_a": {"texto": "Ter prestígio e ser referência na minha área", "valor": "prestigio", "emoji": "⭐"},
     "opcao_b": {"texto": "Fazer um trabalho que me satisfaça pessoalmente, mesmo sem grande fama", "valor": "satisfacao_pessoal", "emoji": "😊"}},
    {"id": "V8", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar com tecnologia e inovação constante", "valor": "tecnologia", "emoji": "💻"},
     "opcao_b": {"texto": "Trabalhar com questões humanas, sociais ou culturais", "valor": "humanismo", "emoji": "❤️"}},
    {"id": "V9", "bloco": "valores",
     "opcao_a": {"texto": "Aprender algo novo todo dia no meu trabalho", "valor": "aprendizado_continuo", "emoji": "📖"},
     "opcao_b": {"texto": "Ter especialização profunda em uma área específica", "valor": "especializacao", "emoji": "🎯"}},
    {"id": "V10", "bloco": "valores",
     "opcao_a": {"texto": "Ter resultados mensuráveis e objetivos claros", "valor": "resultados", "emoji": "📈"},
     "opcao_b": {"texto": "Ter um trabalho com propósito maior, mesmo sem metas rígidas", "valor": "proposito", "emoji": "🌟"}},
    {"id": "V11", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar em grandes cidades com muitas oportunidades", "valor": "centros_urbanos", "emoji": "🏙️"},
     "opcao_b": {"texto": "Ter flexibilidade de onde trabalhar (remoto ou interior)", "valor": "flexibilidade_local", "emoji": "🏡"}},
    {"id": "V12", "bloco": "valores",
     "opcao_a": {"texto": "Trabalho independente ou como empreendedor", "valor": "empreendedorismo", "emoji": "🚀"},
     "opcao_b": {"texto": "Trabalho em empresas ou serviço público com estrutura", "valor": "concurso_empresa", "emoji": "🏛️"}},
]

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 4 — HABILIDADES AUTODECLARADAS
# 12 questões. Escala Likert 1-5 ("Sou bom nisto")
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_HABILIDADES = [
    {"id": "H1", "dimensao": "R", "bloco": "habilidades",
     "texto": "Montar, reparar ou operar equipamentos e aparelhos",
     "emoji": "🔨"},
    {"id": "H2", "dimensao": "I", "bloco": "habilidades",
     "texto": "Raciocínio lógico e resolução de problemas matemáticos",
     "emoji": "🔢"},
    {"id": "H3", "dimensao": "A", "bloco": "habilidades",
     "texto": "Escrita, comunicação verbal ou produção criativa",
     "emoji": "✍️"},
    {"id": "H4", "dimensao": "S", "bloco": "habilidades",
     "texto": "Me comunicar, ouvir e me relacionar com diferentes tipos de pessoas",
     "emoji": "💬"},
    {"id": "H5", "dimensao": "E", "bloco": "habilidades",
     "texto": "Liderar, organizar e motivar pessoas em projetos",
     "emoji": "🎯"},
    {"id": "H6", "dimensao": "C", "bloco": "habilidades",
     "texto": "Organizar, categorizar e controlar informações com precisão",
     "emoji": "📋"},
    {"id": "H7", "dimensao": "I", "bloco": "habilidades",
     "texto": "Pesquisar, analisar e interpretar dados ou textos complexos",
     "emoji": "🔍"},
    {"id": "H8", "dimensao": "A", "bloco": "habilidades",
     "texto": "Pensar de forma inovadora e encontrar soluções não convencionais",
     "emoji": "💡"},
    {"id": "H9", "dimensao": "S", "bloco": "habilidades",
     "texto": "Ensinar, explicar ou passar conhecimento para outras pessoas",
     "emoji": "📚"},
    {"id": "H10", "dimensao": "R", "bloco": "habilidades",
     "texto": "Trabalhar com coordenação motora fina (desenhar, costurar, precisão manual)",
     "emoji": "🖐️"},
    {"id": "H11", "dimensao": "E", "bloco": "habilidades",
     "texto": "Negociar, argumentar e convencer pessoas com facilidade",
     "emoji": "🗣️"},
    {"id": "H12", "dimensao": "C", "bloco": "habilidades",
     "texto": "Lidar bem com cálculos, finanças e controle numérico",
     "emoji": "💹"},
]

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 5 — CONTEXTO DE VIDA
# 5 questões de múltipla escolha (não afetam RIASEC, afetam filtragem de carreiras)
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_CONTEXTO = [
    {"id": "CT1", "bloco": "contexto",
     "texto": "Quanto tempo você está disposto a estudar antes de trabalhar?",
     "emoji": "⏳",
     "opcoes": [
         {"valor": "curto", "texto": "Até 2 anos (curso técnico ou tecnológico)"},
         {"valor": "medio", "texto": "3 a 4 anos (graduação padrão)"},
         {"valor": "longo", "texto": "5 a 6 anos (graduação longa)"},
         {"valor": "muito_longo", "texto": "Mais de 6 anos (residência, pós, carreira militar)"},
     ]},
    {"id": "CT2", "bloco": "contexto",
     "texto": "Qual é a sua prioridade financeira na carreira?",
     "emoji": "💵",
     "opcoes": [
         {"valor": "alta", "texto": "Alta remuneração — é fundamental para mim"},
         {"valor": "media", "texto": "Remuneração razoável com satisfação no trabalho"},
         {"valor": "baixa", "texto": "Propósito e impacto valem mais que salário alto"},
     ]},
    {"id": "CT3", "bloco": "contexto",
     "texto": "Como você prefere trabalhar?",
     "emoji": "💼",
     "opcoes": [
         {"valor": "autonomo", "texto": "Por conta própria / empreendedor"},
         {"valor": "equipe_dinamica", "texto": "Em equipe dinâmica, projetos variados"},
         {"valor": "empresa_estruturada", "texto": "Em empresa ou instituição com estrutura clara"},
         {"valor": "concurso", "texto": "Serviço público / concurso"},
     ]},
    {"id": "CT4", "bloco": "contexto",
     "texto": "Onde você pretende trabalhar?",
     "emoji": "📍",
     "opcoes": [
         {"valor": "capital_grande", "texto": "Em grandes capitais (SP, RJ, BH...)"},
         {"valor": "qualquer_cidade", "texto": "Em qualquer cidade do Brasil"},
         {"valor": "interior_preferencia", "texto": "Prefiro interior ou cidade média"},
         {"valor": "remoto", "texto": "Quer trabalhar de qualquer lugar (remoto)"},
     ]},
    {"id": "CT5", "bloco": "contexto",
     "texto": "O que você considera sobre sua condição atual?",
     "emoji": "🎓",
     "opcoes": [
         {"valor": "foco_total", "texto": "Posso me dedicar 100% aos estudos"},
         {"valor": "trabalha_estuda", "texto": "Preciso trabalhar enquanto estudo"},
         {"valor": "bolsa_necessaria", "texto": "Necessito de bolsa de estudos ou financiamento"},
         {"valor": "ead_opcao", "texto": "EAD é uma opção real para mim"},
     ]},
]

# ─────────────────────────────────────────────────────────────────────────────
# BANCO DE CARREIRAS BRASILEIRAS
# 52 carreiras com perfil RIASEC, valores, habilidades, dados de mercado
# ─────────────────────────────────────────────────────────────────────────────

CARREIRAS = [
    # ════════════════════ SAÚDE ════════════════════
    {
        "id": "medicina",
        "nome": "Medicina",
        "area": "Saúde",
        "emoji": "🩺",
        "descricao": "Diagnostica, trata e previne doenças. Exige dedicação extrema mas oferece impacto humano e prestígio únicos.",
        "riasec": {"I": 0.95, "S": 0.85, "R": 0.40, "A": 0.20, "E": 0.30, "C": 0.60},
        "personalidade": {"abertura": 0.7, "conscienciosidade": 0.95, "extroversao": 0.5, "amabilidade": 0.8},
        "valores_altos": ["impacto_social", "ajudar_pessoas", "desafio_intelectual", "prestigio", "especializacao"],
        "valores_baixos": ["equilibrio", "flexibilidade_local", "autonomia"],
        "habilidades_chave": ["I", "S", "C"],
        "duracao_anos": 8, "duracao_label": "6 anos + 2 anos residência",
        "dificuldade_enem": "Muito alta",
        "salario_min": 8000, "salario_max": 50000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["saúde", "ciências", "prestígio", "longo prazo"]
    },
    {
        "id": "enfermagem",
        "nome": "Enfermagem",
        "area": "Saúde",
        "emoji": "💊",
        "descricao": "Cuida da saúde das pessoas, aplica procedimentos e auxilia na recuperação. Profissão essencial e de alto impacto humano.",
        "riasec": {"S": 0.95, "R": 0.60, "I": 0.50, "C": 0.55, "A": 0.15, "E": 0.25},
        "personalidade": {"abertura": 0.5, "conscienciosidade": 0.85, "extroversao": 0.6, "amabilidade": 0.95},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "estabilidade"],
        "valores_baixos": ["autonomia", "empreendedorismo"],
        "habilidades_chave": ["S", "R", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 9000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["saúde", "cuidado", "estabilidade"]
    },
    {
        "id": "psicologia",
        "nome": "Psicologia",
        "area": "Saúde / Humanas",
        "emoji": "🧠",
        "descricao": "Estuda o comportamento humano e promove saúde mental. Atua em clínicas, escolas, empresas e hospitais.",
        "riasec": {"S": 0.90, "I": 0.75, "A": 0.50, "E": 0.35, "R": 0.10, "C": 0.40},
        "personalidade": {"abertura": 0.80, "conscienciosidade": 0.70, "extroversao": 0.55, "amabilidade": 0.90},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "aprendizado_continuo", "autonomia"],
        "valores_baixos": ["remuneracao_alta", "tecnologia"],
        "habilidades_chave": ["S", "I", "A"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta",
        "salario_min": 3500, "salario_max": 18000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["saúde mental", "humanas", "terapia"]
    },
    {
        "id": "fisioterapia",
        "nome": "Fisioterapia",
        "area": "Saúde",
        "emoji": "🦴",
        "descricao": "Reabilita e trata disfunções físicas e motoras, trabalhando com o corpo humano através de técnicas manuais e exercícios.",
        "riasec": {"S": 0.85, "R": 0.75, "I": 0.60, "C": 0.45, "A": 0.20, "E": 0.25},
        "personalidade": {"conscienciosidade": 0.80, "amabilidade": 0.90, "abertura": 0.55},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "desafio_intelectual"],
        "valores_baixos": ["remoto", "empreendedorismo"],
        "habilidades_chave": ["S", "R", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 10000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["saúde", "reabilitação", "corpo humano"]
    },
    {
        "id": "nutricao",
        "nome": "Nutrição",
        "area": "Saúde",
        "emoji": "🥗",
        "descricao": "Orienta sobre alimentação saudável e trata condições nutricionais. Atua em clínicas, hospitais, empresas e pesquisa.",
        "riasec": {"S": 0.80, "I": 0.70, "C": 0.55, "R": 0.30, "A": 0.25, "E": 0.35},
        "personalidade": {"conscienciosidade": 0.80, "amabilidade": 0.80, "abertura": 0.60},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "aprendizado_continuo"],
        "valores_baixos": [],
        "habilidades_chave": ["S", "I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 9000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["saúde", "alimentação", "bem-estar"]
    },
    {
        "id": "veterinaria",
        "nome": "Medicina Veterinária",
        "area": "Saúde / Agro",
        "emoji": "🐾",
        "descricao": "Cuida da saúde animal e da sanidade de alimentos. Atua em clínicas, fazendas, indústria alimentícia e saúde pública.",
        "riasec": {"I": 0.80, "S": 0.65, "R": 0.70, "C": 0.45, "A": 0.15, "E": 0.30},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.65, "amabilidade": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "desafio_intelectual"],
        "valores_baixos": [],
        "habilidades_chave": ["I", "R", "S"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 20000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["animais", "saúde", "agronegócio"]
    },
    {
        "id": "farmacia",
        "nome": "Farmácia",
        "area": "Saúde",
        "emoji": "💉",
        "descricao": "Cuida do uso racional de medicamentos, formula produtos e atua em laboratórios clínicos e indústria farmacêutica.",
        "riasec": {"I": 0.85, "C": 0.75, "S": 0.55, "R": 0.40, "A": 0.15, "E": 0.25},
        "personalidade": {"conscienciosidade": 0.90, "abertura": 0.65, "amabilidade": 0.60},
        "valores_altos": ["desafio_intelectual", "estabilidade", "especializacao"],
        "valores_baixos": ["empreendedorismo"],
        "habilidades_chave": ["I", "C", "R"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta",
        "salario_min": 3500, "salario_max": 12000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["ciências", "laboratório", "medicamentos"]
    },

    # ════════════════════ EXATAS / TECNOLOGIA ════════════════════
    {
        "id": "engenharia_civil",
        "nome": "Engenharia Civil",
        "area": "Engenharias",
        "emoji": "🏗️",
        "descricao": "Projeta e supervisiona obras, pontes, estradas e infraestrutura urbana. Uma das profissões mais tradicionais e demandadas no Brasil.",
        "riasec": {"R": 0.85, "I": 0.80, "C": 0.65, "E": 0.45, "A": 0.30, "S": 0.25},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.60, "extroversao": 0.50},
        "valores_altos": ["desafio_intelectual", "resultados", "reconhecimento"],
        "valores_baixos": ["remoto", "humanismo"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4500, "salario_max": 20000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["obras", "infraestrutura", "matemática"]
    },
    {
        "id": "engenharia_computacao",
        "nome": "Engenharia da Computação / Ciência da Computação",
        "area": "Tecnologia",
        "emoji": "💻",
        "descricao": "Desenvolve software, hardware e sistemas computacionais. Mercado aquecido com demanda global e alta remuneração.",
        "riasec": {"I": 0.90, "R": 0.70, "C": 0.65, "A": 0.40, "E": 0.35, "S": 0.20},
        "personalidade": {"conscienciosidade": 0.80, "abertura": 0.80, "extroversao": 0.35},
        "valores_altos": ["desafio_intelectual", "tecnologia", "remuneracao", "aprendizado_continuo", "autonomia"],
        "valores_baixos": ["humanismo"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 5000, "salario_max": 30000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["tecnologia", "programação", "inovação", "remoto"]
    },
    {
        "id": "sistemas_informacao",
        "nome": "Sistemas de Informação / Análise e Desenvolvimento",
        "area": "Tecnologia",
        "emoji": "📱",
        "descricao": "Desenvolve sistemas, apps e soluções tecnológicas para empresas. Porta de entrada rápida para o mercado de tecnologia.",
        "riasec": {"I": 0.80, "C": 0.75, "R": 0.60, "E": 0.40, "A": 0.35, "S": 0.25},
        "personalidade": {"conscienciosidade": 0.80, "abertura": 0.70, "extroversao": 0.35},
        "valores_altos": ["tecnologia", "desafio_intelectual", "remuneracao", "autonomia"],
        "valores_baixos": [],
        "habilidades_chave": ["I", "C", "R"],
        "duracao_anos": 3, "duracao_label": "3 anos",
        "dificuldade_enem": "Média",
        "salario_min": 4000, "salario_max": 20000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["tecnologia", "programação", "curto prazo", "remoto"]
    },
    {
        "id": "engenharia_eletrica",
        "nome": "Engenharia Elétrica / Eletrônica",
        "area": "Engenharias",
        "emoji": "⚡",
        "descricao": "Projeta sistemas elétricos, eletrônicos e de energia. Atua em energia renovável, automação e telecomunicações.",
        "riasec": {"R": 0.85, "I": 0.85, "C": 0.60, "A": 0.20, "E": 0.30, "S": 0.15},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.65},
        "valores_altos": ["desafio_intelectual", "tecnologia", "inovacao", "remuneracao"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 5000, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["energia", "automação", "matemática"]
    },
    {
        "id": "engenharia_mecanica",
        "nome": "Engenharia Mecânica",
        "area": "Engenharias",
        "emoji": "⚙️",
        "descricao": "Projeta máquinas, motores e equipamentos industriais. Base para automação, automotivo e manufatura.",
        "riasec": {"R": 0.90, "I": 0.80, "C": 0.55, "A": 0.20, "E": 0.35, "S": 0.15},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.60},
        "valores_altos": ["desafio_intelectual", "resultados", "tecnologia"],
        "valores_baixos": ["remoto", "ajudar_pessoas"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4500, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["indústria", "máquinas", "automação"]
    },
    {
        "id": "matematica",
        "nome": "Matemática / Estatística",
        "area": "Exatas",
        "emoji": "📐",
        "descricao": "Analisa padrões, modela fenômenos e desenvolve soluções quantitativas. Base para ciência de dados, atuária e pesquisa.",
        "riasec": {"I": 0.90, "C": 0.75, "R": 0.30, "A": 0.30, "S": 0.35, "E": 0.25},
        "personalidade": {"abertura": 0.80, "conscienciosidade": 0.85},
        "valores_altos": ["desafio_intelectual", "especializacao", "aprendizado_continuo"],
        "valores_baixos": ["extroversao_social"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 20000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["ciência de dados", "análise", "academia"]
    },
    {
        "id": "ciencia_dados",
        "nome": "Ciência de Dados / IA",
        "area": "Tecnologia",
        "emoji": "🤖",
        "descricao": "Extrai inteligência de grandes volumes de dados usando machine learning e estatística. Área em explosão com demanda global.",
        "riasec": {"I": 0.95, "C": 0.80, "R": 0.50, "A": 0.30, "E": 0.30, "S": 0.20},
        "personalidade": {"abertura": 0.85, "conscienciosidade": 0.80},
        "valores_altos": ["tecnologia", "desafio_intelectual", "aprendizado_continuo", "remuneracao"],
        "valores_baixos": ["ajudar_pessoas"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "Graduação + especializações",
        "dificuldade_enem": "Alta",
        "salario_min": 6000, "salario_max": 35000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["IA", "machine learning", "big data", "remoto"]
    },
    {
        "id": "fisica",
        "nome": "Física",
        "area": "Exatas",
        "emoji": "🔭",
        "descricao": "Estuda as leis fundamentais do universo. Abre portas para pesquisa, tecnologia e docência de alto nível.",
        "riasec": {"I": 0.95, "R": 0.50, "C": 0.60, "A": 0.30, "S": 0.30, "E": 0.20},
        "personalidade": {"abertura": 0.90, "conscienciosidade": 0.85},
        "valores_altos": ["desafio_intelectual", "aprendizado_continuo", "especializacao", "proposito"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos + pós",
        "dificuldade_enem": "Alta",
        "salario_min": 3500, "salario_max": 16000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["ciência", "pesquisa", "academia"]
    },

    # ════════════════════ HUMANAS / SOCIAIS ════════════════════
    {
        "id": "direito",
        "nome": "Direito",
        "area": "Humanas",
        "emoji": "⚖️",
        "descricao": "Interpreta e aplica a lei para garantir direitos e resolver conflitos. Uma das carreiras mais versáteis e com mais prestígio no Brasil.",
        "riasec": {"E": 0.85, "S": 0.70, "I": 0.75, "C": 0.70, "A": 0.45, "R": 0.10},
        "personalidade": {"extroversao": 0.70, "conscienciosidade": 0.85, "abertura": 0.70, "amabilidade": 0.55},
        "valores_altos": ["reconhecimento", "prestigio", "lideranca", "impacto_social"],
        "valores_baixos": ["remoto"],
        "habilidades_chave": ["E", "S", "I", "A"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 50000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["justiça", "debate", "prestígio", "versatilidade"]
    },
    {
        "id": "pedagogia",
        "nome": "Pedagogia / Licenciaturas",
        "area": "Educação",
        "emoji": "📚",
        "descricao": "Forma educadores para transformar vidas através do ensino. Alta empregabilidade via concurso público em todo o Brasil.",
        "riasec": {"S": 0.95, "A": 0.55, "I": 0.55, "C": 0.50, "E": 0.45, "R": 0.15},
        "personalidade": {"amabilidade": 0.95, "extroversao": 0.70, "abertura": 0.70},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "estabilidade", "proposito"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["S", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média",
        "salario_min": 2800, "salario_max": 9000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["educação", "transformação social", "estabilidade"]
    },
    {
        "id": "historia",
        "nome": "História / Ciências Sociais",
        "area": "Humanas",
        "emoji": "🏛️",
        "descricao": "Analisa o passado e o presente da humanidade, formando cidadãos críticos. Carreira docente ou pesquisa.",
        "riasec": {"I": 0.75, "S": 0.70, "A": 0.65, "C": 0.45, "E": 0.35, "R": 0.10},
        "personalidade": {"abertura": 0.90, "amabilidade": 0.70},
        "valores_altos": ["proposito", "impacto_social", "aprendizado_continuo", "humanismo"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["I", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2800, "salario_max": 8000,
        "perspectiva_mercado": "Estável",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["humanidades", "educação", "pesquisa"]
    },
    {
        "id": "relacoes_internacionais",
        "nome": "Relações Internacionais",
        "area": "Humanas / Negócios",
        "emoji": "🌐",
        "descricao": "Estuda política global, diplomacia e negócios internacionais. Para quem quer atuar no mundo globalizado.",
        "riasec": {"E": 0.75, "S": 0.70, "I": 0.70, "A": 0.55, "C": 0.50, "R": 0.10},
        "personalidade": {"extroversao": 0.75, "abertura": 0.85, "amabilidade": 0.70},
        "valores_altos": ["impacto_social", "reconhecimento", "lideranca", "autonomia", "centros_urbanos"],
        "valores_baixos": ["interior_preferencia"],
        "habilidades_chave": ["E", "S", "I", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 18000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["diplomacia", "globalização", "idiomas"]
    },
    {
        "id": "servico_social",
        "nome": "Serviço Social",
        "area": "Humanas",
        "emoji": "🤝",
        "descricao": "Combate desigualdades e garante direitos de populações vulneráveis. Missão de transformação social real.",
        "riasec": {"S": 0.95, "E": 0.55, "I": 0.50, "C": 0.55, "A": 0.35, "R": 0.15},
        "personalidade": {"amabilidade": 0.95, "extroversao": 0.65, "abertura": 0.70},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "proposito", "humanismo"],
        "valores_baixos": ["remuneracao", "prestigio"],
        "habilidades_chave": ["S", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 2500, "salario_max": 7000,
        "perspectiva_mercado": "Estável",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["assistência social", "vulneráveis", "direitos"]
    },
    {
        "id": "filosofia_sociologia",
        "nome": "Filosofia / Sociologia",
        "area": "Humanas",
        "emoji": "💭",
        "descricao": "Investiga questões fundamentais sobre existência, sociedade e ética. Forma pensadores críticos e educadores.",
        "riasec": {"I": 0.80, "A": 0.75, "S": 0.65, "C": 0.35, "E": 0.30, "R": 0.05},
        "personalidade": {"abertura": 0.95, "amabilidade": 0.65},
        "valores_altos": ["proposito", "aprendizado_continuo", "humanismo", "autonomia"],
        "valores_baixos": ["remuneracao", "tecnologia"],
        "habilidades_chave": ["I", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2500, "salario_max": 7000,
        "perspectiva_mercado": "Estável",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["pensamento crítico", "academia", "educação"]
    },

    # ════════════════════ NEGÓCIOS / GESTÃO ════════════════════
    {
        "id": "administracao",
        "nome": "Administração",
        "area": "Negócios",
        "emoji": "📊",
        "descricao": "Gerencia recursos, processos e pessoas em organizações. A graduação mais versátil do mercado brasileiro.",
        "riasec": {"E": 0.85, "C": 0.75, "S": 0.60, "I": 0.55, "A": 0.35, "R": 0.20},
        "personalidade": {"extroversao": 0.70, "conscienciosidade": 0.80, "amabilidade": 0.60},
        "valores_altos": ["lideranca", "resultados", "reconhecimento", "autonomia"],
        "valores_baixos": ["humanismo"],
        "habilidades_chave": ["E", "C", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 20000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["gestão", "versatilidade", "liderança", "negócios"]
    },
    {
        "id": "economia",
        "nome": "Economia",
        "area": "Negócios / Exatas",
        "emoji": "📈",
        "descricao": "Analisa mercados, políticas econômicas e comportamento financeiro. Perfil analítico com alta remuneração.",
        "riasec": {"I": 0.85, "C": 0.80, "E": 0.65, "A": 0.30, "S": 0.35, "R": 0.15},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.75},
        "valores_altos": ["desafio_intelectual", "remuneracao", "resultados", "aprendizado_continuo"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["I", "C", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 5000, "salario_max": 30000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["finanças", "mercado", "análise"]
    },
    {
        "id": "contabilidade",
        "nome": "Contabilidade / Ciências Contábeis",
        "area": "Negócios",
        "emoji": "🧾",
        "descricao": "Controla e analisa o patrimônio de organizações. Alta demanda, estabilidade e possibilidade de carreira própria.",
        "riasec": {"C": 0.90, "I": 0.70, "E": 0.55, "S": 0.35, "R": 0.20, "A": 0.15},
        "personalidade": {"conscienciosidade": 0.90, "extroversao": 0.40},
        "valores_altos": ["estabilidade", "remuneracao", "resultados", "especializacao"],
        "valores_baixos": ["inovacao", "autonomia"],
        "habilidades_chave": ["C", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média",
        "salario_min": 3000, "salario_max": 15000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["finanças", "estabilidade", "números"]
    },
    {
        "id": "marketing",
        "nome": "Marketing / Comunicação Empresarial",
        "area": "Negócios / Comunicação",
        "emoji": "📣",
        "descricao": "Estratégia de marca, comportamento do consumidor e comunicação. Une criatividade e dados para gerar resultados.",
        "riasec": {"E": 0.80, "A": 0.70, "S": 0.65, "C": 0.50, "I": 0.55, "R": 0.15},
        "personalidade": {"extroversao": 0.75, "abertura": 0.80, "conscienciosidade": 0.65},
        "valores_altos": ["inovacao", "resultados", "reconhecimento", "tecnologia"],
        "valores_baixos": ["humanismo"],
        "habilidades_chave": ["E", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["criatividade", "dados", "brand", "digital"]
    },
    {
        "id": "gestao_publica",
        "nome": "Gestão Pública / Políticas Públicas",
        "area": "Negócios / Humanas",
        "emoji": "🏛️",
        "descricao": "Administra recursos do Estado para melhorar serviços públicos e a vida da população.",
        "riasec": {"E": 0.75, "S": 0.75, "I": 0.65, "C": 0.70, "A": 0.35, "R": 0.15},
        "personalidade": {"conscienciosidade": 0.80, "amabilidade": 0.70, "extroversao": 0.60},
        "valores_altos": ["impacto_social", "estabilidade", "proposito", "lideranca"],
        "valores_baixos": ["remuneracao_alta", "empreendedorismo"],
        "habilidades_chave": ["E", "S", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3500, "salario_max": 15000,
        "perspectiva_mercado": "Estável",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["governo", "políticas públicas", "impacto social"]
    },

    # ════════════════════ COMUNICAÇÃO / ARTES ════════════════════
    {
        "id": "jornalismo",
        "nome": "Jornalismo / Comunicação",
        "area": "Comunicação",
        "emoji": "📰",
        "descricao": "Investiga, apura e comunica fatos relevantes à sociedade. Profissão de impacto social com diferentes plataformas.",
        "riasec": {"A": 0.80, "S": 0.75, "E": 0.65, "I": 0.60, "C": 0.35, "R": 0.10},
        "personalidade": {"extroversao": 0.75, "abertura": 0.85, "amabilidade": 0.65},
        "valores_altos": ["impacto_social", "inovacao", "proposito", "autonomia"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["A", "S", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2500, "salario_max": 14000,
        "perspectiva_mercado": "Em transformação",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["mídia", "escrita", "impacto social", "digital"]
    },
    {
        "id": "publicidade",
        "nome": "Publicidade e Propaganda",
        "area": "Comunicação",
        "emoji": "📢",
        "descricao": "Cria campanhas e estratégias de comunicação para marcas. Une criatividade, psicologia do consumidor e dados.",
        "riasec": {"A": 0.85, "E": 0.80, "S": 0.60, "I": 0.50, "C": 0.40, "R": 0.15},
        "personalidade": {"abertura": 0.85, "extroversao": 0.80, "conscienciosidade": 0.60},
        "valores_altos": ["inovacao", "resultados", "autonomia", "tecnologia"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["A", "E", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2800, "salario_max": 20000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["criatividade", "branding", "digital", "agências"]
    },
    {
        "id": "design",
        "nome": "Design Gráfico / UX Design",
        "area": "Comunicação / Tecnologia",
        "emoji": "🎨",
        "descricao": "Cria soluções visuais e experiências digitais que comunicam e encantam. Muito demandado no mercado digital.",
        "riasec": {"A": 0.95, "I": 0.60, "R": 0.55, "E": 0.45, "S": 0.40, "C": 0.35},
        "personalidade": {"abertura": 0.95, "conscienciosidade": 0.65},
        "valores_altos": ["inovacao", "autonomia", "criatividade", "tecnologia"],
        "valores_baixos": ["concurso_empresa", "convencional"],
        "habilidades_chave": ["A", "R", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos (ou cursos livres)",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["criatividade", "visual", "UX", "digital", "remoto"]
    },
    {
        "id": "arquitetura",
        "nome": "Arquitetura e Urbanismo",
        "area": "Artes / Exatas",
        "emoji": "🏠",
        "descricao": "Projeta espaços que unem funcionalidade, estética e humanidade. Profissão que exige criatividade e raciocínio técnico.",
        "riasec": {"A": 0.85, "R": 0.75, "I": 0.65, "E": 0.45, "C": 0.55, "S": 0.35},
        "personalidade": {"abertura": 0.85, "conscienciosidade": 0.75},
        "valores_altos": ["inovacao", "reconhecimento", "autonomia", "impacto_social"],
        "valores_baixos": ["remoto"],
        "habilidades_chave": ["A", "R", "I"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 3500, "salario_max": 16000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["arte", "espaços", "técnico", "criativo"]
    },
    {
        "id": "musica",
        "nome": "Música / Artes Cênicas / Teatro",
        "area": "Artes",
        "emoji": "🎵",
        "descricao": "Expressa a humanidade através da arte. Carreira com múltiplos caminhos: performance, ensino, produção e indústria criativa.",
        "riasec": {"A": 0.95, "S": 0.60, "E": 0.55, "I": 0.45, "R": 0.30, "C": 0.20},
        "personalidade": {"abertura": 0.95, "extroversao": 0.65},
        "valores_altos": ["autonomia", "proposito", "satisfacao_pessoal", "inovacao"],
        "valores_baixos": ["remuneracao", "estabilidade", "concurso_empresa"],
        "habilidades_chave": ["A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 1800, "salario_max": 12000,
        "perspectiva_mercado": "Desafiadora",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["arte", "expressão", "cultura", "independência"]
    },
    {
        "id": "cinema_audiovisual",
        "nome": "Cinema / Audiovisual / Produção de Conteúdo",
        "area": "Comunicação / Artes",
        "emoji": "🎬",
        "descricao": "Cria narrativas visuais para cinema, streaming e redes sociais. Mercado em crescimento com a economia criativa digital.",
        "riasec": {"A": 0.90, "E": 0.65, "I": 0.55, "S": 0.55, "R": 0.45, "C": 0.30},
        "personalidade": {"abertura": 0.90, "extroversao": 0.60},
        "valores_altos": ["inovacao", "autonomia", "proposito", "tecnologia"],
        "valores_baixos": ["estabilidade", "convencional"],
        "habilidades_chave": ["A", "E", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2500, "salario_max": 20000,
        "perspectiva_mercado": "Em crescimento",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["streaming", "criativo", "digital", "narrativa"]
    },
    {
        "id": "letras",
        "nome": "Letras / Literatura / Tradução",
        "area": "Humanas / Comunicação",
        "emoji": "📝",
        "descricao": "Estuda língua e literatura para comunicar, ensinar e traduzir. Forma professores, escritores, revisores e tradutores.",
        "riasec": {"A": 0.85, "I": 0.65, "S": 0.65, "C": 0.45, "E": 0.30, "R": 0.10},
        "personalidade": {"abertura": 0.90, "amabilidade": 0.70},
        "valores_altos": ["aprendizado_continuo", "autonomia", "proposito", "humanismo"],
        "valores_baixos": ["tecnologia", "remuneracao"],
        "habilidades_chave": ["A", "I", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2500, "salario_max": 10000,
        "perspectiva_mercado": "Estável",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["linguagem", "escrita", "educação", "tradução"]
    },

    # ════════════════════ AGRO / MEIO AMBIENTE ════════════════════
    {
        "id": "agronomia",
        "nome": "Agronomia",
        "area": "Agronegócio",
        "emoji": "🌾",
        "descricao": "Desenvolve e melhora a produção agrícola e o agronegócio. Setor que movimenta a maior parte do PIB brasileiro.",
        "riasec": {"R": 0.85, "I": 0.75, "C": 0.55, "S": 0.40, "E": 0.50, "A": 0.20},
        "personalidade": {"conscienciosidade": 0.80, "abertura": 0.65},
        "valores_altos": ["impacto_social", "desafio_intelectual", "remuneracao", "resultados"],
        "valores_baixos": ["centros_urbanos", "remoto"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta",
        "salario_min": 4000, "salario_max": 20000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["campo", "agronegócio", "sustentabilidade"]
    },
    {
        "id": "biologia",
        "nome": "Ciências Biológicas",
        "area": "Ciências",
        "emoji": "🧬",
        "descricao": "Estuda a vida em todas as suas formas. Base para biotecnologia, medicina, ecologia e docência.",
        "riasec": {"I": 0.90, "R": 0.65, "S": 0.55, "C": 0.50, "A": 0.35, "E": 0.25},
        "personalidade": {"abertura": 0.85, "conscienciosidade": 0.80},
        "valores_altos": ["desafio_intelectual", "proposito", "aprendizado_continuo", "especializacao"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["I", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média-alta",
        "salario_min": 3000, "salario_max": 12000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["ciência", "natureza", "pesquisa", "lab"]
    },
    {
        "id": "engenharia_ambiental",
        "nome": "Engenharia Ambiental / Gestão Ambiental",
        "area": "Engenharias / Meio Ambiente",
        "emoji": "🌱",
        "descricao": "Protege o meio ambiente e desenvolve soluções sustentáveis. Área em crescimento com a agenda climática global.",
        "riasec": {"R": 0.75, "I": 0.80, "S": 0.55, "C": 0.60, "E": 0.45, "A": 0.35},
        "personalidade": {"abertura": 0.80, "conscienciosidade": 0.75},
        "valores_altos": ["impacto_social", "proposito", "inovacao", "desafio_intelectual"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 16000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["sustentabilidade", "natureza", "clima", "engenharia"]
    },
    {
        "id": "engenharia_florestal",
        "nome": "Engenharia Florestal",
        "area": "Agronegócio / Meio Ambiente",
        "emoji": "🌳",
        "descricao": "Maneja florestas e recursos naturais de forma sustentável, combatendo o desmatamento e gerindo a biodiversidade.",
        "riasec": {"R": 0.85, "I": 0.70, "C": 0.50, "S": 0.40, "E": 0.40, "A": 0.20},
        "personalidade": {"abertura": 0.70, "conscienciosidade": 0.75},
        "valores_altos": ["proposito", "impacto_social", "flexibilidade_local", "natureza"],
        "valores_baixos": ["centros_urbanos", "tecnologia_pura"],
        "habilidades_chave": ["R", "I"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3500, "salario_max": 12000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["florestas", "sustentabilidade", "campo"]
    },

    # ════════════════════ CARREIRAS MILITARES / SEGURANÇA ════════════════════
    {
        "id": "forças_armadas",
        "nome": "Forças Armadas (Exército, Marinha, Aeronáutica)",
        "area": "Segurança / Defesa",
        "emoji": "🎖️",
        "descricao": "Defesa nacional e missões humanitárias. Carreira com formação completa, estabilidade e progressão hierárquica clara.",
        "riasec": {"E": 0.80, "R": 0.80, "C": 0.70, "S": 0.55, "I": 0.45, "A": 0.20},
        "personalidade": {"conscienciosidade": 0.95, "extroversao": 0.60},
        "valores_altos": ["estabilidade", "reconhecimento", "lideranca", "proposito", "resultados"],
        "valores_baixos": ["autonomia", "empreendedorismo", "remoto"],
        "habilidades_chave": ["E", "R", "C"],
        "duracao_anos": 4, "duracao_label": "Formação nas academias militares",
        "dificuldade_enem": "Alta",
        "salario_min": 4500, "salario_max": 20000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["estabilidade", "hierarquia", "disciplina", "defesa"]
    },
    {
        "id": "segurança_publica",
        "nome": "Segurança Pública (Delegado, Policial, Perito)",
        "area": "Segurança",
        "emoji": "🚔",
        "descricao": "Investiga crimes, mantém a ordem e garante a segurança da população. Diversas carreiras com concurso público.",
        "riasec": {"E": 0.80, "R": 0.70, "I": 0.65, "C": 0.75, "S": 0.55, "A": 0.15},
        "personalidade": {"conscienciosidade": 0.90, "extroversao": 0.60},
        "valores_altos": ["impacto_social", "estabilidade", "resultados", "proposito"],
        "valores_baixos": ["autonomia", "empreendedorismo"],
        "habilidades_chave": ["E", "I", "C"],
        "duracao_anos": 4, "duracao_label": "Concurso público + formação",
        "dificuldade_enem": "Alta (concurso próprio)",
        "salario_min": 4000, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["justiça", "concurso", "estabilidade", "investigação"]
    },
    {
        "id": "bombeiro",
        "nome": "Corpo de Bombeiros / Defesa Civil",
        "area": "Segurança",
        "emoji": "🚒",
        "descricao": "Salva vidas em situações de emergência e desastre. Carreira de alto impacto humano e senso de missão.",
        "riasec": {"S": 0.80, "R": 0.85, "E": 0.65, "C": 0.50, "I": 0.45, "A": 0.15},
        "personalidade": {"conscienciosidade": 0.90, "extroversao": 0.65, "amabilidade": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "proposito", "estabilidade"],
        "valores_baixos": ["autonomia", "remoto"],
        "habilidades_chave": ["S", "R", "E"],
        "duracao_anos": 2, "duracao_label": "Concurso + formação",
        "dificuldade_enem": "Média",
        "salario_min": 3500, "salario_max": 12000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["missão", "ajudar", "ação", "concurso"]
    },

    # ════════════════════ CARREIRAS TÉCNICAS / CURTO PRAZO ════════════════════
    {
        "id": "tecnico_informatica",
        "nome": "Técnico em Informática / Redes",
        "area": "Tecnologia",
        "emoji": "🖥️",
        "descricao": "Instala, mantém e configura sistemas de computação e redes. Entrada rápida no mercado de tecnologia.",
        "riasec": {"R": 0.80, "I": 0.70, "C": 0.65, "A": 0.25, "S": 0.25, "E": 0.30},
        "personalidade": {"conscienciosidade": 0.75, "abertura": 0.60},
        "valores_altos": ["tecnologia", "estabilidade", "aprendizado_continuo"],
        "valores_baixos": ["lideranca"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 2000, "salario_max": 8000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["tecnologia", "curto prazo", "redes", "suporte"]
    },
    {
        "id": "tecnico_saude",
        "nome": "Técnico em Saúde (Enfermagem, Radiologia, Análises Clínicas)",
        "area": "Saúde",
        "emoji": "🏥",
        "descricao": "Auxilia profissionais de saúde em procedimentos clínicos. Entrada rápida no setor de saúde com alta empregabilidade.",
        "riasec": {"S": 0.85, "R": 0.70, "C": 0.65, "I": 0.45, "A": 0.15, "E": 0.20},
        "personalidade": {"amabilidade": 0.90, "conscienciosidade": 0.85},
        "valores_altos": ["ajudar_pessoas", "estabilidade", "impacto_social"],
        "valores_baixos": ["autonomia", "remoto"],
        "habilidades_chave": ["S", "R", "C"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 1800, "salario_max": 5000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["saúde", "curto prazo", "empregabilidade alta"]
    },
    {
        "id": "tecnico_eletrotecnica",
        "nome": "Técnico em Eletrotécnica / Mecatrônica",
        "area": "Técnico / Indústria",
        "emoji": "🔌",
        "descricao": "Instala e mantém sistemas elétricos e automação industrial. Mercado sólido na indústria brasileira.",
        "riasec": {"R": 0.90, "I": 0.65, "C": 0.60, "A": 0.15, "S": 0.20, "E": 0.25},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.50},
        "valores_altos": ["estabilidade", "resultados", "tecnologia"],
        "valores_baixos": ["autonomia", "arte"],
        "habilidades_chave": ["R", "I"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 2200, "salario_max": 7000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["indústria", "curto prazo", "técnico", "elétrica"]
    },
    {
        "id": "tecnico_contabilidade",
        "nome": "Técnico em Contabilidade / Administração",
        "area": "Negócios",
        "emoji": "📁",
        "descricao": "Auxilia na gestão financeira e administrativa de empresas. Porta de entrada para o mundo dos negócios.",
        "riasec": {"C": 0.90, "E": 0.55, "I": 0.50, "S": 0.35, "R": 0.20, "A": 0.15},
        "personalidade": {"conscienciosidade": 0.90},
        "valores_altos": ["estabilidade", "resultados", "aprendizado_continuo"],
        "valores_baixos": [],
        "habilidades_chave": ["C", "E"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 1800, "salario_max": 5000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["finanças", "curto prazo", "escritório"]
    },

    # ════════════════════ CARREIRA PÚBLICA / CONCURSOS ════════════════════
    {
        "id": "auditoria_fiscal",
        "nome": "Auditor Fiscal / Analista Tributário",
        "area": "Serviço Público",
        "emoji": "📑",
        "descricao": "Fiscaliza tributos e garante a arrecadação pública. Uma das carreiras públicas com maior remuneração no Brasil.",
        "riasec": {"C": 0.90, "I": 0.75, "E": 0.55, "S": 0.30, "R": 0.20, "A": 0.15},
        "personalidade": {"conscienciosidade": 0.95, "abertura": 0.60},
        "valores_altos": ["estabilidade", "remuneracao", "resultados", "especializacao"],
        "valores_baixos": ["empreendedorismo", "inovacao"],
        "habilidades_chave": ["C", "I"],
        "duracao_anos": 4, "duracao_label": "Graduação + preparação concurso",
        "dificuldade_enem": "Alta",
        "salario_min": 10000, "salario_max": 30000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": True,
        "tags": ["concurso", "alta renda", "estabilidade", "números"]
    },
    {
        "id": "magistratura",
        "nome": "Magistratura / Ministério Público",
        "area": "Serviço Público / Direito",
        "emoji": "⚖️",
        "descricao": "Julga casos e defende a sociedade como juiz ou promotor. As carreiras jurídicas públicas mais prestigiadas do Brasil.",
        "riasec": {"E": 0.80, "I": 0.85, "C": 0.75, "S": 0.55, "A": 0.40, "R": 0.10},
        "personalidade": {"conscienciosidade": 0.95, "abertura": 0.75, "extroversao": 0.55},
        "valores_altos": ["prestigio", "impacto_social", "remuneracao", "estabilidade", "especializacao"],
        "valores_baixos": ["empreendedorismo", "autonomia"],
        "habilidades_chave": ["I", "E", "C", "A"],
        "duracao_anos": 8, "duracao_label": "5 anos Direito + concurso (anos)",
        "dificuldade_enem": "Alta",
        "salario_min": 20000, "salario_max": 50000,
        "perspectiva_mercado": "Excelente",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["prestígio", "alta renda", "concurso", "longo prazo"]
    },
    {
        "id": "diplomacia",
        "nome": "Diplomacia (Itamaraty)",
        "area": "Serviço Público / Internacional",
        "emoji": "🌐",
        "descricao": "Representa o Brasil no exterior e conduz a política externa nacional. Uma das carreiras públicas mais exclusivas e prestigiadas.",
        "riasec": {"E": 0.75, "I": 0.80, "S": 0.70, "A": 0.60, "C": 0.60, "R": 0.10},
        "personalidade": {"extroversao": 0.70, "abertura": 0.90, "conscienciosidade": 0.85, "amabilidade": 0.70},
        "valores_altos": ["prestigio", "impacto_social", "aprendizado_continuo", "centros_urbanos"],
        "valores_baixos": ["interior_preferencia", "empreendedorismo"],
        "habilidades_chave": ["E", "I", "S", "A"],
        "duracao_anos": 7, "duracao_label": "Graduação + CACD (concurso dificílimo)",
        "dificuldade_enem": "Altíssima",
        "salario_min": 12000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["prestígio", "idiomas", "relações internacionais", "concurso"]
    },

    # ════════════════════ EMPREENDEDORISMO / NOVOS MERCADOS ════════════════════
    {
        "id": "startups_negocios",
        "nome": "Empreendedorismo / Startups",
        "area": "Negócios",
        "emoji": "🚀",
        "descricao": "Criação de empresas e soluções inovadoras. Carreira não-linear de alto risco e alto retorno potencial.",
        "riasec": {"E": 0.95, "I": 0.70, "A": 0.65, "S": 0.55, "C": 0.50, "R": 0.35},
        "personalidade": {"abertura": 0.85, "extroversao": 0.75, "conscienciosidade": 0.70},
        "valores_altos": ["autonomia", "inovacao", "empreendedorismo", "lideranca", "remuneracao"],
        "valores_baixos": ["estabilidade", "concurso_empresa"],
        "habilidades_chave": ["E", "I", "A"],
        "duracao_anos": 4, "duracao_label": "Qualquer graduação + visão de mercado",
        "dificuldade_enem": "Variável",
        "salario_min": 0, "salario_max": 100000,
        "perspectiva_mercado": "Alto risco / Alta recompensa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["risco", "inovação", "liberdade", "liderança"]
    },
    {
        "id": "creator_digital",
        "nome": "Criador de Conteúdo Digital / Influencer",
        "area": "Comunicação / Criativo",
        "emoji": "📲",
        "descricao": "Produz conteúdo em plataformas digitais para audiências segmentadas. Nova carreira com grande potencial de monetização.",
        "riasec": {"A": 0.85, "E": 0.80, "S": 0.70, "I": 0.45, "C": 0.35, "R": 0.30},
        "personalidade": {"extroversao": 0.80, "abertura": 0.90},
        "valores_altos": ["autonomia", "inovacao", "empreendedorismo", "tecnologia", "reconhecimento"],
        "valores_baixos": ["estabilidade", "concurso_empresa", "hierarquia"],
        "habilidades_chave": ["A", "E", "S"],
        "duracao_anos": 1, "duracao_label": "Aprendizado prático / cursos",
        "dificuldade_enem": "Baixa",
        "salario_min": 0, "salario_max": 50000,
        "perspectiva_mercado": "Alta variabilidade",
        "modalidade": ["ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["digital", "criativo", "empreendedor", "redes sociais"]
    },
    {
        "id": "moda_estilo",
        "nome": "Moda / Estilismo / Produção Cultural",
        "area": "Artes / Comunicação",
        "emoji": "👗",
        "descricao": "Cria e produz coleções, identidades visuais e eventos culturais. Mercado criativo com forte presença no Brasil.",
        "riasec": {"A": 0.90, "E": 0.65, "S": 0.55, "I": 0.40, "R": 0.45, "C": 0.30},
        "personalidade": {"abertura": 0.90, "extroversao": 0.70},
        "valores_altos": ["inovacao", "autonomia", "satisfacao_pessoal", "reconhecimento"],
        "valores_baixos": ["estabilidade", "tecnologia_pura"],
        "habilidades_chave": ["A", "E", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 2000, "salario_max": 15000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["criatividade", "estética", "arte", "mercado fashion"]
    },
    {
        "id": "gastronomia",
        "nome": "Gastronomia / Chef",
        "area": "Artes / Serviços",
        "emoji": "👨‍🍳",
        "descricao": "Cria experiências gastronômicas, gerencia cozinhas e desenvolve a cultura alimentar. Mercado em crescimento no Brasil.",
        "riasec": {"A": 0.80, "R": 0.75, "E": 0.60, "S": 0.55, "I": 0.40, "C": 0.45},
        "personalidade": {"abertura": 0.80, "conscienciosidade": 0.75},
        "valores_altos": ["inovacao", "satisfacao_pessoal", "autonomia"],
        "valores_baixos": ["remoto", "estabilidade"],
        "habilidades_chave": ["A", "R", "E"],
        "duracao_anos": 2, "duracao_label": "2 a 4 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 2000, "salario_max": 15000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["culinária", "criativo", "restaurante", "empreendimento"]
    },

    # ════════════════════ ESPORTE / EDUCAÇÃO FÍSICA ════════════════════
    {
        "id": "educacao_fisica",
        "nome": "Educação Física / Esporte",
        "area": "Saúde / Educação",
        "emoji": "⚽",
        "descricao": "Promove saúde, desempenho atlético e qualidade de vida através do movimento. Alta versatilidade de atuação.",
        "riasec": {"S": 0.85, "R": 0.80, "E": 0.60, "I": 0.45, "A": 0.30, "C": 0.35},
        "personalidade": {"extroversao": 0.80, "amabilidade": 0.75, "conscienciosidade": 0.70},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "autonomia", "equilibrio"],
        "valores_baixos": ["remuneracao", "concurso"],
        "habilidades_chave": ["S", "R", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média",
        "salario_min": 2500, "salario_max": 12000,
        "perspectiva_mercado": "Boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["esporte", "saúde", "atividade física", "pessoas"]
    },

    # ════════════════════ ENGENHARIA DE PRODUÇÃO / LOGÍSTICA ════════════════════
    {
        "id": "engenharia_producao",
        "nome": "Engenharia de Produção / Logística",
        "area": "Engenharias / Negócios",
        "emoji": "🏭",
        "descricao": "Otimiza processos produtivos, cadeias de suprimentos e gestão industrial. Ótima remuneração com alta versatilidade.",
        "riasec": {"C": 0.80, "I": 0.80, "R": 0.65, "E": 0.65, "A": 0.25, "S": 0.30},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.65, "extroversao": 0.55},
        "valores_altos": ["resultados", "desafio_intelectual", "tecnologia", "remuneracao"],
        "valores_baixos": ["humanismo", "arte"],
        "habilidades_chave": ["C", "I", "E"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 5000, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": True,
        "tags": ["indústria", "processos", "logística", "gestão"]
    },
    {
        "id": "quimica",
        "nome": "Química / Engenharia Química",
        "area": "Exatas / Indústria",
        "emoji": "⚗️",
        "descricao": "Estuda a composição da matéria e desenvolve processos industriais. Base para petróleo, farmácia, cosméticos e alimentos.",
        "riasec": {"I": 0.90, "R": 0.70, "C": 0.60, "A": 0.25, "S": 0.30, "E": 0.30},
        "personalidade": {"conscienciosidade": 0.85, "abertura": 0.70},
        "valores_altos": ["desafio_intelectual", "tecnologia", "especializacao", "aprendizado_continuo"],
        "valores_baixos": ["extroversao_social"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "4 a 5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 4000, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["ciência", "lab", "indústria", "petróleo"]
    },
    {
        "id": "turismo_hotelaria",
        "nome": "Turismo / Hotelaria / Eventos",
        "area": "Serviços",
        "emoji": "✈️",
        "descricao": "Organiza experiências de viagem, hospedagem e eventos. Carreira para quem ama pessoas, culturas e o mundo.",
        "riasec": {"E": 0.75, "S": 0.80, "A": 0.65, "C": 0.55, "I": 0.40, "R": 0.25},
        "personalidade": {"extroversao": 0.85, "abertura": 0.80, "amabilidade": 0.75},
        "valores_altos": ["ajudar_pessoas", "autonomia", "satisfacao_pessoal", "inovacao"],
        "valores_baixos": ["estabilidade"],
        "habilidades_chave": ["E", "S", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa",
        "salario_min": 2000, "salario_max": 10000,
        "perspectiva_mercado": "Em recuperação",
        "modalidade": ["presencial", "ead"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["viagens", "pessoas", "eventos", "cultura"]
    },
    {
        "id": "fonoaudiologia",
        "nome": "Fonoaudiologia",
        "area": "Saúde",
        "emoji": "🗣️",
        "descricao": "Trata distúrbios da voz, fala, audição e linguagem. Especialidade única com alta demanda em todos os ciclos de vida.",
        "riasec": {"S": 0.90, "I": 0.70, "C": 0.55, "R": 0.35, "A": 0.35, "E": 0.30},
        "personalidade": {"amabilidade": 0.90, "conscienciosidade": 0.80, "abertura": 0.65},
        "valores_altos": ["ajudar_pessoas", "especializacao", "impacto_social"],
        "valores_baixos": ["lideranca", "empreendedorismo"],
        "habilidades_chave": ["S", "I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média",
        "salario_min": 3000, "salario_max": 10000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": True,
        "remoto_opcao": False,
        "tags": ["saúde", "linguagem", "voz", "neurologia"]
    },
    {
        "id": "odontologia",
        "nome": "Odontologia",
        "area": "Saúde",
        "emoji": "🦷",
        "descricao": "Cuida da saúde bucal e realiza procedimentos dentários. Alta autonomia profissional com possibilidade de consultório próprio.",
        "riasec": {"I": 0.80, "S": 0.75, "R": 0.70, "C": 0.55, "E": 0.50, "A": 0.30},
        "personalidade": {"conscienciosidade": 0.90, "amabilidade": 0.75},
        "valores_altos": ["autonomia", "remuneracao", "especializacao", "empreendedorismo"],
        "valores_baixos": ["impacto_social_macro"],
        "habilidades_chave": ["I", "R", "S"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta",
        "salario_min": 5000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa",
        "modalidade": ["presencial"],
        "concurso_opcao": False,
        "remoto_opcao": False,
        "tags": ["saúde", "autônomo", "precisão", "clínica própria"]
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PERFIS RIASEC — descrições e cores para o resultado
# ─────────────────────────────────────────────────────────────────────────────

PERFIS_RIASEC = {
    "R": {
        "nome": "Realista",
        "emoji": "🔧",
        "cor": "#f97316",
        "cor_bg": "rgba(249, 115, 22, 0.15)",
        "descricao_curta": "Prático, técnico e concreto",
        "descricao": "Você tem perfil Realista! Prefere trabalhar com as mãos, ferramentas, máquinas ou em contato com a natureza. É direto, prático e resolve problemas de forma concreta. Se realiza quando vê resultados tangíveis do seu trabalho.",
        "pontos_fortes": ["Trabalho técnico e prático", "Habilidade manual e mecânica", "Pensamento concreto e objetivo", "Persistência e foco"],
        "ambientes_ideais": ["Obras e construção", "Indústria e manufatura", "Campo e natureza", "Laboratórios práticos", "Manutenção e reparos"],
    },
    "I": {
        "nome": "Investigativo",
        "emoji": "🔬",
        "cor": "#3b82f6",
        "cor_bg": "rgba(59, 130, 246, 0.15)",
        "descricao_curta": "Analítico, curioso e científico",
        "descricao": "Você tem perfil Investigativo! Adora explorar, questionar e entender como as coisas funcionam. Pensa de forma analítica, gosta de dados e argumentos lógicos. Se realiza resolvendo problemas complexos e expandindo o conhecimento.",
        "pontos_fortes": ["Raciocínio lógico e analítico", "Curiosidade intelectual profunda", "Pesquisa e investigação", "Pensamento crítico"],
        "ambientes_ideais": ["Laboratórios e pesquisa", "Academia e ciência", "Tecnologia e dados", "Saúde e diagnóstico", "Consultoria e análise"],
    },
    "A": {
        "nome": "Artístico",
        "emoji": "🎨",
        "cor": "#ec4899",
        "cor_bg": "rgba(236, 72, 153, 0.15)",
        "descricao_curta": "Criativo, expressivo e inovador",
        "descricao": "Você tem perfil Artístico! É criativo, imaginativo e valoriza a originalidade. Gosta de expressar ideias de formas únicas e se incomoda com rotinas muito rígidas. Se realiza em ambientes que valorizam inovação e liberdade de criação.",
        "pontos_fortes": ["Criatividade e originalidade", "Sensibilidade estética", "Comunicação expressiva", "Inovação e pensamento não-linear"],
        "ambientes_ideais": ["Design e artes visuais", "Escrita e comunicação", "Música e artes cênicas", "Publicidade e criação", "Arquitetura e moda"],
    },
    "S": {
        "nome": "Social",
        "emoji": "🤝",
        "cor": "#22c55e",
        "cor_bg": "rgba(34, 197, 94, 0.15)",
        "descricao_curta": "Empático, colaborativo e humanista",
        "descricao": "Você tem perfil Social! Seu poder está nas pessoas. É empático, comunicativo e genuinamente se importa com o bem-estar alheio. Se realiza quando pode ensinar, ajudar, cuidar ou colaborar com outros para alcançar algo maior.",
        "pontos_fortes": ["Empatia e escuta ativa", "Comunicação interpessoal", "Trabalho em equipe", "Cuidado e orientação"],
        "ambientes_ideais": ["Saúde e bem-estar", "Educação e ensino", "Assistência social", "Recursos humanos", "Counseling e orientação"],
    },
    "E": {
        "nome": "Empreendedor",
        "emoji": "🚀",
        "cor": "#f59e0b",
        "cor_bg": "rgba(245, 158, 11, 0.15)",
        "descricao_curta": "Líder, ambicioso e persuasivo",
        "descricao": "Você tem perfil Empreendedor! Nasceu pra liderar. É persuasivo, ambicioso e não tem medo de assumir riscos. Se realiza tomando decisões importantes, movimentando pessoas e projetos, e vendo resultados crescerem.",
        "pontos_fortes": ["Liderança natural", "Persuasão e negociação", "Visão estratégica", "Iniciativa e coragem"],
        "ambientes_ideais": ["Negócios e empreendedorismo", "Gestão e liderança", "Vendas e marketing", "Direito e política", "Startups e inovação"],
    },
    "C": {
        "nome": "Convencional",
        "emoji": "📋",
        "cor": "#6366f1",
        "cor_bg": "rgba(99, 102, 241, 0.15)",
        "descricao_curta": "Organizado, preciso e metódico",
        "descricao": "Você tem perfil Convencional! É a pessoa que dá ordem ao caos. Gosta de estrutura, precisão e de ter tudo no lugar certo. Se realiza em ambientes organizados, com regras claras, trabalhando com dados, registros e processos bem definidos.",
        "pontos_fortes": ["Organização e atenção aos detalhes", "Trabalho com dados e números", "Confiabilidade e precisão", "Seguir e criar sistemas eficientes"],
        "ambientes_ideais": ["Finanças e contabilidade", "Serviço público e burocracia", "Administração e gestão", "Auditoria e controle", "TI e banco de dados"],
    },
}

# Função para calcular scores
def calcular_scores(respostas):
    """
    Calcula os scores de cada dimensão a partir das respostas do teste.
    Retorna um dict com scores normalizados (0-1) para cada dimensão RIASEC e personalidade.
    """
    scores_riasec = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    contagens_riasec = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    
    scores_personalidade = {"O": 0, "C_big5": 0, "E_big5": 0, "A_big5": 0, "N": 0}
    contagens_personalidade = {"O": 0, "C_big5": 0, "E_big5": 0, "A_big5": 0, "N": 0}
    
    valores_escolhidos = []
    
    # Processar RIASEC (escala 1-5, normaliza para 0-1)
    todas_questoes_riasec = QUESTOES_RIASEC + QUESTOES_HABILIDADES
    for q in todas_questoes_riasec:
        qid = q["id"]
        if qid in respostas:
            val = int(respostas[qid])
            dim = q["dimensao"]
            scores_riasec[dim] += val
            contagens_riasec[dim] += 1
    
    # Normalizar RIASEC (0-1, onde 5 = 1.0)
    for dim in scores_riasec:
        if contagens_riasec[dim] > 0:
            scores_riasec[dim] = scores_riasec[dim] / (contagens_riasec[dim] * 5)
    
    # Processar Personalidade
    mapa_dim = {"O": "O", "C": "C_big5", "E": "E_big5", "A": "A_big5", "N": "N"}
    for q in QUESTOES_PERSONALIDADE:
        qid = q["id"]
        if qid in respostas:
            val = int(respostas[qid])
            if q.get("inverso"):
                val = 6 - val  # Inverte a escala
            dim = mapa_dim[q["dimensao"]]
            scores_personalidade[dim] += val
            contagens_personalidade[dim] += 1
    
    for dim in scores_personalidade:
        if contagens_personalidade[dim] > 0:
            scores_personalidade[dim] = scores_personalidade[dim] / (contagens_personalidade[dim] * 5)
    
    # Processar Valores (escolha forçada A ou B)
    for q in QUESTOES_VALORES:
        qid = q["id"]
        if qid in respostas:
            escolha = respostas[qid]  # 'a' ou 'b'
            if escolha == 'a':
                valores_escolhidos.append(q["opcao_a"]["valor"])
            elif escolha == 'b':
                valores_escolhidos.append(q["opcao_b"]["valor"])
    
    # Contexto (armazena literalmente)
    contexto = {}
    for q in QUESTOES_CONTEXTO:
        qid = q["id"]
        if qid in respostas:
            contexto[qid] = respostas[qid]
    
    return {
        "riasec": scores_riasec,
        "personalidade": scores_personalidade,
        "valores": valores_escolhidos,
        "contexto": contexto,
    }


def calcular_compatibilidade(scores_usuario, carreira):
    """
    Calcula a compatibilidade entre o perfil do usuário e uma carreira.
    Retorna um score de 0-100.
    """
    riasec_usuario = scores_usuario["riasec"]
    valores_usuario = scores_usuario["valores"]
    
    # ── 1. Score RIASEC (peso 60%) ──────────────────────────────────────────
    riasec_carreira = carreira["riasec"]
    
    # Produto escalar normalizado (similaridade de cosseno adaptada)
    numerador = sum(riasec_usuario[d] * riasec_carreira.get(d, 0) for d in "RIASEC")
    magnitude_usuario = sum(v**2 for v in riasec_usuario.values()) ** 0.5
    magnitude_carreira = sum(v**2 for v in riasec_carreira.values()) ** 0.5
    
    if magnitude_usuario > 0 and magnitude_carreira > 0:
        score_riasec = numerador / (magnitude_usuario * magnitude_carreira)
    else:
        score_riasec = 0
    
    # ── 2. Score de Valores (peso 30%) ──────────────────────────────────────
    valores_altos_carreira = carreira.get("valores_altos", [])
    valores_baixos_carreira = carreira.get("valores_baixos", [])
    
    bonus_valores = sum(1 for v in valores_usuario if v in valores_altos_carreira)
    penalidade_valores = sum(1 for v in valores_usuario if v in valores_baixos_carreira)
    
    max_possivel = max(len(valores_altos_carreira), 1)
    score_valores = max(0, min(1, (bonus_valores - penalidade_valores * 0.5) / max_possivel))
    
    # ── 3. Score de Habilidades (peso 10%) ──────────────────────────────────
    habilidades_chave = carreira.get("habilidades_chave", [])
    score_hab = sum(riasec_usuario.get(h, 0) for h in habilidades_chave)
    score_habilidades = min(1, score_hab / max(len(habilidades_chave), 1))
    
    # ── Score Final Ponderado ────────────────────────────────────────────────
    score_final = (score_riasec * 0.60) + (score_valores * 0.30) + (score_habilidades * 0.10)
    
    # Converter para 0-100 e garantir range
    return round(min(100, max(0, score_final * 100)))


def aplicar_filtros_contexto(carreiras_rankeadas, contexto):
    """
    Aplica bônus/penalidades baseados no contexto de vida do usuário.
    """
    if not contexto:
        return carreiras_rankeadas
    
    duracao_preferida = contexto.get("CT1", "medio")
    prioridade_financeira = contexto.get("CT2", "media")
    modo_trabalho = contexto.get("CT3", "equipe_dinamica")
    precisa_bolsa = contexto.get("CT5", "foco_total") in ["bolsa_necessaria", "trabalha_estuda"]
    prefere_ead = contexto.get("CT5", "foco_total") == "ead_opcao"
    prefere_concurso = contexto.get("CT3", "") == "concurso"
    prefere_remoto = contexto.get("CT4", "") == "remoto"
    
    resultado = []
    for carreira, score in carreiras_rankeadas:
        bonus = 0
        
        # Duração
        anos = carreira.get("duracao_anos", 4)
        if duracao_preferida == "curto" and anos <= 2:
            bonus += 8
        elif duracao_preferida == "medio" and 3 <= anos <= 4:
            bonus += 5
        elif duracao_preferida == "longo" and 5 <= anos <= 6:
            bonus += 5
        elif duracao_preferida == "muito_longo" and anos >= 7:
            bonus += 5
        elif duracao_preferida == "curto" and anos > 4:
            bonus -= 10
        elif duracao_preferida == "medio" and anos > 5:
            bonus -= 5
        
        # Prioridade financeira
        if prioridade_financeira == "alta" and carreira.get("salario_max", 0) >= 15000:
            bonus += 5
        elif prioridade_financeira == "alta" and carreira.get("salario_max", 0) < 8000:
            bonus -= 8
        
        # Concurso
        if prefere_concurso and carreira.get("concurso_opcao", False):
            bonus += 8
        
        # Remoto
        if prefere_remoto and carreira.get("remoto_opcao", False):
            bonus += 6
        
        # EAD
        if prefere_ead and "ead" in carreira.get("modalidade", []):
            bonus += 5
        
        # Precisa de bolsa / trabalha e estuda
        if precisa_bolsa and anos > 5:
            bonus -= 5
        
        resultado.append((carreira, min(99, score + bonus)))
    
    return resultado


def gerar_resultado_completo(respostas):
    """
    Função principal que recebe as respostas e retorna o resultado completo do teste.
    """
    # Calcular scores
    scores = calcular_scores(respostas)
    riasec = scores["riasec"]
    
    # Ordenar dimensões por score para determinar perfil primário e secundário
    ranking_riasec = sorted(riasec.items(), key=lambda x: x[1], reverse=True)
    perfil_primario = ranking_riasec[0][0] if ranking_riasec[0][1] > 0.1 else "I"
    perfil_secundario = ranking_riasec[1][0] if len(ranking_riasec) > 1 and ranking_riasec[1][1] > 0.1 else "S"
    
    # Calcular compatibilidade com todas as carreiras
    carreiras_scores = []
    for carreira in CARREIRAS:
        score = calcular_compatibilidade(scores, carreira)
        carreiras_scores.append((carreira, score))
    
    # Aplicar filtros de contexto
    carreiras_scores = aplicar_filtros_contexto(carreiras_scores, scores.get("contexto", {}))
    
    # Ordenar por score
    carreiras_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Top 8 carreiras
    top_carreiras = [
        {
            "carreira": c,
            "compatibilidade": s,
            "compatibilidade_label": (
                "Excelente match" if s >= 80 else
                "Ótima compatibilidade" if s >= 65 else
                "Boa compatibilidade" if s >= 50 else
                "Compatível"
            )
        }
        for c, s in carreiras_scores[:8]
    ]
    
    # Scores para radar chart (0-100)
    radar_data = {k: round(v * 100) for k, v in riasec.items()}
    
    return {
        "perfil_primario": perfil_primario,
        "perfil_secundario": perfil_secundario,
        "perfil_primario_dados": PERFIS_RIASEC[perfil_primario],
        "perfil_secundario_dados": PERFIS_RIASEC[perfil_secundario],
        "scores_riasec": riasec,
        "radar_data": radar_data,
        "ranking_riasec": ranking_riasec,
        "personalidade": scores["personalidade"],
        "valores": scores["valores"],
        "top_carreiras": top_carreiras,
        "total_questoes_respondidas": len(respostas),
    }
