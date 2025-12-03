import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração do tema escuro
st.set_page_config(page_title="Casos de Dengue - Fortaleza", layout="wide")

# Título do painel
st.title("🦟 Casos de Dengue em Fortaleza - 2024")

# Carregar o arquivo Excel
df = pd.read_excel("Casos dengue - Fortaleza.xlsx")

# Padronizar nomes das colunas
df.columns = df.columns.str.strip().str.upper()

# Exibir os dados completos
st.subheader("Tabela completa de casos por bairro")
st.dataframe(df)

# Filtro por bairro
bairro = st.selectbox("Selecione o bairro:", df["BAIRRO"].unique())
df_bairro = df[df["BAIRRO"] == bairro]

# Exibir dados filtrados
st.subheader(f"Dados para o bairro: {bairro}")
st.dataframe(df_bairro)

# Escolha do indicador
indicador = st.selectbox(
    "Selecione o indicador para visualizar:",
    ("DENGUE", "INCIDÊNCIA", "ÓBITO", "LETALIDADE")
)

# Escolha do tipo de gráfico
tipo_grafico = st.radio(
    "Escolha o tipo de gráfico:",
    ("Barras", "Pizza")
)

# Gerar gráfico conforme escolha
if not df.empty:
    if tipo_grafico == "Barras":
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(df["BAIRRO"], df[indicador], color="orange")
        ax.set_ylabel(indicador)
        ax.set_xlabel("Bairros")
        ax.set_title(f"{indicador} por Bairro - Fortaleza")
        ax.tick_params(axis='x', labelrotation=90)
        st.pyplot(fig)

    elif tipo_grafico == "Pizza":
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts = ax.pie(
            df[indicador],
            startangle=90
        )
        ax.legend(
            wedges,
            df["BAIRRO"],
            title="Bairros",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        ax.set_title(f"Distribuição de {indicador} por Bairro - Fortaleza")
        st.pyplot(fig)
else:
    st.warning("Nenhum dado disponível.")