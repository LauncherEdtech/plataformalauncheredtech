
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from models import db, User, Essay, CompetenceFeedback
from config import Config
from auth import auth_bp
from essay_evaluator import evaluate_essay
from visualization import radar_chart
import plotly
import json
import hmac
import hashlib
from sqlalchemy.orm import scoped_session
import os



from sheets import update_user_credits_in_sheet  # adicione no topo do arquivo


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp, url_prefix='/auth')

    

    @app.route('/')
    def index():
        return render_template('LandingPage.html')

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('auth_bp.login'))

        user = db.session.get(User, session['user_id'])
        essays = Essay.query.filter_by(user_id=user.id).all()

        if essays:
            total_scores = [e.score_total for e in essays if e.score_total is not None]
            if total_scores:
                avg_score = sum(total_scores) / len(total_scores)
                best_score = max(total_scores)
            else:
                avg_score = 0
                best_score = 0
        else:
            avg_score = 0
            best_score = 0

        return render_template('dashboard.html', user=user, essays=essays,
                               avg_score=avg_score, best_score=best_score)

    @app.route('/submit_essay', methods=['GET', 'POST'])
    def submit_essay():
        if 'user_id' not in session:
            return redirect(url_for('auth_bp.login'))
        
        user = User.query.get(session['user_id'])
        
        if request.method == 'POST':
            if user.credits <= 0:
                flash('Você não possui créditos suficientes.')
                return redirect(url_for('dashboard'))
            
            title = request.form.get('title')
            text = request.form.get('text')
            
            # Avalia o texto com GPT-4
            feedback_data = evaluate_essay(text)

            # Cria a redação no banco de dados
            essay = Essay(
                user_id=user.id,
                title=title,
                text=text,
                feedback=feedback_data,
                score_total=feedback_data["nota_total"],
                comp1_score=feedback_data["competencias"][0]["nota"],
                comp2_score=feedback_data["competencias"][1]["nota"],
                comp3_score=feedback_data["competencias"][2]["nota"],
                comp4_score=feedback_data["competencias"][3]["nota"],
                comp5_score=feedback_data["competencias"][4]["nota"],
            )
            db.session.add(essay)
            db.session.commit()

            # Cria os feedbacks por competência
            for c in feedback_data["competencias"]:
                feedback = CompetenceFeedback(
                    essay_id=essay.id,
                    numero=c["numero"],
                    nome=c["nome"],
                    nota=c["nota"],
                    justificativa=c.get("justificativa", ""),
                    pontos_fortes=c.get("pontos_fortes", ""),
                    pontos_fracos=c.get("pontos_fracos", ""),
                    sugestoes=c.get("sugestoes", "")
                )
                db.session.add(feedback)

            db.session.commit()

            # Decrementa o crédito
            user.credits -= 1
            db.session.commit()

	   #  Atualiza os créditos no Google Sheet
            update_user_credits_in_sheet(user)

            return redirect(url_for('feedback_page', essay_id=essay.id))
        
        return render_template('submit_essay.html', user=user)



    @app.route('/webhook', methods=['POST'])
    def receive_webhook():
        secret = app.config.get('KIWIFY_WEBHOOK_SECRET')
        signature = request.args.get('signature')
        payload_raw = request.get_data()

        print("=== DEBUG WEBHOOK ===")
        print("Segredo carregado:", secret)
        print("Payload bruto:", payload_raw.decode())

        if not secret:
            print("Erro: segredo ausente.")
            return jsonify({"status": "erro", "mensagem": "Segredo ausente"}), 403

        if app.config.get("FLASK_ENV") != "development":
            if not signature:
                print("Erro: assinatura ausente.")
                return jsonify({"status": "erro", "mensagem": "Assinatura ausente"}), 403

            expected_signature = hmac.new(
                secret.encode(),
                msg=payload_raw,
                digestmod=hashlib.sha1
            ).hexdigest()

            print("Assinatura esperada:", expected_signature)

            if not hmac.compare_digest(signature, expected_signature):
                print("Erro: assinatura inválida.")
                return jsonify({"status": "erro", "mensagem": "Assinatura inválida"}), 403

        try:
            payload = json.loads(payload_raw)
            print("Payload recebido:", payload)

            if payload.get("order_status") != "paid":
                print("Pagamento não aprovado. Ignorando webhook.")
                return jsonify({"status": "ignorado", "mensagem": "Pagamento não aprovado"}), 200

            email = payload.get("Customer", {}).get("email")
            if not email:
                print("Erro: email não encontrado no payload.")
                return jsonify({"status": "erro", "mensagem": "Email não encontrado no payload"}), 400

            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Erro: usuário com email {email} não encontrado.")
                return jsonify({"status": "erro", "mensagem": f"Usuário com email {email} não encontrado"}), 404

            user.credits += 10
            db.session.commit()

            print(f"Créditos adicionados para {email}")
            return jsonify({"status": "sucesso", "mensagem": f"Créditos adicionados para {email}"}), 200

        except Exception as e:
            print("Erro ao processar webhook:", str(e))
            return jsonify({"status": "erro", "mensagem": str(e)}), 500

    # Trecho do app.py que precisa ser modificado para corrigir o problema dos feedbacks

    @app.route('/feedback/<int:essay_id>')
    def feedback_page(essay_id):
            if 'user_id' not in session:
                return redirect(url_for('auth_bp.login'))

            user = db.session.get(User, session['user_id'])  # Adicione esta linha para obter o usuário
            essay = db.session.get(Essay, essay_id)
            if essay.user_id != session['user_id']:
                return redirect(url_for('dashboard'))

            competence_feedbacks = CompetenceFeedback.query.filter_by(essay_id=essay.id).order_by(CompetenceFeedback.numero).all()
            comp_scores = [cf.nota for cf in competence_feedbacks]
            
            # Limpeza das strings para remover chaves, aspas e substituir vírgulas por pipes
            for cf in competence_feedbacks:
                # Remove as chaves, aspas e outros caracteres indesejados
                if cf.pontos_fortes:
                    cf.pontos_fortes = cf.pontos_fortes.replace('{', '').replace('}', '').replace('"', '')
                    # Substitui vírgulas por pipes para melhor separação no template
                    cf.pontos_fortes = cf.pontos_fortes.replace(',', '|')
                
                if cf.pontos_fracos:
                    cf.pontos_fracos = cf.pontos_fracos.replace('{', '').replace('}', '').replace('"', '')
                    cf.pontos_fracos = cf.pontos_fracos.replace(',', '|')
                
                if cf.sugestoes:
                    cf.sugestoes = cf.sugestoes.replace('{', '').replace('}', '').replace('"', '')
                    cf.sugestoes = cf.sugestoes.replace(',', '|')

            radar_fig = radar_chart(comp_scores)
            radar_div = plotly.offline.plot(radar_fig, include_plotlyjs=False, output_type='div')

            return render_template('feedback.html', essay=essay, competence_feedbacks=competence_feedbacks, radar_div=radar_div, user=user)  # Adicione user=user aqui
    return app
if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
