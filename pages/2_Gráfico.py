import streamlit as st
import pandas as pd 
import numpy as np
import base64
import plotly.express as px

# Função para converter imagem em base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Caminho da imagem local
image_path = "D:/JulioCesar/TJGO/tribunal-de-justica-do-estado-de-goias.png"

# Converter imagem para base64
image_base64 = get_image_base64(image_path)

# Criar título e depois a imagem
st.write(
    f"""
    <h5 style="display: flex; align-items: center;">
        Taxa de Congestionamento
        <img src="data:image/png;base64,{image_base64}" width="100" style="margin-left: 325px;">
    </h5>
    """,
    unsafe_allow_html=True
)


# Verificar se os dados estão disponíveis
if "df_processos" not in st.session_state:
    st.error("Erro: Os dados não foram carregados! Volte à página principal e faça o upload do CSV.")
    st.stop()

# Carregar os dados do session_state
df = st.session_state.df_processos


# Filtro de ano
anos_disponiveis = sorted(df['data_distribuicao'].dt.year.unique())
ano_selecionado = st.selectbox("Selecione o Ano", anos_disponiveis)

# Filtrar dados pelo ano
df_ano = df[df['data_distribuicao'].dt.year == ano_selecionado]

# Agrupar por nome_area_acao
estatisticas = df_ano.groupby('nome_area_acao').agg(
    Distribuídos=('data_distribuicao', 'count'),  # Quantidade de datas distribuídas
    ).reset_index()
        
# Calcular baixados no ano
baixados = df.dropna(subset=['data_baixa'])
baixados_no_ano = baixados[baixados['data_baixa'].dt.year == ano_selecionado]
baixados_por_area = baixados_no_ano.groupby('nome_area_acao')['processo_id'].nunique()
estatisticas['Baixados'] = estatisticas['nome_area_acao'].map(baixados_por_area).fillna(0).astype(int)
  
# Calcular pendentes
pendentes_por_area = df_ano[df_ano['data_baixa'].isna()].groupby('nome_area_acao').size()
estatisticas['Pendentes'] = estatisticas['nome_area_acao'].map(pendentes_por_area).fillna(0).astype(int)

# Calcular total de processos Baixados e Pendentes
estatisticas['Total Baixados'] = estatisticas['Baixados'].sum()
estatisticas['Total Pendentes'] = estatisticas['Pendentes'].sum()      

# Calcular taxa de congestionamento
estatisticas['Taxa de Congestionamento (%)'] = (
    (estatisticas['Total Pendentes'] / (estatisticas['Total Pendentes'] + estatisticas['Total Baixados'])) * 100
    ).round(2)



# Exibir indicadores
col1, col2, col3, col4 = st.columns(4)
col1.metric("Distribuídos", estatisticas["Distribuídos"].sum())
col2.metric("Baixados", estatisticas["Baixados"].sum())
col3.metric("Pendentes", estatisticas["Pendentes"].sum())
col4.metric("Taxa de Cong. (%)", round(estatisticas["Taxa de Congestionamento (%)"].mean(), 2))

# Criar gráfico de colunas
fig = px.bar(
    estatisticas,
    x="nome_area_acao",
    y=["Distribuídos", "Baixados", "Pendentes"],
    barmode="group",
    title=f"Distribuídos X Baixados X Pendentes - {ano_selecionado}",
    labels={"value": "Quantidade", "variable": "Tipo"}
)

# Exibir gráfico
st.plotly_chart(fig, use_container_width=True)



