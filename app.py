        for c in ["INCIDÊNCIA TOTAL", "INCIDÊNCIA DE CASOS GRAVES", "TAXA DE LETALIDADE"]:
            if c in df_exibir.columns:
                df_exibir[c] = df_exibir[c].apply(formatar_br)

        st.subheader(f"Dados para {', '.join(bairros_selecionados)} em {ano}")
        st.dataframe(df_exibir)
    else:
        st.info("Tabela vazia: selecione bairros e ano com dados disponíveis.")

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
            dados_bairro = dados