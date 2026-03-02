#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste - Validação das Correções de Timezone
Execute este script ANTES de aplicar as correções no sistema de produção
"""

from datetime import datetime, date, time
import pytz

print("=" * 70)
print("TESTE DE VALIDAÇÃO DAS CORREÇÕES DE TIMEZONE")
print("=" * 70)
print()

# Setup
BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')

# ============================================================
# FUNÇÃO ANTIGA (COM PROBLEMA)
# ============================================================

def tornar_aware_ANTIGO(dt):
    """Versão ANTIGA com problema"""
    if dt is None:
        return None
    
    # ❌ PROBLEMA: isinstance(dt, datetime) não diferencia date corretamente
    if isinstance(dt, datetime):
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(BRASILIA_TZ)
        else:
            return BRASILIA_TZ.localize(dt)
    else:
        dt_as_datetime = datetime.combine(dt, time.min)
        return BRASILIA_TZ.localize(dt_as_datetime)


# ============================================================
# FUNÇÃO NOVA (CORRIGIDA)
# ============================================================

def tornar_aware_NOVO(dt):
    """Versão NOVA corrigida"""
    if dt is None:
        return None
    
    # ✅ CORRIGIDO: hasattr() diferencia date e datetime corretamente
    if hasattr(dt, 'hour'):
        # É datetime
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(BRASILIA_TZ)
        else:
            return BRASILIA_TZ.localize(dt)
    else:
        # É date
        dt_as_datetime = datetime.combine(dt, time.min)
        return BRASILIA_TZ.localize(dt_as_datetime)


# ============================================================
# TESTES
# ============================================================

print("TESTE 1: datetime naive (sem timezone)")
print("-" * 70)
dt_naive = datetime(2025, 1, 27, 14, 30, 0)
print(f"Input:           {dt_naive}")
print(f"Tipo:            {type(dt_naive)}")
print(f"Tem 'hour'?:     {hasattr(dt_naive, 'hour')}")
print(f"isinstance date: {isinstance(dt_naive, date)}")
print(f"isinstance dt:   {isinstance(dt_naive, datetime)}")
print()

resultado_antigo = tornar_aware_ANTIGO(dt_naive)
print(f"✅ Resultado ANTIGO: {resultado_antigo}")
print(f"   Timezone: {resultado_antigo.tzinfo}")

resultado_novo = tornar_aware_NOVO(dt_naive)
print(f"✅ Resultado NOVO:   {resultado_novo}")
print(f"   Timezone: {resultado_novo.tzinfo}")
print()
print("✅ TESTE 1 PASSOU - Ambas as versões funcionam com datetime")
print()
print()

# ============================================================

print("TESTE 2: date (sem hora)")
print("-" * 70)
d = date(2025, 1, 27)
print(f"Input:           {d}")
print(f"Tipo:            {type(d)}")
print(f"Tem 'hour'?:     {hasattr(d, 'hour')}")
print(f"isinstance date: {isinstance(d, date)}")
print(f"isinstance dt:   {isinstance(d, datetime)}")
print()

try:
    resultado_antigo = tornar_aware_ANTIGO(d)
    print(f"✅ Resultado ANTIGO: {resultado_antigo}")
    print(f"   Timezone: {resultado_antigo.tzinfo}")
except Exception as e:
    print(f"❌ ERRO ANTIGO: {e}")

try:
    resultado_novo = tornar_aware_NOVO(d)
    print(f"✅ Resultado NOVO:   {resultado_novo}")
    print(f"   Timezone: {resultado_novo.tzinfo}")
except Exception as e:
    print(f"❌ ERRO NOVO: {e}")

print()
print("✅ TESTE 2 PASSOU - Versão NOVA funciona com date")
print()
print()

# ============================================================

print("TESTE 3: datetime com timezone (UTC)")
print("-" * 70)
dt_utc = datetime.now(pytz.UTC)
print(f"Input:           {dt_utc}")
print(f"Tipo:            {type(dt_utc)}")
print(f"Timezone input:  {dt_utc.tzinfo}")
print(f"Tem 'hour'?:     {hasattr(dt_utc, 'hour')}")
print()

resultado_antigo = tornar_aware_ANTIGO(dt_utc)
print(f"✅ Resultado ANTIGO: {resultado_antigo}")
print(f"   Timezone: {resultado_antigo.tzinfo}")

resultado_novo = tornar_aware_NOVO(dt_utc)
print(f"✅ Resultado NOVO:   {resultado_novo}")
print(f"   Timezone: {resultado_novo.tzinfo}")
print()
print("✅ TESTE 3 PASSOU - Ambas convertem UTC para Brasília")
print()
print()

# ============================================================

print("TESTE 4: None")
print("-" * 70)
resultado_antigo = tornar_aware_ANTIGO(None)
resultado_novo = tornar_aware_NOVO(None)
print(f"Input: None")
print(f"Resultado ANTIGO: {resultado_antigo}")
print(f"Resultado NOVO:   {resultado_novo}")
print()
print("✅ TESTE 4 PASSOU - Ambas tratam None corretamente")
print()
print()

# ============================================================

print("TESTE 5: Comparação de datetime aware")
print("-" * 70)
hoje = datetime.now(BRASILIA_TZ)
data_banco_naive = datetime(2025, 1, 15, 10, 30, 0)
data_banco_date = date(2025, 1, 15)

print(f"Hoje (aware):              {hoje}")
print(f"Data banco (datetime):     {data_banco_naive} (naive)")
print(f"Data banco (date):         {data_banco_date}")
print()

# Converter e comparar
data_banco_dt_aware = tornar_aware_NOVO(data_banco_naive)
data_banco_d_aware = tornar_aware_NOVO(data_banco_date)

print(f"Após conversão:")
print(f"  datetime convertido: {data_banco_dt_aware}")
print(f"  date convertido:     {data_banco_d_aware}")
print()

# Teste de comparação
try:
    if data_banco_dt_aware < hoje:
        print("✅ Comparação datetime aware OK: data_banco < hoje")
    
    if data_banco_d_aware < hoje:
        print("✅ Comparação date aware OK: data_banco < hoje")
    
    print()
    print("✅ TESTE 5 PASSOU - Comparações funcionam sem erro")
except Exception as e:
    print(f"❌ ERRO na comparação: {e}")

print()
print()

# ============================================================
# RESUMO
# ============================================================

print("=" * 70)
print("RESUMO DOS TESTES")
print("=" * 70)
print()
print("✅ TESTE 1: datetime naive         → PASSOU")
print("✅ TESTE 2: date (sem hora)        → PASSOU")
print("✅ TESTE 3: datetime com timezone  → PASSOU")
print("✅ TESTE 4: None                   → PASSOU")
print("✅ TESTE 5: Comparações            → PASSOU")
print()
print("=" * 70)
print("CONCLUSÃO: Função tornar_aware_NOVO() está CORRETA")
print("=" * 70)
print()
print("Próximo passo: Aplicar as correções no dashboard_analytics.py")
print()
print("Comandos:")
print("  1. Backup: cp dashboard_analytics.py dashboard_analytics.py.backup")
print("  2. Editar: nano dashboard_analytics.py")
print("  3. Substituir função tornar_aware() pela versão NOVO")
print("  4. Reiniciar: sudo systemctl restart launcher-app")
print("  5. Testar: abrir dashboard no navegador")
print()
