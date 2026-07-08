import pandas as pd
from pathlib import Path

Path("data/final").mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("FASE 3 — BALANCEAMENTO E DATASET FINAL")
print("=" * 70)

df = pd.read_csv("data/processed/dados_validados.csv")

phishing = df[df['label'] == 1]
legitimas = df[df['label'] == 0]

print(f"\nAntes do balanceamento:")
print(f"  Phishing: {len(phishing):,}")
print(f"  Legítimas: {len(legitimas):,}")
print(f"  Proporção: 1 phishing para {len(legitimas)/len(phishing):.1f} legítimas")

menor = min(len(phishing), len(legitimas))

df_final = pd.concat([
    phishing.sample(menor, random_state=42),
    legitimas.sample(menor, random_state=42)
]).sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nDepois do balanceamento:")
print(f"  Total: {len(df_final):,}")
print(f"  Phishing: {(df_final['label']==1).sum():,}")
print(f"  Legítimas: {(df_final['label']==0).sum():,}")
print(f"  Proporção: 1:1 (balanceado)")

df_final.to_csv("data/final/dataset_safeclick.csv", index=False)
print(f"\n✓ DATASET FINAL SALVO: data/final/dataset_safeclick.csv")

print("\n" + "=" * 70)
print("✅ MOMENTO 1 CONCLUÍDO!")
print("Dataset pronto para extração de features e treinamento")
print("=" * 70)