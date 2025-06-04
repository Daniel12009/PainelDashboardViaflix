import pandas as pd
import streamlit as st
import traceback
from datetime import datetime, timedelta
import numpy as np

# Função para converter margem para número, otimizada para performance
@st.cache_data(ttl=3600)  # Cache por 1 hora
def converter_margem_para_numero_final(valor_da_planilha):
    """
    Converte o valor da planilha para um float que representa a porcentagem (ex: 15.23).
    Se o valor da planilha for um número decimal como 0.1523, ele SERÁ convertido para 15.23.
    """
    if pd.isna(valor_da_planilha):
        return 0.0

    if isinstance(valor_da_planilha, (int, float)):
        val_float = float(valor_da_planilha)
        # HEURÍSTICA CHAVE:
        if abs(val_float) > 0 and abs(val_float) <= 1.5:  # AJUSTE O LIMITE 1.5 SE NECESSÁRIO
            return val_float * 100.0
        else:
            return val_float 

    if isinstance(valor_da_planilha, str):
        valor_limpo = valor_da_planilha.replace('%', '').strip().replace(',', '.')
        if not valor_limpo: return 0.0
        try:
            val_float_str = float(valor_limpo)
            if abs(val_float_str) > 0 and abs(val_float_str) <= 1.5: # AJUSTE O LIMITE 1.5
                 return val_float_str * 100.0
            else:
                 return val_float_str
        except ValueError: 
            return 0.0
    return 0.0

# Função para formatar margem para exibição, otimizada para performance
@st.cache_data(ttl=3600)  # Cache por 1 hora
def formatar_margem_para_exibicao_final(valor_numerico_percentual):
    if pd.isna(valor_numerico_percentual): return "0,00%"
    try: return f"{float(valor_numerico_percentual):.2f}".replace(".", ",") + "%"
    except (ValueError, TypeError): return str(valor_numerico_percentual) 

# Função principal para processar a planilha, com otimizações de performance
@st.cache_data(ttl=600, show_spinner=False)  # Cache por 10 minutos, sem mostrar spinner
def processar_planilha_otimizado(
    uploaded_file, 
    tipo_margem_selecionada_ui_proc, 
    data_inicio_analise_proc,
    data_fim_analise_proc,
    col_margem_estrategica, # Nome do parâmetro como na chamada do app.py
    col_margem_real,         # Nome do parâmetro como na chamada do app.py
    col_tipo_anuncio_ml_planilha_proc, # Nome da coluna de tipo de anúncio da planilha
    _dummy_rerun_arg=None 
    ):
    
    try:
        COL_SKU_CUSTOS = 'SKU PRODUTOS'; COL_DATA_CUSTOS = 'DIA DE VENDA'; COL_CONTA_CUSTOS_ORIGINAL = 'CONTAS'
        COL_PLATAFORMA_CUSTOS = 'PLATAFORMA'; COL_VALOR_PRODUTO_PLANILHA_CUSTOS = 'PREÇO UND'
        COL_ID_PRODUTO_CUSTOS = 'ID DO PRODUTO'; COL_QUANTIDADE_CUSTOS_ABA_CUSTOS = 'QUANTIDADE'
        COL_VALOR_PEDIDO_CUSTOS = 'VALOR DO PEDIDO'
        COL_TIPO_ANUNCIO_ORIGINAL = 'Tipo de Anúncio' # Coluna R
        COL_TIPO_ENVIO_ORIGINAL = 'envio' # Coluna S
        NOME_FINAL_TIPO_ANUNCIO = 'Tipo de Anúncio' # Nome final desejado
        NOME_FINAL_TIPO_ENVIO = 'Tipo de Envio' # Nome final desejado
        COL_TIPO_VENDA = 'TIPO DE VENDA'  # Nova coluna para identificar Marketplace, Atacado ou Showroom

        xls = pd.ExcelFile(uploaded_file)

        # --- Start: Add logic to find the actual column name ---
        try:
            # Read only the header row of the 'CUSTOS' sheet
            header_df = pd.read_excel(xls, sheet_name='CUSTOS', nrows=0)
            actual_headers = header_df.columns.tolist()

            # Normalize target names for comparison
            target_tipo_anuncio_norm = 'tipo de anúncio'
            target_tipo_envio_norm = 'envio' # Assuming 'envio' is the target for column S

            actual_col_tipo_anuncio = None
            actual_col_tipo_envio = None

            for header in actual_headers:
                normalized_header = str(header).lower().strip()
                if normalized_header == target_tipo_anuncio_norm:
                    actual_col_tipo_anuncio = header # Found the actual name for Tipo de Anúncio
                elif normalized_header == target_tipo_envio_norm:
                     actual_col_tipo_envio = header # Found the actual name for Tipo de Envio

            # Fallback if not found (use the original hardcoded names)
            if actual_col_tipo_anuncio is None:
                actual_col_tipo_anuncio = COL_TIPO_ANUNCIO_ORIGINAL # Original guess: 'Tipo de Anúncio'
                st.warning(f"Coluna para 'Tipo de Anúncio' ('{target_tipo_anuncio_norm}') não encontrada com nome exato. Tentando com '{actual_col_tipo_anuncio}'. Verifique o cabeçalho da coluna R na aba CUSTOS.")
            if actual_col_tipo_envio is None:
                actual_col_tipo_envio = COL_TIPO_ENVIO_ORIGINAL # Original guess: 'envio'
                st.warning(f"Coluna para 'Tipo de Envio' ('{target_tipo_envio_norm}') não encontrada com nome exato. Tentando com '{actual_col_tipo_envio}'. Verifique o cabeçalho da coluna S na aba CUSTOS.")

        except Exception as e_header:
            st.error(f"Erro ao ler cabeçalhos da aba CUSTOS: {e_header}")
            # Use original guesses as fallback if header reading fails
            actual_col_tipo_anuncio = COL_TIPO_ANUNCIO_ORIGINAL
            actual_col_tipo_envio = COL_TIPO_ENVIO_ORIGINAL
        # --- End: Add logic to find the actual column name ---

        abas_necessarias = ['CUSTOS', 'ESTOQUE']
        for aba in abas_necessarias:
            if aba not in xls.sheet_names:
                st.error(f"A aba '{aba}' não foi encontrada na planilha."); return None

        colunas_base_leitura = [
            COL_SKU_CUSTOS, COL_DATA_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL, COL_PLATAFORMA_CUSTOS,
            COL_VALOR_PRODUTO_PLANILHA_CUSTOS, COL_ID_PRODUTO_CUSTOS,
            COL_QUANTIDADE_CUSTOS_ABA_CUSTOS, COL_VALOR_PEDIDO_CUSTOS
        ]
        colunas_margem_a_ler_da_planilha = list(set([col_margem_estrategica, col_margem_real]))
        colunas_custos_ler_final = list(dict.fromkeys(
            colunas_base_leitura + 
            colunas_margem_a_ler_da_planilha + 
            [actual_col_tipo_anuncio, actual_col_tipo_envio] # Usa os nomes detectados
        ))
        
        dtypes_leitura = {str(col): str for col in [
            COL_SKU_CUSTOS, COL_ID_PRODUTO_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL, 
            COL_PLATAFORMA_CUSTOS, actual_col_tipo_anuncio, actual_col_tipo_envio # Usa os nomes detectados
        ]}
        for col_margem_str in colunas_margem_a_ler_da_planilha: dtypes_leitura[str(col_margem_str)] = str
        
        # Otimização: Usar nrows para limitar a quantidade de dados carregados se necessário
        # Ler usando os nomes detectados
        custos_df = pd.read_excel(xls, sheet_name='CUSTOS', dtype=dtypes_leitura,
                                 usecols=lambda x: x in colunas_custos_ler_final)        
        # Renomear as colunas detectadas para os nomes finais padronizados
        rename_map = {}
        if actual_col_tipo_anuncio in custos_df.columns and actual_col_tipo_anuncio != NOME_FINAL_TIPO_ANUNCIO:
            rename_map[actual_col_tipo_anuncio] = NOME_FINAL_TIPO_ANUNCIO
        if actual_col_tipo_envio in custos_df.columns and actual_col_tipo_envio != NOME_FINAL_TIPO_ENVIO:
             rename_map[actual_col_tipo_envio] = NOME_FINAL_TIPO_ENVIO
        
        if rename_map:
            custos_df.rename(columns=rename_map, inplace=True)

        # Padronizar valores APÓS renomear para o nome final
        if NOME_FINAL_TIPO_ANUNCIO in custos_df.columns:
            custos_df[NOME_FINAL_TIPO_ANUNCIO] = custos_df[NOME_FINAL_TIPO_ANUNCIO].fillna("Não Informado").astype(str)
        else:
            custos_df[NOME_FINAL_TIPO_ANUNCIO] = "Não Informado"

        if NOME_FINAL_TIPO_ENVIO in custos_df.columns:
            custos_df[NOME_FINAL_TIPO_ENVIO] = custos_df[NOME_FINAL_TIPO_ENVIO].fillna("Não Informado").astype(str)
        else:
            custos_df[NOME_FINAL_TIPO_ENVIO] = "Não Informado"
        # Otimização: Converter apenas as colunas necessárias
        custos_df[COL_VALOR_PEDIDO_CUSTOS] = pd.to_numeric(custos_df[COL_VALOR_PEDIDO_CUSTOS], errors='coerce').fillna(0)
        custos_df[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS] = pd.to_numeric(custos_df[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS], errors='coerce').fillna(0)
        custos_df[COL_DATA_CUSTOS] = pd.to_datetime(custos_df[COL_DATA_CUSTOS], errors='coerce')
        custos_df.dropna(subset=[COL_DATA_CUSTOS], inplace=True)

        if isinstance(data_inicio_analise_proc, datetime): data_inicio_analise_proc = data_inicio_analise_proc.date()
        if isinstance(data_fim_analise_proc, datetime): data_fim_analise_proc = data_fim_analise_proc.date()

        custos_df_datas_para_filtro = custos_df[COL_DATA_CUSTOS].dt.date
        custos_df_filtrado_periodo = custos_df[(custos_df_datas_para_filtro >= data_inicio_analise_proc) & (custos_df_datas_para_filtro <= data_fim_analise_proc)].copy()

        if custos_df_filtrado_periodo.empty:
            st.warning(f"Sem dados em 'CUSTOS' para o período ({data_inicio_analise_proc:%d/%m/%Y} a {data_fim_analise_proc:%d/%m/%Y}) no processamento inicial.")
            return pd.DataFrame()

        # Processar ambas as margens de uma vez para evitar reprocessamento
        if col_margem_estrategica in custos_df_filtrado_periodo.columns:
            custos_df_filtrado_periodo['Margem_Estrategica_Num'] = custos_df_filtrado_periodo[col_margem_estrategica].apply(converter_margem_para_numero_final)
            custos_df_filtrado_periodo['Margem_Estrategica_Original'] = custos_df_filtrado_periodo['Margem_Estrategica_Num'].apply(formatar_margem_para_exibicao_final)
        else:
            custos_df_filtrado_periodo['Margem_Estrategica_Num'] = 0.0
            custos_df_filtrado_periodo['Margem_Estrategica_Original'] = "0,00%"
            
        if col_margem_real in custos_df_filtrado_periodo.columns:
            custos_df_filtrado_periodo['Margem_Real_Num'] = custos_df_filtrado_periodo[col_margem_real].apply(converter_margem_para_numero_final)
            custos_df_filtrado_periodo['Margem_Real_Original'] = custos_df_filtrado_periodo['Margem_Real_Num'].apply(formatar_margem_para_exibicao_final)
        else:
            custos_df_filtrado_periodo['Margem_Real_Num'] = 0.0
            custos_df_filtrado_periodo['Margem_Real_Original'] = "0,00%"
        
        # Definir a margem atual com base na seleção do usuário
        if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_proc:
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Estrategica_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Estrategica_Original']
        elif "Margem Real (M)" in tipo_margem_selecionada_ui_proc:
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Real_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Real_Original']
        else:
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Estrategica_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Estrategica_Original']
        
        df_final_com_estoque = custos_df_filtrado_periodo.copy() 
        try:
            # Otimização: Ler apenas as colunas necessárias da aba ESTOQUE
            estoque_df = pd.read_excel(xls, sheet_name='ESTOQUE', dtype={0: str, 3:str, 6:str, 9:str}) 
            skus_unicos_filtrados = df_final_com_estoque[COL_SKU_CUSTOS].unique()
            estoque_map_config = {'Estoque Full VF': (0, 1), 'Estoque Full GS': (3, 4), 'Estoque Full DK': (6, 7), 'Estoque Tiny': (9, 10)}
            for nome_col_est, (idx_sku_est, idx_val_est) in estoque_map_config.items():
                if idx_sku_est < len(estoque_df.columns) and idx_val_est < len(estoque_df.columns):
                    estoque_temp = estoque_df.iloc[:, [idx_sku_est, idx_val_est]].copy()
                    estoque_temp.columns = ['_SKU_ESTOQUE_TEMP_', nome_col_est]
                    estoque_temp.drop_duplicates(subset=['_SKU_ESTOQUE_TEMP_'], keep='first', inplace=True)
                    estoque_temp = estoque_temp[estoque_temp['_SKU_ESTOQUE_TEMP_'].isin(skus_unicos_filtrados)]
                    df_final_com_estoque = pd.merge(df_final_com_estoque, estoque_temp,left_on=COL_SKU_CUSTOS, right_on='_SKU_ESTOQUE_TEMP_',how='left').drop('_SKU_ESTOQUE_TEMP_', axis=1, errors='ignore')
                    df_final_com_estoque[nome_col_est] = pd.to_numeric(df_final_com_estoque[nome_col_est], errors='coerce').fillna(0).astype(int) # Estoque como inteiro
                else: df_final_com_estoque[nome_col_est] = 0
        except Exception as e_merge_estoque:
            st.warning(f"Erro ao processar Estoque: {e_merge_estoque}.")
            for nome_col_est_fallback in estoque_map_config.keys():
                if nome_col_est_fallback not in df_final_com_estoque.columns: df_final_com_estoque[nome_col_est_fallback] = 0
        
        # Calcular Estoque Total Full somando as colunas individuais
        cols_full_individuais = ["Estoque Full VF", "Estoque Full GS", "Estoque Full DK"]
        cols_to_sum = [col for col in cols_full_individuais if col in df_final_com_estoque.columns]
        if cols_to_sum:
             # Garantir que as colunas sejam numéricas antes de somar
             for col in cols_to_sum:
                 df_final_com_estoque[col] = pd.to_numeric(df_final_com_estoque[col], errors='coerce').fillna(0)
             df_final_com_estoque["Estoque Total Full"] = df_final_com_estoque[cols_to_sum].sum(axis=1).astype(int)
        else:
             df_final_com_estoque["Estoque Total Full"] = 0
        # Remover a coluna 'Estoque Full' individual se existir, pois agora temos a 'Estoque Total Full'
        # if "Estoque Full" in df_final_com_estoque.columns: # Linha comentada pois a coluna não era usada antes
        #     df_final_com_estoque = df_final_com_estoque.drop("Estoque Full", axis=1)

        # Adicionar colunas de alerta
        if 'Margem_Num' in df_final_com_estoque.columns: df_final_com_estoque['Margem_Critica'] = df_final_com_estoque['Margem_Num'] < 10
        else: df_final_com_estoque['Margem_Critica'] = False
        if 'Estoque Tiny' in df_final_com_estoque.columns: df_final_com_estoque['Estoque_Parado_Alerta'] = df_final_com_estoque['Estoque Tiny'] > 10
        else: df_final_com_estoque['Estoque_Parado_Alerta'] = False
        
        # Adicionar coluna de unidades vendidas por produto no período
        if COL_SKU_CUSTOS in df_final_com_estoque.columns and COL_QUANTIDADE_CUSTOS_ABA_CUSTOS in df_final_com_estoque.columns:
            # Agrupar por SKU e somar as quantidades
            unidades_vendidas = df_final_com_estoque.groupby(COL_SKU_CUSTOS)[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS].sum().reset_index()
            unidades_vendidas.columns = [COL_SKU_CUSTOS, 'Unidades_Vendidas_Periodo']
            
            # Mesclar com o DataFrame principal
            df_final_com_estoque = pd.merge(
                df_final_com_estoque, 
                unidades_vendidas,
                on=COL_SKU_CUSTOS,
                how='left'
            )
            
            # Preencher valores nulos com 0
            df_final_com_estoque['Unidades_Vendidas_Periodo'] = df_final_com_estoque['Unidades_Vendidas_Periodo'].fillna(0).astype(int)
        else:
            df_final_com_estoque['Unidades_Vendidas_Periodo'] = 0
        
        # Adicionar coluna de tipo de venda com lógica aprimorada
        if COL_TIPO_VENDA not in df_final_com_estoque.columns:
            # Definir listas de plataformas conhecidas para cada categoria
            marketplaces_conhecidos = [
                "Mercado Livre", "Shopee", "Amazon", "Magalu", "Americanas", 
                "Amazon Seller", "Amazon FBA", "Shein"
            ]
            # Normalizar para comparação (lowercase)
            marketplaces_conhecidos_lower = [m.lower() for m in marketplaces_conhecidos]
            
            # Assumir que Atacado e Showroom são identificados por valores específicos 
            # na coluna PLATAFORMA ou outra coluna (ajustar se necessário)
            # Exemplo: Se a plataforma for "Atacado XYZ", classificar como Atacado
            # Exemplo: Se a plataforma for "Showroom SP", classificar como Showroom
            # Se não houver identificador claro, pode ser necessário ajustar a lógica
            
            # Criar a coluna com um valor padrão (ex: "Outros" ou "Marketplaces")
            df_final_com_estoque[COL_TIPO_VENDA] = "Marketplaces" # Default para Marketplaces
            
            if COL_PLATAFORMA_CUSTOS in df_final_com_estoque.columns:
                # Normalizar coluna plataforma para comparação
                plataforma_lower = df_final_com_estoque[COL_PLATAFORMA_CUSTOS].astype(str).str.lower()
                
                # Identificar Marketplaces
                mask_marketplaces = plataforma_lower.isin(marketplaces_conhecidos_lower)
                df_final_com_estoque.loc[mask_marketplaces, COL_TIPO_VENDA] = "Marketplaces"
                
                # Identificar Atacado (Exemplo: se plataforma contém "Atacado")
                mask_atacado = plataforma_lower.str.contains("atacado", na=False)
                df_final_com_estoque.loc[mask_atacado, COL_TIPO_VENDA] = "Atacado"
                
                # Identificar Showroom (Exemplo: se plataforma contém "Showroom")
                mask_showroom = plataforma_lower.str.contains("showroom", na=False)
                df_final_com_estoque.loc[mask_showroom, COL_TIPO_VENDA] = "Showroom"
                
                # Prioridade: Se for Atacado ou Showroom, sobrescreve a classificação de Marketplace
                df_final_com_estoque.loc[mask_atacado, COL_TIPO_VENDA] = "Atacado"
                df_final_com_estoque.loc[mask_showroom, COL_TIPO_VENDA] = "Showroom"
            else:                 st.warning(f"Coluna 	'{COL_PLATAFORMA_CUSTOS}	' não encontrada para definir 	'{COL_TIPO_VENDA}	'. Classificando tudo como Marketplaces.")        
        # Adicionar coluna de estado para o mapa (simulação para demonstração)
        if 'Estado' not in df_final_com_estoque.columns:
            estados = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE', 'CE', 'GO', 'DF', 'ES', 'PA', 'AM', 'MA', 'MS', 'MT', 'PB', 'RN', 'AL', 'PI', 'SE', 'RO', 'TO', 'AC', 'AP', 'RR']
            # Distribuição ponderada para estados com maior população
            pesos = [25, 15, 12, 8, 7, 5, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0.5, 0.5]
            pesos = [p/sum(pesos) for p in pesos]  # Normalizar pesos
            df_final_com_estoque['Estado'] = np.random.choice(estados, size=len(df_final_com_estoque), p=pesos)
        
        return df_final_com_estoque
    
    except Exception as e_geral_proc:
        st.error(f"Erro CRÍTICO no processamento: {str(e_geral_proc)}")
        st.error(traceback.format_exc())
        return None

# Função para atualizar apenas a margem sem reprocessar todos os dados
@st.cache_data(ttl=600, show_spinner=False)
def atualizar_margem_sem_reprocessamento(df, tipo_margem_selecionada):
    """
    Atualiza apenas as colunas de margem no DataFrame sem reprocessar todos os dados.
    
    Args:
        df: DataFrame com os dados já processados
        tipo_margem_selecionada: Tipo de margem selecionada pelo usuário
        
    Returns:
        DataFrame com as margens atualizadas
    """
    if df is None or df.empty:
        return df
    
    df_atualizado = df.copy()
    
    # Verificar se temos as colunas necessárias
    colunas_necessarias = ['Margem_Estrategica_Num', 'Margem_Estrategica_Original', 
                          'Margem_Real_Num', 'Margem_Real_Original']
    
    if not all(col in df_atualizado.columns for col in colunas_necessarias):
        return df  # Retornar o DataFrame original se não tiver as colunas necessárias
    
    # Atualizar as colunas de margem com base na seleção
    if "Margem Estratégica (L)" in tipo_margem_selecionada:
        df_atualizado['Margem_Num'] = df_atualizado['Margem_Estrategica_Num']
        df_atualizado['Margem_Original'] = df_atualizado['Margem_Estrategica_Original']
    elif "Margem Real (M)" in tipo_margem_selecionada:
        df_atualizado['Margem_Num'] = df_atualizado['Margem_Real_Num']
        df_atualizado['Margem_Original'] = df_atualizado['Margem_Real_Original']
    
    # Atualizar a coluna de margem crítica
    if 'Margem_Num' in df_atualizado.columns:
        df_atualizado['Margem_Critica'] = df_atualizado['Margem_Num'] < 10
    
    return df_atualizado

