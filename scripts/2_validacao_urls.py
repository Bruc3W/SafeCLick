import pandas as pd
from urllib.parse import urlparse
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor

Path("data/processed").mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("FASE 2 — VALIDAÇÃO (Remove URLs inativas/inválidas)")
print("=" * 70)

df = pd.read_csv("data/raw/dados_combinados_bruto.csv")

# ============================================================
# 1. VALIDAÇÃO SINTÁTICA
# ============================================================
print("\n[1/3] Validação sintática...")

def url_valida_sintax(url):
    try:
        r = urlparse(str(url))
        return r.scheme in ['http','https'] and len(r.netloc) > 3
    except:
        return False

df['valida_sintax'] = df['url'].apply(url_valida_sintax)
antes = len(df)
df = df[df['valida_sintax']].drop('valida_sintax', axis=1)
print(f"  ✓ Removidas {antes - len(df):,} URLs com sintaxe inválida")

# ============================================================
# 2. REMOVER DUPLICATAS
# ============================================================
print("\n[2/3] Removendo duplicatas...")
antes = len(df)
df = df.drop_duplicates('url')
print(f"  ✓ Removidas {antes - len(df):,} duplicatas")

# ============================================================
# 3. VERIFICAR ATIVIDADE (PARALELO)
# ============================================================
print("\n[3/3] Verificando URLs ativas (isso pode levar alguns minutos)...")

def url_ativa(url, timeout=3):
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 500
    except:
        return False

urls_ativas = []
with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(url_ativa, df['url'].values)
    urls_ativas = list(results)

df['ativa'] = urls_ativas
antes = len(df)
df = df[df['ativa']].drop('ativa', axis=1)
print(f"  ✓ Removidas {antes - len(df):,} URLs inativas")

# ============================================================
# RESULTADO
# ============================================================
print(f"\nEstatísticas após validação:")
print(f"  Total: {len(df):,}")
print(f"  Phishing: {(df['label']==1).sum():,}")
print(f"  Legítimas: {(df['label']==0).sum():,}")

df.to_csv("data/processed/dados_validados.csv", index=False)
print(f"\n✓ Salvo em: data/processed/dados_validados.csv")

print("\n" + "=" * 70)
print("PRÓXIMO: python scripts/3_balanceamento.py")
print("=" * 70)