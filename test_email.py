import os
from app.config.email_config import EmailService

# Teste
success, msg = EmailService.send_email(
    to_email="seuemail@gmail.com",
    subject="🚀 Teste Plataforma Launcher", 
    html_body="<h1 style='color: #800000'>Funcionando! 🎉</h1>"
)

print(f"{'✅ Sucesso!' if success else '❌ Erro:'} {msg}")
