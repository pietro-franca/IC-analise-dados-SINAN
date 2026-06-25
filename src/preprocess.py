import hashlib
import json
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from loader import MAP_ESCOLARIDADE_AGREGADA

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")

# Categorias com separação por Ordem (ordinais)
ORDEM_FAIXA_ETARIA = ["<18", "18–24", "25–34", "35–44", "45–54", "55–64", "65+"]
ORDEM_ESCOLARIDADE = [
    "Analfabeto",
    "Fundamental incompleto",
    "Fundamental completo",
    "Médio incompleto",
    "Médio completo",
    "Superior incompleto",
    "Superior completo",
]

# Categorias nominais → one-hot encoded
FEATURES_NOMINAIS = [
    "SEXO_LABEL",
    "RACA_LABEL",
    "TIPO_LABEL",
    "LOCAL_LABEL",
    "SIT_LABEL",
    "EVOL_LABEL",
]

# Ordinal features → integer rank preserving order
FEATURES_ORDINAIS = {
    "FAIXA_ETARIA": ORDEM_FAIXA_ETARIA,
    "ESCOL_AGR":    ORDEM_ESCOLARIDADE,
}

_IGNORADOS = {"Ignorado", "Não se aplica"}
_ESTRATEGIAS_VALIDAS = {"moda", "preditiva"}


def _adicionar_escol_agr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ESCOL_AGR"] = df["ESCOL_LABEL"].map(MAP_ESCOLARIDADE_AGREGADA)
    return df


def _marcar_ausentes(df: pd.DataFrame) -> pd.DataFrame:
    """Substitui ignorados e NaN nativos por np.nan em todas as features de clusterização."""
    for col in FEATURES_ORDINAIS:
        s = df[col].astype(str)
        df[col] = s.mask(s.isin(_IGNORADOS | {"nan", "<NA>"}))
    for col in FEATURES_NOMINAIS:
        df[col] = df[col].mask(df[col].isin(_IGNORADOS))
    return df


def _imputar_moda(df: pd.DataFrame, todas_features: list) -> pd.DataFrame:
    imputer = SimpleImputer(strategy="most_frequent")
    df[todas_features] = imputer.fit_transform(df[todas_features])
    return df


def _imputar_preditiva(df: pd.DataFrame, todas_features: list) -> pd.DataFrame:
    """
    Imputa via IterativeImputer (BayesianRidge):
      1. Codifica todas as features categóricas → inteiros (OrdinalEncoder)
      2. Roda regressão iterativa para estimar cada ausente com base nas demais
      3. Arredonda ao inteiro válido mais próximo e decodifica de volta para strings
    """
    enc = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=np.nan,
        encoded_missing_value=np.nan,
    )
    X_enc = enc.fit_transform(df[todas_features])

    imputer = IterativeImputer(max_iter=10, random_state=42, verbose=1)
    X_imp = imputer.fit_transform(X_enc)

    # Arredonda e limita ao intervalo de categorias válidas
    n_cats = np.array([len(cats) for cats in enc.categories_])
    X_rounded = np.clip(np.round(X_imp), 0, n_cats - 1).astype(float)

    df[todas_features] = enc.inverse_transform(X_rounded)
    return df


def limpar(df: pd.DataFrame, estrategia: str = "moda") -> pd.DataFrame:
    """
    Imputa valores ausentes e "Ignorado" nas features de clusterização.

    estrategia
    ----------
    "moda"      : SimpleImputer(most_frequent) — preenche com o valor mais frequente
                  de cada feature, independentemente das demais. Rápido.
    "preditiva" : IterativeImputer + BayesianRidge — estima cada valor ausente
                  por regressão usando as outras features como preditoras, de forma
                  iterativa (MICE). Mais lento em datasets grandes, mas aproveita
                  correlações entre as features.
    """
    if estrategia not in _ESTRATEGIAS_VALIDAS:
        raise ValueError(f"estrategia deve ser uma de {_ESTRATEGIAS_VALIDAS!r}")

    df = _adicionar_escol_agr(df)
    todas_features = list(FEATURES_ORDINAIS.keys()) + FEATURES_NOMINAIS
    df = _marcar_ausentes(df)

    if estrategia == "moda":
        df = _imputar_moda(df, todas_features)
    else:
        df = _imputar_preditiva(df, todas_features)

    return df.reset_index(drop=True)


def encodar(df: pd.DataFrame):
    """
    Encoda as features para uso no K-Means:
      - Ordinais → rank inteiro (preserva ordem)
      - Nominais → one-hot

    Retorna
    -------
    X_scaled : np.ndarray, shape (n, p)
    feature_names : list[str]
    scaler : StandardScaler ajustado
    """
    partes = []
    nomes = []

    for col, ordem in FEATURES_ORDINAIS.items():
        rank_map = {cat: i for i, cat in enumerate(ordem)}
        valores = df[col].astype(str).map(rank_map).values.reshape(-1, 1)
        partes.append(valores)
        nomes.append(col)

    df_dummies = pd.get_dummies(df[FEATURES_NOMINAIS], drop_first=False)
    partes.append(df_dummies.values)
    nomes.extend(df_dummies.columns.tolist())

    X = np.hstack(partes).astype(float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, nomes, scaler


def _fingerprint(df: pd.DataFrame, estrategia: str) -> str:
    """SHA-1 do conteúdo bruto do DataFrame + estratégia → chave de cache de 10 chars."""
    data_hash = pd.util.hash_pandas_object(df, index=False).values
    return hashlib.sha1(data_hash.tobytes() + estrategia.encode()).hexdigest()[:10]


def _cache_paths(fp: str) -> dict[str, str]:
    return {
        "df":     os.path.join(_CACHE_DIR, f"{fp}_df.parquet"),
        "X":      os.path.join(_CACHE_DIR, f"{fp}_X.npy"),
        "nomes":  os.path.join(_CACHE_DIR, f"{fp}_nomes.json"),
        "scaler": os.path.join(_CACHE_DIR, f"{fp}_scaler.pkl"),
    }


def _salvar_cache(paths: dict, df_limpo: pd.DataFrame, X_scaled: np.ndarray,
                  nomes: list, scaler) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    df_limpo.to_parquet(paths["df"], index=False)
    np.save(paths["X"], X_scaled)
    with open(paths["nomes"], "w", encoding="utf-8") as f:
        json.dump(nomes, f)
    with open(paths["scaler"], "wb") as f:
        pickle.dump(scaler, f)


def _carregar_cache(paths: dict):
    df_limpo = pd.read_parquet(paths["df"])
    X_scaled = np.load(paths["X"])
    with open(paths["nomes"], encoding="utf-8") as f:
        nomes = json.load(f)
    with open(paths["scaler"], "rb") as f:
        scaler = pickle.load(f)
    return df_limpo, X_scaled, nomes, scaler


def preparar_para_clustering(df: pd.DataFrame, estrategia: str = "moda",
                             usar_cache: bool = True):
    """
    Pipeline completo: limpar → encodar → escalar.

    estrategia  : "moda" | "preditiva"
    usar_cache  : se True (padrão), salva/carrega resultado em cache/

    Retorna
    -------
    df_limpo   : pd.DataFrame  — linhas usadas, com ESCOL_AGR adicionada
    X_scaled   : np.ndarray    — matriz pronta para o K-Means
    nomes      : list[str]     — nomes das colunas de X_scaled
    scaler     : StandardScaler ajustado
    """
    if usar_cache:
        fp = _fingerprint(df, estrategia)
        paths = _cache_paths(fp)
        if all(os.path.exists(p) for p in paths.values()):
            print(f"  Cache encontrado [{fp}] — carregando dados pré-processados...")
            return _carregar_cache(paths)

    _desc = {
        "moda":      "moda por feature (SimpleImputer)",
        "preditiva": "regressão iterativa — BayesianRidge (IterativeImputer)",
    }
    df_limpo = limpar(df, estrategia=estrategia)
    print(
        f"  Registros processados: {len(df_limpo):,}  "
        f"(ausentes/ignorados imputados por {_desc[estrategia]})"
    )
    X_scaled, nomes, scaler = encodar(df_limpo)

    if usar_cache:
        print(f"  Salvando cache [{fp}]...")
        _salvar_cache(paths, df_limpo, X_scaled, nomes, scaler)

    return df_limpo, X_scaled, nomes, scaler
