import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2024")

# 1) Ler sem cabeçalho
df_raw = pd.read_excel("Casos dengue - Fortaleza.xlsx", header=None)

def encontrar_linha_cabecalho(df):
    # Procura linha que contenha 'bairro'
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

idx_header = encontrar_linha_cabecalho(df_raw)
if idx_header is None:
    st.error("Não foi possível identificar o cabeçalho com 'bairro' na planilha.")
    st.stop()

# 2) Cabeçalho e dados
header_row = df_raw.iloc[idx_header].astype(str).str.strip()
df = df_raw.iloc[idx_header + 1:].copy()
df.columns = header_row.tolist()

# Substituir colunas NaN por nomes de incidência (quando vierem como NaN, NaN.1 etc.)
df.rename(columns={
    "NaN": "DENGUE INCIDÊNCIA",
    "NaN.1": "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "NaN.2": "DENGUE GRAVE INCIDÊNCIA",
    "NaN.3": "ÓBITO INCIDÊNCIA"
}, inplace=True)

# 3) Remover UNNAMED e padronizar para maiúsculas
valid_cols = [c for c in df.columns if c is not None and not str(c).upper().startswith("UNNAMED")]
df = df[valid_cols]
df.columns = pd.Index([str(c).strip().upper() for c in df.columns])

# 4) Deduplicar nomes de colunas com sufixos .1, .2, ...
def dedupe_columns(cols):
    seen = {}
    new = []
    for c in cols:
        k = str(c)
        if k in seen:
            seen[k] += 1
            new.append(f"{k}.{seen[k]}")
        else:
            seen[k] = 0
            new.append(k)
    return new

df.columns = dedupe_columns(df.columns)

# 5) Mapear incidências duplicadas para nomes claros por grupo
df.rename(columns={
    "INCIDÊNCIA": "DENGUE INCIDÊNCIA",
    "INCIDÊNCIA.1": "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "INCIDÊNCIA.2": "DENGUE GRAVE INCIDÊNCIA",
    "INCIDÊNCIA.3": "ÓBITO INCIDÊNCIA",
    "ÓBITO": "ÓBITO TOTAL"  # se houver apenas 'ÓBITO' sem 'TOTAL'
}, inplace=True)

# 6) Garantir presença de BAIRRO e limpar linhas
if "BAIRRO" not in df.columns:
    st.error("A coluna 'BAIRRO' não foi encontrada após limpeza. Verifique o cabeçalho.")
    st.write("Colunas detectadas:", list(df.columns))
    st.stop()

df = df.dropna(subset=["BAIRRO"])
df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

# 7) Converter colunas numéricas com verificação segura
cols_numericas = [c for c in df.columns if c != "BAIRRO"]
for c in cols_numericas:
    if c in df.columns and isinstance(df[c], pd.Series):
        df[c] = pd.to_numeric(df[c], errors="coerce")

# 8) Exibir tabela organizada
st.subheader("Tabela organizada de casos por bairro")
st.dataframe(df)

# 9) Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", sorted(df["BAIRRO"].astype(str).unique()))
df_bairro = df[df["BAIRRO"].astype(str) == bairro]
st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# 10) Indicadores disponíveis (exclui BAIRRO)
indicadores_disponiveis = [c for c in df.columns if c != "BAIRRO"]
indicador = st.selectbox("Selecione o indicador para visualizar:", indicadores_disponiveis)

# 11) Tipo de gráfico
tipo_grafico = st.radio("Escolha o tipo de gráfico:", ("Barras", "Pizza"))

# 12) Gráficos
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