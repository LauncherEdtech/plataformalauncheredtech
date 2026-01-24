# setup_redacao.ps1
# Script para configurar o ambiente e realizar migrações para o módulo de redação

# Cores para saída
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Red = [System.ConsoleColor]::Red

Write-Host "Iniciando configuração do módulo de redação..." -ForegroundColor $Yellow

# Verificar se o ambiente virtual está ativado
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor $Yellow
    
    # Verificar se existe uma pasta venv
    if (Test-Path "venv") {
        & .\venv\Scripts\Activate.ps1
    }
    elseif (Test-Path ".venv") {
        & .\.venv\Scripts\Activate.ps1
    }
    else {
        Write-Host "Ambiente virtual não encontrado. Criando um novo..." -ForegroundColor $Red
        python -m venv venv
        & .\venv\Scripts\Activate.ps1
    }
}

# Instalar dependências necessárias
Write-Host "Instalando dependências..." -ForegroundColor $Yellow
pip install flask flask-sqlalchemy flask-migrate flask-login python-dotenv requests

# Exportar variáveis de ambiente para a API do OpenAI
Write-Host "Configurando variáveis de ambiente..." -ForegroundColor $Yellow
if (Test-Path ".env") {
    Write-Host "Usando variáveis do arquivo .env"
    $envVars = Get-Content .env | Where-Object { $_ -notmatch '^\s*#' -and $_.trim() -ne '' }
    foreach ($line in $envVars) {
        $name, $value = $line.split('=', 2)
        [Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
    }
}
else {
    Write-Host "Criando arquivo .env temporário"
    "OPENAI_API_KEY=sua-chave-api" | Out-File -FilePath .env -Encoding utf8
    "SECRET_KEY=chave-secreta-temporaria" | Out-File -FilePath .env -Append -Encoding utf8
    "DATABASE_URL=postgresql://postgres:1469@localhost:5432/launcher_db" | Out-File -FilePath .env -Append -Encoding utf8
    
    # Também definimos as variáveis para o processo atual
    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sua-chave-api", [System.EnvironmentVariableTarget]::Process)
    [Environment]::SetEnvironmentVariable("SECRET_KEY", "chave-secreta-temporaria", [System.EnvironmentVariableTarget]::Process)
    [Environment]::SetEnvironmentVariable("DATABASE_URL", "postgresql://postgres:1469@localhost:5432/launcher_db", [System.EnvironmentVariableTarget]::Process)
}

# Executar migrações
Write-Host "Executando migrações do banco de dados..." -ForegroundColor $Yellow
flask db upgrade

# Criar diretórios necessários para templates
Write-Host "Criando diretórios para templates..." -ForegroundColor $Yellow
if (-not (Test-Path "app\templates\redacao")) {
    New-Item -Path "app\templates\redacao" -ItemType Directory -Force
}

Write-Host "Configuração do módulo de redação concluída com sucesso!" -ForegroundColor $Green
Write-Host "Para iniciar a aplicação, execute: flask run" -ForegroundColor $Yellow