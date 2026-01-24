# app/services/redacao_service.py

import os
import json
import time
import logging
import requests
from typing import Any, Dict, List, Tuple

from flask import current_app
from app import db
from app.models.redacao import Redacao

# Logger básico (integra com gunicorn/systemd; safe para produção)
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s'))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


class RedacaoService:
    """
    Serviço para avaliação de redações (ENEM) via OpenAI, com fallback opcional.
    Env suportadas:
      - OPENAI_API_KEY        -> chave de API
      - OPENAI_MODEL          -> ex: "gpt-4o-mini" (default)
      - FORCE_OPENAI=1        -> nunca usa simulado, retorna erro explícito p/ depuração
      - FALLBACK_SIMULADO=1   -> permite usar simulado em erro de chamada
    """

    # ---------------------------
    # API pública
    # ---------------------------
    @staticmethod
    def avaliar_redacao(redacao_id: int) -> Dict[str, Any]:
        """
        Fluxo de avaliação: monta prompt, chama OpenAI, processa JSON, persiste notas.
        Nunca "mascara" erro silenciosamente: erro fica visível (ou simulado se habilitado).
        """
        logger.info(f"[RedacaoService] Avaliar redação id={redacao_id}")
        redacao = Redacao.query.get(redacao_id)
        if not redacao:
            logger.error("Redação não encontrada")
            return {"sucesso": False, "erro": "Redação não encontrada"}

        try:
            # Marca "Em análise"
            redacao.status = "Em análise"
            db.session.commit()

            api_key = RedacaoService._get_api_key()
            if not api_key:
                # Não simular: erro aberto para corrigirmos configuração
                msg = "Chave da API OpenAI ausente"
                logger.error(msg)
                redacao.status = "Erro"
                redacao.resposta_api = json.dumps({"error": msg})
                db.session.commit()
                return {"sucesso": False, "erro": msg}

            prompt = RedacaoService._construir_prompt(redacao)
            redacao.prompt_usado = prompt

            t0 = time.time()
            resultado = RedacaoService._chamar_api_chatgpt(prompt, api_key)
            logger.info(f"[RedacaoService] chamada OpenAI levou {time.time()-t0:.2f}s")

            # Se a função retornou {"error": "..."} nós NÃO mascaramos
            if isinstance(resultado, dict) and "error" in resultado:
                redacao.status = "Erro"
                redacao.resposta_api = json.dumps(resultado)
                db.session.commit()
                logger.error(f"[RedacaoService] Erro da API: {resultado['error']}")
                return {"sucesso": False, "erro": resultado["error"]}

            # Persistimos a resposta crua para auditoria
            redacao.resposta_api = json.dumps(resultado)

            # Processa e persiste notas/competências
            res = RedacaoService._processar_resposta_api(resultado, redacao)

            redacao.status = "Avaliada"
            db.session.commit()
            logger.info("[RedacaoService] Avaliação concluída")

            return res

        except Exception as e:
            logger.exception("[RedacaoService] Exceção inesperada")
            redacao.status = "Erro"
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            return {"sucesso": False, "erro": str(e)}

    # ---------------------------
    # Helpers de Config
    # ---------------------------
    @staticmethod
    def _get_api_key() -> str:
        """
        Busca API key em: Flask config -> env -> (dotenv já deve ter sido carregado no boot).
        """
        # 1) Flask config
        try:
            if current_app:
                k = current_app.config.get("OPENAI_API_KEY")
                if k:
                    return k
        except RuntimeError:
            # sem contexto de app; seguimos
            pass

        # 2) Ambiente
        k = os.environ.get("OPENAI_API_KEY", "")
        return k.strip()

    # ---------------------------
    # Prompt
    # ---------------------------
    @staticmethod
    def _construir_prompt(redacao: Redacao) -> str:
        tema = redacao.tema or "Tema livre"
        return f"""Você é um avaliador experiente de redações do ENEM com mais de 10 anos de experiência. Sua avaliação deve ser RIGOROSA e seguir EXATAMENTE os critérios oficiais do ENEM. Seja CRITERIOSO - a maioria das redações NÃO merece notas altas.

IMPORTANTE: Sua resposta deve ser APENAS o JSON, sem texto adicional.

CRITÉRIOS DE AVALIAÇÃO POR COMPETÊNCIA:

=== COMPETÊNCIA 1: Domínio da modalidade escrita formal da língua portuguesa (0-200) ===
- 200-160: Pouquíssimos desvios. Domínio excelente da norma culta.
- 140-120: Alguns desvios que não comprometem a compreensão.
- 100-80: Desvios que começam a comprometer a compreensão.
- 60-40: Muitos desvios. Compreensão prejudicada.
- 20-0: Desvios graves e constantes. Foge da modalidade escrita formal.

PENALIZE SEVERAMENTE:
- Erros de concordância verbal/nominal, regência, acentuação, ortografia, pontuação
- Informalidades, gírias e coloquialidades

=== COMPETÊNCIA 2: Compreender a proposta e aplicar repertório sociocultural (0-200) ===
- 200-160: Desenvolvimento excelente do tema; repertório produtivo e legitimado.
- 140-120: Desenvolvimento adequado; repertório válido.
- 100-80: Desenvolvimento superficial.
- 60-40: Desenvolvimento insuficiente.
- 20-0: Fuga ao tema.

=== COMPETÊNCIA 3: Selecionar, relacionar, organizar e interpretar (0-200) ===
- 200-160: Projeto de texto excelente; ótima organização.
- 140-120: Organização adequada.
- 100-80: Organização razoável.
- 60-40: Organização insuficiente.
- 20-0: Desorganização.

=== COMPETÊNCIA 4: Mecanismos linguísticos para argumentação (0-200) ===
- 200-160: Conectivos variados e adequados; coesão excelente.
- 140-120: Coesão adequada.
- 100-80: Coesão mediana.
- 60-40: Coesão insuficiente.
- 20-0: Falhas graves.

=== COMPETÊNCIA 5: Proposta de intervenção (0-200) ===
Exigir AGENTE, AÇÃO, MODO, FINALIDADE, DETALHAMENTO e respeito aos direitos humanos.

Formato JSON obrigatório:
{{
  "competencias": [
    {{"numero":1,"nome":"Domínio da norma culta da Língua Portuguesa","nota":<0-200>,"justificativa":"...","pontos_fortes":["..."],"pontos_fracos":["..."],"sugestoes":["..."]}},
    {{"numero":2,"nome":"Compreensão e desenvolvimento do tema","nota":<0-200>,"justificativa":"...","pontos_fortes":["..."],"pontos_fracos":["..."],"sugestoes":["..."]}},
    {{"numero":3,"nome":"Organização textual e coerência","nota":<0-200>,"justificativa":"...","pontos_fortes":["..."],"pontos_fracos":["..."],"sugestoes":["..."]}},
    {{"numero":4,"nome":"Mecanismos linguísticos para argumentação","nota":<0-200>,"justificativa":"...","pontos_fortes":["..."],"pontos_fracos":["..."],"sugestoes":["..."]}},
    {{"numero":5,"nome":"Proposta de intervenção","nota":<0-200>,"justificativa":"...","pontos_fortes":["..."],"pontos_fracos":["..."],"sugestoes":["..."]}}
  ],
  "nota_total": <soma-das-notas>,
  "parecer_geral": "..."
}}



Tema: {tema}

Redação:
{redacao.conteudo}

Retorne APENAS o JSON, sem texto adicional."""

    # ---------------------------
    # Chamada OpenAI (com flags)
    # ---------------------------
    @staticmethod
    def _chamar_api_chatgpt(prompt: str, api_key: str) -> Dict[str, Any]:
        """
        Chamada HTTP p/ OpenAI. Se erro:
         - com FORCE_OPENAI=1 -> retorna {"error": "..."} (nada de simulado)
         - com FALLBACK_SIMULADO=1 -> usa simulado
         - default -> retorna {"error": "..."} (para corrigirmos)
        """
        force_openai = os.environ.get("FORCE_OPENAI", "0") == "1"
        allow_sim = os.environ.get("FALLBACK_SIMULADO", "0") == "1"

        if not api_key or len(api_key) < 40:
            msg = "Chave da API inválida/curta"
            logger.error(msg)
            if allow_sim and not force_openai:
                logger.warning("Usando simulado (FALLBACK_SIMULADO=1)")
                return RedacaoService._resposta_simulada()
            return RedacaoService._erro_aberto(msg)

        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"[RedacaoService] Chamando OpenAI model={model}")

        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 3000,
                },
                timeout=60,
            )
            logger.info(f"[RedacaoService] OpenAI status={resp.status_code}")

            if resp.status_code != 200:
                # Mostra corpo para sabermos a CAUSA (model_not_found, quota, etc.)
                logger.error(f"[RedacaoService] OpenAI body: {resp.text}")
                if allow_sim and not force_openai:
                    logger.warning("Usando simulado (FALLBACK_SIMULADO=1)")
                    return RedacaoService._resposta_simulada()
                return RedacaoService._erro_aberto(f"OpenAI error {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Esperamos JSON "puro" no content
            try:
                parsed = json.loads(content)
                return parsed
            except Exception:
                logger.error("[RedacaoService] Resposta não-JSON; devolvendo erro aberto para depurar")
                return RedacaoService._erro_aberto(f"Resposta não-JSON da OpenAI: {content[:500]}")

        except requests.Timeout:
            msg = "Timeout na chamada OpenAI"
            logger.error(msg)
            if allow_sim and not force_openai:
                return RedacaoService._resposta_simulada()
            return RedacaoService._erro_aberto(msg)

        except requests.RequestException as e:
            msg = f"Erro de rede/OpenAI: {str(e)}"
            logger.error(msg)
            if allow_sim and not force_openai:
                return RedacaoService._resposta_simulada()
            return RedacaoService._erro_aberto(msg)

    # ---------------------------
    # Normalização / Persistência - FUNÇÃO CORRIGIDA
    # ---------------------------
    @staticmethod
    def _processar_resposta_api(payload: Dict[str, Any], redacao: Redacao) -> Dict[str, Any]:
        """
        Espera payload no formato:
        {
          "competencias": [{"numero":1,"nota":...,"justificativa":"...","pontos_fortes":[...],"pontos_fracos":[...],"sugestoes":[...]} * 5],
          "nota_total": 0-1000,
          "parecer_geral": "..."
        }
        Atualiza campos da Redacao e retorna struct com sucesso.
        """
        def _nota(c: Dict[str, Any]) -> int:
            try:
                n = int(c.get("nota", 0))
            except Exception:
                n = 0
            return max(0, min(200, n))

        comps: List[Dict[str, Any]] = payload.get("competencias", []) or []
        if len(comps) != 5:
            raise ValueError("Resposta da API não contém 5 competências")

        # Salvar notas das competências
        c1 = _nota(comps[0]); c2 = _nota(comps[1]); c3 = _nota(comps[2]); c4 = _nota(comps[3]); c5 = _nota(comps[4])
        nota_total = int(payload.get("nota_total", c1 + c2 + c3 + c4 + c5))

        redacao.competencia1 = c1
        redacao.competencia2 = c2
        redacao.competencia3 = c3
        redacao.competencia4 = c4
        redacao.competencia5 = c5
        redacao.nota_final = nota_total
        redacao.parecer_geral = payload.get("parecer_geral")

        # 🔥 CORREÇÃO: Processar feedbacks detalhados de cada competência
        for comp in comps:
            numero = comp.get("numero")
            if numero < 1 or numero > 5:
                logger.warning(f"Número de competência inválido: {numero}")
                continue
            
            # Salvar justificativa (feedback principal)
            justificativa = comp.get("justificativa", "")
            setattr(redacao, f"feedback_comp{numero}", justificativa)
            
            # Salvar pontos fortes, fracos e sugestões como JSON
            pontos_fortes = comp.get("pontos_fortes", [])
            pontos_fracos = comp.get("pontos_fracos", [])
            sugestoes = comp.get("sugestoes", [])
            
            setattr(redacao, f"pontos_fortes_comp{numero}", json.dumps(pontos_fortes, ensure_ascii=False))
            setattr(redacao, f"pontos_fracos_comp{numero}", json.dumps(pontos_fracos, ensure_ascii=False))
            setattr(redacao, f"sugestoes_comp{numero}", json.dumps(sugestoes, ensure_ascii=False))
            
            logger.info(f"Competência {numero} processada: nota {comp.get('nota')}, feedback salvo")

        # Commit acontece no chamador (avaliar_redacao)
        return {
            "sucesso": True,
            "nota_final": nota_total,
            "competencias": [c1, c2, c3, c4, c5],
            "raw": payload,
        }

    # ---------------------------
    # Fallback / Erro aberto
    # ---------------------------
    @staticmethod
    def _resposta_simulada() -> Dict[str, Any]:
        """
        Simulação conservadora — útil apenas para demo.
        Só é usada quando FALLBACK_SIMULADO=1 e FORCE_OPENAI!=1.
        """
        base = [
            {"numero": 1, "nota": 120, "justificativa": "Problemas de ortografia e pontuação.", "pontos_fortes": [], "pontos_fracos": ["concordância", "acentuação"], "sugestoes": ["revisar gramática"]},
            {"numero": 2, "nota": 120, "justificativa": "Desenvolvimento superficial do tema.", "pontos_fortes": [], "pontos_fracos": ["repertório raso"], "sugestoes": ["incluir repertório legitimado"]},
            {"numero": 3, "nota": 120, "justificativa": "Estrutura básica, mas com progressão fraca.", "pontos_fortes": [], "pontos_fracos": ["coesão", "contradições"], "sugestoes": ["melhorar organização textual"]},
            {"numero": 4, "nota": 120, "justificativa": "Conectivos repetitivos, coesão limitada.", "pontos_fortes": [], "pontos_fracos": ["conectivos"], "sugestoes": ["variar conectores"]},
            {"numero": 5, "nota": 120, "justificativa": "Proposta incompleta e genérica.", "pontos_fortes": [], "pontos_fracos": ["detalhamento"], "sugestoes": ["agente, ação, modo, finalidade"]},
        ]
        total = sum(int(c["nota"]) for c in base)
        return {"competencias": base, "nota_total": total, "parecer_geral": "Texto mediano com diversos pontos a melhorar."}

    @staticmethod
    def _erro_aberto(msg: str) -> Dict[str, Any]:
        return {"error": msg}
