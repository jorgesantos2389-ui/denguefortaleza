import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2024")

# 1) Ler o Excel sem cabeçalho e localizar a linha do cabeçalho real (onde aparece 'bairro')
df_raw = pd.read_excel("Casos dengue - Fortaleza.xlsx", header=None)

def encontrar_linha_cabecalho(df):
    # Procura a primeira linha que contenha a palavra 'bairro' (case-insensitive)
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

idx_header = encontrar_linha_cabecalho(df_raw)
if idx_header is None:
    st.error("Não foi possível identificar o cabeçalho com 'bairro' na planilha.")
    st.stop()

# 2) Definir os nomes das colunas a partir da linha encontrada e pegar dados abaixo
cols = df_raw.iloc[idx_header].astype(str).str.strip()
df = df_raw.iloc[idx_header + 1:].copy()
df.columns = cols

# 3) Remover colunas não nomeadas e padronizar nomes
df = df.loc[:, ~df.columns.str.upper().str.startswith("UNNAMED")]
df.columns = df.columns.str.strip().str.upper()

# 4) Selecionar e renomear colunas relevantes (tornando nomes únicos e claros)
# Observação: sua planilha tem pares TOTAL/INCIDÊNCIA para DENGUE, ALERTA, GRAVE, além de ÓBITO TOTAL e LETALIDADE.
mapeamento = {
    "BAIRRO": "BAIRRO",
    "POPULAÇÃO": "POPULAÇÃO",
    "DENGUE": "DENGUE TOTAL",
    "DENGUE TOTAL": "DENGUE TOTAL",
    "DENGUE INCIDÊNCIA": "DENGUE INCIDÊNCIA",
    "INCIDÊNCIA": "DENGUE INCIDÊNCIA",  # quando a coluna geral vier com esse nome ao lado de DENGUE
    "DENGUE SINAL DE ALERTA": "DENGUE SINAL DE ALERTA TOTAL",
    "DENGUE SINAL DE ALERTA TOTAL": "DENGUE SINAL DE ALERTA TOTAL",
    "DENGUE SINAL DE ALERTA INCIDÊNCIA": "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "DENGUE GRAVE": "DENGUE GRAVE TOTAL",
    "DENGUE GRAVE TOTAL": "DENGUE GRAVE TOTAL",
    "DENGUE GRAVE INCIDÊNCIA": "DENGUE GRAVE INCIDÊNCIA",
    "ÓBITO": "ÓBITO TOTAL",
    "ÓBITO TOTAL": "ÓBITO TOTAL",
    "LETALIDADE": "LETALIDADE",
}

# Aplicar mapeamento para colunas existentes
colunas_renomeadas = {}
for c in df.columns:
    c_padrao = c.strip().upper()
    colunas_renomeadas[c] = mapeamento.get(c_padrao, c_padrao)  # mantém se não estiver no mapa

df.rename(columns=colunas_renomeadas, inplace=True)

# 5) Remover linhas nulas e a linha TOTAL (se existir)
if "BAIRRO" in df.columns:
    df = df.dropna(subset=["BAIRRO"])
    df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]
else:
    st.error("A coluna 'BAIRRO' não foi encontrada após limpeza. Verifique a planilha.")
    st.write("Colunas encontradas:", list(df.columns))
    st.stop()

# 6) Converter colunas numéricas
cols_numericas = [
    "POPULAÇÃO",
    "DENGUE TOTAL", "DENGUE INCIDÊNCIA",
    "DENGUE SINAL DE ALERTA TOTAL", "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "DENGUE GRAVE TOTAL", "DENGUE GRAVE INCIDÊNCIA",
    "ÓBITO TOTAL", "LETALIDADE"
]
for c in cols_numericas:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# 7) Exibir tabela organizada
st.subheader("Tabela organizada de casos por bairro")
st.dataframe(df)

# 8) Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", sorted(df["BAIRRO"].astype(str).unique()))
df_bairro = df[df["BAIRRO"].astype(str) == bairro]

st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# 9) Escolha do indicador (apenas entre os que existem de fato)
indicadores_disponiveis = [c for c in [
    "DENGUE TOTAL", "DENGUE INCIDÊNCIA",
    "DENGUE SINAL DE ALERTA TOTAL", "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "DENGUE GRAVE TOTAL", "DENGUE GRAVE INCIDÊNCIA",
    "ÓBITO TOTAL", "LETALIDADE"
] if c in df.columns]

indicador = st.selectbox("Selecione o indicador para visualizar:", indicadores_disponiveis)

# 10) Tipo de gráfico
tipo_grafico = st.radio("Escolha o tipo de gráfico:", ("Barras", "Pizza"))

# 11) Gráficos
if not df.empty and indicador:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(14, 6))
        # Ordena por indicador para leitura melhor
        dados_plot = df[["BAIRRO", indicador]].dropna().sort_values(indicador, ascending=False)
        ax.bar(dados_plot["BAIRRO"], dados_plot[indicador], color="orange")
        ax.set_ylabel(indicador)
        ax.set_xlabel("Bairros")
        ax.set_title(f"{indicador} por Bairro - Fortaleza")
        ax.tick_params(axis='x', labelrotation=90)
        st.pyplot(fig)

    elif tipo_grafico == "Pizza":
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