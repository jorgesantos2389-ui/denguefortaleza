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

# 2) Criar nomes únicos de colunas a partir do cabeçalho encontrado
header_row = df_raw.iloc[idx_header].astype(str).str.strip()

def construir_nomes_unicos(header_series):
    nomes = []
    contexto = None
    for raw in header_series:
        n = str(raw).strip().upper()

        # Ignorar vazios/UNNAMED
        if n == "" or n.startswith("UNNAMED"):
            nomes.append(None)
            continue

        # Atualizar contexto pelos grupos principais
        if "DENGUE SINAL DE ALERTA" in n:
            contexto = "DENGUE SINAL DE ALERTA"
        elif "DENGUE GRAVE" in n:
            contexto = "DENGUE GRAVE"
        elif n.startswith("DENGUE"):
            contexto = "DENGUE"
        elif n in ["BAIRRO", "POPULAÇÃO", "LETALIDADE", "ÓBITO TOTAL"]:
            contexto = None

        # Resolver nomes
        if n == "INCIDÊNCIA" and contexto:
            nomes.append(f"{contexto} INCIDÊNCIA")
        elif n.endswith("TOTAL") and contexto and n != "ÓBITO TOTAL":
            nomes.append(f"{contexto} TOTAL")
        else:
            nomes.append(n)

    # Garantir unicidade (se sobrar duplicados, adicionar sufixo)
    final = []
    contagem = {}
    for c in nomes:
        if c is None:
            final.append(None)
            continue
        contagem[c] = contagem.get(c, 0) + 1
        if contagem[c] > 1:
            final.append(f"{c}.{contagem[c]-1}")
        else:
            final.append(c)
    return final

colunas_unicas = construir_nomes_unicos(header_row)

# 3) Dados abaixo do cabeçalho
df = df_raw.iloc[idx_header + 1:].copy()
df.columns = colunas_unicas

# 4) Remover colunas None/UNNAMED e padronizar nomes
valid_cols = [c for c in df.columns if c is not None and not str(c).upper().startswith("UNNAMED")]
df = df[valid_cols]
df.columns = pd.Index([str(c).strip().upper() for c in df.columns])

# 5) Normalizar conjunto de colunas esperadas (mapeando variações)
mapeamento = {
    "BAIRRO": "BAIRRO",
    "POPULAÇÃO": "POPULAÇÃO",
    "DENGUE TOTAL": "DENGUE TOTAL",
    "DENGUE INCIDÊNCIA": "DENGUE INCIDÊNCIA",
    "DENGUE SINAL DE ALERTA TOTAL": "DENGUE SINAL DE ALERTA TOTAL",
    "DENGUE SINAL DE ALERTA INCIDÊNCIA": "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "DENGUE GRAVE TOTAL": "DENGUE GRAVE TOTAL",
    "DENGUE GRAVE INCIDÊNCIA": "DENGUE GRAVE INCIDÊNCIA",
    "ÓBITO TOTAL": "ÓBITO TOTAL",
    "LETALIDADE": "LETALIDADE",
}
df.rename(columns=lambda c: mapeamento.get(c, c), inplace=True)

# 6) Remover linhas nulas/TOTAL
if "BAIRRO" not in df.columns:
    st.error("A coluna 'BAIRRO' não foi encontrada após limpeza. Verifique o cabeçalho.")
    st.write("Colunas detectadas:", list(df.columns))
    st.stop()

df = df.dropna(subset=["BAIRRO"])
df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

# 7) Converter colunas numéricas
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

# 8) Exibir tabela organizada
st.subheader("Tabela organizada de casos por bairro")
st.dataframe(df)

# 9) Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", sorted(df["BAIRRO"].astype(str).unique()))
df_bairro = df[df["BAIRRO"].astype(str) == bairro]
st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# 10) Indicadores disponíveis (somente os presentes)
indicadores_disponiveis = [c for c in [
    "DENGUE TOTAL", "DENGUE INCIDÊNCIA",
    "DENGUE SINAL DE ALERTA TOTAL", "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "DENGUE GRAVE TOTAL", "DENGUE GRAVE INCIDÊNCIA",
    "ÓBITO TOTAL", "LETALIDADE"
] if c in df.columns]

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