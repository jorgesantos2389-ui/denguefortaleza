import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2024")

# Ler Excel sem cabeçalho para localizar a linha dos nomes
df_raw = pd.read_excel("Casos dengue - Fortaleza.xlsx", header=None)

def encontrar_linha_bairro(df):
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

idx_header = encontrar_linha_bairro(df_raw)
if idx_header is None:
    st.error("Não foi possível identificar o cabeçalho com 'BAIRRO' na planilha.")
    st.stop()

# Definir colunas a partir da linha de cabeçalho detectada
header = df_raw.iloc[idx_header].astype(str).str.strip()
df = df_raw.iloc[idx_header + 1:].copy()
df.columns = header

# Remover colunas UNNAMED e padronizar para maiúsculas
df = df.loc[:, ~df.columns.astype(str).str.upper().str.startswith("UNNAMED")]
df.columns = df.columns.astype(str).str.strip().str.upper()

# Mapear cabeçalhos para o padrão desejado (segundo sua imagem)
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

# Garantir que BAIRRO existe
if "BAIRRO" not in df.columns:
    st.error("A coluna 'BAIRRO' não foi encontrada após limpeza.")
    st.write("Colunas detectadas:", list(df.columns))
    st.stop()

# Remover linhas sem bairro e linha 'TOTAL' se existir
df = df.dropna(subset=["BAIRRO"])
df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

# Converter números tratando vírgula como decimal (BR)
def to_num_br(series):
    s = series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")

for c in df.columns:
    if c != "BAIRRO":
        df[c] = to_num_br(df[c])

st.subheader("Tabela organizada de casos por bairro")
st.dataframe(df)

# Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", sorted(df["BAIRRO"].astype(str).unique()))
df_bairro = df[df["BAIRRO"].astype(str) == bairro]
st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# Indicadores conforme os nomes da tabela fornecida
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
tipo_grafico = st.radio("Escolha o tipo de gráfico:", ("Barras", "Pizza"))

# Gráficos
if not df.empty and indicador:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(14, 6))
        dados_plot = df[["BAIRRO", indicador]].dropna().sort_values(indicador, ascending=False)
        ax.bar(dados_plot["BAIRRO"], dados_plot[indicador], color="orange")
        ax.set_ylabel(indicador)
        ax.set_xlabel("Bairros")
        ax.set_title(f"{indicador} por Bairro - Fortaleza")
        ax.tick_params(axis='x', labelrotation=90)
        st.pyplot(fig)
    else:
        fig, ax = plt.subplots(figsize=(10, 8))
        dados_plot = df[["BAIRRO", indicador]].dropna()
        wedges, _ = ax.pie(dados_plot[indicador], startangle=90)
        ax.legend(
            wedges,
            dados_plot["BAIRRO"],
            title="Bairros",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        ax.set_title(f"Distribuição de {indicador} por Bairro - Fortaleza")
        st.pyplot(fig)
else:
    st.warning("Nenhum dado disponível para plotagem.")