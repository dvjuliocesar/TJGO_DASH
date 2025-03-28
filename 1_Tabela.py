# Importanto Bibliotecas
import streamlit as st 
import pandas as pd 
import numpy as np
import base64

# Configuração da página
st.set_page_config(
    page_title="Dashboard TJGO",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Função para converter imagem em base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Caminho da imagem local
image_path = "D:/JulioCesar/TJGO/tribunal-de-justica-do-estado-de-goias.png"  

# Converter imagem para base64
image_base64 = get_image_base64(image_path)

# Título da página
st.write(
    f"""
    <h5 style="display: flex; align-items: center;">
        Análise de Processos por Área de Ação
        <img src="data:image/png;base64,{image_base64}" width="100" style="margin-left: 230px;">
    </h5>
    """,
    unsafe_allow_html=True
)

class ProcessosAnalisador:
    def __init__(self, arquivo_csv):
        """
        Inicializa o analisador de processos
        """
        self.df = self._carregar_dados(arquivo_csv)
    
    def _carregar_dados(self, arquivo_csv):
        """
        Carrega o arquivo CSV e realiza o pré-processamento dos dados
        """
        # Ler o CSV
        df = pd.read_csv(arquivo_csv)
        
        # Verificar o nome correto das colunas (pode haver diferenças de acentuação ou espaços)
        colunas = df.columns.tolist()
        
        # Encontrar as colunas de data corretamente
        coluna_distribuicao = [col for col in colunas if 'data_distribuicao' in col.lower()][0]
        coluna_baixa = [col for col in colunas if 'data_baixa' in col.lower()][0]
        coluna_area_acao = [col for col in colunas if 'nome_area_acao' in col.lower()][0]
        coluna_processo_id = [col for col in colunas if 'processo_id' in col.lower()][0]
        
        # Renomear colunas para garantir consistência
        df = df.rename(columns={
            coluna_distribuicao: 'data_distribuicao',
            coluna_baixa: 'data_baixa',
            coluna_area_acao: 'nome_area_acao',
            coluna_processo_id: 'processo_id'
        })
        
        # Converter colunas de data para datetime com tratamento de erros
        df['data_distribuicao'] = pd.to_datetime(df['data_distribuicao'], errors='coerce')
        df['data_baixa'] = pd.to_datetime(df['data_baixa'], errors='coerce')
        
        return df
    
    def obter_anos_disponiveis(self):
        """
        Retorna os anos disponíveis na coluna de data de distribuição
        """
        return sorted(self.df['data_distribuicao'].dt.year.unique())
    
    def calcular_estatisticas(self, ano_selecionado):
        """
        Calcula as estatísticas por área de ação para o ano selecionado
        """
        # Filtrar processos distribuídos no ano selecionado
        df_ano = self.df[self.df['data_distribuicao'].dt.year == ano_selecionado]
        
        # Agrupar por nome_area_acao
        estatisticas = df_ano.groupby('nome_area_acao').agg(
            Distribuídos=('data_distribuicao', 'count'),  # Quantidade de datas distribuídas
        ).reset_index()
        
        # Calcular baixados no ano
        baixados = self.df.dropna(subset=['data_baixa'])
        baixados_no_ano = baixados[baixados['data_baixa'].dt.year == ano_selecionado]
        baixados_por_area = baixados_no_ano.groupby('nome_area_acao')['processo_id'].nunique()
        estatisticas['Baixados'] = estatisticas['nome_area_acao'].map(baixados_por_area).fillna(0).astype(int)

        
        # Calcular pendentes
        pendentes_por_area = df_ano[df_ano['data_baixa'].isna()].groupby('nome_area_acao').size()
        estatisticas['Pendentes'] = estatisticas['nome_area_acao'].map(pendentes_por_area).fillna(0).astype(int)
        
        # Calcular taxa de congestionamento
        estatisticas['Taxa de Congestionamento (%)'] = (
            (estatisticas['Pendentes'] / (estatisticas['Pendentes'] + estatisticas['Baixados'])) * 100
        ).round(2)

        # Adicionar linha de totais
        totais = {
            'nome_area_acao': 'TOTAL',
            'Distribuídos': estatisticas['Distribuídos'].sum(),
            'Baixados': estatisticas['Baixados'].sum(),
            'Pendentes': estatisticas['Pendentes'].sum(),
        }

        # Evitar divisão por zero
        if (totais['Pendentes'] + totais['Baixados']) > 0:
            totais['Taxa de Congestionamento (%)'] = round(
                (totais['Pendentes'] / (totais['Pendentes'] + totais['Baixados'])) * 100, 2
            )
        else:
            totais['Taxa de Congestionamento (%)'] = 0.00

        # Adicionar a linha de totais ao DataFrame
        estatisticas = estatisticas.append(totais, ignore_index=True)
                
        return estatisticas

def main():
    
    # Upload do arquivo CSV
    arquivo_csv = st.file_uploader(
        'Carregue seu arquivo CSV', 
        type=['csv']
    )
    
    if arquivo_csv is not None:
        # Carregar dados
        try:
            
            # Se os dados ainda não foram carregados na sessão, processa o arquivo
            if "df_processos" not in st.session_state:
                st.session_state.analisador = ProcessosAnalisador(arquivo_csv)  # Salva o analisador na sessão
                st.session_state.df_processos = st.session_state.analisador.df  
            
            # Obtém os dados carregados
            analisador = st.session_state.analisador
            df = st.session_state.df_processos.copy()
            
            # Verificar se a conversão de datas funcionou
            if analisador.df['data_distribuicao'].dtype != 'datetime64[ns]':
                st.error('Não foi possível converter a coluna de data. Verifique o formato das datas no arquivo.')
                return
            
            # Extrair anos disponíveis
            anos_disponiveis = analisador.obter_anos_disponiveis()
            
            # Adicionar filtro de ano
            ano_selecionado = st.selectbox(
                'Selecione o Ano', 
                options=anos_disponiveis
            )
            
            # Calcular estatísticas
            estatisticas = analisador.calcular_estatisticas(ano_selecionado)
            
            # Exibir tabela
            st.dataframe(estatisticas)
            
            # Opção de download
            st.download_button(
                label='Baixar Estatísticas',
                data=estatisticas.to_csv(index=False),
                file_name=f'estatisticas_processos_{ano_selecionado}.csv',
                mime='text/csv'
            )
        
        except Exception as e:
            st.error(f'Erro ao processar o arquivo: {e}')
            st.error('Verifique se o arquivo CSV está no formato correto')
    
if __name__ == '__main__':
    main()







