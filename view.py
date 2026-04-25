import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (12, 6)})

DATA_DIR = os.path.join(os.path.dirname(__file__), "csvs", "acidente_de_trabalho")

SEXO = {"M": "Masculino", "F": "Feminino", "I": "Ignorado"}

RACA = {
    "1": "Branca", "2": "Preta", "3": "Amarela",
    "4": "Parda",  "5": "Indígena", "9": "Ignorado",
}

ESCOLARIDADE = {
    "00": "Analfabeto",
    "01": "1ª a 4ª série incompleta",
    "02": "4ª série completa",
    "03": "5ª a 8ª série incompleta",
    "04": "Fundamental completo",
    "05": "Médio incompleto",
    "06": "Médio completo",
    "07": "Superior incompleto",
    "08": "Superior completo",
    "09": "Ignorado",
    "10": "Não se aplica",
}

EVOLUCAO = {
    "1": "Cura",
    "2": "Incapacidade Temporária",
    "3": "Incapacidade Parcial Permanente",
    "4": "Incapacidade Total Permanente",
    "5": "Óbito pelo agravo",
    "6": "Óbito por outra causa",
    "8": "Ignorado",
    "9": "Ignorado",
}

SIT_TRAB = {
    "01": "Empregado registrado",
    "02": "Empregado não registrado",
    "03": "Autônomo / conta própria",
    "04": "Servidor público estatutário",
    "05": "Servidor público celetista",
    "06": "Aposentado",
    "07": "Desempregado",
    "08": "Trabalho temporário",
    "09": "Cooperativado",
    "10": "Trabalhador avulso",
    "11": "Aprendiz",
    "12": "Estagiário",
    "13": "Sem vínculo",
    "14": "Ignorado",
}

LOCAL_ACID = {
    "1": "No trabalho habitual",
    "2": "Em outro trabalho",
    "3": "A caminho do trabalho",
    "4": "Em local de treinamento",
    "9": "Ignorado",
}

TIPO_ACID = {
    "1": "Típico",
    "2": "Trajeto",
    "3": "Doença do trabalho",
    "9": "Ignorado",
}

UF_NOMES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}

POP_UF = {
    "SP": 45919049, "MG": 21168791, "RJ": 17264943,
    "BA": 14850513, "PR": 11444380, "RS": 11422973,
    "PE": 9616621,  "CE": 9187103,  "PA": 8777124,
    "SC": 7338473,  "GO": 7206589,  "MA": 7075181,
    "AM": 4207714,  "PB": 4039277,  "ES": 4108508,
    "RN": 3534165,  "MT": 3658813,  "AL": 3351543,
    "PI": 3273227,  "DF": 3094325,  "MS": 2839188,
    "SE": 2318822,  "RO": 1815278,  "TO": 1607363,
    "AC": 906876,   "AP": 877613,   "RR": 652713,
}

POP_FAIXA_ETARIA = {
    "<18": 56000000,
    "18–24": 23000000,
    "25–34": 34000000,
    "35–44": 32000000,
    "45–54": 28000000,
    "55–64": 22000000,
    "65+": 21000000,
}

POP_RACA = {
    "Branca": 0.43,
    "Parda": 0.45,
    "Preta": 0.10,
    "Amarela": 0.01,
    "Indígena": 0.01,
}

POP_TOTAL = 203_000_000
POP_RACA_ABS = {k: v * POP_TOTAL for k, v in POP_RACA.items()}

# proporções da PNAD
POP_ESCOLARIDADE = {
    "Analfabeto": 0.07,
    "Fundamental incompleto": 0.30,
    "Fundamental completo": 0.08,
    "Médio incompleto": 0.10,
    "Médio completo": 0.28,
    "Superior incompleto": 0.05,
    "Superior completo": 0.12,
}

MAP_ESCOLARIDADE_AGREGADA = {
    "Analfabeto": "Analfabeto",
    "1ª a 4ª série incompleta": "Fundamental incompleto",
    "4ª série completa": "Fundamental incompleto",
    "5ª a 8ª série incompleta": "Fundamental incompleto",
    "Fundamental completo": "Fundamental completo",
    "Médio incompleto": "Médio incompleto",
    "Médio completo": "Médio completo",
    "Superior incompleto": "Superior incompleto",
    "Superior completo": "Superior completo",
}

CID_DESCRICOES = {
    "S61": "Ferimento do punho/mão",
    "Y96": "Circunstância relativa às condições de trabalho",
    "S610": "Ferimento de dedo sem dano à unha",
    "B342": "Infecção viral não especificada",
    "S626": "Fratura de outro dedo",
    "S619": "Ferimento não especificado do punho/mão",
    "T07": "Traumatismos múltiplos",
    "S934": "Entorse/torção do tornozelo",
    "S60": "Traumatismo superficial do punho/mão",
    "S62": "Fratura do punho/mão",
}

# ── Carregamento dos dados ───────────────────────────────────────────────────

def carregar_dados(anos=None) -> pd.DataFrame:
    """
    Lê todos os CSVs do diretório e retorna um DataFrame consolidado.
    Parâmetros
    ----------
    anos : list[int] | None
        Filtra apenas os anos informados (ex.: [2018, 2019, 2020]).
        None = todos os anos disponíveis.
    """
    arquivos = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV encontrado em: {DATA_DIR}")

    if anos is not None:
        sufixos = {str(a)[-2:] for a in anos}
        arquivos = [f for f in arquivos if os.path.basename(f)[6:8] in sufixos]

    frames = []
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, dtype=str, encoding="latin-1", low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"[AVISO] Erro ao ler {os.path.basename(arq)}: {e}")

    if not frames:
        raise ValueError("Nenhum arquivo foi carregado com os filtros informados.")

    dados = pd.concat(frames, ignore_index=True)

    if "NU_ANO" in dados.columns:
        dados["ANO"] = pd.to_numeric(dados["NU_ANO"], errors="coerce").astype("Int64")

    if "NU_IDADE_N" in dados.columns:
        num = pd.to_numeric(dados["NU_IDADE_N"], errors="coerce")
        dados["IDADE"] = num.where(num >= 4000, other=pd.NA) - 4000
        dados["FAIXA_ETARIA"] = pd.cut(
            dados["IDADE"],
            bins=[0, 17, 24, 34, 44, 54, 64, 120],
            labels=["<18", "18–24", "25–34", "35–44", "45–54", "55–64", "65+"],
        )

    dados["SEXO_LABEL"]   = dados["CS_SEXO"].map(SEXO).fillna("Ignorado")
    dados["RACA_LABEL"]   = dados["CS_RACA"].map(RACA).fillna("Ignorado")
    dados["ESCOL_LABEL"]  = dados["CS_ESCOL_N"].map(ESCOLARIDADE).fillna("Ignorado")
    dados["EVOL_LABEL"]   = dados["EVOLUCAO"].map(EVOLUCAO).fillna("Ignorado")
    dados["TIPO_LABEL"]   = dados["TIPO_ACID"].map(TIPO_ACID).fillna("Ignorado")
    dados["LOCAL_LABEL"]  = dados["LOCAL_ACID"].map(LOCAL_ACID).fillna("Ignorado")
    dados["SIT_LABEL"]    = dados["SIT_TRAB"].map(SIT_TRAB).fillna("Ignorado")
    dados["UF_LABEL"]     = dados["SG_UF_NOT"].map(UF_NOMES).fillna(dados["SG_UF_NOT"])

    return dados



def adicionar_estatisticas(ax, valores):
    media = valores.mean()
    desvio = valores.std()

    ax.axvline(media, color="red", linestyle="--", label=f"Média: {media:,.0f}")
    ax.axvline(media + desvio, color="gray", linestyle=":", label=f"+1σ: {media+desvio:,.0f}")
    ax.axvline(media - desvio, color="gray", linestyle=":", label=f"-1σ: {media-desvio:,.0f}")

    ax.legend()



def plot_serie_temporal(df: pd.DataFrame):
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


def plot_por_uf_normalizado(df: pd.DataFrame, top_n: int = 27):
    contagem = df["UF_LABEL"].value_counts().reset_index()
    contagem.columns = ["UF", "Casos"]

    # adicionar população
    contagem["Populacao"] = contagem["UF"].map(POP_UF)

    # remover UFs sem população
    contagem = contagem.dropna()

    # taxa por 100 mil habitantes
    contagem["Taxa"] = contagem["Casos"] / contagem["Populacao"] * 100_000
    contagem = contagem.sort_values("Taxa", ascending=False).head(top_n)

    fig, ax = plt.subplots()
    sns.barplot(data=contagem, y="UF", x="Taxa", palette="viridis", ax=ax)

    adicionar_estatisticas(ax, contagem["Taxa"])

    ax.set_title(f"Top {top_n} UF — Taxa por 100 mil habitantes")
    ax.set_xlabel("Casos por 100 mil habitantes")

    plt.tight_layout()
    plt.show()


def plot_por_sexo(df: pd.DataFrame):
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


def plot_por_faixa_etaria_normalizado(df: pd.DataFrame):
    contagem = df["FAIXA_ETARIA"].value_counts()

    contagem = contagem.rename("Casos").to_frame()
    contagem.index = contagem.index.astype(str)  # CategoricalIndex → string para reindex funcionar

    contagem["Populacao"] = contagem.index.map(POP_FAIXA_ETARIA)
    contagem = contagem.dropna()
    contagem["Taxa"] = contagem["Casos"] / contagem["Populacao"] * 100_000

    ordem = list(POP_FAIXA_ETARIA.keys())
    contagem = contagem.reindex(ordem).dropna().reset_index()
    contagem.columns = ["Faixa Etária", "Casos", "População", "Taxa"]

    fig, ax = plt.subplots()
    sns.barplot(data=contagem, x="Taxa", y="Faixa Etária", palette="viridis", ax=ax)

    adicionar_estatisticas(ax, contagem["Taxa"])

    ax.set_title("Taxa de Acidentes por Faixa Etária (por 100 mil hab.)")
    ax.set_xlabel("Casos por 100 mil habitantes")

    plt.tight_layout()
    plt.show()


def plot_por_raca_normalizado(df: pd.DataFrame):
    contagem = (
        df[df["RACA_LABEL"].isin(POP_RACA_ABS.keys())]["RACA_LABEL"]
        .value_counts()
    )

    taxa = (contagem / pd.Series(POP_RACA_ABS)) * 100_000
    taxa = taxa.dropna().reset_index()
    taxa.columns = ["Raça/Cor", "Taxa"]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=taxa, x="Taxa", y="Raça/Cor", palette="Set1", ax=ax)

    adicionar_estatisticas(ax, taxa["Taxa"])

    ax.set_title("Taxa de Acidentes por Raça/Cor (por 100 mil hab.)")

    plt.tight_layout()
    plt.show()


def plot_por_escolaridade_normalizado(df: pd.DataFrame):
    df = df[df["ESCOL_LABEL"].isin(MAP_ESCOLARIDADE_AGREGADA.keys())].copy()
    df["ESCOL_AGR"] = df["ESCOL_LABEL"].map(MAP_ESCOLARIDADE_AGREGADA)

    contagem = df["ESCOL_AGR"].value_counts()

    POP_TOTAL = 203_000_000
    pop_abs = {k: v * POP_TOTAL for k, v in POP_ESCOLARIDADE.items()}

    taxa = (contagem / pd.Series(pop_abs)) * 100_000
    taxa = taxa.dropna().reset_index()
    taxa.columns = ["Escolaridade", "Taxa"]

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=taxa, x="Taxa", y="Escolaridade", palette="rocket", ax=ax)

    adicionar_estatisticas(ax, taxa["Taxa"])

    ax.set_title("Taxa de Acidentes por Escolaridade (por 100 mil hab.)")

    plt.tight_layout()
    plt.show()


def plot_evolucao(df: pd.DataFrame):
    """Distribuição por evolução do caso (desfecho)."""
    evol_original = df["EVOL_LABEL"].copy()

    principais = ["Cura", "Incapacidade Temporária"]

    # categorias agrupadas
    outros_categorias = sorted(
        evol_original[~evol_original.isin(principais)].unique()
    )

    # agrupamento
    evol = evol_original.apply(
        lambda x: x if x in principais else "Outros"
    )

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

    # 🔹 legenda explicativa dos "Outros"
    texto_outros = "Outros inclui:\n" + "\n".join(outros_categorias)

    plt.figtext(
        0.99, 0.5, texto_outros,
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray")
    )

    plt.tight_layout()
    plt.show()


def plot_tipo_acidente(df: pd.DataFrame):
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


def plot_top_cid_lesao(df: pd.DataFrame, top_n: int = 20):
    """Top N CIDs de lesão mais frequentes."""
    contagem = df["CID_LESAO"].value_counts().head(top_n).reset_index()
    contagem.columns = ["CID", "Casos"]

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(data=contagem, x="Casos", y="CID", palette="mako", ax=ax)

    ax.set_title(f"Top {top_n} CIDs de Lesão")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # 🔹 legenda com descrições (top 10)
    top10 = contagem["CID"].head(10)

    descricoes = []
    for cid in top10:
        desc = CID_DESCRICOES.get(cid, "Descrição não definida")
        descricoes.append(f"{cid} — {desc}")

    texto_legenda = "Principais CIDs:\n" + "\n".join(descricoes)

    plt.figtext(
        0.99, 0.5, texto_legenda,
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray")
    )

    plt.tight_layout()
    plt.show()


def plot_heatmap_uf_ano(df: pd.DataFrame):
    """Heatmap de casos por UF e Ano."""
    pivot = (
        df.groupby(["UF_LABEL", "ANO"])
        .size()
        .unstack(fill_value=0)
    )
    # Ordena por total decrescente
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.heatmap(pivot, cmap="YlOrRd", fmt=",d", linewidths=0.3, ax=ax,
                annot=(pivot.shape[0] <= 27))
    ax.set_title("Casos por UF e Ano (Heatmap)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("UF")
    plt.tight_layout()
    plt.show()



def resumo(df: pd.DataFrame):
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



MENU = {
    "1": ("Série temporal (casos por ano)",        plot_serie_temporal),
    "2": ("Casos por UF",                 plot_por_uf_normalizado),
    "3": ("Casos por sexo e ano (empilhado)",      plot_por_sexo),
    "4": ("Casos por faixa etária",                plot_por_faixa_etaria_normalizado),
    "5": ("Casos por raça/cor",                    plot_por_raca_normalizado),
    "6": ("Casos por escolaridade",                plot_por_escolaridade_normalizado),
    "7": ("Desfecho dos casos (gráfico de pizza)", plot_evolucao),
    "8": ("Tipo de acidente por ano",              plot_tipo_acidente),
    "9": ("Top 20 CIDs de lesão",                  plot_top_cid_lesao),
    "h": ("Heatmap UF × Ano",                      plot_heatmap_uf_ano),
    "r": ("Resumo estatístico no terminal",        resumo),
}


def main():
    print("\nCarregando dados do SINAN — Acidente de Trabalho...")
    df = carregar_dados()
    print(f"  {len(df):,} registros carregados de {df['ANO'].min()}–{df['ANO'].max()}.")

    while True:
        print("\n──────── MENU ────────────────────────────────")
        for chave, (descricao, _) in MENU.items():
            print(f"  [{chave}] {descricao}")
        print("  [q] Sair")
        print("──────────────────────────────────────────────")
        opcao = input("Opção: ").strip().lower()

        if opcao == "q":
            break
        elif opcao in MENU:
            _, func = MENU[opcao]
            func(df)
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
