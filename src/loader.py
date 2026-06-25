import os
import glob
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "csvs", "acidente_de_trabalho")

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

COD_BOTUCATU = "350750"
POP_BOTUCATU = 144_200

POP_FAIXA_ETARIA_BOTUCATU = {
    "<18":   30_300,
    "18–24": 17_300,
    "25–34": 23_100,
    "35–44": 21_600,
    "45–54": 20_200,
    "55–64": 15_900,
    "65+":   15_800,
}

POP_RACA_BOTUCATU_PROP = {
    "Branca":   0.620,
    "Parda":    0.290,
    "Preta":    0.070,
    "Amarela":  0.015,
    "Indígena": 0.005,
}
POP_RACA_ABS_BOTUCATU = {k: v * POP_BOTUCATU for k, v in POP_RACA_BOTUCATU_PROP.items()}

POP_ESCOLARIDADE_BOTUCATU = {
    "Analfabeto":             0.03,
    "Fundamental incompleto": 0.20,
    "Fundamental completo":   0.07,
    "Médio incompleto":       0.09,
    "Médio completo":         0.35,
    "Superior incompleto":    0.09,
    "Superior completo":      0.17,
}

POP_ESCOLARIDADE = {
    "Analfabeto":             0.07,
    "Fundamental incompleto": 0.30,
    "Fundamental completo":   0.08,
    "Médio incompleto":       0.10,
    "Médio completo":         0.28,
    "Superior incompleto":    0.05,
    "Superior completo":      0.12,
}

MAP_ESCOLARIDADE_AGREGADA = {
    "Analfabeto":               "Analfabeto",
    "1ª a 4ª série incompleta": "Fundamental incompleto",
    "4ª série completa":        "Fundamental incompleto",
    "5ª a 8ª série incompleta": "Fundamental incompleto",
    "Fundamental completo":     "Fundamental completo",
    "Médio incompleto":         "Médio incompleto",
    "Médio completo":           "Médio completo",
    "Superior incompleto":      "Superior incompleto",
    "Superior completo":        "Superior completo",
}

CID_DESCRICOES = {
    "S61":  "Ferimento do punho/mão",
    "Y96":  "Circunstância relativa às condições de trabalho",
    "S610": "Ferimento de dedo sem dano à unha",
    "B342": "Infecção viral não especificada",
    "S626": "Fratura de outro dedo",
    "S619": "Ferimento não especificado do punho/mão",
    "T07":  "Traumatismos múltiplos",
    "S934": "Entorse/torção do tornozelo",
    "S60":  "Traumatismo superficial do punho/mão",
    "S62":  "Fratura do punho/mão",
}


def carregar_dados(anos=None) -> pd.DataFrame:
    """
    Lê todos os CSVs do diretório e retorna um DataFrame consolidado.

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

    dados["SEXO_LABEL"]  = dados["CS_SEXO"].map(SEXO).fillna("Ignorado")
    dados["RACA_LABEL"]  = dados["CS_RACA"].map(RACA).fillna("Ignorado")
    dados["ESCOL_LABEL"] = dados["CS_ESCOL_N"].map(ESCOLARIDADE).fillna("Ignorado")
    dados["EVOL_LABEL"]  = dados["EVOLUCAO"].map(EVOLUCAO).fillna("Ignorado")
    dados["TIPO_LABEL"]  = dados["TIPO_ACID"].map(TIPO_ACID).fillna("Ignorado")
    dados["LOCAL_LABEL"] = dados["LOCAL_ACID"].map(LOCAL_ACID).fillna("Ignorado")
    dados["SIT_LABEL"]   = dados["SIT_TRAB"].map(SIT_TRAB).fillna("Ignorado")
    dados["UF_LABEL"]    = dados["SG_UF_NOT"].map(UF_NOMES).fillna(dados["SG_UF_NOT"])

    return dados
