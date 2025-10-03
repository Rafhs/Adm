# pages/2_Consulta_por_Funcao.py

import streamlit as st
import pandas as pd
from st_copy_button import st_copy_button
import utils # Importa nosso arquivo de utilitários

# --- CONSTRUÇÃO DA PÁGINA ---
st.title("📋 Consulta de Exames por Função")

st.sidebar.header("Controles")
if st.sidebar.button("🔄 Atualizar Dados"):
    utils.limpar_texto_gerado()
    st.cache_data.clear()
    st.toast("Dados atualizados!", icon="✅")

# --- CARREGAMENTO E PROCESSAMENTO ---
df_funcoes_exames = utils.carregar_dados_planilha(utils.ABA_FUNCOES)
df_funcionarios_bruto = utils.carregar_dados_planilha(utils.ABA_DADOS)

if not df_funcionarios_bruto.empty:
    df_funcionarios = utils.processar_vencimentos(df_funcionarios_bruto)
    vencidos_df = df_funcionarios[df_funcionarios['Status'] == "🔴 Vencido"]
    vence_em_breve_df = df_funcionarios[df_funcionarios['Status'] == "🟡 Vence em Breve"]

    # --- CARDS DE ALERTA ---
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

    funcoes_com_vencidos = sorted(df_funcionarios[df_funcionarios['Status'] == '🔴 Vencido']['Cargo'].unique())

    # --- PAINEL DE ANÁLISE ---
    col_filtro, col_exames, col_funcionarios = st.columns(3, gap="large")

    with col_filtro:
        st.subheader("Análise e Ação")
        st.info("A lista mostra apenas funções com pendências.")
        if funcoes_com_vencidos:
            funcao_selecionada = st.selectbox(
                "Selecione a Função:",
                options=funcoes_com_vencidos,
                on_change=utils.limpar_texto_gerado
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
                        nome = funcionario.get('Nome do Funcionário', '').title()
                        st.markdown(f"🔴 {nome}")
                else:
                    st.info(f"Nenhum funcionário com status 'Vencido' neste cargo.")

        # --- SEÇÃO DE GERAR AUTORIZAÇÃO ---
        st.divider()
        st.subheader("Autorização em massa.")

        if st.button("Gerar Texto"):
            if not funcionarios_vencidos_na_funcao.empty:
                primeiro_funcionario = funcionarios_vencidos_na_funcao.iloc[0]
                empresa_func = primeiro_funcionario.get('Empresa', 'não informada').title()
                cnpj_func = primeiro_funcionario.get('CNPJ', 'não informado')
                area_func = primeiro_funcionario.get('Área', 'não informada').title()
                funcao_formatada = funcao_selecionada.title()
                tipo_exame_generico = "Periódico"

                lista_funcionarios_str = []
                for _, funcionario in funcionarios_vencidos_na_funcao.iterrows():
                    nome_func = funcionario.get('Nome do Funcionário', 'não informado').title()
                    cpf_func = funcionario.get('CPF', 'não informado')
                    cpf_formatado = utils.formatar_cpf(cpf_func)
                    lista_funcionarios_str.append(f"Nome: {nome_func} - CPF: {cpf_formatado}")

                funcionarios_formatados = "\n".join(lista_funcionarios_str)
                bateria_exames_str = "\n".join([f"- {exame.title()}" for exame in exames_obrigatorios])

                texto_final = f"""Autorizamos os funcionários abaixo a realizar exame {tipo_exame_generico}.

Empresa: {empresa_func} - CNPJ: {cnpj_func} 
Área: {area_func}

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