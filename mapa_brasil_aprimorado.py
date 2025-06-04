# Importações necessárias
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from datetime import datetime
import random
import os # Adicionado para verificar existência do GeoJSON

# --- FUNÇÃO PARA CALCULAR VALOR MÉDIO ATACADO (mantida como antes) ---
def calcular_valor_medio_pedido_atacado(df):
    """
    Calcula o valor médio do pedido por estado para a categoria Atacado.
    
    Args:
        df: DataFrame completo.
        
    Returns:
        DataFrame: DataFrame com Estado, Valor Médio Pedido Atacado, Total Vendas Atacado, Total Pedidos Atacado.
    """
    COL_VALOR_PEDIDO_CUSTOS = 'VALOR DO PEDIDO'
    COL_QUANTIDADE_CUSTOS_ABA_CUSTOS = 'QUANTIDADE'
    COL_TIPO_VENDA = 'TIPO DE VENDA'
    COL_ESTADO = 'Estado' # Coluna com a SIGLA do estado (ex: SP, RJ)

    if df is None or df.empty or COL_TIPO_VENDA not in df.columns or COL_ESTADO not in df.columns:
        return pd.DataFrame(columns=[COL_ESTADO, 'Valor Médio Pedido Atacado', 'Total Vendas Atacado', 'Total Pedidos Atacado'])

    df_atacado = df[df[COL_TIPO_VENDA] == 'Atacado'].copy()

    if df_atacado.empty or COL_VALOR_PEDIDO_CUSTOS not in df_atacado.columns or COL_QUANTIDADE_CUSTOS_ABA_CUSTOS not in df_atacado.columns:
        return pd.DataFrame(columns=[COL_ESTADO, 'Valor Médio Pedido Atacado', 'Total Vendas Atacado', 'Total Pedidos Atacado'])

    # Garantir que as colunas são numéricas
    df_atacado[COL_VALOR_PEDIDO_CUSTOS] = pd.to_numeric(df_atacado[COL_VALOR_PEDIDO_CUSTOS], errors='coerce').fillna(0)
    
    # Agrupar por estado
    agg_atacado = df_atacado.groupby(COL_ESTADO).agg(
        Total_Vendas_Atacado=(COL_VALOR_PEDIDO_CUSTOS, 'sum'),
        Total_Pedidos_Atacado=(COL_ESTADO, 'size') # Contagem de linhas como aproximação de pedidos
    ).reset_index()

    # Calcular valor médio do pedido
    agg_atacado['Valor Médio Pedido Atacado'] = agg_atacado.apply(
        lambda row: row['Total_Vendas_Atacado'] / row['Total_Pedidos_Atacado'] if row['Total_Pedidos_Atacado'] > 0 else 0,
        axis=1
    )
    
    # Renomear colunas para clareza
    agg_atacado = agg_atacado.rename(columns={
        'Total_Vendas_Atacado': 'Total Vendas Atacado',
        'Total_Pedidos_Atacado': 'Total Pedidos Atacado'
    })

    return agg_atacado[[COL_ESTADO, 'Valor Médio Pedido Atacado', 'Total Vendas Atacado', 'Total Pedidos Atacado']]

# --- FUNÇÃO PRINCIPAL PARA CRIAR O MAPA (MODIFICADA PARA USAR GEOJSON) ---
def criar_mapa_brasil_interativo(df, df_atacado_medio=None, geojson_path="/home/ubuntu/upload/br_states.json"):
    """
    Cria um mapa Choropleth interativo do Brasil usando GeoJSON.
    Mostra vendas totais por estado e inclui valor médio de atacado no hover.
    
    Args:
        df: DataFrame com os dados de vendas gerais (deve ter 'Estado' e 'VALOR DO PEDIDO').
        df_atacado_medio: DataFrame com valor médio de pedido de atacado por estado (opcional, mas recomendado).
        geojson_path: Caminho para o arquivo GeoJSON dos estados.
        
    Returns:
        figura: Objeto de figura Plotly com o mapa Choropleth.
    """
    try:
        COL_VALOR_PEDIDO_CUSTOS = 'VALOR DO PEDIDO'
        COL_ESTADO = 'Estado' # Coluna com a SIGLA do estado (ex: SP, RJ)
        GEOJSON_ID_FIELD = 'id' # Campo no GeoJSON que contém a sigla do estado (ex: 'AC', 'SP')

        # Verificar se o arquivo GeoJSON existe
        if not os.path.exists(geojson_path):
            st.error(f"Arquivo GeoJSON não encontrado em: {geojson_path}")
            return None
            
        # Carregar GeoJSON
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # --- Preparar Dados para o Mapa ---
        if df is None or df.empty or COL_ESTADO not in df.columns or COL_VALOR_PEDIDO_CUSTOS not in df.columns:
            st.warning("Dados insuficientes para gerar o mapa (DataFrame principal vazio ou colunas faltando).")
            # Criar um DF vazio com as colunas esperadas para evitar erros no Plotly
            map_df = pd.DataFrame(columns=[COL_ESTADO, 'Vendas Totais', 'Valor Médio Pedido Atacado'])
        else:
            # 1. Calcular Vendas Totais por Estado
            vendas_por_estado = df.groupby(COL_ESTADO)[COL_VALOR_PEDIDO_CUSTOS].sum().reset_index()
            vendas_por_estado = vendas_por_estado.rename(columns={COL_VALOR_PEDIDO_CUSTOS: 'Vendas Totais'})
            
            # 2. Preparar DataFrame final para o mapa
            map_df = vendas_por_estado.copy()

            # 3. Adicionar Valor Médio de Atacado (se disponível)
            if df_atacado_medio is not None and not df_atacado_medio.empty and 'Valor Médio Pedido Atacado' in df_atacado_medio.columns:
                map_df = pd.merge(map_df, df_atacado_medio[[COL_ESTADO, 'Valor Médio Pedido Atacado']], on=COL_ESTADO, how='left')
            else:
                map_df['Valor Médio Pedido Atacado'] = 0 # Ou np.nan
            
            # Garantir que valores NA sejam 0 para exibição
            map_df['Valor Médio Pedido Atacado'] = map_df['Valor Médio Pedido Atacado'].fillna(0)
            map_df['Vendas Totais'] = map_df['Vendas Totais'].fillna(0)

        # Verificar se há dados após o processamento
        if map_df.empty:
             st.info("Não há dados de vendas por estado para exibir no mapa.")
             return None

        # --- Criar o Mapa Choropleth ---
        fig = px.choropleth(
            map_df,
            geojson=geojson_data,
            locations=COL_ESTADO,        # Coluna no DataFrame que corresponde ao ID do GeoJSON
            featureidkey=f"properties.{GEOJSON_ID_FIELD}", # Caminho para o ID dentro do GeoJSON (ajuste se necessário, mas 'id' é comum)
            color="Vendas Totais",       # Coluna usada para a escala de cores
            hover_name=COL_ESTADO,       # O que aparece em negrito no hover
            hover_data={                 # Dados adicionais no hover
                'Vendas Totais': ':.2f', # Formatar como float com 2 casas decimais
                'Valor Médio Pedido Atacado': ':.2f'
            },
            color_continuous_scale="Blues", # Escolher uma escala de cores (ex: Viridis, Plasma, Blues)
            # range_color=(map_df['Vendas Totais'].min(), map_df['Vendas Totais'].max()), # Opcional: definir range da cor
            labels={'Vendas Totais': 'Vendas Totais (R$)', 'Valor Médio Pedido Atacado': 'Valor Médio Atacado (R$)'}
        )

        # --- Ajustar Layout do Mapa ---
        fig.update_geos(
            fitbounds="locations",       # Ajusta o zoom aos locais com dados
            visible=False                # Oculta o mapa base padrão do Plotly Geo
        )
        
        fig.update_layout(
            title={
                'text': 'Mapa de Vendas por Estado',
                'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 20, 'color': '#1E3A8A', 'family': 'Inter'}
            },
            margin={"r":0,"t":50,"l":0,"b":0},
            height=600,
            coloraxis_colorbar={
                'title': 'Vendas (R$)',
                'tickprefix': 'R$ ',
                'tickformat': ',.0f' # Formato de milhares
            },
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter")
        )

        return fig

    except FileNotFoundError:
        st.error(f"Erro: Arquivo GeoJSON não encontrado em {geojson_path}. Verifique o caminho.")
        return None
    except KeyError as e:
        st.error(f"Erro: Coluna ou chave não encontrada: {e}. Verifique os nomes das colunas no DataFrame e a estrutura do GeoJSON (especialmente 'featureidkey').")
        # st.dataframe(map_df.head()) # Descomente para depurar o DataFrame
        # print(geojson_data['features'][0]['properties']) # Descomente para depurar o GeoJSON
        return None
    except Exception as e:
        st.error(f"Erro inesperado ao criar mapa Choropleth: {str(e)}")
        # import traceback
        # st.error(traceback.format_exc()) # Para depuração detalhada
        return None

# --- FUNÇÃO PARA EXIBIR DETALHES (mantida, mas pode ser simplificada ou removida se o hover for suficiente) ---
def exibir_detalhes_estado(df, estado_selecionado):
    """
    Exibe detalhes de vendas para um estado específico.
    (Pode ser adaptada ou removida dependendo da interatividade desejada)
    """
    try:
        COL_VALOR_PEDIDO_CUSTOS = 'VALOR DO PEDIDO'
        COL_TIPO_VENDA = 'TIPO DE VENDA'
        COL_ESTADO = 'Estado'
        
        df_estado = df[df[COL_ESTADO] == estado_selecionado].copy()
        
        if df_estado.empty:
            st.info(f"Não há dados detalhados para {estado_selecionado}.")
            return

        with st.container(border=True):
            st.markdown(f"<h4 style='color:#1E3A8A;'>Detalhes - {estado_selecionado}</h4>", unsafe_allow_html=True)
            
            total_vendas_estado = df_estado[COL_VALOR_PEDIDO_CUSTOS].sum()
            total_pedidos_estado = len(df_estado)
            valor_medio_geral = total_vendas_estado / total_pedidos_estado if total_pedidos_estado > 0 else 0
            
            st.metric("Vendas Totais no Estado", f"R$ {total_vendas_estado:,.2f}")
            st.metric("Total de Pedidos no Estado", f"{total_pedidos_estado}")
            st.metric("Valor Médio por Pedido (Geral)", f"R$ {valor_medio_geral:,.2f}")

            # Gráfico de Vendas por Tipo de Venda no Estado
            if COL_TIPO_VENDA in df_estado.columns:
                vendas_por_tipo = df_estado.groupby(COL_TIPO_VENDA)[COL_VALOR_PEDIDO_CUSTOS].sum().reset_index()
                if not vendas_por_tipo.empty:
                    fig_tipo = px.pie(vendas_por_tipo, values=COL_VALOR_PEDIDO_CUSTOS, names=COL_TIPO_VENDA, 
                                    title="Distribuição por Tipo de Venda", hole=0.4, 
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_tipo.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=250, legend_orientation="h")
                    st.plotly_chart(fig_tipo, use_container_width=True)
            
            # Adicionar mais detalhes se necessário
            # st.dataframe(df_estado) # Exemplo: mostrar tabela filtrada

    except Exception as e:
        st.error(f"Erro ao exibir detalhes do estado {estado_selecionado}: {str(e)}")

