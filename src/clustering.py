import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from loader import carregar_dados
from preprocess import (
    preparar_para_clustering,
    FEATURES_NOMINAIS,
    FEATURES_ORDINAIS,
)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 110})

_FEATURES_PLOT = [
    "SEXO_LABEL",
    "RACA_LABEL",
    "FAIXA_ETARIA",
    "ESCOL_AGR",
    "TIPO_LABEL",
    "EVOL_LABEL",
]


# ── Análise do número de clusters ───────────────────────────────────────────

def plot_cotovelo(X: np.ndarray, k_min: int = 2, k_max: int = 12) -> None:
    """Método do cotovelo (inércia) + coeficiente de silhueta lado a lado."""
    inercias: list[float] = []
    silhuetas: list[float] = []
    ks = range(k_min, k_max + 1)

    print("  Calculando inércia e silhueta para cada k (pode levar alguns minutos)...")
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        rotulos = km.fit_predict(X)
        inercias.append(km.inertia_)
        sil = silhouette_score(X, rotulos, sample_size=min(10_000, len(X)), random_state=42)
        silhuetas.append(sil)
        print(f"    k={k:2d}  inércia={km.inertia_:>14,.0f}  silhueta={sil:.4f}")

    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(list(ks), inercias, marker="o", color="steelblue")
    ax1.set_title("Método do Cotovelo (Inércia / WCSS)")
    ax1.set_xlabel("Número de clusters (k)")
    ax1.set_ylabel("Inércia")
    ax1.xaxis.set_major_locator(mticker.MultipleLocator(1))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax2.plot(list(ks), silhuetas, marker="s", color="darkorange")
    ax2.set_title("Coeficiente de Silhueta")
    ax2.set_xlabel("Número de clusters (k)")
    ax2.set_ylabel("Silhueta média")
    ax2.xaxis.set_major_locator(mticker.MultipleLocator(1))

    plt.suptitle("Escolha do número de clusters K", fontsize=13)
    plt.tight_layout()
    plt.show()


# ── Ajuste do modelo ─────────────────────────────────────────────────────────

def ajustar_kmeans(X: np.ndarray, k: int, random_state: int = 42) -> KMeans:
    km = KMeans(n_clusters=k, random_state=random_state, n_init=20)
    km.fit(X)
    return km


# ── Perfil dos clusters ──────────────────────────────────────────────────────

def perfil_clusters(df: pd.DataFrame, rotulos: np.ndarray) -> pd.DataFrame:
    """
    Calcula o perfil de cada cluster (moda de cada feature) e imprime
    um resumo formatado no terminal.

    Retorna um DataFrame com uma linha por cluster.
    """
    df = df.copy()
    df["CLUSTER"] = rotulos

    todas = FEATURES_NOMINAIS + list(FEATURES_ORDINAIS.keys())

    agg = {col: lambda s: s.mode().iloc[0] for col in todas}
    agg["_n"] = "size"

    perfil = df.groupby("CLUSTER").agg(**{
        col: pd.NamedAgg(column=col, aggfunc=lambda s: s.mode().iloc[0])
        for col in todas
    })
    perfil["Tamanho"] = df.groupby("CLUSTER").size()
    perfil["% Total"] = (perfil["Tamanho"] / len(df) * 100).round(1)

    print("\n" + "=" * 80)
    print("  PERFIL DOS CLUSTERS — moda de cada feature")
    print("=" * 80)
    print(perfil.to_string())
    print("=" * 80 + "\n")

    return perfil


# ── Visualizações ────────────────────────────────────────────────────────────

def plot_pca(X: np.ndarray, rotulos: np.ndarray) -> None:
    """Scatter 2-D pela projeção PCA, colorido por cluster."""
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    var = pca.explained_variance_ratio_ * 100

    df_pca = pd.DataFrame({
        "PC1": coords[:, 0],
        "PC2": coords[:, 1],
        "Cluster": rotulos.astype(str),
    })

    _, ax = plt.subplots(figsize=(10, 7))
    sns.scatterplot(
        data=df_pca, x="PC1", y="PC2", hue="Cluster",
        palette="tab10", alpha=0.35, s=12, linewidth=0, ax=ax,
    )
    ax.set_title(
        f"Clusters K-Means — PCA 2D\n"
        f"(variância explicada: PC1 {var[0]:.1f}% · PC2 {var[1]:.1f}%)"
    )
    ax.set_xlabel(f"PC1 ({var[0]:.1f}%)")
    ax.set_ylabel(f"PC2 ({var[1]:.1f}%)")
    plt.tight_layout()
    plt.show()


def plot_distribuicao_clusters(df: pd.DataFrame, rotulos: np.ndarray) -> None:
    """Mostra um gráfico por vez para cada cluster."""
    df = df.copy()
    df["CLUSTER"] = rotulos.astype(int)
    n_clusters = int(np.unique(rotulos).size)

    palette = sns.color_palette("tab10", len(_FEATURES_PLOT))

    for cid in range(n_clusters):
        sub = df[df["CLUSTER"] == cid]
        n_total = len(sub)

        n_category_rows = (
            sum(sub[f].nunique() for f in _FEATURES_PLOT)
            + len(_FEATURES_PLOT)
        )
        fig_height = max(8, n_category_rows * 0.4)

        _, ax = plt.subplots(figsize=(10, fig_height))

        bar_positions, bar_values, bar_colors = [], [], []
        tick_positions, tick_labels = [], []
        y = 0

        for fi, feat in enumerate(_FEATURES_PLOT):
            feat_title = feat.replace("_LABEL", "").replace("_", " ").upper()
            cats = (
                sub[feat]
                .value_counts(normalize=True)
                .sort_values(ascending=False)
                * 100
            )

            tick_positions.append(y)
            tick_labels.append(feat_title)
            y += 1

            for cat, pct in cats.items():
                bar_positions.append(y)
                bar_values.append(pct)
                bar_colors.append(palette[fi])

                tick_positions.append(y)
                tick_labels.append(f"  {cat}")
                y += 1

            y += 0.5

        ax.barh(bar_positions, bar_values, color=bar_colors, height=0.7)
        ax.set_yticks(tick_positions)
        ax.set_yticklabels(tick_labels, fontsize=8)
        ax.set_xlabel("% no cluster")
        ax.set_title(f"Cluster {cid} (n={n_total:,})")
        ax.set_xlim(0, 110)
        ax.invert_yaxis()

        for p, v in zip(bar_positions, bar_values):
            ax.text(v + 0.5, p, f"{v:.1f}%", va="center", fontsize=7)

        for tick, label in zip(ax.get_yticklabels(), tick_labels):
            if not label.startswith("  "):
                tick.set_fontweight("bold")

        plt.tight_layout()
        plt.show()
        input(f"Pressione Enter para visualizar o próximo cluster ({cid+1}/{n_clusters})...")


def plot_tamanho_clusters(rotulos: np.ndarray) -> None:
    """Barras com tamanho absoluto e relativo de cada cluster."""
    serie = pd.Series(rotulos).value_counts().sort_index()
    pct = (serie / serie.sum() * 100).round(1)

    _, ax = plt.subplots(figsize=(max(6, len(serie) * 1.2), 5))
    bars = ax.bar(serie.index.astype(str), serie.values, color=sns.color_palette("tab10", len(serie)))
    ax.bar_label(bars, labels=[f"{v:,}\n({pct[i]:.1f}%)" for i, v in zip(serie.index, serie.values)],
                 padding=4, fontsize=9)
    ax.set_title("Tamanho dos Clusters")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Número de registros")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()
    plt.show()


# ── Menu interativo ──────────────────────────────────────────────────────────

def menu_clustering(df: pd.DataFrame) -> None:
    """Pipeline interativo de clusterização K-Means."""
    print("\n  Estratégia de imputação de ausentes/ignorados:")
    print("  [1] Moda por feature  (SimpleImputer — rápido)")
    print("  [2] Regressão iterativa  (IterativeImputer/BayesianRidge — mais lento)")
    op_imp = input("  Escolha [1]: ").strip() or "1"
    estrategia = "preditiva" if op_imp == "2" else "moda"

    print(f"\nPré-processando dados para clusterização (estratégia: {estrategia})...")
    df_limpo, X, _, _ = preparar_para_clustering(df, estrategia=estrategia)

    rotulos_atual: np.ndarray | None = None
    k_atual: int | None = None

    while True:
        print("\n──────── MENU — CLUSTERIZAÇÃO K-MEANS ─────────────────────────")
        print("  [1] Método do cotovelo + silhueta  (escolher k ideal)")
        print("  [2] Ajustar K-Means com k escolhido")
        if rotulos_atual is not None:
            print(f"  [3] Perfil dos clusters  (k={k_atual} atual)")
            print(f"  [4] Visualização PCA 2D  (k={k_atual} atual)")
            print(f"  [5] Distribuição por feature  (k={k_atual} atual)")
            print(f"  [6] Tamanho dos clusters  (k={k_atual} atual)")
        print("  [q] Voltar")
        print("────────────────────────────────────────────────────────────────")
        op = input("Opção: ").strip().lower()

        if op == "q":
            break

        elif op == "1":
            try:
                k_max = int(input("  k máximo a testar [padrão 12]: ").strip() or "12")
            except ValueError:
                k_max = 12
            plot_cotovelo(X, k_max=k_max)

        elif op == "2":
            try:
                k = int(input("  Informe o número de clusters (k): ").strip())
                if k < 2:
                    raise ValueError
            except ValueError:
                print("  Valor inválido — informe um inteiro ≥ 2.")
                continue

            print(f"\n  Ajustando K-Means com k={k}...")
            km = ajustar_kmeans(X, k)
            rotulos_atual = km.labels_
            k_atual = k

            sil = silhouette_score(
                X, rotulos_atual,
                sample_size=min(10_000, len(X)),
                random_state=42,
            )
            print(f"  Inércia  : {km.inertia_:,.0f}")
            print(f"  Silhueta : {sil:.4f}")
            print("  Use as opções [3]–[6] para explorar os clusters.")

        elif op == "3" and rotulos_atual is not None:
            perfil_clusters(df_limpo, rotulos_atual)

        elif op == "4" and rotulos_atual is not None:
            plot_pca(X, rotulos_atual)

        elif op == "5" and rotulos_atual is not None:
            plot_distribuicao_clusters(df_limpo, rotulos_atual)

        elif op == "6" and rotulos_atual is not None:
            plot_tamanho_clusters(rotulos_atual)

        else:
            print("  Opção inválida ou nenhum modelo ajustado ainda.")


if __name__ == "__main__":
    print("\nCarregando dados...")
    df = carregar_dados()
    menu_clustering(df)
