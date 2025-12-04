import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import re
import numpy as np

st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")
st.title("🦟 Casos de Dengue em Fortaleza - 2022 a 2024")

def encontrar_linha_bairro(df):
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.strip().str.upper()
        if any(cell == "BAIRRO" for cell in linha):
            return i
    return None

def parse_num_br(valor):
    if pd.isna(valor):
        return pd.NA
    s = str(valor).strip()
    s = s.replace("%", "").replace("‰", "")
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s:
        last_dot = s.rfind(".")
        last_comma = s.rfind(",")
        if last_comma > last_dot:
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        if "," in s:
            s = s.replace(",", ".")
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
        "DENGUE TOTAL": "CASOS DE DENGUE TOTAIS",
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

    for c in df.columns:
        if c != "BAIRRO":
            df[c] = df[c].apply(parse_num_br)

    colunas_incidencia = ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES", "TAXA DE LETALIDADE"]
    for c in colunas_incidencia:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)

    df["ANO"] = int(ano)
    return df

# Carregar os três anos
df_2022 = carregar_ano("Casos dengue - Fortaleza - 2022.xlsx", 2022)
df_2023 = carregar_ano("Casos dengue - Fortaleza - 2023.xlsx", 2023)
df_2024 = carregar_ano("Casos dengue - Fortaleza - 2024.xlsx", 2024)

# Consolidar e garantir anos corretos
df = pd.concat([df_2022, df_2023, df_2024], ignore_index=True)
df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce").astype("Int64").astype(int)
df = df[df["ANO"].isin([2022, 2023, 2024])]

# Seleção múltipla de bairros e ano (limitado a 10 bairros)
bairros_selecionados = st.multiselect(
    "Selecione até 10 bairros:",
    options=sorted(df["BAIRRO"].astype(str).unique()),
    max_selections=10
)
ano = st.selectbox("Selecione o ano:", sorted(df["ANO"].unique()))

# Toggle para mostrar/ocultar tabelas
mostrar_tabelas = st.checkbox("Mostrar tabelas", value=False)

# Filtragem
df_filtrado = df[(df["BAIRRO"].astype(str).isin(bairros_selecionados)) & (df["ANO"] == ano)]

def formatar_br_valor(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Exibir tabela se marcado
if mostrar_tabelas:
    df_exibir = df_filtrado.copy()
    if not df_exibir.empty:
        for c in ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES", "TAXA DE LETALIDADE"]:
            if c in df_exibir.columns:
                df_exibir[c] = df_exibir[c].apply(formatar_br_valor)
        if "ANO" in df_exibir.columns:
            df_exibir["ANO"] = df_exibir["ANO"].astype(int)
        st.subheader(f"Dados para {', '.join(bairros_selecionados)} em {ano}")
        st.dataframe(df_exibir)
    else:
        st.info("Tabela vazia: selecione bairros e um ano com dados disponíveis.")

# Indicadores e visualizações
indicadores_disponiveis = [
    "CASOS DE DENGUE TOTAIS",
    "INCIDÊNCIA TOTAL",
    "CASOS GRAVES TOTAIS",
    "INCIDÊNCIA DE CASOS GRAVES",
    "TOTAL DE ÓBITOS",
    "TAXA DE LETALIDADE",
]
indicadores_disponiveis = [c for c in indicadores_disponiveis if c in df.columns]

indicador = st.selectbox("Selecione o indicador para visualizar:", indicadores_disponiveis)
tipo_grafico = st.radio("Escolha o tipo de gráfico:", ("Barras", "Evolução por ano"))

# Formatter do eixo Y somente para os gráficos de incidência
def yformatter_br(x, pos):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def aplicar_formato_eixo_y(ax, indicador):
    if indicador in ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES"]:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(yformatter_br))
    else:
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

# Função para cores diferentes por bairro
def gerar_cores(n):
    cmap = plt.get_cmap("tab20")
    return [cmap(i % 20) for i in range(n)]

# Gráficos
if not df.empty and indicador and len(bairros_selecionados) > 0:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(14, 6))
        base = df[(df["ANO"] == ano) & (df["BAIRRO"].astype(str).isin(bairros_selecionados))].copy()
        dados_plot = base[["BAIRRO", indicador]].dropna().sort_values(indicador, ascending=False)

        bairros = dados_plot["BAIRRO"].astype(str).tolist()
        valores = dados_plot[indicador].tolist()
        cores = gerar_cores(len(bairros))

        ax.bar(bairros, valores, color=cores)
        ax.set_ylabel(indicador)
        ax.set_xlabel("Bairros")
        ax.set_title(f"{indicador} por Bairro - Fortaleza ({ano})")
        ax.tick_params(axis="x", labelrotation=45)
        aplicar_formato_eixo_y(ax, indicador)
        st.pyplot(fig)
    else:
        base_evo = df[df["BAIRRO"].astype(str).isin(bairros_selecionados)].copy()
        fig, ax = plt.subplots(figsize=(12, 6))
        dados_plot = base_evo[["ANO", "BAIRRO", indicador]].dropna()

        variacoes_totais = []

        for bairro in bairros_selecionados:
            dados_bairro = dados_plot[dados_plot["BAIRRO"].astype(str) == bairro].sort_values("ANO")
            ax.plot(dados_bairro["ANO"].astype(int), dados_bairro[indicador], marker="o", label=bairro)

            # calcular variação total entre 2022 e 2024
            valores = dados_bairro[indicador].values
            if len(valores) == 3:
            # calcular variação total entre 2022 e 2024
            valores = dados_bairro[indicador].values
            if len(valores) == 3:  # temos os três anos
                perc_total = ((valores[2] - valores[0]) / valores[0] * 100) if valores[0] != 0 else 0
                variacoes_totais.append(
                    f"{bairro}: Variação total 2022→2024 = {perc_total:.2f}%"
                )

        ax.set_xticks([2022, 2023, 2024])
        ax.set_ylabel(indicador)
        ax.set_xlabel("Ano")
        ax.set_title(f"Evolução de {indicador} nos bairros selecionados")
        aplicar_formato_eixo_y(ax, indicador)
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        st.pyplot(fig)

        # mostrar variação percentual total abaixo do gráfico
        if variacoes_totais:
            st.markdown("**Variação total entre 2022 e 2024:**")
            for texto in variacoes_totais:
                st.write(texto)
else:
    st.warning("Nenhum dado disponível para visualização. Selecione ao menos um bairro e um indicador.")

