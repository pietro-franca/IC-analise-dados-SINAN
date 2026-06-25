import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from loader import (
    carregar_dados,
    COD_BOTUCATU,
    POP_BOTUCATU,
    POP_UF,
    POP_FAIXA_ETARIA,
    POP_FAIXA_ETARIA_BOTUCATU,
    POP_RACA_ABS,
    POP_RACA_ABS_BOTUCATU,
    POP_ESCOLARIDADE,
    POP_ESCOLARIDADE_BOTUCATU,
    MAP_ESCOLARIDADE_AGREGADA,
    CID_DESCRICOES,
)
from clustering import menu_clustering

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (12, 6)})


def adicionar_estatisticas(ax, valores):
    media = valores.mean()
    desvio = valores.std()

    ax.axvline(media, color="red", linestyle="--", label=f"Média: {media:,.0f}")
    ax.axvline(media + desvio, color="gray", linestyle=":", label=f"+1σ: {media+desvio:,.0f}")
    ax.axvline(media - desvio, color="gray", linestyle=":", label=f"-1σ: {media-desvio:,.0f}")

    ax.legend()


def plot_serie_temporal(df):
    """Casos notificados por ano."""
    serie = df.groupby("ANO").size().reset_index(name="Casos")

    fig, ax = plt.subplots()
    sns.lineplot(data=serie, x="ANO", y="Casos", marker="o", ax=ax, color="steelblue")

    media = serie["Casos"].mean()
    desvio = serie["Casos"].std()

    ax.axhline(media, color="red", linestyle="--", label=f"Média: {media:,.0f}")
    ax.fill_between(
        serie["ANO"],
        media - desvio,
        media + desvio,
        color="gray",
        alpha=0.1,
        label="±1 desvio padrão",
    )

    ax.legend()
    ax.set_title("Casos de Acidente de Trabalho por Ano — Brasil (SINAN)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Número de casos")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    for _, row in serie.iterrows():
        ax.annotate(f"{int(row.Casos):,}", (row.ANO, row.Casos),
                    textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    plt.tight_layout()
    plt.show()


def plot_por_uf_normalizado(df, top_n: int = 27):
    contagem = df["UF_LABEL"].value_counts().reset_index()
    contagem.columns = ["UF", "Casos"]

    contagem["Populacao"] = contagem["UF"].map(POP_UF)
    contagem = contagem.dropna()
    contagem["Taxa"] = contagem["Casos"] / contagem["Populacao"] * 100_000
    contagem = contagem.sort_values("Taxa", ascending=False).head(top_n)

    fig, ax = plt.subplots()
    sns.barplot(data=contagem, y="UF", x="Taxa", palette="viridis", ax=ax)

    adicionar_estatisticas(ax, contagem["Taxa"])

    ax.set_title(f"Top {top_n} UF — Taxa por 100 mil habitantes")
    ax.set_xlabel("Casos por 100 mil habitantes")

    plt.tight_layout()
    plt.show()


def plot_por_sexo(df):
    """Distribuição por sexo, empilhada por ano."""
    pivot = (
        df[df["SEXO_LABEL"].isin(["Masculino", "Feminino"])]
        .groupby(["ANO", "SEXO_LABEL"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    pivot.plot(x="ANO", kind="bar", stacked=True, colormap="Set2", figsize=(12, 6))
    plt.title("Casos por Sexo e Ano")
    plt.xlabel("Ano")
    plt.ylabel("Casos")
    plt.legend(title="Sexo")
    plt.tight_layout()
    plt.show()


def plot_por_faixa_etaria_normalizado(df, pop_faixa: dict = None):
    if pop_faixa is None:
        pop_faixa = POP_FAIXA_ETARIA

    contagem = df["FAIXA_ETARIA"].value_counts()
    contagem = contagem.rename("Casos").to_frame()
    contagem.index = contagem.index.astype(str)

    contagem["Populacao"] = contagem.index.map(pop_faixa)
    contagem = contagem.dropna()
    contagem["Taxa"] = contagem["Casos"] / contagem["Populacao"] * 100_000

    ordem = list(pop_faixa.keys())
    contagem = contagem.reindex(ordem).dropna().reset_index()
    contagem.columns = ["Faixa Etária", "Casos", "População", "Taxa"]

    fig, ax = plt.subplots()
    sns.barplot(data=contagem, x="Taxa", y="Faixa Etária", palette="viridis", ax=ax)

    adicionar_estatisticas(ax, contagem["Taxa"])

    ax.set_title("Taxa de Acidentes por Faixa Etária (por 100 mil hab.)")
    ax.set_xlabel("Casos por 100 mil habitantes")

    plt.tight_layout()
    plt.show()


def plot_por_raca_normalizado(df, pop_raca_abs: dict = None):
    if pop_raca_abs is None:
        pop_raca_abs = POP_RACA_ABS

    contagem = (
        df[df["RACA_LABEL"].isin(pop_raca_abs.keys())]["RACA_LABEL"]
        .value_counts()
    )

    taxa = (contagem / pd.Series(pop_raca_abs)) * 100_000
    taxa = taxa.dropna().reset_index()
    taxa.columns = ["Raça/Cor", "Taxa"]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=taxa, x="Taxa", y="Raça/Cor", palette="Set1", ax=ax)

    adicionar_estatisticas(ax, taxa["Taxa"])

    ax.set_title("Taxa de Acidentes por Raça/Cor (por 100 mil hab.)")

    plt.tight_layout()
    plt.show()


def plot_por_escolaridade_normalizado(df, pop_escol: dict = None, pop_total_local: int = None):
    if pop_escol is None:
        pop_escol = POP_ESCOLARIDADE
    if pop_total_local is None:
        pop_total_local = 203_000_000

    df = df[df["ESCOL_LABEL"].isin(MAP_ESCOLARIDADE_AGREGADA.keys())].copy()
    df["ESCOL_AGR"] = df["ESCOL_LABEL"].map(MAP_ESCOLARIDADE_AGREGADA)

    contagem = df["ESCOL_AGR"].value_counts()

    pop_abs = {k: v * pop_total_local for k, v in pop_escol.items()}

    taxa = (contagem / pd.Series(pop_abs)) * 100_000
    taxa = taxa.dropna().reset_index()
    taxa.columns = ["Escolaridade", "Taxa"]

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=taxa, x="Taxa", y="Escolaridade", palette="rocket", ax=ax)

    adicionar_estatisticas(ax, taxa["Taxa"])

    ax.set_title("Taxa de Acidentes por Escolaridade (por 100 mil hab.)")

    plt.tight_layout()
    plt.show()


def plot_evolucao(df):
    """Distribuição por evolução do caso (desfecho)."""
    evol_original = df["EVOL_LABEL"].copy()

    principais = ["Cura", "Incapacidade Temporária"]
    outros_categorias = sorted(evol_original[~evol_original.isin(principais)].unique())

    evol = evol_original.apply(lambda x: x if x in principais else "Outros")

    contagem = evol.value_counts().reset_index()
    contagem.columns = ["Evolução", "Casos"]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.pie(
        contagem["Casos"],
        labels=contagem["Evolução"],
        autopct="%1.1f%%",
        startangle=140,
    )
    ax.set_title("Desfecho dos Casos (Evolução)")

    texto_outros = "Outros inclui:\n" + "\n".join(outros_categorias)
    plt.figtext(
        0.99, 0.5, texto_outros,
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"),
    )

    plt.tight_layout()
    plt.show()


def plot_tipo_acidente(df):
    """Tipos de acidente por ano."""
    pivot = (
        df[df["TIPO_LABEL"] != "Ignorado"]
        .groupby(["ANO", "TIPO_LABEL"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    pivot.plot(x="ANO", kind="bar", stacked=False, figsize=(12, 6))
    plt.title("Tipo de Acidente por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Casos")
    plt.legend(title="Tipo")
    plt.tight_layout()
    plt.show()


def plot_top_cid_lesao(df, top_n: int = 20):
    """Top N CIDs de lesão mais frequentes."""
    contagem = df["CID_LESAO"].value_counts().head(top_n).reset_index()
    contagem.columns = ["CID", "Casos"]

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(data=contagem, x="Casos", y="CID", palette="mako", ax=ax)

    ax.set_title(f"Top {top_n} CIDs de Lesão")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    top10 = contagem["CID"].head(10)
    descricoes = [f"{cid} — {CID_DESCRICOES.get(cid, 'Descrição não definida')}" for cid in top10]
    plt.figtext(
        0.99, 0.5, "Principais CIDs:\n" + "\n".join(descricoes),
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"),
    )

    plt.tight_layout()
    plt.show()


def plot_heatmap_uf_ano(df):
    """Heatmap de casos por UF e Ano."""
    pivot = (
        df.groupby(["UF_LABEL", "ANO"])
        .size()
        .unstack(fill_value=0)
    )
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.heatmap(pivot, cmap="YlOrRd", fmt=",d", linewidths=0.3, ax=ax,
                annot=(pivot.shape[0] <= 27))
    ax.set_title("Casos por UF e Ano (Heatmap)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("UF")
    plt.tight_layout()
    plt.show()


def plot_por_sit_trab(df):
    """Distribuição por situação no trabalho."""
    contagem = (
        df[df["SIT_LABEL"] != "Ignorado"]["SIT_LABEL"]
        .value_counts()
        .reset_index()
    )
    contagem.columns = ["Situação", "Casos"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=contagem, x="Casos", y="Situação", palette="viridis", ax=ax)

    ax.set_title("Distribuição por Situação no Trabalho")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()
    plt.show()


def plot_heatmap_mes_ano(df):
    """Heatmap de casos por Mês e Ano."""
    df2 = df.copy()
    df2["MES"] = pd.to_datetime(df2["DT_NOTIFIC"], format="%Y%m%d", errors="coerce").dt.month
    df2 = df2.dropna(subset=["MES", "ANO"])
    df2["MES"] = df2["MES"].astype(int)

    MESES = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai",  6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
    }

    pivot = df2.groupby(["ANO", "MES"]).size().unstack(fill_value=0)
    pivot.columns = [MESES.get(m, str(m)) for m in pivot.columns]

    _, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(pivot, cmap="YlOrRd", fmt=",d", linewidths=0.3, ax=ax, annot=True)
    ax.set_title("Casos por Mês e Ano — Botucatu/SP")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Ano")
    plt.tight_layout()
    plt.show()


def resumo(df):
    """Imprime estatísticas descritivas gerais no terminal."""
    total = len(df)
    print("\n" + "=" * 60)
    print("  RESUMO DOS DADOS — SINAN Acidente de Trabalho")
    print("=" * 60)
    print(f"  Total de registros : {total:,}")
    if "ANO" in df.columns:
        print(f"  Período            : {df['ANO'].min()} – {df['ANO'].max()}")
    print(f"  UFs presentes      : {df['UF_LABEL'].nunique()}")

    if "SEXO_LABEL" in df.columns:
        dist_sexo = df["SEXO_LABEL"].value_counts(normalize=True) * 100
        print("\n  Distribuição por sexo:")
        for k, v in dist_sexo.items():
            print(f"    {k:<20} {v:.1f}%")

    if "EVOL_LABEL" in df.columns:
        obitos = (df["EVOLUCAO"] == "5").sum()
        print(f"\n  Óbitos pelo agravo : {obitos:,} ({obitos/total*100:.2f}%)")

    if "IDADE" in df.columns:
        print(f"\n  Idade média        : {df['IDADE'].mean():.1f} anos")
        print(f"  Mediana da idade   : {df['IDADE'].median():.1f} anos")

    print("=" * 60 + "\n")


# ── Menus ────────────────────────────────────────────────────────────────────

MENU = {
    "1": ("Série temporal (casos por ano)",        plot_serie_temporal),
    "2": ("Casos por UF",                          plot_por_uf_normalizado),
    "3": ("Casos por sexo e ano (empilhado)",      plot_por_sexo),
    "4": ("Casos por faixa etária",                plot_por_faixa_etaria_normalizado),
    "5": ("Casos por raça/cor",                    plot_por_raca_normalizado),
    "6": ("Casos por escolaridade",                plot_por_escolaridade_normalizado),
    "7": ("Desfecho dos casos (gráfico de pizza)", plot_evolucao),
    "8": ("Tipo de acidente por ano",              plot_tipo_acidente),
    "9": ("Top 20 CIDs de lesão",                  plot_top_cid_lesao),
    "h": ("Heatmap UF × Ano",                      plot_heatmap_uf_ano),
    "c": ("Clusterização K-Means",                 menu_clustering),
    "r": ("Resumo estatístico no terminal",        resumo),
}

MENU_BOTUCATU = {
    "1": ("Série temporal (casos por ano)",        plot_serie_temporal),
    "2": ("Distribuição por situação no trabalho", plot_por_sit_trab),
    "3": ("Casos por sexo e ano (empilhado)",      plot_por_sexo),
    "4": ("Casos por faixa etária",                lambda df: plot_por_faixa_etaria_normalizado(df, POP_FAIXA_ETARIA_BOTUCATU)),
    "5": ("Casos por raça/cor",                    lambda df: plot_por_raca_normalizado(df, POP_RACA_ABS_BOTUCATU)),
    "6": ("Casos por escolaridade",                lambda df: plot_por_escolaridade_normalizado(df, POP_ESCOLARIDADE_BOTUCATU, POP_BOTUCATU)),
    "7": ("Desfecho dos casos (gráfico de pizza)", plot_evolucao),
    "8": ("Tipo de acidente por ano",              plot_tipo_acidente),
    "9": ("Top 20 CIDs de lesão",                  plot_top_cid_lesao),
    "h": ("Heatmap Mês × Ano",                     plot_heatmap_mes_ano),
    "c": ("Clusterização K-Means",                 menu_clustering),
    "r": ("Resumo estatístico no terminal",        resumo),
}


def _rodar_menu(df, menu: dict, titulo: str):
    while True:
        print(f"\n──────── {titulo} ────────────────────────────────")
        for chave, (descricao, _) in menu.items():
            print(f"  [{chave}] {descricao}")
        print("  [q] Sair")
        print("──────────────────────────────────────────────")
        opcao = input("Opção: ").strip().lower()

        if opcao == "q":
            break
        elif opcao in menu:
            _, func = menu[opcao]
            func(df)
        else:
            print("Opção inválida. Tente novamente.")


def main_brasil():
    print("\nCarregando dados do SINAN — Acidente de Trabalho (Brasil)...")
    df = carregar_dados()
    print(f"  {len(df):,} registros carregados de {df['ANO'].min()}–{df['ANO'].max()}.")
    _rodar_menu(df, MENU, "MENU — BRASIL")


def main_botucatu():
    print("\nCarregando dados do SINAN — Acidente de Trabalho (Botucatu/SP)...")
    df = carregar_dados()
    df = df[df["ID_MUNICIP"] == COD_BOTUCATU]

    if df.empty:
        print(f"Nenhum registro encontrado para Botucatu (cód. {COD_BOTUCATU}).")
        return

    print(f"  {len(df):,} registros de Botucatu ({df['ANO'].min()}–{df['ANO'].max()}).")
    _rodar_menu(df, MENU_BOTUCATU, "MENU — BOTUCATU/SP")


def main():
    print("\n══════════════════════════════════════════════")
    print("  SINAN — Análise de Acidentes de Trabalho")
    print("══════════════════════════════════════════════")
    print("  [1] Brasil (todos os municípios)")
    print("  [2] Botucatu/SP")
    print("  [q] Sair")
    print("══════════════════════════════════════════════")
    escolha = input("Escopo: ").strip().lower()

    if escolha == "1":
        main_brasil()
    elif escolha == "2":
        main_botucatu()


if __name__ == "__main__":
    main()
