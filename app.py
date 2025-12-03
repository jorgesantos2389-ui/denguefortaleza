import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2022 a 2024")

def encontrar_linha_bairro(df):
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

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

    def to_num_br(series):
        s = series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        return pd.to_numeric(s, errors="coerce")

    for c in df.columns:
        if c != "BAIRRO":
            df[c] = to_num_br(df[c])

    df["ANO"] = ano
    return df

# Carregar os três anos
df_2022 = carregar_ano("Casos dengue - Fortaleza - 2022.xlsx", 2022)
df_2023 = carregar_ano("Casos dengue - Fortaleza - 2023.xlsx", 2023)
df_2024 = carregar_ano("Casos dengue - Fortaleza - 2024.xlsx", 2024)

df = pd.concat([df_2022, df_2023, df_2024], ignore_index=True)

# Filtro por múltiplos bairros e ano
bairros_selecionados = st.multiselect("Selecione o(s) bairro(s):", sorted(df["BAIRRO"].astype(str).unique()))
ano = st.selectbox("Selecione o ano:", sorted(df["ANO"].unique()))

# Toggle para mostrar/ocultar tabelas no site (dataframes continuam no código)
mostrar_tabelas = st.checkbox("Mostrar tabelas", value=False)

df_filtrado = df[(df["BAIRRO"].astype(str).isin(bairros_selecionados)) & (df["ANO"] == ano)]

if mostrar_tabelas:
    if not df_filtrado.empty:
        st.subheader(f"Dados para {', '.join(bairros_selecionados)} em {ano}")
        st.dataframe(df_filtrado)
    else:
        st.warning("Nenhum dado disponível para os bairros e ano selecionados.")

# Indicadores disponíveis
indicadores_disponiveis = [
    "DENGUE TOTAL",
    "INCIDÊNCIA TOTAL",
    "CASOS GRAVES TOTAIS",
    "INCIDÊNCIA DE CASOS GRAVES",
    "TOTAL DE ÓBITOS",
    "TAXA DE LETALIDADE",
]
indicadores_disponiveis = [c for c in indicadores_disponiveis if c in df.columns]

indicador = st.selectbox("Selecione o indicador para visualizar:", indicadores_disponiveis)
tipo_grafico = st.radio("Escolha o tipo de gráfico:", ("Barras", "Evolução por ano"))

# Gráficos
if not df.empty and indicador:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(14, 6))
        dados_plot = df[(df["ANO"] == ano) & (df["BAIRRO"].astype(str).isin(bairros_selecionados))][["BAIRRO", indicador]].dropna().sort_values(indicador, ascending=False)
        ax.bar(dados_plot["BAIRRO"], dados_plot[indicador], color="orange")
        ax.set_ylabel(indicador)
        ax.set_xlabel("Bairros")
        ax.set_title(f"{indicador} por Bairro - Fortaleza ({ano})")
        ax.tick_params(axis='x', labelrotation=90)
        st.pyplot(fig)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        dados_plot = df[df["BAIRRO"].astype(str).isin(bairros_selecionados)][["ANO", "BAIRRO", indicador]].dropna()
        for bairro in bairros_selecionados:
            dados_bairro = dados_plot[dados_plot["BAIRRO"] == bairro].sort_values("ANO")
            ax.plot(dados_bairro["ANO"], dados_bairro[indicador], marker="o", label=bairro)
        ax.set_ylabel(indicador)
        ax.set_xlabel("Ano")
        ax.set_title(f"Evolução de {indicador} nos bairros selecionados")
        ax.legend()
        st.pyplot(fig)
else:
    st.warning("Nenhum dado disponível para visualização.")