import os
import openai
import json
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (se estiver usando)
load_dotenv()

# Configure logging (opcional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pega a chave do ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Seta a chave na lib
openai.api_key = OPENAI_API_KEY

def evaluate_essay(essay_text):
    """
    Avalia a redação usando a API GPT-4, retornando um dicionário com feedback em JSON.
    """
    try:
        logger.info("Iniciando avaliação da redação...")

        prompt = f"""Você atuará como um avaliador especialista nas redações do ENEM. 
        Avalie a redação abaixo seguindo ESTRITAMENTE o formato JSON especificado.

        IMPORTANTE: Sua resposta deve ser APENAS o JSON, sem texto adicional.

        Para cada competência, atribua uma nota de 0 a 200 pontos e forneça justificativas detalhadas.

	Evite nomes candidato, corrija como se vc estivesse falando com a segunda pessa do discurso, então pode usar o 'você' 
        Formato JSON obrigatório:
        {{
            "competencias": [
                {{
                    "numero": 1,
                    "nome": "Domínio da norma culta da Língua Portuguesa",
                    "nota": <0-200>,
                    "justificativa": "<texto>",
                    "pontos_fortes": ["<ponto1>", "<ponto2>"],
                    "pontos_fracos": ["<ponto1>", "<ponto2>"],
                    "sugestoes": ["<sugestao1>", "<sugestao2>"]
                }},
                {{
                    "numero": 2,
                    "nome": "Compreensão e desenvolvimento do tema proposto",
                    "nota": <0-200>,
                    "justificativa": "<texto>",
                    "pontos_fortes": ["<ponto1>", "<ponto2>"],
                    "pontos_fracos": ["<ponto1>", "<ponto2>"],
                    "sugestoes": ["<sugestao1>", "<sugestao2>"]
                }},
                {{
                    "numero": 3,
                    "nome": "Organização textual e coerência",
                    "nota": <0-200>,
                    "justificativa": "<texto>",
                    "pontos_fortes": ["<ponto1>", "<ponto2>"],
                    "pontos_fracos": ["<ponto1>", "<ponto2>"],
                    "sugestoes": ["<sugestao1>", "<sugestao2>"]
                }},
                {{
                    "numero": 4,
                    "nome": "Conhecimento dos mecanismos linguísticos necessários para argumentação",
                    "nota": <0-200>,
                    "justificativa": "<texto>",
                    "pontos_fortes": ["<ponto1>", "<ponto2>"],
                    "pontos_fracos": ["<ponto1>", "<ponto2>"],
                    "sugestoes": ["<sugestao1>", "<sugestao2>"]
                }},
                {{
                    "numero": 5,
                    "nome": "Elaboração de proposta de intervenção adequada ao problema abordado",
                    "nota": <0-200>,
                    "justificativa": "<texto>",
                    "pontos_fortes": ["<ponto1>", "<ponto2>"],
                    "pontos_fracos": ["<ponto1>", "<ponto2>"],
                    "sugestoes": ["<sugestao1>", "<sugestao2>"]
                }}
            ],
            "nota_total": <soma-das-notas>,
            "parecer_geral": "<texto>"
        }}

        Redação a ser avaliada:
        {essay_text}

        Lembre-se: Retorne APENAS o JSON, sem nenhum texto adicional antes ou depois.
        """

        logger.info("Enviando requisição para a API...")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um avaliador especialista em redações do ENEM. "
                        "Responda apenas com o JSON solicitado, sem texto adicional."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        logger.info("Resposta recebida, processando resultado...")
        result_text = response["choices"][0]["message"]["content"]

        # Tenta decodificar como JSON
        result = json.loads(result_text)

        # Valida a estrutura mínima
        if "competencias" not in result or "nota_total" not in result:
            raise ValueError("Resposta da API não está no formato esperado.")

        logger.info("Avaliação concluída com sucesso.")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise Exception("Erro ao processar a resposta da avaliação. Resposta não é um JSON válido.")
    except Exception as e:
        logger.error(f"Erro na avaliação da redação: {str(e)}")
        raise Exception(f"Erro na avaliação da redação: {str(e)}")
