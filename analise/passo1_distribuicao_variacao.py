"""
passo1_distribuicao_variacao.py
===============================
PASSO 1 da análise de variações bruscas de matrícula.

O que faz
---------
1. Lê o consolidado (bd5.csv) e calcula a matrícula total de cada escola em cada
   ano (soma das 6 colunas QT_MAT_*).
2. Para cada escola, compara anos CONSECUTIVOS (t-1 -> t) e calcula a variação
   percentual:   VAR_PCT = (M(t) - M(t-1)) / M(t-1)
   Só entram pares em que M(t-1) >= MIN_BASE (padrão 50): variação percentual em
   escola minúscula (3 -> 6 alunos = +100%) distorce a distribuição.
3. Mostra os quartis dessa variação e desenha o boxplot.

Ainda NÃO decide o que é "brusco". Isso é o passo 2 (regra do IQR).

Saídas (pasta PASTA_SAIDA)
--------------------------
pares_variacao.csv        uma linha por escola e par de anos (usado nos próximos passos)
resumo_quartis.csv        quartis e estatísticas da variação
boxplot_variacao.png      boxplot geral (esquerda) e ampliado entre -100% e +100% (direita)

Uso:  python passo1_distribuicao_variacao.py [--entrada caminho/bd5.csv] [--base-minima 50]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------
# Estrutura esperada (a pasta do projeto é a que contém "dados/" e "analise/"):
#   Trabalho Final - Inglês 2/
#       dados/bd5.csv
#       analise/passo1_distribuicao_variacao.py   <-- este arquivo
#       analise/resultados/passo1/                <-- criado automaticamente
# Os caminhos são calculados a partir da localização deste arquivo, então
# funcionam de qualquer pasta em que você abrir o terminal.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_ENTRADA = RAIZ_PROJETO / "dados" / "bd5.csv"
PASTA_SAIDA = RAIZ_PROJETO / "analise" / "resultados" / "passo1"
CSV_SEP = ";"
CSV_ENCODING = "latin-1"
CSV_ENCODING_SAIDA = "utf-8-sig"

COL_ANO = "ANO"
COL_ESCOLA = "CO_ESCOLA"
COLS_MAT = ["QT_MAT_AI_REG", "QT_MAT_AF_REG", "QT_MAT_EM_REG",
            "QT_MAT_AI_INT", "QT_MAT_AF_INT", "QT_MAT_EM_INT"]
# Colunas descritivas, guardadas para os passos 3 e 4 (rede, localização, estado)
COLS_CADASTRO = ["NO_ESCOLA", "UF", "REGIAO", "LOCALIZACAO", "DEP_ADM"]

BASE_MINIMA = 50


# ----------------------------------------------------------------------
def detectar_encoding(caminho: Path) -> str:
    with open(caminho, "rb") as f:
        return "utf-8-sig" if f.read(3) == b"\xef\xbb\xbf" else CSV_ENCODING


def limpar_nome(c: str) -> str:
    return str(c).replace("﻿", "").replace("ï»¿", "").strip()


def carregar(caminho: Path) -> pd.DataFrame:
    obrigatorias = [COL_ANO, COL_ESCOLA] + COLS_MAT
    desejadas = obrigatorias + COLS_CADASTRO
    enc = detectar_encoding(caminho)
    df = pd.read_csv(caminho, sep=CSV_SEP, encoding=enc,
                     usecols=lambda c: limpar_nome(c) in desejadas, low_memory=False)
    df.columns = [limpar_nome(c) for c in df.columns]
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise KeyError(f"Colunas ausentes em {caminho.name}: {faltando}")
    for c in COLS_MAT:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["MAT_TOTAL"] = df[COLS_MAT].sum(axis=1)
    return df


def montar_pares(df: pd.DataFrame, base_minima: int) -> pd.DataFrame:
    """Uma linha por escola e par de anos consecutivos (t-1, t)."""
    cad = [c for c in COLS_CADASTRO if c in df.columns]
    atual = df[[COL_ESCOLA, COL_ANO, "MAT_TOTAL"] + cad]
    ant = df[[COL_ESCOLA, COL_ANO, "MAT_TOTAL"]].copy()
    ant[COL_ANO] = ant[COL_ANO] + 1                      # alinha t-1 com t
    ant = ant.rename(columns={"MAT_TOTAL": "MAT_ANO_ANTERIOR"})
    p = atual.merge(ant, on=[COL_ESCOLA, COL_ANO], how="inner")
    p = p.rename(columns={COL_ANO: "ANO_EVENTO", "MAT_TOTAL": "MAT_ANO_EVENTO"})
    p["ANO_ANTERIOR"] = p["ANO_EVENTO"] - 1
    p = p[p["MAT_ANO_ANTERIOR"] >= base_minima].copy()
    p["VAR_ABS"] = p["MAT_ANO_EVENTO"] - p["MAT_ANO_ANTERIOR"]
    p["VAR_PCT"] = p["VAR_ABS"] / p["MAT_ANO_ANTERIOR"]
    ordem = ([COL_ESCOLA, "ANO_ANTERIOR", "ANO_EVENTO", "MAT_ANO_ANTERIOR",
              "MAT_ANO_EVENTO", "VAR_ABS", "VAR_PCT"] + cad)
    return p[ordem].sort_values([COL_ESCOLA, "ANO_EVENTO"]).reset_index(drop=True)


def resumo(v: pd.Series) -> pd.DataFrame:
    q1, med, q3 = v.quantile([0.25, 0.5, 0.75])
    d = {
        "n_pares": len(v), "minimo": v.min(), "Q1": q1, "mediana": med, "Q3": q3,
        "maximo": v.max(), "IQR": q3 - q1, "media": v.mean(), "desvio_padrao": v.std(),
        "pct_zero": 100 * (v == 0).mean(),
        "pct_queda": 100 * (v < 0).mean(), "pct_aumento": 100 * (v > 0).mean(),
    }
    return pd.DataFrame([d])


def desenhar(v: pd.Series, destino: Path):
    fig, eixos = plt.subplots(1, 2, figsize=(11, 5))
    for ax, titulo, lim in ((eixos[0], "Todos os valores", None),
                            (eixos[1], "Ampliado (-100% a +100%)", (-1, 1))):
        ax.boxplot(v * 100, widths=0.5, whis=1.5,
                   flierprops=dict(marker=".", markersize=2, alpha=0.3),
                   medianprops=dict(color="tab:red"))
        ax.set_title(titulo)
        ax.set_ylabel("Variação da matrícula (%)")
        ax.set_xticks([])
        ax.grid(axis="y", alpha=0.3)
        if lim:
            ax.set_ylim(lim[0] * 100, lim[1] * 100)
    fig.suptitle("Variação percentual anual da matrícula por escola")
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path, default=ARQUIVO_ENTRADA)
    ap.add_argument("--saida", type=Path, default=PASTA_SAIDA)
    ap.add_argument("--base-minima", type=int, default=BASE_MINIMA)
    a = ap.parse_args()

    a.saida.mkdir(parents=True, exist_ok=True)
    print(f"Lendo {a.entrada} ...")
    df = carregar(a.entrada)
    pares = montar_pares(df, a.base_minima)
    print(f"{len(pares):,} pares escola/ano consecutivos com matrícula >= {a.base_minima} "
          f"no ano anterior.\n")

    r = resumo(pares["VAR_PCT"])
    pares.to_csv(a.saida / "pares_variacao.csv", sep=CSV_SEP, index=False,
                 encoding=CSV_ENCODING_SAIDA)
    r.to_csv(a.saida / "resumo_quartis.csv", sep=CSV_SEP, index=False,
             encoding=CSV_ENCODING_SAIDA)
    desenhar(pares["VAR_PCT"], a.saida / "boxplot_variacao.png")

    x = r.iloc[0]
    print("=== DISTRIBUIÇÃO DA VARIAÇÃO PERCENTUAL ANUAL ===")
    print(f"Mínimo    : {x.minimo:.1%}")
    print(f"Q1 (25%)  : {x.Q1:.1%}")
    print(f"Mediana   : {x.mediana:.1%}")
    print(f"Q3 (75%)  : {x.Q3:.1%}")
    print(f"Máximo    : {x.maximo:.1%}")
    print(f"IQR (Q3-Q1): {x.IQR:.1%}")
    print(f"Média     : {x.media:.1%}  (puxada pelos extremos; compare com a mediana)")
    print(f"\nSem mudança: {x.pct_zero:.1f}% | quedas: {x.pct_queda:.1f}% | "
          f"aumentos: {x.pct_aumento:.1f}%")
    print(f"\nArquivos salvos em {a.saida.resolve()}")


if __name__ == "__main__":
    main()