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
# FILTRO 1 — TODAS as URLs brasileiras (sem limite de quantidade)
# ============================================================
print(f"\n[0/3] Filtrando URLs relevantes...")
print(f"  Total bruto: {len(df):,} URLs")

marcas_br = [
    'bradesco', 'itau', 'caixa', 'nubank', 'inter', 'c6bank',
    'mercadolivre', 'mercado-livre', 'magazineluiza', 'magazine',
    'americanas', 'shopee',
    'correios', 'sedex',
    'receita', 'inss', 'detran', 'gov.br',
    'claro', 'vivo', 'tim',
    'petrobras', 'equatorial', 'bb.com.br'
]

mask_br = (
    df['url'].str.contains(r'\.br', case=False, na=False) |
    df['url'].str.contains('|'.join(marcas_br), case=False, na=False)
)
df_br = df[mask_br].copy()

# ============================================================
# FILTRO 2 — Principais URLs globais usadas por brasileiros
# (Netflix, Facebook, Google, Instagram, WhatsApp etc.)
# ============================================================
principais_globais = [
    'netflix', 'facebook', 'google', 'instagram', 'whatsapp',
    'youtube', 'amazon', 'twitter', 'x.com', 'gmail',
    'microsoft', 'apple', 'tiktok', 'linkedin', 'spotify', 'paypal'
]

mask_global = df['url'].str.contains('|'.join(principais_globais), case=False, na=False)
df_global = df[mask_global & ~mask_br].copy()  # evita contar 2x quem já é BR

# ============================================================
# FILTRO 3 — Amostra adicional de domínios globais diversos
# (evita que "legítimo" no treino signifique só "marca famosa")
# ============================================================
ja_incluidos = set(df_br['url']) | set(df_global['url'])

pool_diverso = df[(df['label'] == 0) & (~df['url'].isin(ja_incluidos))]

AMOSTRA_DIVERSA = 2000  # ajuste aqui se quiser mais ou menos diversidade

df_diverso = pool_diverso.sample(
    n=min(AMOSTRA_DIVERSA, len(pool_diverso)),
    random_state=42
)

# ============================================================
# COMBINA OS TRÊS GRUPOS (sem sampling artificial nos dois primeiros)
# ============================================================
df = pd.concat([df_br, df_global, df_diverso], ignore_index=True)
df = df.drop_duplicates('url')

print(f"  Brasileiras (todas): {len(df_br):,}")
print(f"  Globais relevantes (marcas conhecidas): {len(df_global):,}")
print(f"  Globais diversas (amostra extra): {len(df_diverso):,}")
print(f"  Total combinado: {len(df):,}")
print(f"  Phishing: {(df['label']==1).sum():,}")
print(f"  Legítimas: {(df['label']==0).sum():,}")

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
print(f"\n[3/3] Verificando URLs ativas...")
print(f"  URLs a verificar: {len(df):,}")
print(f"  Tempo estimado: ~{(len(df) / 20) / 60:.0f} min (20 threads, timeout 1s)")

# NOTA: este passo confirma se a URL ainda está no ar. O modelo usa
# apenas características estruturais da própria URL (comprimento,
# hífens, TLD etc.) — não depende da página estar ativa. Por isso,
# esta etapa é uma checagem de qualidade, não um requisito para o
# treino. Se o tempo estimado acima estiver alto demais, comente as
# linhas entre "def url_ativa" e "df = df[df['ativa']]..." e siga
# direto para o balanceamento — o dataset continua válido.

def url_ativa(url, timeout=1):
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 500
    except:
        return False

urls_ativas = []
with ThreadPoolExecutor(max_workers=20) as executor:
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