# app/config/email_config.py - CONFIGURAÇÃO DE EMAIL PARA RESET DE SENHA (CORRIGIDA)

import os
from flask import current_app

class EmailConfig:
    """Configurações de email para a aplicação"""
    
    # Configurações SMTP
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # Configurações do remetente
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', SMTP_USER)
    MAIL_SUBJECT_PREFIX = '[Plataforma Launcher] '
    
    # Templates de email
    RESET_PASSWORD_SUBJECT = 'Redefinição de Senha'
    WELCOME_SUBJECT = 'Bem-vindo à Plataforma Launcher'
    
    @classmethod
    def is_configured(cls):
        """Verifica se o email está configurado"""
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD)


# Templates de email
class EmailTemplates:
    """Templates de email em HTML"""
    
    @staticmethod
    def get_reset_password_template(user_name, reset_url, expiry_hours=1):
        """Template para reset de senha"""
        return f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Redefinição de Senha - Plataforma Launcher</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #800000, #a00000);
                    color: white;
                    padding: 40px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content h2 {{
                    color: #800000;
                    margin-top: 0;
                    font-size: 20px;
                }}
                .reset-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #800000, #a00000);
                    color: white !important;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: 600;
                    margin: 20px 0;
                    transition: all 0.3s ease;
                }}
                .reset-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(128, 0, 0, 0.3);
                }}
                .info-box {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                .security-tips {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .security-tips h4 {{
                    color: #856404;
                    margin-top: 0;
                }}
                .security-tips ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .security-tips li {{
                    color: #856404;
                    margin-bottom: 5px;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        margin: 10px;
                    }}
                    .content {{
                        padding: 20px 15px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Plataforma Launcher</h1>
                    <p>Redefinição de Senha</p>
                </div>
                
                <div class="content">
                    <h2>Olá, {user_name}!</h2>
                    
                    <p>Você solicitou a redefinição de sua senha na Plataforma Launcher. Clique no botão abaixo para criar uma nova senha:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="reset-button">
                            🔒 Redefinir Minha Senha
                        </a>
                    </div>
                    
                    <div class="info-box">
                        <strong>⏰ Importante:</strong> Este link expira em {expiry_hours} hora(s) por motivos de segurança.
                    </div>
                    
                    <p>Se você não conseguir clicar no botão, copie e cole o link abaixo no seu navegador:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                        {reset_url}
                    </p>
                    
                    <div class="security-tips">
                        <h4>🛡️ Dicas de Segurança:</h4>
                        <ul>
                            <li>Nunca compartilhe este link com outras pessoas</li>
                            <li>Este link funciona apenas uma vez</li>
                            <li>Se você não solicitou esta redefinição, ignore este email</li>
                            <li>Use uma senha forte com pelo menos 8 caracteres</li>
                            <li>Inclua letras maiúsculas, minúsculas, números e símbolos</li>
                        </ul>
                    </div>
                    
                    <p>Se você não solicitou esta redefinição de senha, pode ignorar este email com segurança. Sua senha atual permanecerá inalterada.</p>
                    
                    <p>Em caso de dúvidas, entre em contato conosco através do suporte.</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>Equipe Plataforma Launcher</strong></p>
                </div>
                
                <div class="footer">
                    <p>📧 Este é um email automático, não responda a esta mensagem.</p>
                    <p>Plataforma Launcher - Decole rumo à aprovação no ENEM 2025</p>
                    <p>
                        <a href="https://plataforma-launcher.com">Site</a> | 
                        <a href="https://plataforma-launcher.com/suporte">Suporte</a> | 
                        <a href="https://plataforma-launcher.com/privacidade">Privacidade</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def get_welcome_template(user_name, username):
        """Template para email de boas-vindas"""
        return f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bem-vindo à Plataforma Launcher</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #800000, #a00000);
                    color: white;
                    padding: 40px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .welcome-badge {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 15px 25px;
                    border-radius: 25px;
                    display: inline-block;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .feature-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .feature-card {{
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    border-left: 4px solid #800000;
                }}
                .feature-card h4 {{
                    color: #800000;
                    margin-top: 0;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #800000, #a00000);
                    color: white !important;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Bem-vindo à Plataforma Launcher!</h1>
                    <p>Sua jornada rumo à aprovação começa agora</p>
                </div>
                
                <div class="content">
                    <h2>Olá, {user_name}! 👋</h2>
                    
                    <div style="text-align: center;">
                        <div class="welcome-badge">
                            ✅ Conta criada com sucesso!
                        </div>
                    </div>
                    
                    <p>Parabéns por dar este importante passo em direção ao seu futuro! Seu username é: <strong>@{username}</strong></p>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <h4>📚 Simulados</h4>
                            <p>Pratique com questões reais do ENEM e acompanhe seu progresso</p>
                        </div>
                        <div class="feature-card">
                            <h4>✍️ Redações</h4>
                            <p>Melhore sua escrita com correções detalhadas</p>
                        </div>
                        <div class="feature-card">
                            <h4>💎 Sistema XP</h4>
                            <p>Ganhe pontos estudando e troque por recompensas</p>
                        </div>
                        <div class="feature-card">
                            <h4>🎯 Help Zone</h4>
                            <p>Tire suas dúvidas com a comunidade</p>
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://plataforma-launcher.com/login" class="cta-button">
                            🎓 Começar a Estudar
                        </a>
                    </div>
                    
                    <p>Dicas para começar:</p>
                    <ul>
                        <li>Complete seu perfil para personalizar sua experiência</li>
                        <li>Faça seu primeiro simulado para avaliar seu nível</li>
                        <li>Explore as matérias disponíveis</li>
                        <li>Participe da comunidade na Help Zone</li>
                    </ul>
                    
                    <p>Estamos aqui para ajudar você a alcançar seus objetivos!</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>Equipe Plataforma Launcher</strong></p>
                </div>
                
                <div class="footer">
                    <p>Plataforma Launcher - Decole rumo à aprovação no ENEM 2025</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_plain_reset_template(user_name, reset_url, expiry_hours=1):
        """Template de texto simples para reset de senha"""
        return f"""
        Olá, {user_name}!

        Você solicitou a redefinição de sua senha na Plataforma Launcher.

        Clique no link abaixo para criar uma nova senha:
        {reset_url}

        IMPORTANTE: Este link expira em {expiry_hours} hora(s) por motivos de segurança.

        Se você não solicitou esta redefinição de senha, pode ignorar este email com segurança.

        Dicas de Segurança:
        - Nunca compartilhe este link com outras pessoas
        - Este link funciona apenas uma vez
        - Use uma senha forte com pelo menos 8 caracteres

        Atenciosamente,
        Equipe Plataforma Launcher

        ---
        Este é um email automático, não responda a esta mensagem.
        """

# Serviço de envio de email
class EmailService:
    """Serviço para envio de emails"""
    
    @staticmethod
    def send_email(to_email, subject, html_body, plain_body=None):
        """Envia email com template HTML e fallback em texto"""
        import smtplib
        from email.mime.text import MimeText
        from email.mime.multipart import MimeMultipart
        
        try:
            # Verificar se o email está configurado
            if not EmailConfig.is_configured():
                raise Exception("Configurações de email não definidas")
            
            # Criar mensagem
            msg = MimeMultipart('alternative')
            msg['From'] = EmailConfig.MAIL_DEFAULT_SENDER
            msg['To'] = to_email
            msg['Subject'] = EmailConfig.MAIL_SUBJECT_PREFIX + subject
            
            # Adicionar versão em texto simples
            if plain_body:
                part1 = MimeText(plain_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Adicionar versão HTML
            part2 = MimeText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # Conectar ao servidor SMTP
            server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
            
            if EmailConfig.SMTP_USE_TLS:
                server.starttls()
            
            server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
            
            # Enviar email
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email enviado com sucesso para: {to_email}")
            return True, "Email enviado com sucesso"
            
        except Exception as e:
            error_msg = f"Erro ao enviar email: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    @staticmethod
    def send_reset_password_email(user_email, user_name, reset_token):
        """Envia email de reset de senha"""
        try:
            # Para testes locais, usar URL simples
            reset_url = f"http://localhost:5000/reset-senha/{reset_token}"
            
            # Gerar templates
            html_body = EmailTemplates.get_reset_password_template(user_name, reset_url)
            plain_body = EmailTemplates.get_plain_reset_template(user_name, reset_url)
            
            # Enviar email
            return EmailService.send_email(
                to_email=user_email,
                subject=EmailConfig.RESET_PASSWORD_SUBJECT,
                html_body=html_body,
                plain_body=plain_body
            )
        except Exception as e:
            print(f"❌ Erro ao enviar email de reset: {e}")
            return False, str(e)
    
    @staticmethod
    def send_welcome_email(user_email, user_name, username):
        """Envia email de boas-vindas"""
        html_body = EmailTemplates.get_welcome_template(user_name, username)
        
        return EmailService.send_email(
            to_email=user_email,
            subject=EmailConfig.WELCOME_SUBJECT,
            html_body=html_body
        )
    
    @staticmethod
    def test_email_configuration():
        """Testa a configuração de email"""
        try:
            import smtplib
            
            if not EmailConfig.is_configured():
                return False, "Configurações de email não definidas"
            
            print(f"🔧 Testando configuração:")
            print(f"   Servidor: {EmailConfig.SMTP_SERVER}:{EmailConfig.SMTP_PORT}")
            print(f"   Usuário: {EmailConfig.SMTP_USER}")
            print(f"   TLS: {EmailConfig.SMTP_USE_TLS}")
            
            # Testar conexão
            server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
            
            if EmailConfig.SMTP_USE_TLS:
                server.starttls()
            
            server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
            server.quit()
            
            return True, "✅ Configuração de email válida"
            
        except Exception as e:
            return False, f"❌ Erro na configuração: {str(e)}"


# Configurações para desenvolvimento/produção
class DevelopmentEmailConfig(EmailConfig):
    """Configurações de email para desenvolvimento"""
    
    # Para desenvolvimento, você pode usar MailHog ou similar
    SMTP_SERVER = os.environ.get('DEV_SMTP_SERVER', 'localhost')
    SMTP_PORT = int(os.environ.get('DEV_SMTP_PORT', 1025))
    SMTP_USE_TLS = False
    SMTP_USER = os.environ.get('DEV_SMTP_USER', 'test@launcher.com')
    SMTP_PASSWORD = os.environ.get('DEV_SMTP_PASSWORD', 'password')


class ProductionEmailConfig(EmailConfig):
    """Configurações de email para produção"""
    
    # Configurações mais rigorosas para produção
    @classmethod
    def is_configured(cls):
        required_vars = [
            'SMTP_SERVER',
            'SMTP_USER', 
            'SMTP_PASSWORD',
            'MAIL_DEFAULT_SENDER'
        ]
        
        return all(os.environ.get(var) for var in required_vars)


# Exemplo de uso das configurações no app
def configure_email(app):
    """Configura email baseado no ambiente"""
    
    if app.config.get('ENVIRONMENT') == 'development':
        email_config = DevelopmentEmailConfig
    else:
        email_config = ProductionEmailConfig
    
    # Adicionar configurações ao app
    app.config.update({
        'SMTP_SERVER': email_config.SMTP_SERVER,
        'SMTP_PORT': email_config.SMTP_PORT,
        'SMTP_USE_TLS': email_config.SMTP_USE_TLS,
        'SMTP_USER': email_config.SMTP_USER,
        'SMTP_PASSWORD': email_config.SMTP_PASSWORD,
        'MAIL_DEFAULT_SENDER': email_config.MAIL_DEFAULT_SENDER,
    })
    
    return email_config.is_configured()


if __name__ == "__main__":
    """Script de teste para configuração de email"""
    
    print("🧪 Testando configuração de email da Plataforma Launcher...")
    print("=" * 60)
    
    # Teste das configurações
    is_configured = EmailConfig.is_configured()
    print(f"📧 Email configurado: {'✅ Sim' if is_configured else '❌ Não'}")
    
    if is_configured:
        success, message = EmailService.test_email_configuration()
        print(f"🔗 Teste de conexão: {message}")
        
        if success:
            print("\n📨 Testando envio de email...")
            test_result = EmailService.send_email(
                to_email=EmailConfig.SMTP_USER,  # Envia para si mesmo
                subject="🧪 Teste da Plataforma Launcher",
                html_body="<h1 style='color: #800000;'>✅ Email funcionando!</h1><p>Configuração de SMTP está correta.</p>"
            )
            print(f"📬 Resultado do envio: {'✅ Sucesso' if test_result[0] else '❌ Falha'} - {test_result[1]}")
    else:
        print("\n⚙️ Para configurar o email:")
        print("1. Defina as variáveis de ambiente no .env")
        print("2. Use suas credenciais reais do Gmail")
        print("3. Execute novamente este teste")
    
    print("\n" + "=" * 60)
    print("🎯 Teste concluído!")
