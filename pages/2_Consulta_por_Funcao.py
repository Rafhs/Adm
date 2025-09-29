import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import numpy as np
from st_copy_button import st_copy_button

st.set_page_config(layout="wide")

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
def carregar_dados_planilha(nome_planilha, nome_aba):
    if gc is None: return pd.DataFrame()
    try:
        spreadsheet = gc.open("Controle de Exames Ocupacionais")
        worksheet = spreadsheet.worksheet(nome_aba)
        df = pd.DataFrame(worksheet.get_all_records())
        for col in ['Matrícula', 'CPF', 'CNPJ']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar a aba '{nome_aba}': {e}")
        return pd.DataFrame()
def processar_vencimentos(df):
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
    cpf_limpo = "".join(filter(str.isdigit, str(cpf_str)))
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf_str
def limpar_texto_gerado():
    if 'texto_gerado' in st.session_state:
        del st.session_state['texto_gerado']

# CONSTRUÇÃO DA PÁGINA
st.title("📋 Consulta de Exames por Função")
st.sidebar.header("Controles")
if st.sidebar.button("🔄 Atualizar Dados"):
    limpar_texto_gerado()
    st.cache_data.clear()
    st.toast("Dados atualizados!", icon="✅")

df_funcoes_exames = carregar_dados_planilha("Controle de Exames Ocupacionais", "FuncaoExames")
df_funcionarios_bruto = carregar_dados_planilha("Controle de Exames Ocupacionais", "Dados")

if not df_funcionarios_bruto.empty:
    df_funcionarios = processar_vencimentos(df_funcionarios_bruto)
    vencidos_df = df_funcionarios[df_funcionarios['Status'] == "🔴 Vencido"]
    vence_em_breve_df = df_funcionarios[df_funcionarios['Status'] == "🟡 Vence em Breve"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Exames Vencidos")
        with st.container(border=True, height=200):
            if not vencidos_df.empty:
                for index, row in vencidos_df.iterrows():
                    st.markdown(f"- {row['Nome do Funcionário']} *(Cargo: {row['Cargo']})*")
            else:
                st.info("Nenhum funcionário com exames vencidos.")
    with col2:
        st.subheader("Vencem em Breve")
        with st.container(border=True, height=200):
            if not vence_em_breve_df.empty:
                for index, row in vence_em_breve_df.iterrows():
                    st.markdown(f"- {row['Nome do Funcionário']} *(Cargo: {row['Cargo']})*")
            else:
                st.info("Nenhum funcionário com exames vencendo em breve.")

if df_funcoes_exames.empty or df_funcionarios_bruto.empty:
    st.warning("Não foi possível carregar os dados de configuração ou dos funcionários.")
else:
    st.divider()
    col_filtro, col_exames, col_funcionarios = st.columns(3, gap="large")
    with col_filtro:
        st.subheader("Análise e Ação")
        st.info("A lista mostra apenas funções com pendências.")
        funcoes_com_vencidos = sorted(df_funcionarios[df_funcionarios['Status'] == '🔴 Vencido']['Cargo'].unique())
        if funcoes_com_vencidos:
            funcao_selecionada = st.selectbox(
                "Selecione a Função:",
                options=funcoes_com_vencidos,
                on_change=limpar_texto_gerado
            )
        else:
            st.success("🎉 Nenhuma função com pendências.")
            funcao_selecionada = None

    if funcao_selecionada:
        exames_obrigatorios = []
        linha_funcao = df_funcoes_exames[df_funcoes_exames['Função'] == funcao_selecionada]
        if not linha_funcao.empty:
            string_de_exames = linha_funcao['Exames Obrigatórios'].iloc[0]
            if pd.notna(string_de_exames) and string_de_exames:
                exames_obrigatorios = [exame.strip() for exame in string_de_exames.split(',')]

        funcionarios_vencidos_na_funcao = df_funcionarios[
            (df_funcionarios['Cargo'] == funcao_selecionada) &
            (df_funcionarios['Status'] == '🔴 Vencido')
            ].drop_duplicates(subset=['Nome do Funcionário'])

        with col_exames:
            st.subheader(f"Exames para: {funcao_selecionada}")
            with st.container(border=True, height=300):
                if exames_obrigatorios:
                    for exame in exames_obrigatorios:
                        st.markdown(f"- {exame}")
                else:
                    st.info(f"Nenhum exame obrigatório cadastrado.")

        with col_funcionarios:
            st.subheader("Funcionários Pendentes")
            with st.container(border=True, height=300):
                if not funcionarios_vencidos_na_funcao.empty:
                    for _, funcionario in funcionarios_vencidos_na_funcao.iterrows():
                        nome = funcionario['Nome do Funcionário']
                        st.markdown(f"🔴 {nome}")
                else:
                    st.info(f"Nenhum funcionário com status 'Vencido' neste cargo.")

        st.divider()
        st.subheader("Gerar Autorização em Massa")

        if st.button("Gerar Texto para Todos os Funcionários"):
            if not funcionarios_vencidos_na_funcao.empty:
                primeiro_funcionario = funcionarios_vencidos_na_funcao.iloc[0]

                empresa_func = primeiro_funcionario.get('Empresa', 'não informada').title()
                area_func = primeiro_funcionario.get('Area', 'não informada').title()
                funcao_formatada = funcao_selecionada.title()

                cnpj_func = primeiro_funcionario.get('CNPJ', 'não informado')
                tipo_exame_generico = "Periódico"

                lista_funcionarios_str = []
                for _, funcionario in funcionarios_vencidos_na_funcao.iterrows():
                    nome_func = funcionario.get('Nome do Funcionário', 'não informado').title()
                    cpf_func = funcionario.get('CPF', 'não informado')
                    cpf_formatado = formatar_cpf(cpf_func)
                    lista_funcionarios_str.append(f"- Nome: {nome_func} - CPF: {cpf_formatado}")

                funcionarios_formatados = "\n".join(lista_funcionarios_str)
                bateria_exames_str = "\n".join([f"- {exame}" for exame in exames_obrigatorios])

                texto_final = f"""Autorizamos os funcionários abaixo a realizar exame {tipo_exame_generico}.

Empresa: {empresa_func} - CNPJ: {cnpj_func} - Área: {area_func}

{funcionarios_formatados}

Função: {funcao_formatada}

Seguir bateria de exames conforme PCMSO:
{bateria_exames_str}
"""
                st.session_state['texto_gerado'] = texto_final
            else:
                st.warning("Não há funcionários com pendências para gerar autorização.")

        if 'texto_gerado' in st.session_state:
            st.text_area("Texto da Autorização:", value=st.session_state['texto_gerado'], height=400)
            st_copy_button(st.session_state['texto_gerado'], "Copiar Texto da Autorização")

    else:
        pass