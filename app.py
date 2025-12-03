import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2024")

# Ler sem cabeçalho
df_raw = pd.read_excel("Casos dengue - Fortaleza.xlsx", header=None)

# Encontrar linha com 'bairro' (cabeçalho principal)
def encontrar_linha_bairro(df):
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

idx_main = encontrar_linha_bairro(df_raw)
if idx_main is None:
    st.error("Não foi possível identificar a linha com 'bairro' no cabeçalho.")
    st.stop()

# A linha seguinte costuma ter as subcolunas (TOTAL, INCIDÊNCIA, LETALIDADE)
idx_sub = idx_main + 1
header_main = df_raw.iloc[idx_main].astype(str).str.strip()
header_sub = df_raw.iloc[idx_sub].astype(str).str.strip()

# Construir nomes compostos
col_names = []
for g, s in zip(header_main, header_sub):
    g_clean = str(g).strip().upper()
    s_clean = str(s).strip().upper()

    # Ignorar colunas vazias/UNNAMED
    if (g_clean == "" or g_clean.startswith("UNNAMED")) and (s_clean == "" or s_clean.startswith("UNNAMED")):
        col_names.append(None)
        continue

    # Colunas simples
    if g_clean in ["BAIRRO", "POPULAÇÃO"]:
        col_names.append(g_clean)
        continue

    # Casos especiais para ÓBITO/LETALIDADE que vêm em dois níveis
    if g_clean == "ÓBITO":
        # Subcolunas devem ser TOTAL (contagem de óbitos) e LETALIDADE (%)
        if s_clean == "TOTAL":
            col_names.append("ÓBITO TOTAL")
        elif s_clean == "LETALIDADE":
            col_names.append("LETALIDADE")
        else:
            # fallback
            col_names.append("ÓBITO TOTAL" if "TOTAL" in s_clean else "LETALIDADE" if "LETALIDADE" in s_clean else "ÓBITO TOTAL")
        continue

    # Grupos de dengue
    grupos_validos = [
        "DENGUE", "DENGUE SINAL DE ALERTA", "DENGUE GRAVE"
    ]
    if g_clean in grupos_validos:
        if s_clean in ["TOTAL", "INCIDÊNCIA"]:
            col_names.append(f"{g_clean} {s_clean}")
        else:
            # se subcoluna vier vazia, tenta inferir
            col_names.append(f"{g_clean} TOTAL")
        continue

    # Se não casou, mantém o grupo
    col_names.append(g_clean if g_clean else s_clean or None)

# Pegar os dados abaixo das duas linhas de cabeçalho
df = df_raw.iloc[idx_sub + 1:].copy()
df.columns = col_names

# Remover colunas None/UNNAMED e duplicadas
df = df.loc[:, [c for c in df.columns if c is not None and not str(c).upper().startswith("UNNAMED")]]
# Desduplicar nomes (se houver)
def dedupe(cols):
    seen = {}
    out = []
    for c in cols:
        k = str(c)
        if k in seen:
            seen[k] += 1
            out.append(f"{k}.{seen[k]}")
        else:
            seen[k] = 0
            out.append(k)
    return out
df.columns = dedupe(df.columns)

# Padronizar para maiúsculas
df.columns = pd.Index([str(c).strip().upper() for c in df.columns])

# Garantir colunas essenciais
essenciais = ["BAIRRO", "POPULAÇÃO", "DENGUE TOTAL", "DENGUE INCIDÊNCIA",
              "DENGUE SINAL DE ALERTA TOTAL", "DENGUE SINAL DE ALERTA INCIDÊNCIA",
              "DENGUE GRAVE TOTAL", "DENGUE GRAVE INCIDÊNCIA",
              "ÓBITO TOTAL", "LETALIDADE"]
# Mapear possíveis variações (ex.: INCIDÊNCIA.1 -> DENGUE SINAL DE ALERTA INCIDÊNCIA)
variacoes = {
    "INCIDÊNCIA": "DENGUE INCIDÊNCIA",
    "INCIDÊNCIA.1": "DENGUE SINAL DE ALERTA INCIDÊNCIA",
    "INCIDÊNCIA.2": "DENGUE GRAVE INCIDÊNCIA",
    "INCIDÊNCIA.3": "ÓBITO INCIDÊNCIA",
    "ÓBITO": "ÓBITO TOTAL"
}
df.rename(columns=variacoes, inplace=True)

# Limpar linhas nulas e TOTAL
if "BAIRRO" not in df.columns:
    st.error("A coluna 'BAIRRO' não foi encontrada após limpeza.")
    st.write("Colunas detectadas:", list(df.columns))
    st.stop()

df = df.dropna(subset=["BAIRRO"])
df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

# Converter números (tratar vírgula como decimal)
def to_num_safe(series):
    return pd.to_numeric(series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")

for c in df.columns:
    if c != "BAIRRO":
        if isinstance(df[c], pd.Series):
            df[c] = to_num_safe(df[c])

st.subheader("Tabela organizada de casos por bairro")
st.dataframe(df)

# Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", sorted(df["BAIRRO"].astype(str).unique()))
df_bairro = df[df["BAIRRO"].astype(str) == bairro]
st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# Indicadores disponíveis (apenas numéricos)
indicadores_disponiveis = [c for c in essenciais if c in df.columns and c != "BAIRRO"]
indicador = st.selectbox("Selecione o indicador para visualizar:", indicadores_disponiveis)

# Tipo de gráfico
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