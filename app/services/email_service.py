# app/services/email_service.py
"""
Serviço de envio de emails para a plataforma Launcher
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Serviço para envio de emails via SMTP"""

    # ====================================================
    # 🧩 FUNÇÃO CENTRAL DE ENVIO
    # ====================================================
    @staticmethod
    def _enviar_email(destinatario, assunto, corpo_html):
        """Função interna para enviar e-mails usando SMTP"""
        try:
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            remetente = current_app.config.get('MAIL_DEFAULT_SENDER', 'launcher.contato@gmail.com')

            if not all([smtp_server, smtp_user, smtp_password]):
                logger.error("⚠️ Configurações SMTP incompletas. Verifique .env")
                return False, "Configurações de email ausentes"

            mensagem = MIMEMultipart("alternative")
            mensagem["Subject"] = assunto
            mensagem["From"] = remetente
            mensagem["To"] = destinatario
            mensagem.attach(MIMEText(corpo_html, "html", "utf-8"))

            with smtplib.SMTP(smtp_server, smtp_port) as servidor:
                servidor.starttls()
                servidor.login(smtp_user, smtp_password)
                servidor.send_message(mensagem)

            logger.info(f"📧 Email enviado com sucesso para: {destinatario} | Assunto: {assunto}")
            return True, "Enviado com sucesso"

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Falha na autenticação SMTP — verifique usuário e senha.")
            return False, "Erro de autenticação SMTP"
        except smtplib.SMTPException as e:
            logger.error(f"❌ Erro SMTP: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar e-mail: {e}")
            return False, str(e)


    # ====================================================
    # 🎁 TAXA DE RESGATE
    # ====================================================
    @staticmethod
    def enviar_email_taxa_resgate(destinatario, nome):
        """Envia email confirmando pagamento da taxa de resgate"""
        assunto = "🎁 Taxa de Resgate Confirmada - Launcher"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; background:#f9f9f9;">
            <div style="background: linear-gradient(135deg, #00205B 0%, #0055D4 100%);
                        padding:30px; text-align:center; color:white; border-radius:8px 8px 0 0;">
                <h1 style="margin:0;">🎉 Taxa de Resgate Confirmada!</h1>
            </div>

            <div style="background:white; padding:30px; border-radius:0 0 8px 8px;">
                <p>Olá, <strong>{nome}</strong>!</p>
                <p>Recebemos o pagamento da sua taxa de resgate. Agora você já pode resgatar seu prêmio da roleta! 🎊</p>

                <div style="background:#f0f8ff; border-left:5px solid #0055D4; padding:15px; margin:20px 0;">
                    <h3>Próximos passos:</h3>
                    <ol>
                        <li>Acesse a plataforma</li>
                        <li>Vá até <strong>"Roleta"</strong> no menu</li>
                        <li>Clique em <strong>"Resgatar Prêmio"</strong></li>
                        <li>Preencha seus dados de entrega</li>
                    </ol>
                </div>

                <p>Em breve entraremos em contato para confirmar o envio do seu prêmio.</p>
                <p>Abraços,<br><strong>Equipe Launcher 🚀</strong></p>
            </div>
        </body>
        </html>
        """
        return EmailService._enviar_email(destinatario, assunto, corpo_html)


    # ====================================================
    # 🚀 PLANO ATIVADO
    # ====================================================
    @staticmethod
    def enviar_email_plano_ativado(destinatario, nome, tipo_plano, dias):
        """Envia email confirmando ativação do plano"""
        assunto = f"🚀 Plano {tipo_plano.capitalize()} Ativado - Launcher"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; background:#f9f9f9;">
            <div style="background: linear-gradient(135deg, #00205B 0%, #0055D4 100%);
                        padding:30px; text-align:center; color:white; border-radius:8px 8px 0 0;">
                <h1 style="margin:0;">🚀 Seu Plano {tipo_plano.capitalize()} foi Ativado!</h1>
            </div>

            <div style="background:white; padding:30px; border-radius:0 0 8px 8px;">
                <p>Olá, <strong>{nome}</strong>!</p>
                <p>O seu <strong>Plano {tipo_plano}</strong> foi ativado com sucesso! 🎉</p>

                <div style="background:#f0f8ff; border-left:5px solid #0055D4; padding:15px; margin:20px 0;">
                    <h3>Agora você tem acesso a:</h3>
                    <ul>
                        <li>✅ Redações ilimitadas com correção por IA</li>
                        <li>✅ Simulados completos estilo ENEM</li>
                        <li>✅ Aulas ilimitadas em vídeo</li>
                        <li>✅ PDFs e plano de estudos</li>
                        <li>✅ Rankings + Loja de prêmios</li>
                    </ul>
                    <p><strong>Válido por {dias} dias</strong></p>
                </div>

                <div style="text-align:center; margin:30px 0;">
                    <a href="https://plataformalauncher.com.br/login"
                       style="background:#0055D4; color:white; padding:15px 40px; text-decoration:none;
                              border-radius:8px; display:inline-block;">
                        Acessar Plataforma
                    </a>
                </div>

                <p>Bons estudos e sucesso na sua jornada rumo à aprovação!</p>
                <p>Abraços,<br><strong>Equipe Launcher 💙</strong></p>
            </div>
        </body>
        </html>
        """
        return EmailService._enviar_email(destinatario, assunto, corpo_html)


    # ====================================================
    # ✉️ BOAS-VINDAS (mantida do seu código original)
    # ====================================================
    @staticmethod
    def enviar_email_boas_vindas(email_destino, nome_completo, cpf):
        """Envia email de boas-vindas com credenciais de acesso"""
        try:
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            remetente = current_app.config.get('MAIL_DEFAULT_SENDER', 'launcher.contato@gmail.com')

            if not all([smtp_server, smtp_user, smtp_password]):
                logger.error("⚠️ Configurações SMTP incompletas no .env")
                return False, "Configurações de email não encontradas"

            senha_inicial = ''.join(filter(str.isdigit, cpf)) if cpf and len(cpf) == 11 else "launcher123"
            primeiro_nome = nome_completo.split()[0] if nome_completo else "Aluno"

            assunto = "🎓 Bem-vindo à Plataforma Launcher"
            corpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; background:#f9f9f9;">
                <div style="background: linear-gradient(135deg, #00205B 0%, #0055D4 100%);
                            padding:30px; text-align:center; color:white; border-radius:8px 8px 0 0;">
                    <h1>Bem-vindo(a), {primeiro_nome}! 🚀</h1>
                </div>

                <div style="background:white; padding:30px; border-radius:0 0 8px 8px;">
                    <p>Olá, <strong>{primeiro_nome}</strong>!</p>
                    <p>Seu cadastro foi criado com sucesso na Plataforma Launcher.</p>
                    <p><strong>Seus dados de acesso:</strong></p>
                    <p>Email: <code>{email_destino}</code><br>Senha provisória: <code>{senha_inicial}</code></p>
                    <p>Acesse: <a href="https://plataformalauncher.com.br/login">plataformalauncher.com.br/login</a></p>
                    <p>Recomendamos alterar sua senha no primeiro login.</p>
                    <p>Suporte: <a href="mailto:launcher.contato@gmail.com">launcher.contato@gmail.com</a></p>
                    <p>Abraços,<br><strong>Equipe Launcher 💙</strong></p>
                </div>
            </body>
            </html>
            """

            return EmailService._enviar_email(email_destino, assunto, corpo_html)

        except Exception as e:
            logger.error(f"❌ Erro ao enviar e-mail de boas-vindas: {e}")
            return False, str(e)



    @staticmethod
    def enviar_email_reset_senha(destinatario, nome, token):
        """Envia email com link para redefinir senha"""
        assunto = "🔐 Redefinir Senha - Plataforma Launcher"

        # Link com token (30 minutos de validade)
        link_reset = f"https://plataformalauncher.com.br/reset-senha/{token}"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; background:#f9f9f9;">
            <div style="background: linear-gradient(135deg, #00205B 0%, #0055D4 100%);
                        padding:30px; text-align:center; color:white; border-radius:8px 8px 0 0;">
                <h1 style="margin:0; font-size:24px;">🔐 Redefinir Senha</h1>
            </div>

            <div style="background:white; padding:30px; border-radius:0 0 8px 8px;">
                <p style="font-size:16px;">Olá, <strong>{nome}</strong>!</p>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta na Plataforma Launcher.</p>

                <div style="background:#fff3e0; border-left:5px solid #f57f17; padding:15px; margin:20px 0;">
                    <p style="margin:0;"><strong>⚠️ Importante:</strong></p>
                    <ul style="margin:10px 0; padding-left:20px;">
                        <li>Este link é válido por <strong>30 minutos</strong></li>
                        <li>Use apenas se você solicitou esta alteração</li>
                        <li>Sua senha atual continua ativa até você criar uma nova</li>
                    </ul>
                </div>

                <div style="text-align:center; margin:30px 0;">
                    <a href="{link_reset}"
                       style="background: linear-gradient(135deg, #0055D4, #00d9ff);
                              color:white; 
                              padding:15px 40px; 
                              text-decoration:none;
                              border-radius:8px; 
                              display:inline-block; 
                              font-weight:bold;
                              font-size:16px;
                              box-shadow: 0 4px 15px rgba(0, 85, 212, 0.3);">
                        🔐 Redefinir Minha Senha
                    </a>
                </div>

                <div style="background:#f0f8ff; border-left:5px solid #0055D4; padding:15px; margin:20px 0;">
                    <p style="margin:0; font-size:14px;">
                        <strong>Se o botão não funcionar:</strong><br>
                        Copie e cole este link no navegador:
                    </p>
                    <code style="background:#e3f2fd; 
                                 padding:8px; 
                                 display:block; 
                                 margin-top:10px; 
                                 word-break:break-all;
                                 font-size:12px;
                                 border-radius:4px;">
                        {link_reset}
                    </code>
                </div>

                <div style="background:#ffebee; border-left:5px solid #ef4444; padding:15px; margin:20px 0;">
                    <p style="margin:0; font-size:14px;">
                        <strong>🛡️ Segurança:</strong><br>
                        Se você <strong>não solicitou</strong> esta alteração, ignore este email. 
                        Sua senha permanecerá segura e nada será alterado.
                    </p>
                </div>

                <hr style="border:none; border-top:1px solid #e0e0e0; margin:30px 0;">

                <p style="color:#666; font-size:14px; margin-top:30px;">
                    <strong>Precisa de ajuda?</strong><br>
                    📱 WhatsApp: <a href="https://wa.me/5562995594055" style="color:#0055D4;">(62) 99559-4055</a><br>
                    📧 Email: <a href="mailto:suporte@plataformalauncher.com.br" style="color:#0055D4;">suporte@plataformalauncher.com.br</a>
                </p>

                <p style="margin-top:20px;">
                    Abraços,<br>
                    <strong style="color:#0055D4;">Equipe Launcher 💙</strong>
                </p>
            </div>

            <div style="text-align:center; padding:20px; color:#999; font-size:12px;">
                <p>© 2026 Plataforma Launcher - Todos os direitos reservados</p>
                <p>Este é um email automático, por favor não responda.</p>
            </div>
        </body>
        </html>
        """

        return EmailService._enviar_email(destinatario, assunto, corpo_html)


    # ====================================================
    # 🎉 EMAIL DE BOAS-VINDAS COM COMPRA (NOVO DESIGN)
    # ====================================================
# ====================================================
    # 🎉 EMAIL DE BOAS-VINDAS COM COMPRA - DESIGN FINAL
    # ====================================================
    @staticmethod
    def enviar_email_boas_vindas_compra(email_destino, nome_completo, cpf, tipo_plano="Premium"):
        """
        Envia email de boas-vindas para cliente que acabou de comprar
        Design idêntico ao template aprovado
        """
        try:
            # Gerar senha inicial baseada no CPF
            senha_inicial = ''.join(filter(str.isdigit, cpf)) if cpf and len(cpf) == 11 else "launcher123"
            primeiro_nome = nome_completo.split()[0] if nome_completo else "Aluno"

            assunto = f"🚀 Bem-vindo(a) à Plataforma Launcher, {primeiro_nome}!"
            
            corpo_html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem-vindo à Plataforma Launcher</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    
    <!-- Container principal -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                
                <!-- Card do email -->
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                    
                    <!-- Logo/Header -->
                    <tr>
                        <td align="center" style="padding: 40px 20px; background-color: #ffffff;">
                            <img src="https://plataformalauncher.com.br/static/images/logoemail.png" 
                                 alt="Plataforma Launcher" 
                                 style="max-width: 280px; height: auto; display: block; margin: 0 auto;">
                        </td>
                    </tr>
                    
                    <!-- Saudação -->
                    <tr>
                        <td style="padding: 0 40px 20px;">
                            <h1 style="color: #1a1a1a; font-size: 26px; font-weight: 600; text-align: center; margin: 0 0 10px 0;">
                                Bem-vindo(a), {primeiro_nome}! 🚀
                            </h1>
                            <p style="color: #666; font-size: 15px; text-align: center; margin: 0; line-height: 1.5;">
                                Sua compra foi confirmada e seu acesso está liberado.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Mensagem motivacional -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <p style="color: #1a1a1a; font-size: 14px; text-align: center; margin: 0; line-height: 1.6;">
                                <strong>Parabéns pela decisão</strong> em fazer parte da plataforma que valoriza o seu esforço e acelera sua aprovação no Enem!
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Box: Crie sua senha agora -->
                    <tr>
                        <td style="padding: 0 40px 20px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 25px;">
                                        <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">
                                            Crie sua senha agora
                                        </h2>
                                        <p style="color: #666; font-size: 13px; margin: 0 0 20px 0; line-height: 1.5;">
                                            Para manter sua conta segura, altere sua senha.
                                        </p>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td align="center">
                                                    <a href="https://plataformalauncher.com.br/login" 
                                                       style="display: inline-block; background-color: #00bfff; color: #ffffff; text-decoration: none; padding: 12px 40px; border-radius: 4px; font-weight: 600; font-size: 14px;">
                                                        Acessar Platforma Launcher
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="color: #999; font-size: 11px; text-align: center; margin: 15px 0 0 0; line-height: 1.4;">
                                            No login, você poderá criar uma nova senha segura.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Box: Seus dados de acesso -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 25px;">
                                        <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 600; margin: 0 0 15px 0;">
                                            Seus dados de acesso
                                        </h2>
                                        
                                        <!-- Endereço -->
                                        <div style="margin-bottom: 15px;">
                                            <p style="color: #666; font-size: 13px; margin: 0 0 4px 0; font-weight: 600;">
                                                Endereço:
                                            </p>
                                            <p style="margin: 0;">
                                                <a href="https://plataformalauncher.com.br/login" 
                                                   style="color: #00bfff; font-size: 13px; text-decoration: none; word-break: break-all;">
                                                    https://plataformalauncher.com.br/login
                                                </a>
                                            </p>
                                        </div>
                                        
                                        <!-- Usuário -->
                                        <div style="margin-bottom: 15px;">
                                            <p style="color: #666; font-size: 13px; margin: 0 0 4px 0; font-weight: 600;">
                                                Usuário (e-mail):
                                            </p>
                                            <p style="margin: 0;">
                                                <a href="mailto:{email_destino}" 
                                                   style="color: #00bfff; font-size: 13px; text-decoration: none; word-break: break-all;">
                                                    {email_destino}
                                                </a>
                                            </p>
                                        </div>
                                        
                                        <!-- Senha provisória -->
                                        <div>
                                            <p style="color: #666; font-size: 13px; margin: 0 0 6px 0; font-weight: 600;">
                                                Senha provisória:
                                            </p>
                                            <p style="margin: 0;">
                                                <span style="display: inline-block; background-color: #ffffff; border: 1px solid #dee2e6; padding: 8px 16px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 16px; color: #1a1a1a; letter-spacing: 2px; font-weight: 600;">
                                                    {senha_inicial}
                                                </span>
                                            </p>
                                        </div>
                                        
                                        <p style="color: #999; font-size: 11px; margin: 15px 0 0 0; line-height: 1.4;">
                                            Por segurança, altere a senha no primeiro login.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Suporte rápido -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <div style="background-color: #f8f9fa; border-left: 4px solid #00bfff; padding: 20px; border-radius: 4px;">
                                <h3 style="color: #1a1a1a; font-size: 14px; font-weight: 600; margin: 0 0 8px 0;">
                                    Suporte rápido
                                </h3>
                                <p style="color: #666; font-size: 13px; margin: 0; line-height: 1.5;">
                                    <strong>launcher.contato@gmail.com</strong> | +55 62 9 9559-4055
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8f9fa; border-top: 1px solid #e9ecef; text-align: center;">
                            <p style="color: #999; font-size: 11px; margin: 0 0 8px 0; line-height: 1.4;">
                                © 2026 Plataforma Launcher. Todos os direitos reservados.
                            </p>
                            <p style="color: #999; font-size: 10px; margin: 0; line-height: 1.4;">
                                Você recebeu este e-mail porque realizou uma compra em nossa plataforma.
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
    
</body>
</html>
            """

            return EmailService._enviar_email(email_destino, assunto, corpo_html)

        except Exception as e:
            logger.error(f"❌ Erro ao enviar e-mail de boas-vindas com compra: {e}")
            return False, str(e)
