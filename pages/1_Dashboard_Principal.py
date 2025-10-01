# pages/1_Dashboard_Principal.py

import streamlit as st
import utils # Importa nosso arquivo de utilitários

st.title("📊 Dashboard Principal")
st.markdown("Visão geral do status dos exames ocupacionais.")

# --- BARRA LATERAL ---
st.sidebar.header("Controles")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.toast("Dados atualizados!", icon="✅")

st.sidebar.header("Filtros")

# --- CARREGAMENTO E PROCESSAMENTO ---
df_bruto = utils.carregar_dados_planilha(utils.ABA_DADOS)

if not df_bruto.empty:
    df_processado = utils.processar_vencimentos(df_bruto)

    # --- MÉTRICAS DE RESUMO ---
    st.header("Resumo Geral", divider='rainbow')
    status_counts = df_processado['Status'].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Exames Vencidos", status_counts.get("🔴 Vencido", 0))
    col2.metric("🟡 Vencem em Breve", status_counts.get("🟡 Vence em Breve", 0))
    col3.metric("🟢 Exames em Dia", status_counts.get("🟢 Em Dia", 0))

    # --- FILTROS ---
    opcoes_empresa = ["Todas"] + sorted(df_processado['Empresa'].unique())
    opcoes_tipo_exame = ["Todos"] + sorted(df_processado['Tipo de Exame'].unique())
    opcoes_status = ["Todos"] + ["🔴 Vencido", "🟡 Vence em Breve", "🟢 Em Dia"]

    selecao_empresa = st.sidebar.selectbox("Empresa:", options=opcoes_empresa)
    selecao_tipo_exame = st.sidebar.selectbox("Tipo de Exame:", options=opcoes_tipo_exame)
    selecao_status = st.sidebar.selectbox("Status:", options=opcoes_status)

    # --- LÓGICA DE FILTRAGEM ---
    df_filtrado = df_processado.copy()
    if selecao_empresa != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == selecao_empresa]
    if selecao_tipo_exame != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Tipo de Exame'] == selecao_tipo_exame]
    if selecao_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Status'] == selecao_status]

    # --- TABELA DETALHADA ---
    st.header("Situação Detalhada")
    df_para_exibir = df_filtrado[[
        'Matrícula', 'Nome do Funcionário', 'Empresa', 'Cargo', 'Tipo de Exame',
        'Data do Último Exame', 'Data de Vencimento', 'Status'
    ]].copy()
    df_para_exibir['Data do Último Exame'] = df_para_exibir['Data do Último Exame'].dt.strftime('%d/%m/%Y')
    df_para_exibir['Data de Vencimento'] = df_para_exibir['Data de Vencimento'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_para_exibir, use_container_width=True, hide_index=True)
else:
    st.warning("Não foi possível carregar os dados para o dashboard.")