# utils.py

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import numpy as np

# --- CONSTANTES DO PROJETO ---
NOME_PLANILHA = "Controle de Exames Ocupacionais"
ABA_DADOS = "Dados"
ABA_FUNCOES = "FuncaoExames"
COLUNAS_TEXTO = ['Matrícula', 'CPF', 'CNPJ']

# --- FUNÇÕES DE CONEXÃO E CACHE ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

@st.cache_resource(ttl=600)
def autenticar_google():
    """Autentica com a API do Google Sheets usando as credenciais."""
    try:
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"], scopes=SCOPES)
    except Exception:
        try:
            return gspread.service_account("credentials.json", scopes=SCOPES)
        except FileNotFoundError:
            st.error("Arquivo 'credentials.json' não encontrado.")
            return None

@st.cache_data(ttl=600)
def carregar_dados_planilha(nome_aba):
    """Carrega uma aba específica da planilha do Google Sheets."""
    gc = autenticar_google()
    if gc is None: return pd.DataFrame()
    try:
        spreadsheet = gc.open(NOME_PLANILHA)
        worksheet = spreadsheet.worksheet(nome_aba)
        df = pd.DataFrame(worksheet.get_all_records())
        for col in COLUNAS_TEXTO:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar a aba '{nome_aba}': {e}")
        return pd.DataFrame()

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---
def processar_vencimentos(df):
    """Calcula as datas de vencimento e os status dos exames."""
    if df.empty or 'Data do Último Exame' not in df.columns:
        return df

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

def formatar_cpf(cpf_str):
    """Aplica a máscara de formatação 000.000.000-00 a uma string de CPF."""
    cpf_limpo = "".join(filter(str.isdigit, str(cpf_str)))
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf_str

def limpar_texto_gerado():
    """Remove o texto de autorização da memória da sessão."""
    if 'texto_gerado' in st.session_state:
        del st.session_state['texto_gerado']