import requests
import pandas as pd
from pathlib import Path
import time

Path("data/raw").mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("FASE 1 — COLETA BRUTA (com tratamento de erro)")
print("=" * 70)

# ============================================================
# COLETA 1: OpenPhish (mais confiável)
# ============================================================
print("\n[1/3] OpenPhish...")
try:
    response = requests.get("https://openphish.com/feed.txt", timeout=15)
    response.raise_for_status()
    
    urls = [u.strip() for u in response.text.split('\n') if u.strip()]
    
    df_openphish = pd.DataFrame({
        'url': urls,
        'source': 'openphish',
        'label': 1
    })
    
    df_openphish.to_csv("data/raw/openphish_bruto.csv", index=False)
    print(f"  ✓ {len(urls)} URLs coletadas")
except requests.exceptions.Timeout:
    print("  ✗ Timeout — OpenPhish pode estar fora")
except Exception as e:
    print(f"  ✗ Erro: {e}")

time.sleep(2)

# COLETA 2: PhishTank (com validação de formato)

print("\n[2/3] PhishTank...")
try:
    url = "http://data.phishtank.com/data/online-valid.csv"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    
    if 'url' not in response.text[:100].lower():
        print("  ✗ Formato não reconhecido (não é CSV)")
    else:
        df_phishtank = pd.read_csv(
            pd.io.common.StringIO(response.text),
            usecols=['url'],
            dtype={'url': str}
        )
        
        df_phishtank['source'] = 'phishtank'
        df_phishtank['label'] = 1
        
        df_phishtank.to_csv("data/raw/phishtank_bruto.csv", index=False)
        print(f"  ✓ {len(df_phishtank)} URLs coletadas")
except Exception as e:
    print(f"  ✗ Erro: {e}")

time.sleep(2)

# ============================================================
# COLETA 3: Tranco (URLs legítimas)
# ============================================================
print("\n[3/3] Tranco (URLs legítimas)...")
try:
    if not Path("data/raw/tranco_top1m.csv").exists():
        print("  ⚠ Arquivo não encontrado!")
        print("    Baixe em: https://tranco-list.eu/")
        print("    E salve em: data/raw/tranco_top1m.csv")
    else:
        df_tranco = pd.read_csv(
            "data/raw/tranco_top1m.csv",
            header=None,
            names=['rank', 'dominio'],
            dtype={'rank': int, 'dominio': str}
        )
        
        df_legitimas = pd.DataFrame({
            'url': 'https://' + df_tranco['dominio'],
            'source': 'tranco',
            'label': 0
        })
        
        df_legitimas.to_csv("data/raw/tranco_legitimas.csv", index=False)
        print(f"  ✓ {len(df_legitimas)} URLs coletadas")
except MemoryError:
    print("  ✗ Falta de memória — tente em um computador com mais RAM")
except Exception as e:
    print(f"  ✗ Erro: {e}")

# ============================================================
# COMBINAR TUDO
# ============================================================
print("\n[4/4] Combinando dados brutos...")
try:
    dfs = []
    
    for arquivo in Path("data/raw").glob("*_bruto.csv"):
        dfs.append(pd.read_csv(arquivo))
    
    if Path("data/raw/tranco_legitimas.csv").exists():
        dfs.append(pd.read_csv("data/raw/tranco_legitimas.csv"))
    
    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        
        print(f"\n  Estatísticas BRUTAS:")
        print(f"    Total de URLs: {len(df_total):,}")
        print(f"    Phishing: {(df_total['label']==1).sum():,}")
        print(f"    Legítimas: {(df_total['label']==0).sum():,}")
        
        df_total.to_csv("data/raw/dados_combinados_bruto.csv", index=False)
        print(f"\n  ✓ Salvo em: data/raw/dados_combinados_bruto.csv")
    else:
        print("  ✗ Nenhum arquivo foi coletado com sucesso")

except Exception as e:
    print(f"  ✗ Erro ao combinar: {e}")

print("\n" + "=" * 70)
print("PRÓXIMO: python scripts/2_validacao_urls.py")
print("=" * 70)