import streamlit as st

st.set_page_config(
    page_title="Gestão de Saúde Ocupacional",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 Sistema de Gestão de Saúde Ocupacional")

st.markdown("""
    ### Bem-vindo!

    Este é o sistema central para acompanhamento dos exames periódicos dos funcionários.

    **Utilize o menu na barra lateral para navegar entre as páginas:**

    - **Dashboard Principal:** Visualize o status geral dos exames, com filtros e métricas.
    - **Consulta por Função:** Analise as pendências de exames por cargo.
    ---
""")

st.info("⬅️ Selecione uma página na barra lateral para começar.")