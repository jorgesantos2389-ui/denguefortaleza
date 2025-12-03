import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2022 a 2024")

def encontrar_linha_bairro(df):
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

# Parser robusto para números em formato BR (evita 5934 em vez de 59,34)
def parse_num_br(valor):
    if pd.isna(valor):
        return pd.NA
    s = str(valor).strip()

    # Remover símbolos comuns
    s = s.replace("%", "").replace("‰", "")
    # Remover espaços e caracteres não-numéricos exceto . , -
    s = re.sub(r"[^\d\.,\-]", "", s)

    # Se tiver ambos . e , decidir o decimal pelo último símbolo que aparece
    if "." in s and "," in s:
        last_dot = s.rfind(".")
        last_comma = s.rfind(",")
        # O último símbolo é considerado decimal, o outro é milhar
        if last_comma > last_dot:
            # , é decimal; . é milhar
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # . é decimal; , é milhar
            s = s.replace(",", "")
            # s já tem . como decimal
    else:
        # Apenas vírgula: tratar como decimal
        if "," in s:
            s = s.replace(",", ".")
        # Apenas ponto: manter como decimal (nenhuma remoção)

    try:
        return float(s)
    except:
        return pd.NA

def carregar_ano(caminho, ano):
    df_raw = pd.read_excel(caminho, header=None)
    idx_header = encontrar_linha_bairro(df_raw)
    if idx_header is None:
        st.warning(f"Não foi possível identificar o cabeçalho no arquivo {caminho}")
        return pd.DataFrame()

    header = df_raw.iloc[idx_header].astype(str).str.strip()
    df = df_raw.iloc[idx_header + 1:].copy()
    df.columns = header

    df = df.loc[:, ~df.columns.astype(str).str.upper().str.startswith("UNNAMED")]
    df.columns = df.columns.astype(str).str.strip().str.upper()

    mapeamento = {
        "BAIRRO": "BAIRRO",
        "POPULAÇÃO": "POPULAÇÃO",
        "DENGUE TOTAL": "DENGUE TOTAL",
        "INCIDÊNCIA TOTAL": "INCIDÊNCIA TOTAL",
        "CASOS GRAVES TOTAIS": "CASOS GRAVES TOTAIS",
        "INCIDÊNCIA DE CASOS GRAVES": "INCIDÊNCIA DE CASOS GRAVES",
        "TOTAL DE ÓBITOS": "TOTAL DE ÓBITOS",
        "TAXA DE LETALIDADE": "TAXA DE LETALIDADE",
    }
    df.rename(columns=lambda c: mapeamento.get(c, c), inplace=True)

    if "BAIRRO" not in df.columns:
        st.warning(f"A coluna 'BAIRRO' não foi encontrada no arquivo {caminho}")
        return pd.DataFrame()

    df = df.dropna(subset=["BAIRRO"])
    df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

    # Converter colunas numéricas com parser robusto
    for c in df.columns:
        if c != "BAIRRO":
            df[c] = df[c].apply(parse_num_br)

    # Arredondar incidências para 2 casas decimais
    colunas_incidencia = ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES", "TAXA DE LETALIDADE"]
    for c in colunas_incidencia:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)

    df["ANO"] = ano
    return df

# Carregar os três anos
df_2022 = carregar_ano("Casos dengue - Fortaleza - 2022.xlsx", 2022)
df_2023 = carregar_ano("Casos dengue - Fortaleza - 2023.xlsx", 2023)
df_2024 = carregar_ano("Casos dengue - Fortaleza - 2024.xlsx", 2024)

df = pd.concat([df_2022, df_2023, df_2024], ignore_index=True)

# Seleção múltipla de bairros e ano
bairros_selecionados = st.multiselect("Selecione o(s) bairro(s):", sorted(df["BAIRRO"].astype(str).unique()))
ano = st.selectbox("Selecione o ano:", sorted(df["ANO"].unique()))

# Toggle para mostrar/ocultar tabelas no site (dataframes continuam no código)
mostrar_tabelas = st.checkbox("Mostrar tabelas", value=False)

df_filtrado = df[(df["BAIRRO"].astype(str).isin(bairros_selecionados)) & (df["ANO"] == ano)]

# Formatação BR para exibição (sem alterar os dados originais)
def formatar_br(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

if mostrar_tabelas:
    if not df_filtrado.empty:
        df_exibir = df_filtrado.copy()
       