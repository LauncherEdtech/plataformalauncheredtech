# =============================================================================
# TESTE VOCACIONAL v2 — LAUNCHER EDUCAÇÃO
# Algoritmo: RIASEC + Big Five + Valores + Hexágono Holland + Situacional
# 95 questões | 80 carreiras | Algoritmo de matching v2
# =============================================================================
#
# MELHORIAS v2 vs v1:
# 1. Big Five agora É USADO no matching (era coletado e ignorado)
# 2. Algoritmo RIASEC ponderado: top dim 3x, 2ª dim 2x, resto 1x
# 3. Adjacência do hexágono Holland aplicada como bônus científico
# 4. Penalidades de valores reforçadas (1.0x, era 0.5x) 
# 5. Score "Paixão × Habilidade": bônus quando interesse E aptidão coincidem
# 6. Distribuição de scores calibrada para usar range 30-95% efetivamente
# 7. +23 questões situacionais e comportamentais (mais precisas que Likert puro)
# 8. +28 novas carreiras com perfis Big Five mapeados
# =============================================================================

import math


# ─────────────────────────────────────────────────────────────────────────────
# HEXÁGONO DE HOLLAND — Adjacências científicas entre tipos RIASEC
# Tipos adjacentes têm overlap de interesses e habilidades
# R-I-A-S-E-C-R (em círculo, cada tipo é adjacente aos 2 vizinhos)
# ─────────────────────────────────────────────────────────────────────────────
HEXAGONO_ADJACENCIAS = {
    "R": {"I", "C"},   # Realista é adjacente a Investigativo e Convencional
    "I": {"R", "A"},   # Investigativo é adjacente a Realista e Artístico
    "A": {"I", "S"},   # Artístico é adjacente a Investigativo e Social
    "S": {"A", "E"},   # Social é adjacente a Artístico e Empreendedor
    "E": {"S", "C"},   # Empreendedor é adjacente a Social e Convencional
    "C": {"E", "R"},   # Convencional é adjacente a Empreendedor e Realista
}

# Tipos opostos no hexágono (menor compatibilidade natural)
HEXAGONO_OPOSTOS = {
    "R": "S", "S": "R",
    "I": "E", "E": "I",
    "A": "C", "C": "A",
}


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 1 — INTERESSES VOCACIONAIS (RIASEC) — 42 questões, 7 por dimensão
# Formato misto: Likert clássico + âncoras comportamentais mais específicas
# Escala 1-5: 1=Odeio, 2=Não gosto, 3=Indiferente, 4=Gosto, 5=Amo
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_RIASEC = [
    # ══ REALISTA (R) — prático, manual, técnico, físico, natureza ══
    {"id": "R1", "dimensao": "R", "bloco": "riasec",
     "texto": "Consertar, montar ou construir coisas com as mãos",
     "emoji": "🔧"},
    {"id": "R2", "dimensao": "R", "bloco": "riasec",
     "texto": "Trabalhar com máquinas, ferramentas ou equipamentos industriais",
     "emoji": "⚙️"},
    {"id": "R3", "dimensao": "R", "bloco": "riasec",
     "texto": "Estar em campo, obra ou ambiente ao ar livre em vez de escritório",
     "emoji": "🌿"},
    {"id": "R4", "dimensao": "R", "bloco": "riasec",
     "texto": "Fazer atividades físicas como parte regular do trabalho",
     "emoji": "💪"},
    {"id": "R5", "dimensao": "R", "bloco": "riasec",
     "texto": "Trabalhar com animais, plantas ou recursos naturais",
     "emoji": "🌱"},
    {"id": "R6", "dimensao": "R", "bloco": "riasec",
     "texto": "Resolver problemas práticos do dia a dia com soluções concretas e visíveis",
     "emoji": "🏗️"},
    {"id": "R7", "dimensao": "R", "bloco": "riasec",
     "texto": "Usar habilidade manual, precisão e coordenação motora no trabalho",
     "emoji": "🖐️"},

    # ══ INVESTIGATIVO (I) — pesquisa, ciência, análise, raciocínio lógico ══
    {"id": "I1", "dimensao": "I", "bloco": "riasec",
     "texto": "Pesquisar profundamente e entender como as coisas funcionam por dentro",
     "emoji": "🔬"},
    {"id": "I2", "dimensao": "I", "bloco": "riasec",
     "texto": "Resolver problemas complexos que exigem raciocínio lógico intenso",
     "emoji": "🧮"},
    {"id": "I3", "dimensao": "I", "bloco": "riasec",
     "texto": "Estudar ciências como biologia, química, física ou matemática avançada",
     "emoji": "⚗️"},
    {"id": "I4", "dimensao": "I", "bloco": "riasec",
     "texto": "Analisar dados, gráficos e informações para tirar conclusões precisas",
     "emoji": "📊"},
    {"id": "I5", "dimensao": "I", "bloco": "riasec",
     "texto": "Mergulhar num tema desconhecido até entender todos os seus detalhes",
     "emoji": "🔍"},
    {"id": "I6", "dimensao": "I", "bloco": "riasec",
     "texto": "Fazer experimentos ou testes para descobrir como algo realmente funciona",
     "emoji": "🧪"},
    {"id": "I7", "dimensao": "I", "bloco": "riasec",
     "texto": "Pensar de forma abstrata e desenvolver teorias sobre fenômenos complexos",
     "emoji": "🧬"},

    # ══ ARTÍSTICO (A) — criatividade, expressão, arte, inovação, originalidade ══
    {"id": "A1", "dimensao": "A", "bloco": "riasec",
     "texto": "Criar coisas originais: textos, imagens, músicas ou vídeos",
     "emoji": "🎨"},
    {"id": "A2", "dimensao": "A", "bloco": "riasec",
     "texto": "Expressar ideias, sentimentos ou visões de formas criativas e únicas",
     "emoji": "✍️"},
    {"id": "A3", "dimensao": "A", "bloco": "riasec",
     "texto": "Trabalhar com design, estética visual ou comunicação não verbal",
     "emoji": "🖌️"},
    {"id": "A4", "dimensao": "A", "bloco": "riasec",
     "texto": "Inventar histórias, roteiros, campanhas ou conceitos completamente novos",
     "emoji": "💡"},
    {"id": "A5", "dimensao": "A", "bloco": "riasec",
     "texto": "Trabalhar em ambientes que valorizam inovação, liberdade e experimentação",
     "emoji": "🌈"},
    {"id": "A6", "dimensao": "A", "bloco": "riasec",
     "texto": "Apreciar e criar arte, literatura, cinema, música ou arquitetura",
     "emoji": "🎭"},
    {"id": "A7", "dimensao": "A", "bloco": "riasec",
     "texto": "Pensar fora do convencional e propor soluções que ninguém considerou antes",
     "emoji": "🚀"},

    # ══ SOCIAL (S) — ensinar, ajudar, cuidar, orientar, colaborar ══
    {"id": "S1", "dimensao": "S", "bloco": "riasec",
     "texto": "Ajudar pessoas com problemas emocionais, práticos ou de saúde",
     "emoji": "🤝"},
    {"id": "S2", "dimensao": "S", "bloco": "riasec",
     "texto": "Ensinar, explicar ou treinar outras pessoas de forma clara",
     "emoji": "📚"},
    {"id": "S3", "dimensao": "S", "bloco": "riasec",
     "texto": "Trabalhar em equipe com muita interação humana diária",
     "emoji": "👥"},
    {"id": "S4", "dimensao": "S", "bloco": "riasec",
     "texto": "Atuar em áreas que fazem diferença concreta na vida das pessoas",
     "emoji": "❤️"},
    {"id": "S5", "dimensao": "S", "bloco": "riasec",
     "texto": "Ouvir genuinamente e entender o ponto de vista das outras pessoas",
     "emoji": "👂"},
    {"id": "S6", "dimensao": "S", "bloco": "riasec",
     "texto": "Trabalhar em saúde, educação, assistência social ou psicologia",
     "emoji": "🏥"},
    {"id": "S7", "dimensao": "S", "bloco": "riasec",
     "texto": "Orientar, aconselhar ou guiar pessoas em situações difíceis",
     "emoji": "🧭"},

    # ══ EMPREENDEDOR (E) — liderança, negócios, persuasão, risco, poder ══
    {"id": "E1", "dimensao": "E", "bloco": "riasec",
     "texto": "Liderar times, projetos ou organizações rumo a resultados grandes",
     "emoji": "🚀"},
    {"id": "E2", "dimensao": "E", "bloco": "riasec",
     "texto": "Convencer, influenciar e persuadir outras pessoas com facilidade",
     "emoji": "🎯"},
    {"id": "E3", "dimensao": "E", "bloco": "riasec",
     "texto": "Iniciar projetos novos do zero e assumir riscos calculados",
     "emoji": "💼"},
    {"id": "E4", "dimensao": "E", "bloco": "riasec",
     "texto": "Competir, superar metas e vencer desafios difíceis",
     "emoji": "🏆"},
    {"id": "E5", "dimensao": "E", "bloco": "riasec",
     "texto": "Negociar, vender ideias, produtos ou serviços",
     "emoji": "🤑"},
    {"id": "E6", "dimensao": "E", "bloco": "riasec",
     "texto": "Ter poder de decisão sobre pessoas, recursos e estratégias",
     "emoji": "⚡"},
    {"id": "E7", "dimensao": "E", "bloco": "riasec",
     "texto": "Buscar crescimento rápido, escala e impacto de grande porte",
     "emoji": "📈"},

    # ══ CONVENCIONAL (C) — organização, dados, processos, regras, precisão ══
    {"id": "C1", "dimensao": "C", "bloco": "riasec",
     "texto": "Organizar informações, arquivos e processos com alto grau de precisão",
     "emoji": "📋"},
    {"id": "C2", "dimensao": "C", "bloco": "riasec",
     "texto": "Trabalhar com números, planilhas, finanças e cálculos detalhados",
     "emoji": "🔢"},
    {"id": "C3", "dimensao": "C", "bloco": "riasec",
     "texto": "Seguir procedimentos e garantir que as coisas sejam feitas corretamente",
     "emoji": "✅"},
    {"id": "C4", "dimensao": "C", "bloco": "riasec",
     "texto": "Trabalhar em ambientes estruturados com papéis e regras bem definidas",
     "emoji": "🏛️"},
    {"id": "C5", "dimensao": "C", "bloco": "riasec",
     "texto": "Verificar detalhes, identificar erros e garantir qualidade e exatidão",
     "emoji": "🔎"},
    {"id": "C6", "dimensao": "C", "bloco": "riasec",
     "texto": "Trabalhar com registros, relatórios, auditorias ou controles sistemáticos",
     "emoji": "📊"},
    {"id": "C7", "dimensao": "C", "bloco": "riasec",
     "texto": "Criar e manter sistemas, bancos de dados e fluxos de trabalho eficientes",
     "emoji": "🗂️"},
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 2 — QUESTÕES SITUACIONAIS — 8 questões de cenário
# Formato: "Em qual situação você se sentiria mais realizado?"
# Mais precisas que Likert puro — capturam preferências reais em contexto
# Cada opção mapeia para 1-2 dimensões RIASEC
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_SITUACIONAIS = [
    {"id": "ST1", "bloco": "situacional",
     "emoji": "🏢",
     "texto": "Imagina que você acabou de entrar numa empresa nova. Qual projeto você escolheria?",
     "opcoes": [
         {"valor": "ST1_RI", "dims": {"R": 2, "I": 2}, "texto": "Resolver um problema técnico complexo que ninguém conseguiu ainda"},
         {"valor": "ST1_AS", "dims": {"A": 2, "S": 2}, "texto": "Criar uma campanha criativa para engajar os funcionários"},
         {"valor": "ST1_EC", "dims": {"E": 2, "C": 2}, "texto": "Organizar e liderar um processo de mudança na empresa"},
         {"valor": "ST1_SR", "dims": {"S": 2, "R": 2}, "texto": "Treinar a equipe em novas habilidades práticas"},
     ]},
    {"id": "ST2", "bloco": "situacional",
     "emoji": "🌍",
     "texto": "Se você pudesse mudar o mundo, qual seria sua abordagem?",
     "opcoes": [
         {"valor": "ST2_IS", "dims": {"I": 2, "S": 2}, "texto": "Pesquisar e desenvolver soluções científicas para doenças ou crises"},
         {"valor": "ST2_AE", "dims": {"A": 2, "E": 2}, "texto": "Criar obras culturais que mudem a forma como as pessoas pensam"},
         {"valor": "ST2_SE", "dims": {"S": 2, "E": 2}, "texto": "Liderar movimentos sociais e políticas de transformação"},
         {"valor": "ST2_RC", "dims": {"R": 2, "C": 2}, "texto": "Construir infraestrutura e sistemas organizados que funcionem"},
     ]},
    {"id": "ST3", "bloco": "situacional",
     "emoji": "📅",
     "texto": "Qual seria o seu dia de trabalho ideal?",
     "opcoes": [
         {"valor": "ST3_I", "dims": {"I": 3}, "texto": "Analisando dados, lendo pesquisas e resolvendo problemas complexos sozinho"},
         {"valor": "ST3_SA", "dims": {"S": 2, "A": 1}, "texto": "Em reuniões, orientando pessoas e criando apresentações impactantes"},
         {"valor": "ST3_ER", "dims": {"E": 2, "R": 1}, "texto": "Tomando decisões rápidas, visitando clientes e resolvendo urgências"},
         {"valor": "ST3_CA", "dims": {"C": 2, "A": 1}, "texto": "Organizando projetos, revisando documentos e planejando com cuidado"},
     ]},
    {"id": "ST4", "bloco": "situacional",
     "emoji": "😤",
     "texto": "O que te deixaria mais INFELIZ no trabalho? (escolha o pior cenário)",
     "opcoes": [
         {"valor": "ST4_naoI", "dims": {"I": -2}, "texto": "Trabalho superficial, sem necessidade de raciocinar profundamente"},
         {"valor": "ST4_naoA", "dims": {"A": -2}, "texto": "Trabalho mecânico e repetitivo, sem nenhum espaço criativo"},
         {"valor": "ST4_naoS", "dims": {"S": -2}, "texto": "Trabalhar completamente isolado, sem contato humano real"},
         {"valor": "ST4_naoE", "dims": {"E": -2}, "texto": "Não ter autonomia, seguir ordens sem poder opinar ou liderar"},
     ]},
    {"id": "ST5", "bloco": "situacional",
     "emoji": "🎓",
     "texto": "Numa matéria do ENEM, qual tipo de questão te dá mais satisfação ao resolver?",
     "opcoes": [
         {"valor": "ST5_I", "dims": {"I": 2, "C": 1}, "texto": "Problemas de matemática, física ou química que exigem raciocínio lógico"},
         {"valor": "ST5_AS", "dims": {"A": 1, "S": 2}, "texto": "Redação ou questões de literatura, filosofia e sociologia"},
         {"valor": "ST5_RI", "dims": {"R": 1, "I": 2}, "texto": "Ciências da natureza: biologia, genética, ecologia"},
         {"valor": "ST5_EC", "dims": {"E": 1, "C": 2}, "texto": "Questões de interpretação histórica, geopolítica e atualidades"},
     ]},
    {"id": "ST6", "bloco": "situacional",
     "emoji": "🤔",
     "texto": "Qual frase descreve melhor sua forma de trabalhar?",
     "opcoes": [
         {"valor": "ST6_R", "dims": {"R": 3}, "texto": "\"Prefiro fazer do que falar. Resultado concreto é o que importa.\""},
         {"valor": "ST6_I", "dims": {"I": 3}, "texto": "\"Preciso entender o porquê de tudo antes de agir.\""},
         {"valor": "ST6_A", "dims": {"A": 3}, "texto": "\"Me inspiro, crio, experimento e nunca faço do mesmo jeito duas vezes.\""},
         {"valor": "ST6_SEC", "dims": {"S": 1, "E": 1, "C": 1}, "texto": "\"Organizo as pessoas, traço o plano e executo com método.\""},
     ]},
    {"id": "ST7", "bloco": "situacional",
     "emoji": "💰",
     "texto": "Se você ganhasse dinheiro suficiente para parar de trabalhar, o que faria?",
     "opcoes": [
         {"valor": "ST7_IA", "dims": {"I": 2, "A": 1}, "texto": "Continuaria estudando, pesquisando e criando coisas por puro prazer"},
         {"valor": "ST7_SE", "dims": {"S": 2, "E": 1}, "texto": "Criaria um projeto social ou empresa para impactar mais pessoas"},
         {"valor": "ST7_AR", "dims": {"A": 2, "R": 1}, "texto": "Me dedicaria a uma arte ou ofício manual que sempre quis aprender"},
         {"valor": "ST7_CE", "dims": {"C": 1, "E": 2}, "texto": "Investiria e empreenderia para multiplicar o patrimônio"},
     ]},
    {"id": "ST8", "bloco": "situacional",
     "emoji": "👥",
     "texto": "Num projeto em grupo, qual papel você naturalmente assume?",
     "opcoes": [
         {"valor": "ST8_E", "dims": {"E": 3}, "texto": "O líder — organizo o time, delego e sou responsável pelo resultado"},
         {"valor": "ST8_IS", "dims": {"I": 2, "S": 1}, "texto": "O especialista — vou fundo no problema técnico e trago as soluções"},
         {"valor": "ST8_AS", "dims": {"A": 2, "S": 1}, "texto": "O criativo — gero as melhores ideias e faço a apresentação brilhar"},
         {"valor": "ST8_CS", "dims": {"C": 2, "S": 1}, "texto": "O organizador — garanto que tudo está no prazo e sem erros"},
     ]},
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 3 — PERSONALIDADE (Big Five) — 20 questões
# Dimensões: O=Abertura, C=Conscienciosidade, E=Extroversão, A=Amabilidade, N=Estabilidade
# Escala 1-5. Itens marcados "inverso": True têm a escala invertida no cálculo.
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_PERSONALIDADE = [
    # ── ABERTURA À EXPERIÊNCIA ──
    {"id": "P1", "dimensao": "O", "bloco": "personalidade",
     "texto": "Gosto de explorar ideias novas e questionar verdades estabelecidas",
     "emoji": "🌍"},
    {"id": "P2", "dimensao": "O", "bloco": "personalidade",
     "texto": "Fico genuinamente curioso com assuntos que nunca estudei antes",
     "emoji": "🔭"},
    {"id": "P3", "dimensao": "O", "bloco": "personalidade",
     "texto": "Prefiro rotinas previsíveis e estáveis a mudanças e novidades constantes",
     "emoji": "🔄", "inverso": True},
    {"id": "P4", "dimensao": "O", "bloco": "personalidade",
     "texto": "Tenho imaginação fértil e frequentemente fico imerso em pensamentos criativos",
     "emoji": "💭"},

    # ── CONSCIENCIOSIDADE ──
    {"id": "P5", "dimensao": "C", "bloco": "personalidade",
     "texto": "Costumo planejar minhas tarefas com antecedência e raramente perco prazos",
     "emoji": "📅"},
    {"id": "P6", "dimensao": "C", "bloco": "personalidade",
     "texto": "Quando começo algo, raramente desisto antes de terminar mesmo sendo difícil",
     "emoji": "🏁"},
    {"id": "P7", "dimensao": "C", "bloco": "personalidade",
     "texto": "Sou muito detalhista e me incomoda quando algo está impreciso ou incompleto",
     "emoji": "🔎"},
    {"id": "P8", "dimensao": "C", "bloco": "personalidade",
     "texto": "Às vezes deixo as coisas para a última hora e começo sem muito planejamento",
     "emoji": "⏰", "inverso": True},

    # ── EXTROVERSÃO ──
    {"id": "P9", "dimensao": "E", "bloco": "personalidade",
     "texto": "Prefiro trabalhar e estudar em grupo do que sozinho na maior parte do tempo",
     "emoji": "🗣️"},
    {"id": "P10", "dimensao": "E", "bloco": "personalidade",
     "texto": "Me sinto energizado depois de estar com muitas pessoas, não esgotado",
     "emoji": "⚡"},
    {"id": "P11", "dimensao": "E", "bloco": "personalidade",
     "texto": "Prefiro tomar decisões rápidas a ficar analisando por muito tempo",
     "emoji": "🎯"},
    {"id": "P12", "dimensao": "E", "bloco": "personalidade",
     "texto": "Preciso de muito tempo sozinho para recarregar as energias",
     "emoji": "🧘", "inverso": True},

    # ── AMABILIDADE ──
    {"id": "P13", "dimensao": "A", "bloco": "personalidade",
     "texto": "Me preocupo genuinamente com o bem-estar das pessoas ao meu redor",
     "emoji": "💛"},
    {"id": "P14", "dimensao": "A", "bloco": "personalidade",
     "texto": "Prefiro chegar a um acordo do que entrar em conflito mesmo que eu tenha razão",
     "emoji": "🕊️"},
    {"id": "P15", "dimensao": "A", "bloco": "personalidade",
     "texto": "Fico satisfeito quando contribuo para o sucesso de outra pessoa",
     "emoji": "🌟"},
    {"id": "P16", "dimensao": "A", "bloco": "personalidade",
     "texto": "Sou direto e firme nas minhas opiniões, mesmo que isso gere desconforto",
     "emoji": "💬", "inverso": True},

    # ── ESTABILIDADE EMOCIONAL (N invertido) ──
    {"id": "P17", "dimensao": "N", "bloco": "personalidade",
     "texto": "Consigo manter a calma bem mesmo em situações de alta pressão",
     "emoji": "😌"},
    {"id": "P18", "dimensao": "N", "bloco": "personalidade",
     "texto": "Críticas ou opiniões negativas sobre meu trabalho não me afetam muito",
     "emoji": "🛡️"},
    {"id": "P19", "dimensao": "N", "bloco": "personalidade",
     "texto": "Raramente me sinto sobrecarregado ou ansioso com minhas responsabilidades",
     "emoji": "⚖️"},
    {"id": "P20", "dimensao": "N", "bloco": "personalidade",
     "texto": "Tenho facilidade em lidar com ambiguidade e situações incertas",
     "emoji": "🌊"},
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 4 — VALORES DE TRABALHO — 15 questões de escolha forçada
# Força o aluno a priorizar, eliminando respostas "tudo é importante"
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_VALORES = [
    {"id": "V1", "bloco": "valores",
     "opcao_a": {"texto": "Ter estabilidade e segurança no emprego", "valor": "estabilidade", "emoji": "🏠"},
     "opcao_b": {"texto": "Ter liberdade e autonomia total no trabalho", "valor": "autonomia", "emoji": "🦅"}},
    {"id": "V2", "bloco": "valores",
     "opcao_a": {"texto": "Ganhar muito bem financeiramente", "valor": "remuneracao", "emoji": "💰"},
     "opcao_b": {"texto": "Ter impacto positivo real na sociedade", "valor": "impacto_social", "emoji": "🌍"}},
    {"id": "V3", "bloco": "valores",
     "opcao_a": {"texto": "Crescer e ser reconhecido profissionalmente", "valor": "reconhecimento", "emoji": "🏆"},
     "opcao_b": {"texto": "Ter equilíbrio real entre trabalho e vida pessoal", "valor": "equilibrio", "emoji": "⚖️"}},
    {"id": "V4", "bloco": "valores",
     "opcao_a": {"texto": "Trabalho que me desafia intelectualmente todo dia", "valor": "desafio_intelectual", "emoji": "🧠"},
     "opcao_b": {"texto": "Trabalho que me permita ajudar pessoas diretamente", "valor": "ajudar_pessoas", "emoji": "🤝"}},
    {"id": "V5", "bloco": "valores",
     "opcao_a": {"texto": "Inovar e criar coisas que nunca existiram", "valor": "inovacao", "emoji": "💡"},
     "opcao_b": {"texto": "Aperfeiçoar e melhorar o que já existe com excelência", "valor": "melhoria", "emoji": "🔧"}},
    {"id": "V6", "bloco": "valores",
     "opcao_a": {"texto": "Liderar e ser o responsável por decisões importantes", "valor": "lideranca", "emoji": "👑"},
     "opcao_b": {"texto": "Trabalhar em colaboração sem pressão de hierarquia", "valor": "colaboracao", "emoji": "👥"}},
    {"id": "V7", "bloco": "valores",
     "opcao_a": {"texto": "Ter prestígio e ser referência na minha área", "valor": "prestigio", "emoji": "⭐"},
     "opcao_b": {"texto": "Fazer um trabalho que me satisfaça mesmo sem fama", "valor": "satisfacao_pessoal", "emoji": "😊"}},
    {"id": "V8", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar com tecnologia e inovação constante", "valor": "tecnologia", "emoji": "💻"},
     "opcao_b": {"texto": "Trabalhar com questões humanas, sociais ou culturais", "valor": "humanismo", "emoji": "❤️"}},
    {"id": "V9", "bloco": "valores",
     "opcao_a": {"texto": "Aprender algo novo todo dia no trabalho", "valor": "aprendizado_continuo", "emoji": "📖"},
     "opcao_b": {"texto": "Ser profundo especialista em uma área específica", "valor": "especializacao", "emoji": "🎯"}},
    {"id": "V10", "bloco": "valores",
     "opcao_a": {"texto": "Metas claras e resultados mensuráveis", "valor": "resultados", "emoji": "📈"},
     "opcao_b": {"texto": "Propósito maior e significado no trabalho", "valor": "proposito", "emoji": "🌟"}},
    {"id": "V11", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar por conta própria ou empreender", "valor": "empreendedorismo", "emoji": "🚀"},
     "opcao_b": {"texto": "Trabalhar em empresa ou serviço público estruturado", "valor": "concurso_empresa", "emoji": "🏛️"}},
    {"id": "V12", "bloco": "valores",
     "opcao_a": {"texto": "Alta remuneração mesmo que o trabalho seja estressante", "valor": "alta_remuneracao_stress", "emoji": "💵"},
     "opcao_b": {"texto": "Trabalho tranquilo mesmo que pague menos", "valor": "qualidade_vida_paga_menos", "emoji": "🌿"}},
    {"id": "V13", "bloco": "valores",
     "opcao_a": {"texto": "Trabalhar com projetos variados e sempre diferentes", "valor": "variedade", "emoji": "🎲"},
     "opcao_b": {"texto": "Ter especialização profunda e rotina previsível", "valor": "rotina_especializada", "emoji": "📌"}},
    {"id": "V14", "bloco": "valores",
     "opcao_a": {"texto": "Trabalho com alto impacto para muitas pessoas (escala)", "valor": "escala", "emoji": "📡"},
     "opcao_b": {"texto": "Trabalho com impacto profundo para poucas pessoas (intimidade)", "valor": "profundidade_relacional", "emoji": "🫂"}},
    {"id": "V15", "bloco": "valores",
     "opcao_a": {"texto": "Ser pioneiro numa área emergente, mesmo com risco", "valor": "pioneirismo", "emoji": "🌋"},
     "opcao_b": {"texto": "Seguir carreira consolidada com caminho claro", "valor": "carreira_consolidada", "emoji": "🗺️"}},
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 5 — HABILIDADES AUTODECLARADAS — 18 questões
# Escala 1-5 ("Sou muito bom nisso" → "Sou ruim nisso")
# Cruza com interesses para detectar "paixão + habilidade" = super bônus
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_HABILIDADES = [
    {"id": "H1", "dimensao": "R", "bloco": "habilidades",
     "texto": "Montar, reparar ou operar equipamentos e aparelhos",
     "emoji": "🔨"},
    {"id": "H2", "dimensao": "I", "bloco": "habilidades",
     "texto": "Raciocínio matemático e resolução de problemas lógicos complexos",
     "emoji": "🔢"},
    {"id": "H3", "dimensao": "A", "bloco": "habilidades",
     "texto": "Escrita criativa, comunicação verbal ou produção de conteúdo",
     "emoji": "✍️"},
    {"id": "H4", "dimensao": "S", "bloco": "habilidades",
     "texto": "Comunicar, ouvir e me relacionar com diferentes tipos de pessoas",
     "emoji": "💬"},
    {"id": "H5", "dimensao": "E", "bloco": "habilidades",
     "texto": "Liderar, organizar e motivar pessoas em projetos e equipes",
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
     "texto": "Ensinar, explicar ou transmitir conhecimento de forma clara",
     "emoji": "📚"},
    {"id": "H10", "dimensao": "R", "bloco": "habilidades",
     "texto": "Trabalho manual que exige coordenação fina (desenho técnico, precisão física)",
     "emoji": "🖐️"},
    {"id": "H11", "dimensao": "E", "bloco": "habilidades",
     "texto": "Negociar, argumentar e convencer pessoas com naturalidade",
     "emoji": "🗣️"},
    {"id": "H12", "dimensao": "C", "bloco": "habilidades",
     "texto": "Lidar bem com cálculos financeiros, orçamentos e controle numérico",
     "emoji": "💹"},
    {"id": "H13", "dimensao": "I", "bloco": "habilidades",
     "texto": "Aprender linguagens de programação, algoritmos ou lógica computacional",
     "emoji": "💻"},
    {"id": "H14", "dimensao": "A", "bloco": "habilidades",
     "texto": "Criar artes visuais, design gráfico ou comunicação visual impactante",
     "emoji": "🎨"},
    {"id": "H15", "dimensao": "S", "bloco": "habilidades",
     "texto": "Mediar conflitos e ajudar pessoas a encontrar soluções em comum",
     "emoji": "🤝"},
    {"id": "H16", "dimensao": "R", "bloco": "habilidades",
     "texto": "Trabalhar com meu corpo de forma eficiente (atletismo, dança, trabalho físico)",
     "emoji": "💪"},
    {"id": "H17", "dimensao": "E", "bloco": "habilidades",
     "texto": "Identificar oportunidades de negócio e transformá-las em projetos viáveis",
     "emoji": "🚀"},
    {"id": "H18", "dimensao": "C", "bloco": "habilidades",
     "texto": "Criar sistemas e processos para que as coisas funcionem com consistência",
     "emoji": "⚙️"},
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 6 — CONTEXTO DE VIDA — 7 questões de múltipla escolha
# Não afetam RIASEC diretamente, mas filtram carreiras por viabilidade real
# ─────────────────────────────────────────────────────────────────────────────

QUESTOES_CONTEXTO = [
    {"id": "CT1", "bloco": "contexto",
     "texto": "Quanto tempo você está disposto a estudar antes de trabalhar na área?",
     "emoji": "⏳",
     "opcoes": [
         {"valor": "curto", "texto": "Até 2 anos (técnico ou tecnólogo)"},
         {"valor": "medio", "texto": "3 a 4 anos (graduação padrão)"},
         {"valor": "longo", "texto": "5 a 6 anos (medicina, engenharia, direito...)"},
         {"valor": "muito_longo", "texto": "Mais de 6 anos (residência, pós, academia)"},
     ]},
    {"id": "CT2", "bloco": "contexto",
     "texto": "Qual é sua prioridade financeira na carreira?",
     "emoji": "💵",
     "opcoes": [
         {"valor": "alta", "texto": "Alta remuneração — é fundamental para mim"},
         {"valor": "media", "texto": "Remuneração razoável com satisfação no trabalho"},
         {"valor": "baixa", "texto": "Propósito e impacto valem mais que salário alto"},
     ]},
    {"id": "CT3", "bloco": "contexto",
     "texto": "Como você prefere trabalhar no dia a dia?",
     "emoji": "💼",
     "opcoes": [
         {"valor": "autonomo", "texto": "Por conta própria / empreendedor / freelancer"},
         {"valor": "equipe_dinamica", "texto": "Em equipe dinâmica com projetos variados"},
         {"valor": "empresa_estruturada", "texto": "Em empresa ou instituição com estrutura clara"},
         {"valor": "concurso", "texto": "Serviço público / estabilidade do concurso"},
     ]},
    {"id": "CT4", "bloco": "contexto",
     "texto": "Onde você pretende trabalhar?",
     "emoji": "📍",
     "opcoes": [
         {"valor": "capital_grande", "texto": "Grandes capitais (SP, RJ, BH, BSB...)"},
         {"valor": "qualquer_cidade", "texto": "Qualquer cidade do Brasil"},
         {"valor": "interior_preferencia", "texto": "Prefiro interior ou cidade média"},
         {"valor": "remoto", "texto": "Trabalhar de qualquer lugar (remoto total)"},
     ]},
    {"id": "CT5", "bloco": "contexto",
     "texto": "Qual sua situação atual de estudos?",
     "emoji": "🎓",
     "opcoes": [
         {"valor": "foco_total", "texto": "Posso me dedicar 100% aos estudos"},
         {"valor": "trabalha_estuda", "texto": "Preciso trabalhar enquanto estudo"},
         {"valor": "bolsa_necessaria", "texto": "Necessito de bolsa de estudos ou ProUni"},
         {"valor": "ead_opcao", "texto": "EAD é uma opção real e preferida para mim"},
     ]},
    {"id": "CT6", "bloco": "contexto",
     "texto": "Como você lida com a questão do risco profissional?",
     "emoji": "⚡",
     "opcoes": [
         {"valor": "risco_alto", "texto": "Aceito alto risco por alta recompensa potencial"},
         {"valor": "risco_medio", "texto": "Aceito algum risco com plano B claro"},
         {"valor": "risco_baixo", "texto": "Prefiro segurança e estabilidade previsível"},
     ]},
    {"id": "CT7", "bloco": "contexto",
     "texto": "Qual aspecto físico do trabalho é mais importante para você?",
     "emoji": "🏃",
     "opcoes": [
         {"valor": "acao_campo", "texto": "Prefiro trabalho físico, campo ou movimento"},
         {"valor": "misto", "texto": "Gosto de mistura: escritório e campo/atendimento"},
         {"valor": "escritorio", "texto": "Prefiro ambiente de escritório ou laboratório"},
         {"valor": "remoto_digital", "texto": "Só digital — computador e reuniões online"},
     ]},
]


# ─────────────────────────────────────────────────────────────────────────────
# BANCO DE CARREIRAS v2 — 80 carreiras
# Cada carreira tem:
#   riasec: perfil ideal nas 6 dimensões (0-1)
#   big5: perfil Big Five ideal (0-1) — NOVO, usado no algoritmo v2
#   valores_altos/baixos: valores que combinam/conflitam
#   habilidades_chave: dimensões RIASEC críticas
#   dados de mercado: salário, duração, modalidade, concurso, remoto
# ─────────────────────────────────────────────────────────────────────────────

CARREIRAS = [

    # ══════════════════════════════════════════════════════════════
    # SAÚDE — 12 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "medicina", "nome": "Medicina", "area": "Saúde", "emoji": "🩺",
        "descricao": "Diagnostica, trata e previne doenças humanas. Exige dedicação extrema mas oferece impacto, prestígio e remuneração únicos.",
        "riasec": {"I": 0.95, "S": 0.85, "C": 0.70, "R": 0.55, "E": 0.35, "A": 0.20},
        "big5": {"O": 0.75, "C": 0.95, "E": 0.60, "A": 0.80, "N": 0.85},
        "valores_altos": ["impacto_social", "ajudar_pessoas", "desafio_intelectual", "prestigio", "especializacao", "escala"],
        "valores_baixos": ["equilibrio", "autonomia", "qualidade_vida_paga_menos"],
        "habilidades_chave": ["I", "S", "C"],
        "duracao_anos": 8, "duracao_label": "6 anos + 2-5 anos de residência",
        "dificuldade_enem": "Muito alta", "salario_min": 8000, "salario_max": 60000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["saúde", "ciências", "prestígio", "longo prazo", "alta nota ENEM"]
    },
    {
        "id": "enfermagem", "nome": "Enfermagem", "area": "Saúde", "emoji": "💊",
        "descricao": "Cuida e trata pacientes, aplica procedimentos clínicos e lidera equipes de saúde. Profissão essencial e de alto impacto humano.",
        "riasec": {"S": 0.95, "R": 0.65, "C": 0.60, "I": 0.55, "E": 0.30, "A": 0.15},
        "big5": {"O": 0.50, "C": 0.90, "E": 0.65, "A": 0.95, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "estabilidade", "profundidade_relacional"],
        "valores_baixos": ["autonomia", "empreendedorismo", "alta_remuneracao_stress"],
        "habilidades_chave": ["S", "R", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 9000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["saúde", "cuidado", "estabilidade", "concurso"]
    },
    {
        "id": "psicologia", "nome": "Psicologia", "area": "Saúde / Humanas", "emoji": "🧠",
        "descricao": "Estuda e promove saúde mental. Atua em clínicas, escolas, hospitais e empresas. Mistura ciência, escuta e intervenção humana.",
        "riasec": {"S": 0.90, "I": 0.80, "A": 0.55, "E": 0.40, "C": 0.40, "R": 0.10},
        "big5": {"O": 0.85, "C": 0.70, "E": 0.55, "A": 0.90, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "aprendizado_continuo", "autonomia", "profundidade_relacional"],
        "valores_baixos": ["remuneracao", "tecnologia", "escala"],
        "habilidades_chave": ["S", "I", "A"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 3500, "salario_max": 20000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["saúde mental", "humanas", "terapia", "clínica", "escuta"]
    },
    {
        "id": "fisioterapia", "nome": "Fisioterapia", "area": "Saúde", "emoji": "🦴",
        "descricao": "Reabilita e trata disfunções físicas e motoras. Trabalha com o corpo humano através de técnicas manuais e exercícios específicos.",
        "riasec": {"S": 0.85, "R": 0.80, "I": 0.65, "C": 0.50, "E": 0.25, "A": 0.20},
        "big5": {"O": 0.55, "C": 0.85, "E": 0.60, "A": 0.90, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "desafio_intelectual", "profundidade_relacional"],
        "valores_baixos": ["remoto_digital", "empreendedorismo", "escala"],
        "habilidades_chave": ["S", "R", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 12000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["saúde", "reabilitação", "corpo humano", "esporte"]
    },
    {
        "id": "nutricao", "nome": "Nutrição", "area": "Saúde", "emoji": "🥗",
        "descricao": "Orienta sobre alimentação saudável e trata condições nutricionais. Atua em clínicas, hospitais, esportes, indústria e pesquisa.",
        "riasec": {"S": 0.80, "I": 0.70, "C": 0.60, "R": 0.30, "A": 0.25, "E": 0.35},
        "big5": {"O": 0.65, "C": 0.80, "E": 0.55, "A": 0.80, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "aprendizado_continuo", "autonomia"],
        "valores_baixos": ["escala", "tecnologia"],
        "habilidades_chave": ["S", "I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 12000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["saúde", "alimentação", "bem-estar", "esporte"]
    },
    {
        "id": "medicina_veterinaria", "nome": "Medicina Veterinária", "area": "Saúde / Agro", "emoji": "🐾",
        "descricao": "Cuida da saúde animal e da sanidade alimentar. Atua em clínicas, fazendas, saúde pública e indústria — com mercado excelente no agro brasileiro.",
        "riasec": {"I": 0.85, "S": 0.70, "R": 0.75, "C": 0.50, "A": 0.15, "E": 0.35},
        "big5": {"O": 0.70, "C": 0.85, "E": 0.55, "A": 0.75, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "desafio_intelectual", "natureza"],
        "valores_baixos": ["remoto_digital", "escala_urbana"],
        "habilidades_chave": ["I", "R", "S"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4000, "salario_max": 25000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["animais", "saúde", "agronegócio", "campo"]
    },
    {
        "id": "farmacia", "nome": "Farmácia / Bioquímica", "area": "Saúde", "emoji": "💉",
        "descricao": "Desenvolve e controla medicamentos, realiza análises clínicas e atua na indústria farmacêutica. Perfil científico com alta precisão técnica.",
        "riasec": {"I": 0.90, "C": 0.80, "S": 0.55, "R": 0.45, "A": 0.15, "E": 0.25},
        "big5": {"O": 0.65, "C": 0.90, "E": 0.40, "A": 0.60, "N": 0.85},
        "valores_altos": ["desafio_intelectual", "estabilidade", "especializacao", "melhoria"],
        "valores_baixos": ["empreendedorismo", "alta_remuneracao_stress"],
        "habilidades_chave": ["I", "C", "R"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 3500, "salario_max": 15000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["ciências", "laboratório", "medicamentos", "indústria"]
    },
    {
        "id": "odontologia", "nome": "Odontologia", "area": "Saúde", "emoji": "🦷",
        "descricao": "Cuida da saúde bucal com procedimentos precisos. Alta autonomia e possibilidade real de consultório próprio.",
        "riasec": {"I": 0.80, "S": 0.75, "R": 0.75, "C": 0.60, "E": 0.55, "A": 0.30},
        "big5": {"O": 0.55, "C": 0.90, "E": 0.60, "A": 0.75, "N": 0.85},
        "valores_altos": ["autonomia", "remuneracao", "especializacao", "empreendedorismo", "profundidade_relacional"],
        "valores_baixos": ["escala", "impacto_social_macro"],
        "habilidades_chave": ["I", "R", "S"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 30000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["saúde", "autônomo", "precisão", "clínica própria"]
    },
    {
        "id": "fonoaudiologia", "nome": "Fonoaudiologia", "area": "Saúde", "emoji": "🗣️",
        "descricao": "Trata distúrbios da voz, fala, audição e linguagem. Especialidade única com alta demanda em todas as fases da vida.",
        "riasec": {"S": 0.90, "I": 0.70, "C": 0.55, "R": 0.35, "A": 0.40, "E": 0.30},
        "big5": {"O": 0.65, "C": 0.80, "E": 0.60, "A": 0.90, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "especializacao", "impacto_social", "profundidade_relacional"],
        "valores_baixos": ["lideranca", "empreendedorismo"],
        "habilidades_chave": ["S", "I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 12000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["saúde", "linguagem", "voz", "neurologia", "educação"]
    },
    {
        "id": "terapia_ocupacional", "nome": "Terapia Ocupacional", "area": "Saúde", "emoji": "🧩",
        "descricao": "Reabilita pessoas com limitações físicas, cognitivas ou sociais através de atividades cotidianas. Profissão de altíssimo impacto humano.",
        "riasec": {"S": 0.95, "R": 0.65, "I": 0.60, "A": 0.55, "C": 0.45, "E": 0.25},
        "big5": {"O": 0.70, "C": 0.80, "E": 0.60, "A": 0.95, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "profundidade_relacional", "inovacao"],
        "valores_baixos": ["remuneracao", "empreendedorismo"],
        "habilidades_chave": ["S", "R", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2800, "salario_max": 9000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["saúde", "reabilitação", "inclusão", "neurologia"]
    },
    {
        "id": "biomedicina", "nome": "Biomedicina", "area": "Saúde / Ciências", "emoji": "🔬",
        "descricao": "Analisa doenças no nível celular e molecular, realiza análises clínicas e trabalha com pesquisa biomédica. Perfil altamente científico.",
        "riasec": {"I": 0.95, "R": 0.65, "C": 0.70, "S": 0.40, "A": 0.20, "E": 0.20},
        "big5": {"O": 0.80, "C": 0.90, "E": 0.35, "A": 0.55, "N": 0.85},
        "valores_altos": ["desafio_intelectual", "especializacao", "aprendizado_continuo", "melhoria"],
        "valores_baixos": ["extroversao_social", "lideranca"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 3500, "salario_max": 14000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["ciência", "laboratório", "diagnóstico", "pesquisa", "biotecnologia"]
    },
    {
        "id": "saude_coletiva", "nome": "Saúde Coletiva / Saúde Pública", "area": "Saúde", "emoji": "🏛️",
        "descricao": "Planeja e avalia políticas de saúde para populações. Combate doenças em escala social. Carreira de impacto macro.",
        "riasec": {"I": 0.80, "S": 0.85, "E": 0.65, "C": 0.70, "A": 0.35, "R": 0.20},
        "big5": {"O": 0.80, "C": 0.80, "E": 0.60, "A": 0.80, "N": 0.75},
        "valores_altos": ["impacto_social", "escala", "proposito", "aprendizado_continuo"],
        "valores_baixos": ["remuneracao", "autonomia", "empreendedorismo"],
        "habilidades_chave": ["I", "S", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos + especialização",
        "dificuldade_enem": "Média-alta", "salario_min": 4000, "salario_max": 16000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["saúde pública", "epidemiologia", "políticas", "concurso"]
    },

    # ══════════════════════════════════════════════════════════════
    # TECNOLOGIA — 10 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "engenharia_computacao", "nome": "Engenharia da Computação / Ciência da Computação",
        "area": "Tecnologia", "emoji": "💻",
        "descricao": "Desenvolve software, hardware e sistemas. Mercado global aquecido com altíssima remuneração e demanda crescente.",
        "riasec": {"I": 0.95, "R": 0.70, "C": 0.70, "A": 0.40, "E": 0.35, "S": 0.20},
        "big5": {"O": 0.85, "C": 0.80, "E": 0.35, "A": 0.45, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "tecnologia", "remuneracao", "aprendizado_continuo", "autonomia"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 35000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["tecnologia", "programação", "inovação", "remoto", "alta renda"]
    },
    {
        "id": "sistemas_informacao", "nome": "Sistemas de Informação / ADS",
        "area": "Tecnologia", "emoji": "📱",
        "descricao": "Desenvolve sistemas, apps e soluções tecnológicas para empresas. Entrada rápida no mercado tech com excelente empregabilidade.",
        "riasec": {"I": 0.80, "C": 0.80, "R": 0.60, "E": 0.40, "A": 0.35, "S": 0.25},
        "big5": {"O": 0.70, "C": 0.80, "E": 0.40, "A": 0.50, "N": 0.75},
        "valores_altos": ["tecnologia", "desafio_intelectual", "remuneracao", "autonomia", "variedade"],
        "valores_baixos": [],
        "habilidades_chave": ["I", "C", "R"],
        "duracao_anos": 3, "duracao_label": "3 anos",
        "dificuldade_enem": "Média", "salario_min": 4000, "salario_max": 22000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["tecnologia", "programação", "curto prazo", "remoto"]
    },
    {
        "id": "ciencia_dados_ia", "nome": "Ciência de Dados / Inteligência Artificial",
        "area": "Tecnologia", "emoji": "🤖",
        "descricao": "Extrai inteligência de grandes volumes de dados com machine learning e IA. Área em explosão global com demanda muito maior que a oferta.",
        "riasec": {"I": 0.95, "C": 0.85, "R": 0.50, "A": 0.30, "E": 0.30, "S": 0.20},
        "big5": {"O": 0.90, "C": 0.80, "E": 0.35, "A": 0.45, "N": 0.80},
        "valores_altos": ["tecnologia", "desafio_intelectual", "aprendizado_continuo", "remuneracao", "inovacao"],
        "valores_baixos": ["ajudar_pessoas", "profundidade_relacional"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "Graduação + especializações contínuas",
        "dificuldade_enem": "Alta", "salario_min": 6000, "salario_max": 40000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["IA", "machine learning", "big data", "remoto", "alta renda"]
    },
    {
        "id": "seguranca_informacao", "nome": "Segurança da Informação / Cybersecurity",
        "area": "Tecnologia", "emoji": "🔐",
        "descricao": "Protege sistemas e dados contra ataques e vazamentos. Uma das áreas mais estratégicas e bem pagas da tecnologia atual.",
        "riasec": {"I": 0.90, "C": 0.80, "R": 0.65, "E": 0.45, "A": 0.30, "S": 0.20},
        "big5": {"O": 0.80, "C": 0.85, "E": 0.35, "A": 0.45, "N": 0.85},
        "valores_altos": ["desafio_intelectual", "tecnologia", "remuneracao", "resultados"],
        "valores_baixos": ["ajudar_pessoas", "lideranca"],
        "habilidades_chave": ["I", "C", "R"],
        "duracao_anos": 4, "duracao_label": "Graduação + certificações",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 30000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["cybersecurity", "hacking ético", "proteção de dados", "remoto"]
    },
    {
        "id": "game_design", "nome": "Design de Games / Desenvolvimento de Jogos",
        "area": "Tecnologia / Artes", "emoji": "🎮",
        "descricao": "Cria jogos digitais combinando criatividade, programação e narrativa. Mercado global bilionário em crescimento acelerado.",
        "riasec": {"A": 0.85, "I": 0.80, "R": 0.65, "E": 0.50, "C": 0.45, "S": 0.30},
        "big5": {"O": 0.90, "C": 0.70, "E": 0.50, "A": 0.55, "N": 0.70},
        "valores_altos": ["inovacao", "tecnologia", "satisfacao_pessoal", "variedade", "autonomia"],
        "valores_baixos": ["concurso_empresa", "rotina_especializada"],
        "habilidades_chave": ["A", "I", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos (ou autodidata)",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["games", "criativo", "programação", "narrativa", "digital"]
    },
    {
        "id": "engenharia_software", "nome": "Engenharia de Software",
        "area": "Tecnologia", "emoji": "⌨️",
        "descricao": "Projeta e constrói sistemas de software robustos em escala. Difere de TI por focar arquitetura, metodologias e engenharia de produto.",
        "riasec": {"I": 0.85, "C": 0.85, "R": 0.60, "A": 0.35, "E": 0.40, "S": 0.20},
        "big5": {"O": 0.75, "C": 0.90, "E": 0.35, "A": 0.50, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "tecnologia", "remuneracao", "resultados", "melhoria"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta", "salario_min": 5500, "salario_max": 35000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["software", "programação", "remoto", "alta renda"]
    },
    {
        "id": "design_ux", "nome": "UX Design / Design Digital",
        "area": "Tecnologia / Artes", "emoji": "🎨",
        "descricao": "Cria interfaces e experiências digitais que encantam usuários. Une pensamento criativo e dados para resolver problemas reais.",
        "riasec": {"A": 0.90, "I": 0.65, "S": 0.55, "R": 0.50, "E": 0.45, "C": 0.40},
        "big5": {"O": 0.90, "C": 0.70, "E": 0.60, "A": 0.65, "N": 0.70},
        "valores_altos": ["inovacao", "autonomia", "tecnologia", "variedade", "criatividade"],
        "valores_baixos": ["concurso_empresa", "rotina_especializada"],
        "habilidades_chave": ["A", "I", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos (ou cursos específicos)",
        "dificuldade_enem": "Média", "salario_min": 3500, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["UX", "design", "criativo", "digital", "remoto"]
    },
    {
        "id": "tecnico_informatica", "nome": "Técnico em Informática / Redes / Suporte",
        "area": "Tecnologia", "emoji": "🖥️",
        "descricao": "Instala, mantém e configura sistemas, redes e equipamentos. Entrada rápida no mercado de tecnologia sem precisar de graduação longa.",
        "riasec": {"R": 0.85, "I": 0.70, "C": 0.65, "A": 0.20, "S": 0.30, "E": 0.30},
        "big5": {"O": 0.55, "C": 0.75, "E": 0.45, "A": 0.55, "N": 0.75},
        "valores_altos": ["tecnologia", "estabilidade", "aprendizado_continuo"],
        "valores_baixos": ["lideranca", "escala"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa", "salario_min": 2000, "salario_max": 8000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["tecnologia", "curto prazo", "redes", "suporte", "rápido"]
    },
    {
        "id": "matematica_estatistica", "nome": "Matemática / Estatística / Atuária",
        "area": "Exatas", "emoji": "📐",
        "descricao": "Analisa padrões, modela fenômenos e resolve problemas quantitativos. Base para ciência de dados, finanças e pesquisa.",
        "riasec": {"I": 0.95, "C": 0.80, "R": 0.30, "A": 0.30, "S": 0.30, "E": 0.25},
        "big5": {"O": 0.85, "C": 0.90, "E": 0.30, "A": 0.45, "N": 0.85},
        "valores_altos": ["desafio_intelectual", "especializacao", "aprendizado_continuo", "resultados"],
        "valores_baixos": ["extroversao_social", "ajudar_pessoas"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos + pós (recomendado)",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 25000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["ciência de dados", "análise", "atuária", "finanças quantitativas"]
    },
    {
        "id": "fisica", "nome": "Física",
        "area": "Exatas", "emoji": "🔭",
        "descricao": "Estuda as leis fundamentais do universo. Abre portas para pesquisa, tecnologia avançada, astronomia e docência.",
        "riasec": {"I": 0.95, "C": 0.65, "R": 0.55, "A": 0.30, "S": 0.30, "E": 0.20},
        "big5": {"O": 0.95, "C": 0.85, "E": 0.30, "A": 0.45, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "aprendizado_continuo", "especializacao", "proposito", "pioneirismo"],
        "valores_baixos": ["remuneracao", "extroversao_social"],
        "habilidades_chave": ["I", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos + pós obrigatório",
        "dificuldade_enem": "Alta", "salario_min": 3500, "salario_max": 20000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["ciência", "pesquisa", "academia", "astronomia", "inovação"]
    },

    # ══════════════════════════════════════════════════════════════
    # ENGENHARIAS — 9 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "engenharia_civil", "nome": "Engenharia Civil",
        "area": "Engenharias", "emoji": "🏗️",
        "descricao": "Projeta e supervisiona obras, pontes, estradas e infraestrutura. Uma das mais tradicionais e sempre demandadas no Brasil.",
        "riasec": {"R": 0.90, "I": 0.80, "C": 0.65, "E": 0.50, "A": 0.30, "S": 0.25},
        "big5": {"O": 0.60, "C": 0.90, "E": 0.55, "A": 0.50, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "resultados", "reconhecimento", "melhoria"],
        "valores_baixos": ["remoto_digital", "humanismo"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["obras", "infraestrutura", "matemática", "concreto"]
    },
    {
        "id": "engenharia_eletrica", "nome": "Engenharia Elétrica / Eletrônica",
        "area": "Engenharias", "emoji": "⚡",
        "descricao": "Projeta sistemas elétricos, de automação e energia. Atua em energia renovável, telecomunicações e eletroeletrônica.",
        "riasec": {"R": 0.85, "I": 0.90, "C": 0.65, "A": 0.20, "E": 0.30, "S": 0.15},
        "big5": {"O": 0.70, "C": 0.85, "E": 0.40, "A": 0.45, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "tecnologia", "inovacao", "remuneracao"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["energia renovável", "automação", "eletrônica"]
    },
    {
        "id": "engenharia_mecanica", "nome": "Engenharia Mecânica",
        "area": "Engenharias", "emoji": "⚙️",
        "descricao": "Projeta máquinas, motores e sistemas mecânicos. Base para automação, indústria automotiva e manufatura.",
        "riasec": {"R": 0.90, "I": 0.85, "C": 0.60, "A": 0.20, "E": 0.35, "S": 0.15},
        "big5": {"O": 0.65, "C": 0.85, "E": 0.50, "A": 0.45, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "resultados", "tecnologia", "melhoria"],
        "valores_baixos": ["remoto_digital", "ajudar_pessoas"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["indústria", "máquinas", "automação", "automotivo"]
    },
    {
        "id": "engenharia_producao", "nome": "Engenharia de Produção / Logística",
        "area": "Engenharias / Negócios", "emoji": "🏭",
        "descricao": "Otimiza processos, cadeias de suprimentos e gestão industrial. Ótima remuneração com alta versatilidade — funciona tanto em fábrica quanto em consultoria.",
        "riasec": {"C": 0.85, "I": 0.80, "E": 0.70, "R": 0.60, "A": 0.25, "S": 0.30},
        "big5": {"O": 0.65, "C": 0.90, "E": 0.60, "A": 0.55, "N": 0.80},
        "valores_altos": ["resultados", "desafio_intelectual", "tecnologia", "remuneracao", "melhoria"],
        "valores_baixos": ["humanismo", "arte"],
        "habilidades_chave": ["C", "I", "E"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["indústria", "processos", "logística", "gestão", "versatilidade"]
    },
    {
        "id": "engenharia_quimica", "nome": "Engenharia Química",
        "area": "Engenharias", "emoji": "⚗️",
        "descricao": "Desenvolve processos industriais químicos — petróleo, alimentos, cosméticos, farmácia. Alta remuneração no setor industrial.",
        "riasec": {"I": 0.90, "R": 0.75, "C": 0.65, "A": 0.20, "S": 0.25, "E": 0.30},
        "big5": {"O": 0.70, "C": 0.90, "E": 0.40, "A": 0.45, "N": 0.85},
        "valores_altos": ["desafio_intelectual", "tecnologia", "especializacao", "remuneracao"],
        "valores_baixos": ["extroversao_social", "ajudar_pessoas"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["ciência", "indústria", "petróleo", "alimentícia", "cosméticos"]
    },
    {
        "id": "engenharia_ambiental", "nome": "Engenharia Ambiental / Gestão Ambiental",
        "area": "Engenharias / Meio Ambiente", "emoji": "🌱",
        "descricao": "Protege o meio ambiente e desenvolve soluções sustentáveis. Área em forte crescimento com a agenda climática global.",
        "riasec": {"I": 0.80, "R": 0.75, "S": 0.55, "C": 0.60, "E": 0.50, "A": 0.35},
        "big5": {"O": 0.80, "C": 0.80, "E": 0.55, "A": 0.65, "N": 0.75},
        "valores_altos": ["impacto_social", "proposito", "inovacao", "desafio_intelectual"],
        "valores_baixos": ["remuneracao", "escala_urbana"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4000, "salario_max": 18000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["sustentabilidade", "natureza", "clima", "futuro"]
    },
    {
        "id": "engenharia_aeronautica", "nome": "Engenharia Aeronáutica / Aeroespacial",
        "area": "Engenharias", "emoji": "✈️",
        "descricao": "Projeta aeronaves, foguetes e sistemas aeroespaciais. Uma das engenharias mais desafiadoras e fascinantes — base em aviação e exploração espacial.",
        "riasec": {"I": 0.95, "R": 0.85, "C": 0.65, "A": 0.30, "E": 0.30, "S": 0.15},
        "big5": {"O": 0.85, "C": 0.90, "E": 0.40, "A": 0.45, "N": 0.90},
        "valores_altos": ["desafio_intelectual", "pioneirismo", "tecnologia", "especializacao"],
        "valores_baixos": ["ajudar_pessoas", "humanismo"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos (ITA, UNICAMP, USP...)",
        "dificuldade_enem": "Altíssima", "salario_min": 7000, "salario_max": 35000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["aviação", "espaço", "defesa", "alta nota ENEM", "ITA"]
    },
    {
        "id": "engenharia_petroleo", "nome": "Engenharia de Petróleo / Minas",
        "area": "Engenharias", "emoji": "🛢️",
        "descricao": "Extrai e processa recursos naturais como petróleo, gás e minérios. Setor estratégico brasileiro com das maiores remunerações da engenharia.",
        "riasec": {"R": 0.90, "I": 0.85, "C": 0.60, "E": 0.45, "A": 0.15, "S": 0.15},
        "big5": {"O": 0.65, "C": 0.85, "E": 0.50, "A": 0.45, "N": 0.80},
        "valores_altos": ["remuneracao", "desafio_intelectual", "resultados", "carreira_consolidada"],
        "valores_baixos": ["equilibrio", "remoto_digital"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 7000, "salario_max": 40000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["Petrobras", "mineração", "alta renda", "campo", "Petróleo"]
    },
    {
        "id": "engenharia_biomedica", "nome": "Engenharia Biomédica",
        "area": "Engenharias / Saúde", "emoji": "🫀",
        "descricao": "Desenvolve equipamentos e tecnologias médicas: próteses, diagnósticos por imagem, robótica cirúrgica. Intersecção fascinante entre medicina e engenharia.",
        "riasec": {"I": 0.90, "R": 0.80, "S": 0.50, "C": 0.65, "A": 0.35, "E": 0.30},
        "big5": {"O": 0.85, "C": 0.85, "E": 0.40, "A": 0.60, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "impacto_social", "tecnologia", "inovacao", "pioneirismo"],
        "valores_baixos": ["extroversao_social"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 25000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["saúde", "inovação", "robótica", "alta tecnologia", "medicina"]
    },

    # ══════════════════════════════════════════════════════════════
    # NEGÓCIOS / GESTÃO — 8 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "administracao", "nome": "Administração",
        "area": "Negócios", "emoji": "📊",
        "descricao": "Gerencia recursos, processos e pessoas em organizações. A graduação mais versátil do mercado — abre portas para qualquer setor.",
        "riasec": {"E": 0.85, "C": 0.75, "S": 0.60, "I": 0.55, "A": 0.35, "R": 0.20},
        "big5": {"O": 0.65, "C": 0.80, "E": 0.75, "A": 0.65, "N": 0.75},
        "valores_altos": ["lideranca", "resultados", "reconhecimento", "autonomia", "variedade"],
        "valores_baixos": ["humanismo"],
        "habilidades_chave": ["E", "C", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["gestão", "versatilidade", "liderança", "negócios"]
    },
    {
        "id": "economia", "nome": "Economia",
        "area": "Negócios / Exatas", "emoji": "📈",
        "descricao": "Analisa mercados, políticas econômicas e comportamento financeiro. Alta remuneração com perfil muito analítico.",
        "riasec": {"I": 0.85, "C": 0.85, "E": 0.65, "A": 0.30, "S": 0.35, "R": 0.15},
        "big5": {"O": 0.80, "C": 0.85, "E": 0.55, "A": 0.50, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "remuneracao", "resultados", "aprendizado_continuo"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["I", "C", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 35000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["finanças", "mercado", "análise", "banco", "alta renda"]
    },
    {
        "id": "contabilidade", "nome": "Ciências Contábeis",
        "area": "Negócios", "emoji": "🧾",
        "descricao": "Controla e analisa o patrimônio de organizações. Alta demanda, estabilidade e carreira própria possível como contador autônomo.",
        "riasec": {"C": 0.90, "I": 0.70, "E": 0.55, "S": 0.35, "R": 0.20, "A": 0.15},
        "big5": {"O": 0.50, "C": 0.95, "E": 0.40, "A": 0.55, "N": 0.85},
        "valores_altos": ["estabilidade", "remuneracao", "resultados", "especializacao", "carreira_consolidada"],
        "valores_baixos": ["inovacao", "variedade"],
        "habilidades_chave": ["C", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média", "salario_min": 3000, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["finanças", "estabilidade", "números", "tributário"]
    },
    {
        "id": "marketing", "nome": "Marketing / Comunicação Empresarial",
        "area": "Negócios / Comunicação", "emoji": "📣",
        "descricao": "Estratégia de marca, comportamento do consumidor e comunicação. Une criatividade e dados para gerar resultados de negócio.",
        "riasec": {"E": 0.80, "A": 0.75, "S": 0.65, "C": 0.50, "I": 0.55, "R": 0.15},
        "big5": {"O": 0.80, "C": 0.65, "E": 0.80, "A": 0.65, "N": 0.70},
        "valores_altos": ["inovacao", "resultados", "reconhecimento", "tecnologia", "variedade"],
        "valores_baixos": ["humanismo", "rotina_especializada"],
        "habilidades_chave": ["E", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["criatividade", "dados", "brand", "digital marketing"]
    },
    {
        "id": "gestao_publica", "nome": "Gestão Pública / Políticas Públicas",
        "area": "Negócios / Humanas", "emoji": "🏛️",
        "descricao": "Administra recursos do Estado para melhorar a vida da população. Impacto macro com estabilidade.",
        "riasec": {"E": 0.75, "S": 0.75, "I": 0.65, "C": 0.70, "A": 0.35, "R": 0.15},
        "big5": {"O": 0.70, "C": 0.80, "E": 0.65, "A": 0.75, "N": 0.75},
        "valores_altos": ["impacto_social", "estabilidade", "proposito", "lideranca", "escala"],
        "valores_baixos": ["remuneracao", "empreendedorismo"],
        "habilidades_chave": ["E", "S", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3500, "salario_max": 18000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["governo", "políticas públicas", "impacto social", "concurso"]
    },
    {
        "id": "recursos_humanos", "nome": "Recursos Humanos / Gestão de Pessoas",
        "area": "Negócios", "emoji": "👤",
        "descricao": "Atrai, desenvolve e retém talentos em organizações. Área estratégica que une psicologia organizacional e gestão de negócios.",
        "riasec": {"S": 0.85, "E": 0.70, "A": 0.55, "C": 0.60, "I": 0.55, "R": 0.15},
        "big5": {"O": 0.70, "C": 0.75, "E": 0.75, "A": 0.85, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "reconhecimento", "impacto_social", "lideranca"],
        "valores_baixos": ["remuneracao", "tecnologia"],
        "habilidades_chave": ["S", "E", "C"],
        "duracao_anos": 4, "duracao_label": "4 anos (ou técnico em 2 anos)",
        "dificuldade_enem": "Baixa-média", "salario_min": 2800, "salario_max": 15000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["pessoas", "gestão", "seleção", "T&D", "cultura organizacional"]
    },
    {
        "id": "relacoes_internacionais", "nome": "Relações Internacionais / Negócios Internacionais",
        "area": "Negócios / Humanas", "emoji": "🌐",
        "descricao": "Estuda geopolítica, diplomacia e comércio exterior. Para quem quer atuar no mundo globalizado.",
        "riasec": {"E": 0.75, "S": 0.70, "I": 0.70, "A": 0.55, "C": 0.55, "R": 0.10},
        "big5": {"O": 0.90, "C": 0.70, "E": 0.80, "A": 0.70, "N": 0.75},
        "valores_altos": ["impacto_social", "reconhecimento", "lideranca", "aprendizado_continuo", "variedade"],
        "valores_baixos": ["rotina_especializada", "concurso_empresa_fechado"],
        "habilidades_chave": ["E", "S", "I", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Alta", "salario_min": 4000, "salario_max": 22000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["diplomacia", "globalização", "idiomas", "mundo"]
    },
    {
        "id": "startups_empreendedorismo", "nome": "Empreendedorismo / Startups",
        "area": "Negócios", "emoji": "🚀",
        "descricao": "Criação de empresas e soluções inovadoras. Carreira não-linear de alto risco e alto potencial — para quem não se encaixa nos modelos tradicionais.",
        "riasec": {"E": 0.95, "I": 0.70, "A": 0.65, "S": 0.55, "C": 0.50, "R": 0.35},
        "big5": {"O": 0.90, "C": 0.70, "E": 0.85, "A": 0.55, "N": 0.65},
        "valores_altos": ["autonomia", "inovacao", "empreendedorismo", "lideranca", "remuneracao", "pioneirismo", "risco_alto"],
        "valores_baixos": ["estabilidade", "concurso_empresa", "qualidade_vida_paga_menos"],
        "habilidades_chave": ["E", "I", "A"],
        "duracao_anos": 4, "duracao_label": "Qualquer graduação + visão de mercado",
        "dificuldade_enem": "Variável", "salario_min": 0, "salario_max": 150000,
        "perspectiva_mercado": "Alto risco / Alta recompensa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["risco", "inovação", "liberdade", "liderança", "venture"]
    },

    # ══════════════════════════════════════════════════════════════
    # HUMANAS / SOCIAIS — 8 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "direito", "nome": "Direito",
        "area": "Humanas", "emoji": "⚖️",
        "descricao": "Interpreta e aplica a lei. Uma das carreiras mais versáteis e com maior prestígio no Brasil — advocacia, magistratura, MP, concursos.",
        "riasec": {"E": 0.85, "S": 0.70, "I": 0.75, "C": 0.70, "A": 0.50, "R": 0.10},
        "big5": {"O": 0.75, "C": 0.85, "E": 0.70, "A": 0.55, "N": 0.80},
        "valores_altos": ["reconhecimento", "prestigio", "lideranca", "impacto_social", "remuneracao"],
        "valores_baixos": ["remoto_digital", "rotina_especializada"],
        "habilidades_chave": ["E", "S", "I", "A"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4000, "salario_max": 60000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["justiça", "debate", "prestígio", "versatilidade", "OAB"]
    },
    {
        "id": "pedagogia_licenciaturas", "nome": "Pedagogia / Licenciaturas",
        "area": "Educação", "emoji": "📚",
        "descricao": "Forma educadores para transformar vidas através do ensino. Alta empregabilidade via concurso público em todo o Brasil.",
        "riasec": {"S": 0.95, "A": 0.55, "I": 0.55, "C": 0.50, "E": 0.45, "R": 0.15},
        "big5": {"O": 0.75, "C": 0.80, "E": 0.70, "A": 0.90, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "estabilidade", "proposito", "profundidade_relacional"],
        "valores_baixos": ["remuneracao", "escala"],
        "habilidades_chave": ["S", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média", "salario_min": 2800, "salario_max": 10000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["educação", "transformação social", "estabilidade", "concurso"]
    },
    {
        "id": "psicologia_organizacional", "nome": "Administração / Psicologia com foco Organizacional",
        "area": "Negócios / Humanas", "emoji": "🏢",
        "descricao": "Aplica ciência do comportamento em empresas para aumentar performance e bem-estar organizacional.",
        "riasec": {"S": 0.80, "E": 0.70, "I": 0.70, "A": 0.50, "C": 0.55, "R": 0.15},
        "big5": {"O": 0.75, "C": 0.75, "E": 0.70, "A": 0.80, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "reconhecimento", "aprendizado_continuo", "lideranca"],
        "valores_baixos": ["humanismo_exclusivo"],
        "habilidades_chave": ["S", "E", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3500, "salario_max": 18000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["pessoas", "comportamento organizacional", "liderança", "coaching"]
    },
    {
        "id": "ciencias_sociais", "nome": "Ciências Sociais / Sociologia / Ciência Política",
        "area": "Humanas", "emoji": "🏛️",
        "descricao": "Analisa sociedades, poder e estruturas sociais. Forma pesquisadores, consultores, jornalistas e profissionais de política.",
        "riasec": {"I": 0.80, "S": 0.75, "A": 0.65, "E": 0.45, "C": 0.40, "R": 0.10},
        "big5": {"O": 0.90, "C": 0.65, "E": 0.60, "A": 0.70, "N": 0.70},
        "valores_altos": ["proposito", "impacto_social", "aprendizado_continuo", "humanismo"],
        "valores_baixos": ["remuneracao", "tecnologia"],
        "habilidades_chave": ["I", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2800, "salario_max": 12000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["humanidades", "educação", "pesquisa", "política"]
    },
    {
        "id": "filosofia", "nome": "Filosofia / Ética",
        "area": "Humanas", "emoji": "💭",
        "descricao": "Investiga questões fundamentais sobre existência, ética e conhecimento. Forma pensadores críticos para academia, ensino e consultoria.",
        "riasec": {"I": 0.85, "A": 0.75, "S": 0.55, "C": 0.35, "E": 0.30, "R": 0.05},
        "big5": {"O": 0.95, "C": 0.65, "E": 0.40, "A": 0.65, "N": 0.70},
        "valores_altos": ["proposito", "aprendizado_continuo", "humanismo", "autonomia"],
        "valores_baixos": ["remuneracao", "tecnologia", "resultados"],
        "habilidades_chave": ["I", "A"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2500, "salario_max": 8000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["pensamento crítico", "academia", "educação", "ética"]
    },
    {
        "id": "servico_social", "nome": "Serviço Social",
        "area": "Humanas", "emoji": "🤝",
        "descricao": "Combate desigualdades e garante direitos de populações vulneráveis. Missão de transformação social real e concreta.",
        "riasec": {"S": 0.95, "E": 0.55, "I": 0.50, "C": 0.55, "A": 0.35, "R": 0.15},
        "big5": {"O": 0.70, "C": 0.75, "E": 0.65, "A": 0.95, "N": 0.70},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "proposito", "humanismo"],
        "valores_baixos": ["remuneracao", "prestigio", "escala"],
        "habilidades_chave": ["S", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa", "salario_min": 2500, "salario_max": 8000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["assistência social", "vulneráveis", "direitos", "CRAS"]
    },
    {
        "id": "letras_traducao", "nome": "Letras / Tradução / Interpretação",
        "area": "Humanas / Comunicação", "emoji": "📝",
        "descricao": "Estuda língua e literatura para comunicar, ensinar e traduzir. Professores, escritores, revisores, tradutores e intérpretes.",
        "riasec": {"A": 0.85, "I": 0.65, "S": 0.65, "C": 0.45, "E": 0.30, "R": 0.10},
        "big5": {"O": 0.90, "C": 0.70, "E": 0.50, "A": 0.70, "N": 0.70},
        "valores_altos": ["aprendizado_continuo", "autonomia", "proposito", "humanismo"],
        "valores_baixos": ["tecnologia", "remuneracao"],
        "habilidades_chave": ["A", "I", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2500, "salario_max": 15000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["linguagem", "escrita", "educação", "idiomas", "remoto"]
    },
    {
        "id": "historia", "nome": "História",
        "area": "Humanas", "emoji": "🏺",
        "descricao": "Analisa o passado e o presente da humanidade, formando cidadãos críticos e historiadores.",
        "riasec": {"I": 0.80, "S": 0.65, "A": 0.65, "C": 0.50, "E": 0.35, "R": 0.10},
        "big5": {"O": 0.90, "C": 0.65, "E": 0.50, "A": 0.65, "N": 0.70},
        "valores_altos": ["proposito", "impacto_social", "aprendizado_continuo", "humanismo"],
        "valores_baixos": ["remuneracao", "tecnologia"],
        "habilidades_chave": ["I", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2800, "salario_max": 9000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial", "ead"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["humanidades", "educação", "pesquisa", "museu"]
    },

    # ══════════════════════════════════════════════════════════════
    # COMUNICAÇÃO / ARTES / CRIATIVO — 9 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "jornalismo", "nome": "Jornalismo / Comunicação",
        "area": "Comunicação", "emoji": "📰",
        "descricao": "Investiga, apura e comunica fatos relevantes à sociedade. Profissão de impacto social em plena transformação digital.",
        "riasec": {"A": 0.80, "S": 0.75, "E": 0.65, "I": 0.65, "C": 0.35, "R": 0.10},
        "big5": {"O": 0.85, "C": 0.65, "E": 0.80, "A": 0.65, "N": 0.70},
        "valores_altos": ["impacto_social", "inovacao", "proposito", "autonomia", "variedade"],
        "valores_baixos": ["remuneracao", "estabilidade"],
        "habilidades_chave": ["A", "S", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2500, "salario_max": 18000,
        "perspectiva_mercado": "Em transformação", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["mídia", "escrita", "impacto social", "digital", "podcast"]
    },
    {
        "id": "publicidade_propaganda", "nome": "Publicidade e Propaganda",
        "area": "Comunicação", "emoji": "📢",
        "descricao": "Cria campanhas e estratégias de comunicação para marcas. Une criatividade, psicologia do consumidor e dados.",
        "riasec": {"A": 0.85, "E": 0.80, "S": 0.60, "I": 0.50, "C": 0.40, "R": 0.15},
        "big5": {"O": 0.85, "C": 0.65, "E": 0.85, "A": 0.65, "N": 0.70},
        "valores_altos": ["inovacao", "resultados", "autonomia", "tecnologia", "reconhecimento"],
        "valores_baixos": ["humanismo", "ajudar_pessoas"],
        "habilidades_chave": ["A", "E", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2800, "salario_max": 25000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["criatividade", "branding", "digital", "agências", "marca"]
    },
    {
        "id": "arquitetura", "nome": "Arquitetura e Urbanismo",
        "area": "Artes / Exatas", "emoji": "🏠",
        "descricao": "Projeta espaços que unem funcionalidade, estética e humanidade. Criatividade técnica com impacto visual permanente.",
        "riasec": {"A": 0.85, "R": 0.75, "I": 0.65, "E": 0.45, "C": 0.55, "S": 0.35},
        "big5": {"O": 0.90, "C": 0.75, "E": 0.60, "A": 0.60, "N": 0.75},
        "valores_altos": ["inovacao", "reconhecimento", "autonomia", "impacto_social"],
        "valores_baixos": ["remoto_digital", "rotina_especializada"],
        "habilidades_chave": ["A", "R", "I"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 3500, "salario_max": 20000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["arte", "espaços", "técnico", "criativo", "urbanismo"]
    },
    {
        "id": "design_grafico", "nome": "Design Gráfico / Visual",
        "area": "Comunicação / Artes", "emoji": "🎨",
        "descricao": "Cria soluções visuais que comunicam, informam e encantam. Muito demandado no mercado digital com alta versatilidade.",
        "riasec": {"A": 0.95, "I": 0.55, "R": 0.55, "E": 0.45, "S": 0.35, "C": 0.35},
        "big5": {"O": 0.95, "C": 0.65, "E": 0.55, "A": 0.60, "N": 0.70},
        "valores_altos": ["inovacao", "autonomia", "variedade", "satisfacao_pessoal"],
        "valores_baixos": ["concurso_empresa", "rotina_especializada"],
        "habilidades_chave": ["A", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos (ou cursos livres)",
        "dificuldade_enem": "Média", "salario_min": 2800, "salario_max": 18000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial", "ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["criatividade", "visual", "branding", "digital", "remoto"]
    },
    {
        "id": "cinema_audiovisual", "nome": "Cinema / Audiovisual / Streaming",
        "area": "Comunicação / Artes", "emoji": "🎬",
        "descricao": "Cria narrativas visuais para cinema, streaming e redes sociais. Mercado em crescimento com a economia criativa e plataformas digitais.",
        "riasec": {"A": 0.90, "E": 0.65, "I": 0.55, "S": 0.55, "R": 0.45, "C": 0.30},
        "big5": {"O": 0.90, "C": 0.65, "E": 0.65, "A": 0.60, "N": 0.65},
        "valores_altos": ["inovacao", "autonomia", "proposito", "satisfacao_pessoal", "variedade"],
        "valores_baixos": ["estabilidade", "carreira_consolidada"],
        "habilidades_chave": ["A", "E", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2500, "salario_max": 25000,
        "perspectiva_mercado": "Em crescimento", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["streaming", "criativo", "digital", "narrativa", "YouTube"]
    },
    {
        "id": "musica_artes_cenicas", "nome": "Música / Teatro / Artes Cênicas",
        "area": "Artes", "emoji": "🎵",
        "descricao": "Expressa a humanidade através da arte. Performance, ensino, produção e indústria criativa.",
        "riasec": {"A": 0.95, "S": 0.65, "E": 0.55, "I": 0.40, "R": 0.30, "C": 0.20},
        "big5": {"O": 0.95, "C": 0.55, "E": 0.70, "A": 0.70, "N": 0.60},
        "valores_altos": ["autonomia", "proposito", "satisfacao_pessoal", "inovacao"],
        "valores_baixos": ["remuneracao", "estabilidade"],
        "habilidades_chave": ["A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 1800, "salario_max": 15000,
        "perspectiva_mercado": "Desafiadora", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["arte", "expressão", "cultura", "independência", "palco"]
    },
    {
        "id": "moda_estilismo", "nome": "Moda / Estilismo / Design de Moda",
        "area": "Artes / Comunicação", "emoji": "👗",
        "descricao": "Cria coleções e identidades visuais na interseção de arte, cultura e negócio.",
        "riasec": {"A": 0.90, "E": 0.65, "S": 0.55, "I": 0.40, "R": 0.50, "C": 0.35},
        "big5": {"O": 0.90, "C": 0.65, "E": 0.75, "A": 0.65, "N": 0.70},
        "valores_altos": ["inovacao", "autonomia", "satisfacao_pessoal", "reconhecimento"],
        "valores_baixos": ["estabilidade", "rotina_especializada"],
        "habilidades_chave": ["A", "E", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2000, "salario_max": 18000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["criatividade", "estética", "arte", "mercado fashion"]
    },
    {
        "id": "creator_digital", "nome": "Criador de Conteúdo Digital / Influência",
        "area": "Comunicação / Criativo", "emoji": "📲",
        "descricao": "Produz conteúdo em plataformas digitais para audiências segmentadas. Nova carreira com alto potencial mas grande variabilidade.",
        "riasec": {"A": 0.85, "E": 0.80, "S": 0.70, "I": 0.45, "C": 0.35, "R": 0.30},
        "big5": {"O": 0.90, "C": 0.60, "E": 0.85, "A": 0.60, "N": 0.55},
        "valores_altos": ["autonomia", "inovacao", "empreendedorismo", "tecnologia", "reconhecimento", "pioneirismo"],
        "valores_baixos": ["estabilidade", "carreira_consolidada"],
        "habilidades_chave": ["A", "E", "S"],
        "duracao_anos": 1, "duracao_label": "Aprendizado prático / cursos",
        "dificuldade_enem": "Baixa", "salario_min": 0, "salario_max": 80000,
        "perspectiva_mercado": "Alta variabilidade", "modalidade": ["ead"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["digital", "criativo", "empreendedor", "redes sociais", "YouTube"]
    },
    {
        "id": "producao_cultural", "nome": "Produção Cultural / Gestão Cultural",
        "area": "Artes / Negócios", "emoji": "🎪",
        "descricao": "Organiza e viabiliza eventos, exposições e manifestações culturais. Conecta arte e sociedade através da gestão.",
        "riasec": {"E": 0.75, "A": 0.80, "S": 0.70, "C": 0.50, "I": 0.40, "R": 0.25},
        "big5": {"O": 0.85, "C": 0.70, "E": 0.75, "A": 0.75, "N": 0.65},
        "valores_altos": ["inovacao", "impacto_social", "variedade", "autonomia"],
        "valores_baixos": ["remuneracao", "estabilidade"],
        "habilidades_chave": ["E", "A", "S"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 2000, "salario_max": 12000,
        "perspectiva_mercado": "Estável", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": True,
        "tags": ["cultura", "eventos", "arte", "gestão", "diversidade"]
    },

    # ══════════════════════════════════════════════════════════════
    # AGRONEGÓCIO / MEIO AMBIENTE / BIOLOGIA — 6 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "agronomia", "nome": "Agronomia",
        "area": "Agronegócio", "emoji": "🌾",
        "descricao": "Desenvolve e melhora a produção agrícola. Setor que movimenta o maior PIB setorial do Brasil, com excelente mercado.",
        "riasec": {"R": 0.85, "I": 0.80, "C": 0.55, "S": 0.40, "E": 0.55, "A": 0.20},
        "big5": {"O": 0.65, "C": 0.85, "E": 0.55, "A": 0.60, "N": 0.80},
        "valores_altos": ["impacto_social", "desafio_intelectual", "remuneracao", "resultados"],
        "valores_baixos": ["remoto_digital"],
        "habilidades_chave": ["R", "I", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 4000, "salario_max": 25000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["campo", "agronegócio", "sustentabilidade", "Brasil"]
    },
    {
        "id": "ciencias_biologicas", "nome": "Ciências Biológicas / Biologia",
        "area": "Ciências", "emoji": "🧬",
        "descricao": "Estuda a vida em todas as suas formas. Base para biotecnologia, medicina, ecologia, docência e pesquisa.",
        "riasec": {"I": 0.90, "R": 0.65, "S": 0.55, "C": 0.50, "A": 0.35, "E": 0.25},
        "big5": {"O": 0.90, "C": 0.80, "E": 0.40, "A": 0.65, "N": 0.75},
        "valores_altos": ["desafio_intelectual", "proposito", "aprendizado_continuo", "especializacao"],
        "valores_baixos": ["remuneracao", "lideranca"],
        "habilidades_chave": ["I", "R"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 3000, "salario_max": 15000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["ciência", "natureza", "pesquisa", "laboratório", "bio"]
    },
    {
        "id": "zootecnia", "nome": "Zootecnia / Produção Animal",
        "area": "Agronegócio", "emoji": "🐄",
        "descricao": "Melhora a produção animal para alimentação e derivados. Ligada ao agronegócio brasileiro com forte mercado no interior.",
        "riasec": {"R": 0.85, "I": 0.70, "C": 0.55, "S": 0.45, "E": 0.45, "A": 0.15},
        "big5": {"O": 0.60, "C": 0.80, "E": 0.55, "A": 0.65, "N": 0.75},
        "valores_altos": ["impacto_social", "resultados", "natureza", "carreira_consolidada"],
        "valores_baixos": ["remoto_digital", "centros_urbanos"],
        "habilidades_chave": ["R", "I"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Média", "salario_min": 3000, "salario_max": 14000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["agro", "animais", "campo", "pecuária"]
    },
    {
        "id": "engenharia_alimentos", "nome": "Engenharia de Alimentos / Tecnologia de Alimentos",
        "area": "Engenharias / Agronegócio", "emoji": "🍎",
        "descricao": "Desenvolve e melhora processos de produção, conservação e qualidade de alimentos. Brasil é líder mundial no agronegócio.",
        "riasec": {"I": 0.85, "R": 0.75, "C": 0.65, "S": 0.35, "A": 0.20, "E": 0.30},
        "big5": {"O": 0.65, "C": 0.90, "E": 0.45, "A": 0.55, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "melhoria", "resultados", "impacto_social"],
        "valores_baixos": ["extroversao_social"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Média-alta", "salario_min": 4000, "salario_max": 16000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["alimentos", "qualidade", "indústria", "agronegócio"]
    },
    {
        "id": "geologia_geociencias", "nome": "Geologia / Geociências",
        "area": "Ciências / Engenharias", "emoji": "🪨",
        "descricao": "Estuda a Terra — rochas, recursos minerais, estruturas e riscos geológicos. Alta remuneração especialmente em mineração e petróleo.",
        "riasec": {"I": 0.90, "R": 0.80, "C": 0.55, "A": 0.25, "S": 0.25, "E": 0.30},
        "big5": {"O": 0.80, "C": 0.80, "E": 0.45, "A": 0.50, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "especializacao", "aprendizado_continuo"],
        "valores_baixos": ["extroversao_social", "centros_urbanos"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 5000, "salario_max": 30000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["mineração", "petróleo", "natureza", "campo", "alta renda"]
    },
    {
        "id": "oceanografia_meteorologia", "nome": "Oceanografia / Meteorologia",
        "area": "Ciências", "emoji": "🌊",
        "descricao": "Estuda oceanos, clima e fenômenos atmosféricos. Área crítica para o futuro climático com mercado em expansão global.",
        "riasec": {"I": 0.90, "R": 0.65, "C": 0.60, "A": 0.30, "S": 0.35, "E": 0.25},
        "big5": {"O": 0.85, "C": 0.80, "E": 0.40, "A": 0.55, "N": 0.80},
        "valores_altos": ["desafio_intelectual", "proposito", "aprendizado_continuo", "pioneirismo"],
        "valores_baixos": ["remuneracao", "centros_urbanos"],
        "habilidades_chave": ["I", "R", "C"],
        "duracao_anos": 5, "duracao_label": "5 anos",
        "dificuldade_enem": "Alta", "salario_min": 4000, "salario_max": 18000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["clima", "oceano", "natureza", "pesquisa", "futuro"]
    },

    # ══════════════════════════════════════════════════════════════
    # SEGURANÇA / MILITARES / SERVIÇO PÚBLICO — 5 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "forcas_armadas", "nome": "Forças Armadas (Exército / Marinha / Aeronáutica)",
        "area": "Segurança / Defesa", "emoji": "🎖️",
        "descricao": "Defesa nacional e missões humanitárias. Carreira com formação completa, estabilidade total e progressão hierárquica clara.",
        "riasec": {"E": 0.85, "R": 0.85, "C": 0.75, "S": 0.55, "I": 0.50, "A": 0.20},
        "big5": {"O": 0.55, "C": 0.95, "E": 0.65, "A": 0.60, "N": 0.90},
        "valores_altos": ["estabilidade", "reconhecimento", "lideranca", "proposito", "resultados", "carreira_consolidada"],
        "valores_baixos": ["autonomia", "empreendedorismo", "remoto_digital"],
        "habilidades_chave": ["E", "R", "C"],
        "duracao_anos": 4, "duracao_label": "Academias militares (4 anos)",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 25000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["estabilidade", "hierarquia", "disciplina", "defesa", "missão"]
    },
    {
        "id": "seguranca_publica", "nome": "Segurança Pública (Delegado / Perito / Agente)",
        "area": "Segurança", "emoji": "🚔",
        "descricao": "Investiga crimes, produz provas científicas e garante a segurança da população. Diversas carreiras com concurso público e alta remuneração.",
        "riasec": {"E": 0.80, "I": 0.70, "R": 0.70, "C": 0.75, "S": 0.55, "A": 0.15},
        "big5": {"O": 0.65, "C": 0.90, "E": 0.65, "A": 0.55, "N": 0.85},
        "valores_altos": ["impacto_social", "estabilidade", "resultados", "proposito", "remuneracao"],
        "valores_baixos": ["autonomia", "empreendedorismo"],
        "habilidades_chave": ["E", "I", "C"],
        "duracao_anos": 4, "duracao_label": "Graduação + concurso",
        "dificuldade_enem": "Alta", "salario_min": 4500, "salario_max": 22000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["justiça", "concurso", "estabilidade", "investigação", "perícia"]
    },
    {
        "id": "auditoria_fiscal", "nome": "Auditor Fiscal / Analista Tributário",
        "area": "Serviço Público", "emoji": "📑",
        "descricao": "Fiscaliza tributos e garante a arrecadação pública. Uma das carreiras públicas com maior remuneração do Brasil.",
        "riasec": {"C": 0.90, "I": 0.80, "E": 0.55, "S": 0.30, "R": 0.20, "A": 0.15},
        "big5": {"O": 0.60, "C": 0.95, "E": 0.45, "A": 0.45, "N": 0.85},
        "valores_altos": ["estabilidade", "remuneracao", "resultados", "especializacao", "carreira_consolidada"],
        "valores_baixos": ["empreendedorismo", "inovacao"],
        "habilidades_chave": ["C", "I"],
        "duracao_anos": 4, "duracao_label": "Graduação + preparação para concurso",
        "dificuldade_enem": "Alta", "salario_min": 12000, "salario_max": 35000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": True,
        "tags": ["concurso", "alta renda", "estabilidade", "fisco", "tributário"]
    },
    {
        "id": "magistratura_mp", "nome": "Magistratura / Ministério Público",
        "area": "Serviço Público / Direito", "emoji": "⚖️",
        "descricao": "Julga casos como juiz ou defende a sociedade como promotor. As carreiras jurídicas públicas mais prestigiadas e bem remuneradas do Brasil.",
        "riasec": {"E": 0.80, "I": 0.85, "C": 0.75, "S": 0.55, "A": 0.45, "R": 0.10},
        "big5": {"O": 0.75, "C": 0.95, "E": 0.60, "A": 0.55, "N": 0.90},
        "valores_altos": ["prestigio", "impacto_social", "remuneracao", "estabilidade", "especializacao"],
        "valores_baixos": ["empreendedorismo", "autonomia_total"],
        "habilidades_chave": ["I", "E", "C", "A"],
        "duracao_anos": 8, "duracao_label": "5 anos Direito + anos de concurso",
        "dificuldade_enem": "Alta", "salario_min": 22000, "salario_max": 60000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["prestígio", "alta renda", "concurso", "longo prazo", "poder"]
    },
    {
        "id": "diplomacia", "nome": "Diplomacia (Itamaraty / MRE)",
        "area": "Serviço Público / Internacional", "emoji": "🌐",
        "descricao": "Representa o Brasil no exterior e conduz a política externa. Uma das mais exclusivas e exigentes carreiras públicas.",
        "riasec": {"E": 0.75, "I": 0.85, "S": 0.70, "A": 0.65, "C": 0.60, "R": 0.10},
        "big5": {"O": 0.95, "C": 0.85, "E": 0.75, "A": 0.70, "N": 0.85},
        "valores_altos": ["prestigio", "impacto_social", "aprendizado_continuo", "variedade", "carreira_consolidada"],
        "valores_baixos": ["interior_preferencia", "empreendedorismo", "equilibrio"],
        "habilidades_chave": ["E", "I", "S", "A"],
        "duracao_anos": 7, "duracao_label": "Graduação + CACD (dificílimo)",
        "dificuldade_enem": "Altíssima", "salario_min": 15000, "salario_max": 30000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["prestígio", "idiomas", "mundo", "concurso", "excelência"]
    },

    # ══════════════════════════════════════════════════════════════
    # CARREIRAS TÉCNICAS / CURTO PRAZO — 5 carreiras
    # ══════════════════════════════════════════════════════════════

    {
        "id": "tecnico_saude", "nome": "Técnico em Saúde (Enfermagem / Radiologia / Lab)",
        "area": "Saúde", "emoji": "🏥",
        "descricao": "Auxilia profissionais de saúde em procedimentos clínicos. Entrada rápida no setor com altíssima empregabilidade.",
        "riasec": {"S": 0.85, "R": 0.70, "C": 0.65, "I": 0.50, "A": 0.15, "E": 0.20},
        "big5": {"O": 0.50, "C": 0.85, "E": 0.60, "A": 0.90, "N": 0.80},
        "valores_altos": ["ajudar_pessoas", "estabilidade", "impacto_social"],
        "valores_baixos": ["autonomia", "remoto_digital"],
        "habilidades_chave": ["S", "R", "C"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa", "salario_min": 1800, "salario_max": 5000,
        "perspectiva_mercado": "Excelente", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["saúde", "curto prazo", "empregabilidade alta", "IFET"]
    },
    {
        "id": "tecnico_eletrotecnica", "nome": "Técnico em Eletrotécnica / Mecatrônica / Automação",
        "area": "Técnico / Indústria", "emoji": "🔌",
        "descricao": "Instala e mantém sistemas elétricos e de automação industrial. Mercado sólido na indústria brasileira.",
        "riasec": {"R": 0.90, "I": 0.70, "C": 0.60, "A": 0.15, "S": 0.20, "E": 0.25},
        "big5": {"O": 0.55, "C": 0.85, "E": 0.45, "A": 0.50, "N": 0.80},
        "valores_altos": ["estabilidade", "resultados", "tecnologia", "melhoria"],
        "valores_baixos": ["arte", "escala"],
        "habilidades_chave": ["R", "I"],
        "duracao_anos": 2, "duracao_label": "1,5 a 2 anos",
        "dificuldade_enem": "Baixa", "salario_min": 2200, "salario_max": 8000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["indústria", "curto prazo", "técnico", "elétrica", "IFET"]
    },
    {
        "id": "piloto_aviacao", "nome": "Piloto de Aviação Civil",
        "area": "Transporte / Técnico", "emoji": "✈️",
        "descricao": "Comanda aeronaves comerciais e particulares. Alta remuneração, carreira clara e estilo de vida único.",
        "riasec": {"R": 0.85, "C": 0.80, "I": 0.65, "E": 0.55, "S": 0.35, "A": 0.20},
        "big5": {"O": 0.65, "C": 0.95, "E": 0.60, "A": 0.55, "N": 0.90},
        "valores_altos": ["remuneracao", "variedade", "reconhecimento", "carreira_consolidada"],
        "valores_baixos": ["equilibrio", "remoto_digital", "humanismo"],
        "habilidades_chave": ["R", "C", "I"],
        "duracao_anos": 2, "duracao_label": "2-3 anos (escola de aviação)",
        "dificuldade_enem": "Média", "salario_min": 8000, "salario_max": 35000,
        "perspectiva_mercado": "Muito boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["aviação", "alta renda", "viagens", "técnico", "precisão"]
    },
    {
        "id": "educacao_fisica", "nome": "Educação Física / Esporte",
        "area": "Saúde / Educação", "emoji": "⚽",
        "descricao": "Promove saúde, desempenho atlético e qualidade de vida através do movimento. Alta versatilidade de atuação.",
        "riasec": {"S": 0.85, "R": 0.85, "E": 0.60, "I": 0.45, "A": 0.30, "C": 0.35},
        "big5": {"O": 0.60, "C": 0.75, "E": 0.80, "A": 0.75, "N": 0.75},
        "valores_altos": ["ajudar_pessoas", "impacto_social", "autonomia", "equilibrio", "satisfacao_pessoal"],
        "valores_baixos": ["remuneracao"],
        "habilidades_chave": ["S", "R", "E"],
        "duracao_anos": 4, "duracao_label": "4 anos",
        "dificuldade_enem": "Baixa-média", "salario_min": 2500, "salario_max": 15000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": True, "remoto_opcao": False,
        "tags": ["esporte", "saúde", "atividade física", "pessoas"]
    },
    {
        "id": "gastronomia", "nome": "Gastronomia / Chef",
        "area": "Artes / Serviços", "emoji": "👨‍🍳",
        "descricao": "Cria experiências gastronômicas e gerencia cozinhas. Mercado em crescimento no Brasil com forte cultura alimentar.",
        "riasec": {"A": 0.80, "R": 0.80, "E": 0.60, "S": 0.55, "I": 0.40, "C": 0.45},
        "big5": {"O": 0.80, "C": 0.75, "E": 0.70, "A": 0.65, "N": 0.65},
        "valores_altos": ["inovacao", "satisfacao_pessoal", "autonomia", "reconhecimento"],
        "valores_baixos": ["remoto_digital", "estabilidade"],
        "habilidades_chave": ["A", "R", "E"],
        "duracao_anos": 2, "duracao_label": "2 a 4 anos",
        "dificuldade_enem": "Baixa", "salario_min": 2000, "salario_max": 20000,
        "perspectiva_mercado": "Boa", "modalidade": ["presencial"],
        "concurso_opcao": False, "remoto_opcao": False,
        "tags": ["culinária", "criativo", "restaurante", "empreendimento"]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# PERFIS RIASEC — dados para o frontend
# ─────────────────────────────────────────────────────────────────────────────

PERFIS_RIASEC = {
    "R": {
        "nome": "Realista", "emoji": "🔧",
        "cor": "#f97316", "cor_bg": "rgba(249, 115, 22, 0.15)",
        "descricao_curta": "Prático, técnico e concreto",
        "descricao": "Você tem perfil Realista! Prefere trabalhar com as mãos, ferramentas, máquinas ou em contato com a natureza. É direto, prático e resolve problemas de forma concreta. Se realiza quando vê resultados tangíveis do seu trabalho.",
        "pontos_fortes": ["Trabalho técnico e prático", "Habilidade manual e mecânica", "Pensamento concreto e objetivo", "Persistência e foco no resultado"],
        "ambientes_ideais": ["Obras e construção", "Indústria e manufatura", "Campo e natureza", "Laboratórios práticos", "Manutenção e reparos"],
    },
    "I": {
        "nome": "Investigativo", "emoji": "🔬",
        "cor": "#3b82f6", "cor_bg": "rgba(59, 130, 246, 0.15)",
        "descricao_curta": "Analítico, curioso e científico",
        "descricao": "Você tem perfil Investigativo! Adora explorar, questionar e entender como as coisas funcionam. Pensa de forma analítica, gosta de dados e argumentos lógicos. Se realiza resolvendo problemas complexos e expandindo o conhecimento.",
        "pontos_fortes": ["Raciocínio lógico e analítico", "Curiosidade intelectual profunda", "Pesquisa e investigação", "Pensamento crítico e científico"],
        "ambientes_ideais": ["Laboratórios e pesquisa", "Academia e ciência", "Tecnologia e dados", "Saúde e diagnóstico", "Consultoria e análise"],
    },
    "A": {
        "nome": "Artístico", "emoji": "🎨",
        "cor": "#ec4899", "cor_bg": "rgba(236, 72, 153, 0.15)",
        "descricao_curta": "Criativo, expressivo e inovador",
        "descricao": "Você tem perfil Artístico! É criativo, imaginativo e valoriza a originalidade. Gosta de expressar ideias de formas únicas e se incomoda com rotinas muito rígidas. Se realiza em ambientes que valorizam inovação e liberdade de criação.",
        "pontos_fortes": ["Criatividade e originalidade", "Sensibilidade estética", "Comunicação expressiva", "Inovação e pensamento não-linear"],
        "ambientes_ideais": ["Design e artes visuais", "Escrita e comunicação", "Música e artes cênicas", "Publicidade e criação", "Arquitetura e moda"],
    },
    "S": {
        "nome": "Social", "emoji": "🤝",
        "cor": "#22c55e", "cor_bg": "rgba(34, 197, 94, 0.15)",
        "descricao_curta": "Empático, colaborativo e humanista",
        "descricao": "Você tem perfil Social! Seu poder está nas pessoas. É empático, comunicativo e genuinamente se importa com o bem-estar alheio. Se realiza quando pode ensinar, ajudar, cuidar ou colaborar com outros para alcançar algo maior.",
        "pontos_fortes": ["Empatia e escuta ativa", "Comunicação interpessoal", "Trabalho em equipe", "Cuidado e orientação genuínos"],
        "ambientes_ideais": ["Saúde e bem-estar", "Educação e ensino", "Assistência social", "Recursos humanos", "Orientação e counseling"],
    },
    "E": {
        "nome": "Empreendedor", "emoji": "🚀",
        "cor": "#f59e0b", "cor_bg": "rgba(245, 158, 11, 0.15)",
        "descricao_curta": "Líder, ambicioso e persuasivo",
        "descricao": "Você tem perfil Empreendedor! Nasceu pra liderar. É persuasivo, ambicioso e não tem medo de assumir riscos. Se realiza tomando decisões importantes, movimentando pessoas e projetos, e vendo resultados crescerem.",
        "pontos_fortes": ["Liderança natural", "Persuasão e negociação", "Visão estratégica", "Iniciativa e coragem"],
        "ambientes_ideais": ["Negócios e empreendedorismo", "Gestão e liderança", "Vendas e marketing", "Direito e política", "Startups e inovação"],
    },
    "C": {
        "nome": "Convencional", "emoji": "📋",
        "cor": "#6366f1", "cor_bg": "rgba(99, 102, 241, 0.15)",
        "descricao_curta": "Organizado, preciso e metódico",
        "descricao": "Você tem perfil Convencional! É a pessoa que dá ordem ao caos. Gosta de estrutura, precisão e de ter tudo no lugar certo. Se realiza em ambientes organizados, com regras claras, trabalhando com dados, registros e processos bem definidos.",
        "pontos_fortes": ["Organização e atenção aos detalhes", "Trabalho com dados e números", "Confiabilidade e precisão absoluta", "Criar sistemas eficientes"],
        "ambientes_ideais": ["Finanças e contabilidade", "Serviço público e burocracia", "Administração e gestão", "Auditoria e controle", "TI e banco de dados"],
    },
}


# ═════════════════════════════════════════════════════════════════════════════
# ALGORITMO v2 — MATCHING CIENTÍFICO APRIMORADO
# Baseado em: RIASEC ponderado + Big Five + Hexágono Holland + Valores fortes
# ═════════════════════════════════════════════════════════════════════════════

def calcular_scores(respostas):
    """
    Processa todas as respostas e retorna o perfil completo do usuário.
    Novidade v2: questões situacionais também alimentam o RIASEC.
    """
    scores_riasec = {"R": 0.0, "I": 0.0, "A": 0.0, "S": 0.0, "E": 0.0, "C": 0.0}
    contagens_riasec = {"R": 0.0, "I": 0.0, "A": 0.0, "S": 0.0, "E": 0.0, "C": 0.0}

    scores_personalidade = {"O": 0.0, "C_big5": 0.0, "E_big5": 0.0, "A_big5": 0.0, "N": 0.0}
    contagens_personalidade = {"O": 0.0, "C_big5": 0.0, "E_big5": 0.0, "A_big5": 0.0, "N": 0.0}

    valores_escolhidos = []

    # ── Bloco 1: RIASEC (interesses) ──
    for q in QUESTOES_RIASEC:
        qid = q["id"]
        if qid in respostas:
            val = int(respostas[qid])
            dim = q["dimensao"]
            scores_riasec[dim] += val
            contagens_riasec[dim] += 1

    # ── Bloco 2: Situacionais (contribui para RIASEC com peso 2x) ──
    for q in QUESTOES_SITUACIONAIS:
        qid = q["id"]
        if qid in respostas:
            resp = respostas[qid]
            # Achar a opção selecionada
            for opcao in q["opcoes"]:
                if opcao["valor"] == resp:
                    for dim, peso in opcao["dims"].items():
                        if peso > 0:
                            scores_riasec[dim] += peso * 2.5  # Situacionais têm mais peso
                            contagens_riasec[dim] += 2.0
                        else:
                            # Antipreferência: subtrai do score
                            scores_riasec[dim] = max(0, scores_riasec[dim] - abs(peso) * 1.5)
                    break

    # ── Bloco 3: Personalidade ──
    mapa_dim = {"O": "O", "C": "C_big5", "E": "E_big5", "A": "A_big5", "N": "N"}
    for q in QUESTOES_PERSONALIDADE:
        qid = q["id"]
        if qid in respostas:
            val = int(respostas[qid])
            if q.get("inverso"):
                val = 6 - val
            dim = mapa_dim[q["dimensao"]]
            scores_personalidade[dim] += val
            contagens_personalidade[dim] += 1

    # ── Bloco 4: Habilidades (contribui para RIASEC com peso ajustado) ──
    for q in QUESTOES_HABILIDADES:
        qid = q["id"]
        if qid in respostas:
            val = int(respostas[qid])
            dim = q["dimensao"]
            # Habilidades têm peso menor que interesses puros (0.8x)
            scores_riasec[dim] += val * 0.8
            contagens_riasec[dim] += 0.8

    # ── Bloco 5: Valores ──
    for q in QUESTOES_VALORES:
        qid = q["id"]
        if qid in respostas:
            escolha = respostas[qid]
            if escolha == 'a':
                valores_escolhidos.append(q["opcao_a"]["valor"])
            elif escolha == 'b':
                valores_escolhidos.append(q["opcao_b"]["valor"])

    # ── Bloco 6: Contexto ──
    contexto = {}
    for q in QUESTOES_CONTEXTO:
        qid = q["id"]
        if qid in respostas:
            contexto[qid] = respostas[qid]

    # ── Normalizar RIASEC (0.0 a 1.0) ──
    for dim in scores_riasec:
        if contagens_riasec[dim] > 0:
            max_possivel = contagens_riasec[dim] * 5
            scores_riasec[dim] = min(1.0, scores_riasec[dim] / max_possivel)

    # ── Normalizar Personalidade (0.0 a 1.0) ──
    for dim in scores_personalidade:
        if contagens_personalidade[dim] > 0:
            scores_personalidade[dim] = scores_personalidade[dim] / (contagens_personalidade[dim] * 5)

    return {
        "riasec": scores_riasec,
        "personalidade": scores_personalidade,
        "valores": valores_escolhidos,
        "contexto": contexto,
    }


def calcular_compatibilidade_v2(scores_usuario, carreira):
    """
    Algoritmo de matching v2 — muito mais preciso que v1.

    Melhorias:
    1. RIASEC ponderado: top dim 3x, 2ª dim 2x, demais 1x
    2. Big Five agora É usado (era ignorado em v1)
    3. Adjacência do hexágono Holland como bônus científico
    4. Penalidade de valores reforçada (1.0x, era 0.5x)
    5. Score "paixão × habilidade": bônus duplo quando interesse + habilidade coincidem
    6. Calibração final para usar range 0-100 mais distribuído
    """
    riasec_u = scores_usuario["riasec"]
    pers_u = scores_usuario["personalidade"]
    valores_u = scores_usuario["valores"]

    riasec_c = carreira.get("riasec", {})
    big5_c = carreira.get("big5", {})

    # ────────────────────────────────────────────────────────────
    # 1. SCORE RIASEC PONDERADO (peso 50%)
    # Peso dado ao top-3 do usuário aumenta discriminação
    # ────────────────────────────────────────────────────────────
    ranking_u = sorted(riasec_u.items(), key=lambda x: x[1], reverse=True)
    pesos_usuario = {}
    pesos_dim = {0: 3.0, 1: 2.0, 2: 1.5, 3: 1.0, 4: 0.7, 5: 0.5}
    for pos, (dim, val) in enumerate(ranking_u):
        pesos_usuario[dim] = pesos_dim.get(pos, 0.5)

    numerador = 0.0
    denominador_u = 0.0
    denominador_c = 0.0
    for dim in "RIASEC":
        pu = pesos_usuario.get(dim, 1.0)
        wu = riasec_u.get(dim, 0) * pu
        wc = riasec_c.get(dim, 0)
        numerador += wu * wc
        denominador_u += wu ** 2
        denominador_c += wc ** 2

    if denominador_u > 0 and denominador_c > 0:
        score_riasec = numerador / (math.sqrt(denominador_u) * math.sqrt(denominador_c))
    else:
        score_riasec = 0.0

    # ────────────────────────────────────────────────────────────
    # 2. BÔNUS HEXÁGONO DE HOLLAND (até +0.08 no score final)
    # Quando top-2 do usuário é adjacente ao top-2 da carreira
    # ────────────────────────────────────────────────────────────
    top2_usuario = {dim for dim, _ in ranking_u[:2]}
    ranking_c = sorted(riasec_c.items(), key=lambda x: x[1], reverse=True)
    top2_carreira = {dim for dim, _ in ranking_c[:2]}

    bonus_hexagono = 0.0
    for dim_u in top2_usuario:
        adjacentes_u = HEXAGONO_ADJACENCIAS.get(dim_u, set())
        for dim_c in top2_carreira:
            if dim_u == dim_c:
                bonus_hexagono += 0.03  # Coincidência exata
            elif dim_c in adjacentes_u:
                bonus_hexagono += 0.015  # Tipos adjacentes

    # Penalidade se o top do usuário é oposto ao top da carreira
    top1_u = ranking_u[0][0] if ranking_u else "I"
    top1_c = ranking_c[0][0] if ranking_c else "I"
    if HEXAGONO_OPOSTOS.get(top1_u) == top1_c:
        bonus_hexagono -= 0.04

    # ────────────────────────────────────────────────────────────
    # 3. SCORE BIG FIVE (peso 20%) — ERA IGNORADO EM V1
    # Compara perfil de personalidade do usuário com o ideal da carreira
    # ────────────────────────────────────────────────────────────
    mapa_big5 = {
        "O": "O", "C": "C_big5", "E": "E_big5", "A": "A_big5", "N": "N"
    }
    score_big5 = 0.0
    if big5_c:
        diffs = []
        for dim_c, ideal in big5_c.items():
            dim_u_key = mapa_big5.get(dim_c, dim_c)
            val_u = pers_u.get(dim_u_key, 0.5)
            # Diferença quadrática (menor é melhor)
            diff = (val_u - ideal) ** 2
            diffs.append(diff)
        if diffs:
            mse = sum(diffs) / len(diffs)
            # Converte MSE para score 0-1 (0 MSE = 1.0, MSE = 1.0 → score = 0)
            score_big5 = max(0, 1.0 - mse * 2.5)

    # ────────────────────────────────────────────────────────────
    # 4. SCORE DE VALORES (peso 20%) — PENALIDADE FORTALECIDA
    # v1 penalizava conflitos em 0.5x → agora é 1.0x
    # ────────────────────────────────────────────────────────────
    valores_altos_c = carreira.get("valores_altos", [])
    valores_baixos_c = carreira.get("valores_baixos", [])

    bonus_v = sum(1.0 for v in valores_u if v in valores_altos_c)
    penalidade_v = sum(1.0 for v in valores_u if v in valores_baixos_c)  # Era 0.5x!

    max_possivel_v = max(len(valores_altos_c), 1)
    score_valores = max(0.0, min(1.0, (bonus_v - penalidade_v) / max_possivel_v))

    # ────────────────────────────────────────────────────────────
    # 5. BÔNUS "PAIXÃO × HABILIDADE" (até +0.06) — NOVO EM V2
    # Quando o usuário é forte E gosta muito de dimensões críticas da carreira
    # Detecta alinhamento entre interesse (RIASEC de interesses) e aptidão (RIASEC de habilidades)
    # ────────────────────────────────────────────────────────────
    habilidades_chave_c = carreira.get("habilidades_chave", [])
    bonus_paixao_hab = 0.0
    for dim in habilidades_chave_c:
        val_interesse = riasec_u.get(dim, 0)
        if val_interesse >= 0.75:  # Alto interesse E
            bonus_paixao_hab += 0.02  # Alta habilidade deduzida (via RIASEC de habilidades)

    # ────────────────────────────────────────────────────────────
    # 6. COMPOSIÇÃO FINAL
    # RIASEC ponderado: 50%
    # Big Five: 20%
    # Valores: 20%
    # Hexágono: bônus até ±8%
    # Paixão×Habilidade: bônus até +6%
    # ────────────────────────────────────────────────────────────
    score_bruto = (
        score_riasec * 0.50
        + score_big5 * 0.20
        + score_valores * 0.20
        + bonus_hexagono
        + bonus_paixao_hab
    )

    # ── Calibração: esticar para melhor distribuição ──
    # Sem calibração, scores ficam entre 0.30-0.75. 
    # Isso mapa 0.2→20, 0.5→55, 0.8→90
    score_calibrado = (score_bruto - 0.20) / (0.85 - 0.20)
    score_percentual = round(min(97, max(15, score_calibrado * 100)))

    return score_percentual


def aplicar_filtros_contexto_v2(carreiras_rankeadas, scores_usuario):
    """
    Aplica bônus e penalidades de contexto com maior granularidade.
    v2: usa mais variáveis de contexto e bônus mais diferenciados.
    """
    contexto = scores_usuario.get("contexto", {})
    if not contexto:
        return carreiras_rankeadas

    duracao_pref = contexto.get("CT1", "medio")
    financeiro = contexto.get("CT2", "media")
    modo_trabalho = contexto.get("CT3", "equipe_dinamica")
    localizacao = contexto.get("CT4", "qualquer_cidade")
    situacao_estudos = contexto.get("CT5", "foco_total")
    tolerancia_risco = contexto.get("CT6", "risco_medio")
    aspecto_fisico = contexto.get("CT7", "misto")

    resultado = []
    for carreira, score in carreiras_rankeadas:
        bonus = 0.0
        anos = carreira.get("duracao_anos", 4)

        # ── Duração desejada ──
        match_duracao = {
            "curto": (anos <= 2, anos > 4, 10, -12),
            "medio": (3 <= anos <= 4, anos > 5, 6, -6),
            "longo": (5 <= anos <= 6, anos < 3, 5, -4),
            "muito_longo": (anos >= 7, anos < 4, 6, -3),
        }
        if duracao_pref in match_duracao:
            positivo, negativo, bon, pen = match_duracao[duracao_pref]
            if positivo: bonus += bon
            elif negativo: bonus += pen

        # ── Prioridade financeira ──
        sal_max = carreira.get("salario_max", 0)
        if financeiro == "alta":
            if sal_max >= 20000: bonus += 8
            elif sal_max >= 12000: bonus += 4
            elif sal_max < 7000: bonus -= 10
        elif financeiro == "baixa":
            if sal_max < 8000 and carreira.get("concurso_opcao", False): bonus += 3

        # ── Modo de trabalho ──
        if modo_trabalho == "concurso" and carreira.get("concurso_opcao", False):
            bonus += 12
        elif modo_trabalho == "autonomo" and carreira.get("remoto_opcao", False):
            bonus += 6
        elif modo_trabalho == "empresa_estruturada" and not carreira.get("concurso_opcao", False):
            bonus += 2

        # ── Localização ──
        if localizacao == "remoto" and carreira.get("remoto_opcao", False):
            bonus += 8
        elif localizacao == "interior_preferencia" and carreira.get("remoto_opcao", False):
            bonus += 4

        # ── Situação financeira ──
        if situacao_estudos in ["bolsa_necessaria", "trabalha_estuda"]:
            if anos > 5: bonus -= 6
            if anos <= 3: bonus += 4
        if situacao_estudos == "ead_opcao" and "ead" in carreira.get("modalidade", []):
            bonus += 6

        # ── Tolerância ao risco ──
        perspectiva = carreira.get("perspectiva_mercado", "Boa")
        if tolerancia_risco == "risco_baixo" and "variabilidade" in perspectiva.lower():
            bonus -= 8
        elif tolerancia_risco == "risco_alto" and "alto" in perspectiva.lower():
            bonus += 5
        elif tolerancia_risco == "risco_baixo" and carreira.get("concurso_opcao", False):
            bonus += 6

        # ── Aspecto físico ──
        if aspecto_fisico == "acao_campo" and not carreira.get("remoto_opcao", False):
            bonus += 4
        elif aspecto_fisico == "remoto_digital" and carreira.get("remoto_opcao", False):
            bonus += 6
        elif aspecto_fisico == "escritorio" and carreira.get("remoto_opcao", False):
            bonus += 2

        resultado.append((carreira, min(97, max(15, score + bonus))))

    return resultado


def gerar_resultado_completo(respostas):
    """
    Função principal: processa respostas e retorna resultado completo para o template.
    """
    scores = calcular_scores(respostas)
    riasec = scores["riasec"]

    # Ordenar dimensões para definir perfil
    ranking_riasec = sorted(riasec.items(), key=lambda x: x[1], reverse=True)
    perfil_primario = ranking_riasec[0][0] if ranking_riasec[0][1] > 0.08 else "I"
    perfil_secundario = ranking_riasec[1][0] if len(ranking_riasec) > 1 and ranking_riasec[1][1] > 0.08 else "S"

    # Calcular compatibilidade com todas as carreiras (algoritmo v2)
    carreiras_scores = []
    for carreira in CARREIRAS:
        score = calcular_compatibilidade_v2(scores, carreira)
        carreiras_scores.append((carreira, score))

    # Aplicar filtros de contexto v2
    carreiras_scores = aplicar_filtros_contexto_v2(carreiras_scores, scores)

    # Ordenar por score
    carreiras_scores.sort(key=lambda x: x[1], reverse=True)

    # Top 10 carreiras (mais que v1 que tinha 8)
    top_carreiras = []
    for c, s in carreiras_scores[:10]:
        top_carreiras.append({
            "carreira": c,
            "compatibilidade": s,
            "compatibilidade_label": (
                "Match perfeito 🎯" if s >= 85 else
                "Excelente match" if s >= 75 else
                "Ótima compatibilidade" if s >= 62 else
                "Boa compatibilidade" if s >= 48 else
                "Compatível"
            )
        })

    # Insights de personalidade para o resultado
    pers = scores["personalidade"]
    insights_personalidade = _gerar_insights_personalidade(pers)

    # Scores radar (0-100)
    radar_data = {k: round(v * 100) for k, v in riasec.items()}

    # Combinações especiais de perfil
    combo_label = _gerar_label_combo(perfil_primario, perfil_secundario)

    return {
        "perfil_primario": perfil_primario,
        "perfil_secundario": perfil_secundario,
        "perfil_primario_dados": PERFIS_RIASEC[perfil_primario],
        "perfil_secundario_dados": PERFIS_RIASEC[perfil_secundario],
        "combo_label": combo_label,
        "scores_riasec": riasec,
        "radar_data": radar_data,
        "ranking_riasec": ranking_riasec,
        "personalidade": pers,
        "insights_personalidade": insights_personalidade,
        "valores": scores["valores"],
        "top_carreiras": top_carreiras,
        "total_questoes_respondidas": len(respostas),
    }


def _gerar_insights_personalidade(pers):
    """Gera insights em linguagem natural sobre a personalidade do usuário."""
    insights = []
    O = pers.get("O", 0.5)
    C = pers.get("C_big5", 0.5)
    E = pers.get("E_big5", 0.5)
    A = pers.get("A_big5", 0.5)
    N = pers.get("N", 0.5)

    if O >= 0.75:
        insights.append({"icon": "🌍", "texto": "Você tem alta abertura a novas experiências — aprende rápido e se adapta bem a mudanças."})
    elif O <= 0.35:
        insights.append({"icon": "📌", "texto": "Você prefere ambientes previsíveis e estruturados — valoriza a tradição e a consistência."})

    if C >= 0.75:
        insights.append({"icon": "✅", "texto": "Alta conscienciosidade: você é organizado, confiável e termina o que começa."})
    elif C <= 0.35:
        insights.append({"icon": "🎲", "texto": "Você prefere espontaneidade a planejamento rígido — bom para ambientes ágeis e criativos."})

    if E >= 0.75:
        insights.append({"icon": "⚡", "texto": "Você é extrovertido e se energiza com pessoas — natural para liderança e trabalho colaborativo."})
    elif E <= 0.35:
        insights.append({"icon": "🧘", "texto": "Você é introvertido — prefere aprofundamento a contato constante, ideal para pesquisa e análise."})

    if A >= 0.75:
        insights.append({"icon": "❤️", "texto": "Alta amabilidade: você é empático e cooperativo — essencial para carreiras de cuidado e ensino."})

    if N >= 0.75:
        insights.append({"icon": "🛡️", "texto": "Você tem alta estabilidade emocional — lida bem com pressão, incerteza e situações difíceis."})
    elif N <= 0.35:
        insights.append({"icon": "⚠️", "texto": "Você tende a sentir mais intensamente as pressões — carreiras de baixo estresse podem ser mais satisfatórias."})

    return insights[:3]  # Máximo 3 insights


def _gerar_label_combo(p1, p2):
    """Gera um label especial para combinações RIASEC conhecidas."""
    combos = {
        ("I", "R"): "O Engenheiro / Técnico-Científico",
        ("R", "I"): "O Engenheiro / Técnico-Científico",
        ("I", "A"): "O Pesquisador Criativo",
        ("A", "I"): "O Pesquisador Criativo",
        ("A", "S"): "O Educador-Artista",
        ("S", "A"): "O Educador-Artista",
        ("S", "E"): "O Líder Humanista",
        ("E", "S"): "O Líder Humanista",
        ("E", "C"): "O Gestor Estratégico",
        ("C", "E"): "O Gestor Estratégico",
        ("C", "R"): "O Técnico Organizado",
        ("R", "C"): "O Técnico Organizado",
        ("I", "C"): "O Analista de Sistemas",
        ("C", "I"): "O Analista de Sistemas",
        ("A", "E"): "O Empreendedor Criativo",
        ("E", "A"): "O Empreendedor Criativo",
        ("S", "I"): "O Cientista Social",
        ("I", "S"): "O Cientista Social",
        ("E", "I"): "O Estrategista Analítico",
        ("I", "E"): "O Estrategista Analítico",
        ("R", "S"): "O Profissional de Campo Humanitário",
        ("S", "R"): "O Profissional de Campo Humanitário",
    }
    return combos.get((p1, p2), f"Perfil {p1}-{p2}")
