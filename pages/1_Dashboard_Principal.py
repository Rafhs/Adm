import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import numpy as np

st.sidebar.header("Controles")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.toast("Dados atualizados!", icon="✅")

st.sidebar.header("Filtros")

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

@st.cache_resource(ttl=600)
def autenticar_google():
    try:
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"], scopes=SCOPES)
    except Exception:
        try:
            return gspread.service_account("credentials.json", scopes=SCOPES)
        except FileNotFoundError:
            st.error("Arquivo 'credentials.json' não encontrado.")
            return None

gc = autenticar_google()

@st.cache_data(ttl=600)
def carregar_dados_dashboard():
    if gc is None: return pd.DataFrame()
    try:
        spreadsheet = gc.open("Controle de Exames Ocupacionais")
        worksheet = spreadsheet.worksheet("Dados")
        df = pd.DataFrame(worksheet.get_all_records())

        colunas_necessarias = ['Data do Último Exame', 'Empresa', 'Tipo de Exame']
        for col in colunas_necessarias:
            if col not in df.columns:
                st.error(f"ERRO: A coluna obrigatória '{col}' não foi encontrada na aba 'Dados'.")
                return pd.DataFrame()

        df.dropna(subset=['Data do Último Exame'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do dashboard: {e}")
        return pd.DataFrame()

def processar_vencimentos(df):
    if df.empty: return df
    df_proc = df.copy()
    df_proc['Data do Último Exame'] = pd.to_datetime(df_proc['Data do Último Exame'], format='%d/%m/%Y', errors='coerce')
    df_proc.dropna(subset=['Data do Último Exame'], inplace=True)

    hoje = pd.to_datetime(datetime.now().date())
    df_proc['Data de Vencimento'] = df_proc['Data do Último Exame'] + timedelta(days=365)
    condicoes = [
        (pd.to_datetime(df_proc['Data de Vencimento'].dt.date) < hoje),
        (pd.to_datetime(df_proc['Data de Vencimento'].dt.date) - timedelta(days=30) <= hoje)
    ]
    resultados = ["🔴 Vencido", "🟡 Vence em Breve"]
    df_proc['Status'] = np.select(condicoes, resultados, default="🟢 Em Dia")
    return df_proc

# CONSTRUÇÃO DA PÁGINA
st.title("📊 Dashboard")
st.markdown("Visão geral do status dos exames ocupacionais.")

df_bruto = carregar_dados_dashboard()

if not df_bruto.empty:
    df_processado = processar_vencimentos(df_bruto)

    st.header("Resumo Geral", divider='rainbow')
    status_counts = df_processado['Status'].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Exames Vencidos", status_counts.get("🔴 Vencido", 0))
    col2.metric("🟡 Vencem em Breve", status_counts.get("🟡 Vence em Breve", 0))
    col3.metric("🟢 Exames em Dia", status_counts.get("🟢 Em Dia", 0))

    opcoes_empresa = ["Todas"] + sorted(df_processado['Empresa'].unique())
    opcoes_tipo_exame = ["Todos"] + sorted(df_processado['Tipo'].unique())
    opcoes_status = ["Todos"] + ["🔴 Vencido", "🟡 Vence em Breve", "🟢 Em Dia"]

    selecao_empresa = st.sidebar.selectbox("Empresa:", options=opcoes_empresa)
    selecao_tipo_exame = st.sidebar.selectbox("Tipo de Exame:", options=opcoes_tipo_exame)
    selecao_status = st.sidebar.selectbox("Status:", options=opcoes_status)

    df_filtrado = df_processado.copy()
    if selecao_empresa != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == selecao_empresa]
    if selecao_tipo_exame != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Tipo de Exame'] == selecao_tipo_exame]
    if selecao_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Status'] == selecao_status]

    st.header("Situação")
    df_para_exibir = df_filtrado[[
        'Matrícula', 'Nome do Funcionário', 'Empresa', 'Cargo', 'Tipo de Exame',
        'Data do Último Exame', 'Data de Vencimento', 'Status'
    ]].copy()
    df_para_exibir['Data do Último Exame'] = df_para_exibir['Data do Último Exame'].dt.strftime('%d/%m/%Y')
    df_para_exibir['Data de Vencimento'] = df_para_exibir['Data de Vencimento'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_para_exibir, width='stretch', hide_index=True)

else:
    st.warning("Não foi possível carregar os dados para o dashboard.")