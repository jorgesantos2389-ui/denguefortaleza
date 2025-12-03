import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

# Parser robusto para números BR (evita 5934 em vez de 59,34)
def parse_num_br(valor):
    if pd.isna(valor):
        return pd.NA
    s = str(valor).strip()

    # Remover símbolos comuns e manter apenas dígitos, . , -
    s = s.replace("%", "").replace("‰", "")
    s = re.sub(r"[^\d\.,\-]", "", s)

    # Decidir separador decimal conforme último símbolo
    if "." in s and "," in s:
        last_dot = s.rfind(".")
        last_comma = s.rfind(",")
        if last_comma > last_dot:
            # vírgula é decimal; ponto é milhar
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # ponto é decimal; vírgula é milhar
            s = s.replace(",", "")
    else:
        # Apenas vírgula => decimal
        if "," in s:
            s = s.replace(",", ".")
        # Apenas ponto => já decimal

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

    # Limpar colunas e padronizar nomes
    df = df.loc[:, ~df.columns.astype(str).str.upper().str.startswith("UNNAMED")]
    df.columns = df.columns.astype(str).str.strip().str.upper()

    # Mapear cabeçalhos
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

    # Remover linhas inválidas
    df = df.dropna(subset=["BAIRRO"])
    df = df[df["BAIRRO"].astype(str).str.upper() != "TOTAL"]

    # Converter colunas numéricas
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

# Consolidar
df = pd.concat([df_2022, df_2023, df_2024], ignore_index=True)

# Seleção múltipla de bairros e ano
bairros_selecionados = st.multiselect("Selecione o(s) bairro(s):", sorted(df["BAIRRO"].astype(str).unique()))
ano = st.selectbox("Selecione o ano:", sorted(df["ANO"].unique()))

# Toggle para mostrar/ocultar tabelas
mostrar_tabelas = st.checkbox("Mostrar tabelas", value=False)

# Filtragem
df_filtrado = df[(df["BAIRRO"].astype(str).isin(bairros_selecionados)) & (df["ANO"] == ano)]

# Formatação BR para exibição (sem alterar dados originais)
def formatar_br(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Exibir tabela se marcado
if mostrar_tabelas:
    df_exibir = df_filtrado.copy()
    if not df_exibir.empty:
        for c in ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES", "TAXA DE LETALIDADE"]:
            if c in df_exibir.columns:
                df_exibir[c] = df_exibir[c].apply(formatar_br)
        st.subheader(f"Dados para {', '.join(bairros_selecionados)} em {ano}")
        st.dataframe(df_exibir)
    else:
        st.info("Tabela vazia: selecione bairros e um ano com dados disponíveis.")

# Indicadores e visualizações
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
if not df.empty and indicador and len(bairros_selecionados) > 0:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(14, 6))
        base = df[(df["ANO"] == ano) & (df["BAIRRO"].astype(str).isin(bairros_selecionados))].copy()

        # Caso especial: INCIDÊNCIA TOTAL + DENGUE TOTAL lado a lado
        if indicador == "INCIDÊNCIA TOTAL" and "DENGUE TOTAL" in base.columns:
            dados_plot = base[["BAIRRO", "INCIDÊNCIA TOTAL", "DENGUE TOTAL"]].dropna()
            # Ordena por incidência
            dados_plot = dados_plot.sort_values("INCIDÊNCIA TOTAL", ascending=False)
            x_labels = dados_plot["BAIRRO"].astype(str).tolist()
            x = np.arange(len(x_labels))
            width = 0.4

            ax.bar(x - width/2, dados_plot["INCIDÊNCIA TOTAL"], width=width, label="Incidência", color="orange")
            ax.bar(x + width/2, dados_plot["DENGUE TOTAL"], width=width, label="Casos Totais", color="steelblue")

            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=90)
            ax.set_ylabel("Valor")
            ax.set_xlabel("Bairros")
            ax.set_title(f"Incidência e Casos Totais por Bairro - Fortaleza ({ano})")
            ax.legend()
            st.pyplot(fig)
        else:
            dados_plot = base[["BAIRRO", indicador]].dropna().sort_values(indicador, ascending=False)
            ax.bar(dados_plot["BAIRRO"], dados_plot[indicador], color="orange")
            ax.set_ylabel(indicador)
            ax.set_xlabel("Bairros")
            ax.set_title(f"{indicador} por Bairro - Fortaleza ({ano})")
            ax.tick_params(axis='x', labelrotation=90)
            st.pyplot(fig)
    else:
        base_evo = df[df["BAIRRO"].astype(str).isin(bairros_selecionados)].copy()

        # Caso especial: mostrar evolução de Incidência e Casos Totais em dois gráficos
        if indicador == "INCIDÊNCIA TOTAL" and "DENGUE TOTAL" in base_evo.columns:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            for bairro in bairros_selecionados:
                dados_bairro = base_evo[base_evo["BAIRRO"].astype(str) == bairro].sort_values("ANO")
                ax1.plot(dados_bairro["ANO"], dados_bairro["INCIDÊNCIA TOTAL"], marker="o", label=bairro)
                ax2.plot(dados_bairro["ANO"], dados_bairro["DENGUE TOTAL"], marker="o", label=bairro)
            ax1.set_ylabel("Incidência total")
            ax1.set_title("Evolução de Incidência total nos bairros selecionados")
            ax1.legend(loc="upper left", bbox_to_anchor=(1, 1))

            ax2.set_ylabel("Casos totais de dengue")
            ax2.set_xlabel("Ano")
            ax2.set_title("Evolução de Casos totais nos bairros selecionados")
            ax2.legend(loc="upper left", bbox_to_anchor=(1, 1))

            st.pyplot(fig)
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            dados_plot = base_evo[["ANO", "BAIRRO", indicador]].dropna()
            for bairro in bairros_selecionados:
                dados_bairro = dados_plot[dados_plot["BAIRRO"].astype(str) == bairro].sort_values("ANO")
                ax.plot(dados_bairro["ANO"], dados_bairro[indicador], marker="o", label=bairro)
            ax.set_ylabel(indicador)
            ax.set_xlabel("Ano")
            ax.set_title(f"Evolução de {indicador} nos bairros selecionados")
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
            st.pyplot(fig)
else:
    st.warning("Nenhum dado disponível para visualização. Selecione ao menos um bairro e um indicador.")