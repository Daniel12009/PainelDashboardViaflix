# Importações necessárias
import pandas as pd
import streamlit as st
import traceback
from datetime import datetime, timedelta
import numpy as np
import io # Manter io caso seja usado em outro lugar, mas não para leitura direta de URL

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
            # HEURÍSTICA: Se o valor lido como string e convertido para float for pequeno (provável decimal), multiplica por 100
            # Ajuste o limite 1.5 se necessário para sua base de dados
            if abs(val_float_str) > 0 and abs(val_float_str) <= 1.5:
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

# Função principal para processar a planilha, AGORA LENDO DO GOOGLE SHEETS
@st.cache_data(ttl=600, show_spinner="Lendo dados do Google Sheets...")  # Cache por 10 minutos
def processar_planilha_google_sheets(
    google_sheet_url, # Alterado: Recebe a URL da planilha publicada
    tipo_margem_selecionada_ui_proc,
    data_inicio_analise_proc,
    data_fim_analise_proc,
    col_margem_estrategica, # Nome da coluna na aba CUSTOS
    col_margem_real,         # Nome da coluna na aba CUSTOS
    col_tipo_anuncio_ml_planilha_proc, # Nome original esperado na aba CUSTOS
    _dummy_rerun_arg=None
    ):

    try:
        # Constantes das colunas
        COL_SKU_CUSTOS = 'SKU PRODUTOS'; COL_DATA_CUSTOS = 'DIA DE VENDA'; COL_CONTA_CUSTOS_ORIGINAL = 'CONTAS'
        COL_PLATAFORMA_CUSTOS = 'PLATAFORMA'; COL_VALOR_PRODUTO_PLANILHA_CUSTOS = 'PREÇO UND'
        COL_ID_PRODUTO_CUSTOS = 'ID DO PRODUTO'; COL_QUANTIDADE_CUSTOS_ABA_CUSTOS = 'QUANTIDADE'
        COL_VALOR_PEDIDO_CUSTOS = 'VALOR DO PEDIDO'
        COL_TIPO_ANUNCIO_ORIGINAL = col_tipo_anuncio_ml_planilha_proc # Usar o nome passado como parâmetro
        COL_TIPO_ENVIO_ORIGINAL = 'envio' # Coluna S (presumido)
        NOME_FINAL_TIPO_ANUNCIO = 'Tipo de Anúncio' # Nome padrão interno
        NOME_FINAL_TIPO_ENVIO = 'Tipo de Envio' # Nome padrão interno
        COL_TIPO_VENDA = 'TIPO DE VENDA'
        COL_ESTADO = "Estado" # Coluna de estado adicionada no processamento

        # Novas colunas de estoque
        COL_ESTOQUE_VF = "Estoque Full VF"
        COL_ESTOQUE_GS = "Estoque Full GS"
        COL_ESTOQUE_DK = "Estoque Full DK"
        COL_ESTOQUE_TINY = "Estoque Tiny"
        COL_ESTOQUE_TOTAL_FULL = "Estoque Total Full"

        # --- Leitura do Google Sheets --- 
        st.info(f"Iniciando leitura da planilha: {google_sheet_url}")
        # Ler todas as abas necessárias de uma vez
        # O Pandas pode ler diretamente da URL publicada no formato xlsx
        # Usar sheet_name=None para ler todas as abas em um dicionário
        try:
            sheets_dict = pd.read_excel(google_sheet_url, sheet_name=None, engine='openpyxl')
            st.success("Planilha lida com sucesso!")
        except Exception as e_read:
            st.error(f"Erro ao ler a planilha do Google Sheets: {e_read}")
            st.error(f"Verifique se a URL está correta e se a planilha está publicada para a web no formato XLSX: {google_sheet_url}")
            return None, None # Retorna None para indicar falha

        # Verificar se as abas necessárias existem no dicionário
        abas_necessarias = ['CUSTOS', 'ESTOQUE', 'VENDAS', 'ADS-ML']
        abas_encontradas = list(sheets_dict.keys())
        for aba in abas_necessarias:
            # Procurar por variações de maiúsculas/minúsculas
            aba_encontrada = next((key for key in abas_encontradas if key.upper() == aba.upper()), None)
            if not aba_encontrada:
                st.error(f"A aba necessária '{aba}' não foi encontrada na planilha. Abas encontradas: {abas_encontradas}")
                return None, None # Retorna None para indicar falha
            # Renomear a chave para o nome padrão (ex: 'Custos' -> 'CUSTOS')
            if aba_encontrada != aba:
                 sheets_dict[aba] = sheets_dict.pop(aba_encontrada)

        custos_df_original = sheets_dict['CUSTOS'].copy()
        estoque_df_original = sheets_dict['ESTOQUE'].copy()
        vendas_df_original = sheets_dict['VENDAS'].copy()  # DataFrame da aba VENDAS
        ads_ml_df_original = sheets_dict.get('ADS-ML', pd.DataFrame()).copy()

        # --- Lógica para encontrar nome real das colunas (adaptada para DataFrame) ---
        try:
            # Priorizar nomes confirmados e comuns para Tipo de Anúncio
            nomes_possiveis_tipo_anuncio = ["Tipo de anúncio", "Tipo de Anúncio", col_tipo_anuncio_ml_planilha_proc, "TIPO ANUNCIO ML"]
            nomes_possiveis_tipo_envio = ["envio", "Tipo de Envio"]

            actual_col_tipo_anuncio = None
            actual_col_tipo_envio = None
            actual_headers = custos_df_original.columns.tolist()
            actual_headers_lower = [str(h).lower().strip() for h in actual_headers]

            # Buscar Tipo Anúncio
            for nome_tentativa in nomes_possiveis_tipo_anuncio:
                nome_tentativa_lower = str(nome_tentativa).lower().strip()
                if nome_tentativa_lower in actual_headers_lower:
                    idx = actual_headers_lower.index(nome_tentativa_lower)
                    actual_col_tipo_anuncio = actual_headers[idx]
                    st.info(f"Coluna 'Tipo de Anúncio' encontrada como: '{actual_col_tipo_anuncio}'")
                    break # Encontrou, parar busca
            
            # Buscar Tipo Envio
            for nome_tentativa in nomes_possiveis_tipo_envio:
                nome_tentativa_lower = str(nome_tentativa).lower().strip()
                if nome_tentativa_lower in actual_headers_lower:
                    idx = actual_headers_lower.index(nome_tentativa_lower)
                    actual_col_tipo_envio = actual_headers[idx]
                    st.info(f"Coluna 'Tipo de Envio' encontrada como: '{actual_col_tipo_envio}'")
                    break # Encontrou, parar busca

            # Fallback e avisos se não encontrar
            if actual_col_tipo_anuncio is None:
                st.error(f"Coluna para 'Tipo de Anúncio' não encontrada na aba CUSTOS. Nomes tentados: {nomes_possiveis_tipo_anuncio}. Verifique o nome exato na sua planilha.")
                actual_col_tipo_anuncio = "Tipo Anuncio Ausente" # Criar coluna placeholder
                custos_df_original[actual_col_tipo_anuncio] = "Não Informado"
                st.warning("Continuando sem a coluna 'Tipo de Anúncio'.")
                
            if actual_col_tipo_envio is None:
                actual_col_tipo_envio = COL_TIPO_ENVIO_ORIGINAL 
                if actual_col_tipo_envio not in custos_df_original.columns:
                     st.warning(f"Coluna para 'Tipo de Envio' não encontrada (nomes tentados: {nomes_possiveis_tipo_envio}). Tentando fallback para '{COL_TIPO_ENVIO_ORIGINAL}', mas também não encontrada. A coluna 'Tipo de Envio' não será processada.")
                     actual_col_tipo_envio = "Tipo Envio Ausente"
                     custos_df_original[actual_col_tipo_envio] = "Não Informado"
                else:
                     st.warning(f"Coluna para 'Tipo de Envio' não encontrada (nomes tentados: {nomes_possiveis_tipo_envio}). Usando fallback '{COL_TIPO_ENVIO_ORIGINAL}'.")

        except Exception as e_header:
            st.error(f"Erro ao verificar cabeçalhos da aba CUSTOS: {e_header}")
            actual_col_tipo_anuncio = "Tipo de anúncio" # Usar o nome mais provável como fallback
            actual_col_tipo_envio = "envio"
            if actual_col_tipo_anuncio not in custos_df_original.columns: custos_df_original[actual_col_tipo_anuncio] = "Não Informado"
            if actual_col_tipo_envio not in custos_df_original.columns: custos_df_original[actual_col_tipo_envio] = "Não Informado"
        # --- Fim da lógica de nomes de coluna ---

        # Verificar se as colunas necessárias existem no DataFrame CUSTOS
        colunas_base_necessarias = [
            COL_SKU_CUSTOS, COL_DATA_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL, COL_PLATAFORMA_CUSTOS,
            COL_VALOR_PRODUTO_PLANILHA_CUSTOS, COL_ID_PRODUTO_CUSTOS,
            COL_QUANTIDADE_CUSTOS_ABA_CUSTOS, COL_VALOR_PEDIDO_CUSTOS
        ]
        colunas_margem_necessarias = list(set([col_margem_estrategica, col_margem_real]))
        colunas_outras_necessarias = [actual_col_tipo_anuncio, actual_col_tipo_envio]
         # Colunas opcionais de líquido
        col_liquido_real = "Liquido Real"
        col_liquido_estrategico = "Liquido Estratégico"
        colunas_liquido = [c for c in [col_liquido_real, col_liquido_estrategico] if c in custos_df_original.columns]

        colunas_custos_necessarias_final = list(dict.fromkeys(
             colunas_base_necessarias + colunas_margem_necessarias + colunas_outras_necessarias + colunas_liquido
        ))

        colunas_faltantes_custos = [col for col in colunas_custos_necessarias_final if col not in custos_df_original.columns]
        if colunas_faltantes_custos:
            st.error(f"Erro na aba CUSTOS: Colunas necessárias não encontradas: {colunas_faltantes_custos}")
            return None, None

        # Selecionar e copiar apenas as colunas necessárias para evitar modificar o original
        custos_df = custos_df_original[colunas_custos_necessarias_final].copy()

        # --- Processamento do DataFrame CUSTOS (similar ao anterior) ---
        # Renomear colunas detectadas para nomes padrão internos
        rename_map = {}
        if actual_col_tipo_anuncio != NOME_FINAL_TIPO_ANUNCIO:
            rename_map[actual_col_tipo_anuncio] = NOME_FINAL_TIPO_ANUNCIO
        if actual_col_tipo_envio != NOME_FINAL_TIPO_ENVIO:
             rename_map[actual_col_tipo_envio] = NOME_FINAL_TIPO_ENVIO
        if rename_map:
            custos_df.rename(columns=rename_map, inplace=True)

        # Padronizar e converter tipos
        if NOME_FINAL_TIPO_ANUNCIO in custos_df.columns:
            custos_df[NOME_FINAL_TIPO_ANUNCIO] = custos_df[NOME_FINAL_TIPO_ANUNCIO].fillna("Não Informado").astype(str)
        else: custos_df[NOME_FINAL_TIPO_ANUNCIO] = "Não Informado"
        if NOME_FINAL_TIPO_ENVIO in custos_df.columns:
            custos_df[NOME_FINAL_TIPO_ENVIO] = custos_df[NOME_FINAL_TIPO_ENVIO].fillna("Não Informado").astype(str)
        else: custos_df[NOME_FINAL_TIPO_ENVIO] = "Não Informado"

        custos_df[COL_VALOR_PEDIDO_CUSTOS] = pd.to_numeric(custos_df[COL_VALOR_PEDIDO_CUSTOS], errors='coerce').fillna(0)
        custos_df[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS] = pd.to_numeric(custos_df[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS], errors='coerce').fillna(0)
        custos_df[COL_DATA_CUSTOS] = pd.to_datetime(custos_df[COL_DATA_CUSTOS], errors='coerce')
        
        if col_liquido_real in custos_df.columns:
            custos_df[col_liquido_real] = pd.to_numeric(custos_df[col_liquido_real], errors='coerce').fillna(0)
        if col_liquido_estrategico in custos_df.columns:
            custos_df[col_liquido_estrategico] = pd.to_numeric(custos_df[col_liquido_estrategico], errors='coerce').fillna(0)
        custos_df.dropna(subset=[COL_DATA_CUSTOS], inplace=True)

        # Filtrar por período
        if isinstance(data_inicio_analise_proc, datetime): data_inicio_analise_proc = data_inicio_analise_proc.date()
        if isinstance(data_fim_analise_proc, datetime): data_fim_analise_proc = data_fim_analise_proc.date()
        custos_df_datas_para_filtro = custos_df[COL_DATA_CUSTOS].dt.date
        custos_df_filtrado_periodo = custos_df[(custos_df_datas_para_filtro >= data_inicio_analise_proc) & (custos_df_datas_para_filtro <= data_fim_analise_proc)].copy()

        if custos_df_filtrado_periodo.empty:
            st.warning(f"Sem dados em 'CUSTOS' para o período ({data_inicio_analise_proc:%d/%m/%Y} a {data_fim_analise_proc:%d/%m/%Y}).")
            # Retornar DataFrames vazios mas com colunas esperadas para evitar erros posteriores
            # return pd.DataFrame(columns=colunas_custos_necessarias_final), pd.DataFrame()
            return pd.DataFrame(), pd.DataFrame() # Simplificado

        # Processar margens
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

        # Definir a margem atual com base na seleção
        if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_proc:
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Estrategica_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Estrategica_Original']
        elif "Margem Real (M)" in tipo_margem_selecionada_ui_proc:
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Real_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Real_Original']
        else: # Default para Estratégica
            custos_df_filtrado_periodo['Margem_Num'] = custos_df_filtrado_periodo['Margem_Estrategica_Num']
            custos_df_filtrado_periodo['Margem_Original'] = custos_df_filtrado_periodo['Margem_Estrategica_Original']

        # --- Processamento da Aba ESTOQUE --- 
        df_final_com_estoque = custos_df_filtrado_periodo.copy()
        # Definir config ANTES do try/except
        estoque_map_config = {COL_ESTOQUE_VF: (0, 1), COL_ESTOQUE_GS: (3, 4), COL_ESTOQUE_DK: (6, 7), COL_ESTOQUE_TINY: (9, 10)}
        try:
            estoque_df = estoque_df_original.copy() # Usar a cópia lida
            
            # Verificar se as colunas de índice existem (0, 3, 6, 9)
            max_col_index_needed = 10 # O índice 10 é necessário para o valor do estoque Tiny
            if estoque_df.shape[1] <= max_col_index_needed:
                 st.warning(f"A aba 'ESTOQUE' parece ter menos colunas ({estoque_df.shape[1]}) do que o esperado ({max_col_index_needed + 1}). A leitura do estoque pode falhar ou estar incompleta.")

            # --- AJUSTE: Converter colunas de SKU para string usando índices numéricos --- 
            # Criar o dicionário de tipos apenas para colunas existentes
            dtype_map = {}
            sku_indices = [0, 3, 6, 9]
            for idx in sku_indices:
                if idx < estoque_df.shape[1]:
                    # Usar o índice numérico como chave, pois vamos acessar via iloc
                    dtype_map[idx] = str 
                else:
                    st.warning(f"Índice de coluna SKU {idx} fora dos limites da aba ESTOQUE. Não será convertido para string.")
            
            # Tentar converter as colunas existentes para string
            # Nota: astype com índices numéricos pode falhar se as colunas tiverem nomes string.
            # Uma abordagem mais segura seria renomear colunas para índices ou usar iloc consistentemente.
            # Por enquanto, vamos tentar converter e tratar o erro.
            try:
                # Vamos converter coluna por coluna para identificar melhor o erro
                for idx in dtype_map.keys():
                    estoque_df.iloc[:, idx] = estoque_df.iloc[:, idx].astype(str)
                st.info("Colunas SKU da aba ESTOQUE convertidas para texto.")
            except Exception as e_astype:
                st.error(f"Erro ao tentar converter colunas SKU da aba ESTOQUE para texto usando índices: {e_astype}")
                st.error(f"Verifique se a aba ESTOQUE tem cabeçalhos. O código espera colunas acessíveis por índice numérico (0, 3, 6, 9).")
                # Adicionar colunas de estoque vazias para evitar erros posteriores
                for nome_col_est_fallback in estoque_map_config.keys():
                    if nome_col_est_fallback not in df_final_com_estoque.columns:
                        df_final_com_estoque[nome_col_est_fallback] = 0
                # Pular o resto do processamento de estoque se a conversão falhar
                raise e_astype # Re-lança a exceção para ser pega pelo bloco externo

            skus_unicos_filtrados = df_final_com_estoque[COL_SKU_CUSTOS].unique()
            # estoque_map_config já está definido fora do try

            for nome_col_est, (idx_sku_est, idx_val_est) in estoque_map_config.items():
                if idx_sku_est < estoque_df.shape[1] and idx_val_est < estoque_df.shape[1]:
                    # Selecionar colunas pelo índice numérico (iloc) e renomear imediatamente
                    estoque_temp = estoque_df.iloc[:, [idx_sku_est, idx_val_est]].copy()
                    estoque_temp.columns = ['_SKU_ESTOQUE_TEMP_', nome_col_est] # Renomeia para nomes temporários

                    # Limpar SKUs nulos ou vazios ANTES do merge
                    estoque_temp.dropna(subset=['_SKU_ESTOQUE_TEMP_'], inplace=True)
                    # Garantir que a coluna SKU temporária seja string após a cópia
                    estoque_temp['_SKU_ESTOQUE_TEMP_'] = estoque_temp['_SKU_ESTOQUE_TEMP_'].astype(str).str.strip()
                    estoque_temp = estoque_temp[estoque_temp['_SKU_ESTOQUE_TEMP_'] != '']

                    # Remover duplicados no lado do estoque
                    estoque_temp.drop_duplicates(subset=['_SKU_ESTOQUE_TEMP_'], keep='first', inplace=True)

                    # Merge
                    df_final_com_estoque = pd.merge(
                        df_final_com_estoque,
                        estoque_temp,
                        left_on=COL_SKU_CUSTOS,
                        right_on='_SKU_ESTOQUE_TEMP_',
                        how='left'
                    )
                    # Remover coluna temporária APÓS o merge
                    df_final_com_estoque.drop('_SKU_ESTOQUE_TEMP_', axis=1, inplace=True, errors='ignore')

                    # Converter para numérico e preencher NaN com 0 APÓS o merge
                    df_final_com_estoque[nome_col_est] = pd.to_numeric(df_final_com_estoque[nome_col_est], errors='coerce').fillna(0).astype(int)
                else:
                    st.warning(f"Índices de coluna ({idx_sku_est}, {idx_val_est}) para '{nome_col_est}' fora dos limites da aba ESTOQUE. Coluna não será adicionada.")
                    if nome_col_est not in df_final_com_estoque.columns:
                         df_final_com_estoque[nome_col_est] = 0 # Adicionar coluna com zeros se não puder ler

        except Exception as e_merge_estoque:
            st.error(f"Erro detalhado ao processar ou mesclar Estoque: {e_merge_estoque}")
            st.error(traceback.format_exc()) # Mostra traceback completo para debug
            # Adicionar colunas de estoque vazias em caso de erro grave no processamento
            for nome_col_est_fallback in estoque_map_config.keys():
                 if nome_col_est_fallback not in df_final_com_estoque.columns:
                     df_final_com_estoque[nome_col_est_fallback] = 0
            st.warning("Continuando análise sem dados de estoque devido ao erro.")

        # --- CORREÇÃO: Calcular Estoque Total Full SEMPRE após o merge --- 
        cols_to_sum = [col for col in [COL_ESTOQUE_VF, COL_ESTOQUE_GS, COL_ESTOQUE_DK, COL_ESTOQUE_TINY] if col in df_final_com_estoque.columns]
        if cols_to_sum:
            # Garantir que as colunas são numéricas antes de somar
            for col in cols_to_sum:
                df_final_com_estoque[col] = pd.to_numeric(df_final_com_estoque[col], errors='coerce').fillna(0)
            df_final_com_estoque[COL_ESTOQUE_TOTAL_FULL] = df_final_com_estoque[cols_to_sum].sum(axis=1).astype(int)
        else:
            # Se nenhuma coluna de estoque individual foi criada/encontrada, define o total como 0
            df_final_com_estoque[COL_ESTOQUE_TOTAL_FULL] = 0
 # --- Processamento da Aba ADS-ML ---
        ads_agg = pd.DataFrame()
        try:
            nome_aba_ads = next((key for key in abas_encontradas if key.upper() == 'ADS-ML'), None)
            if nome_aba_ads and not ads_ml_df_original.empty:
                ads_df = ads_ml_df_original.copy()
                needed_idx = [5, 7, 8, 9]  # F, H, I, J
                if ads_df.shape[1] > max(needed_idx):
                    ads_df = ads_df.iloc[:, needed_idx].copy()
                    ads_df.columns = ['Data', 'Valor ADS', COL_SKU_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL]
                    ads_df['Data'] = pd.to_datetime(ads_df['Data'], errors='coerce')
                    ads_df.dropna(subset=['Data'], inplace=True)
                    ads_df['Valor ADS'] = pd.to_numeric(ads_df['Valor ADS'], errors='coerce').fillna(0)
                    ads_df[COL_SKU_CUSTOS] = ads_df[COL_SKU_CUSTOS].astype(str).str.strip()
                    ads_df[COL_CONTA_CUSTOS_ORIGINAL] = ads_df[COL_CONTA_CUSTOS_ORIGINAL].astype(str).str.strip()
                    ads_df_filter = ads_df[(ads_df['Data'].dt.date >= data_inicio_analise_proc) & (ads_df['Data'].dt.date <= data_fim_analise_proc)]
                    ads_agg = ads_df_filter.groupby([COL_SKU_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL], as_index=False)['Valor ADS'].sum()
                else:
                    st.warning("A aba 'ADS-ML' não possui colunas suficientes para o processamento.")
            else:
                st.info("Aba 'ADS-ML' não encontrada. Valores de ADS não serão adicionados.")
        except Exception as e_ads:
            st.error(f"Erro ao processar aba ADS-ML: {e_ads}")
            st.error(traceback.format_exc())
            ads_agg = pd.DataFrame()

        if not ads_agg.empty:
            df_final_com_estoque = pd.merge(
                df_final_com_estoque,
                ads_agg.rename(columns={'Valor ADS': 'Valor de ADS'}),
                on=[COL_SKU_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL],
                how='left'
            )
            df_final_com_estoque['Valor de ADS'] = pd.to_numeric(df_final_com_estoque['Valor de ADS'], errors='coerce').fillna(0.0)
        else:
            df_final_com_estoque['Valor de ADS'] = 0.0



        # --- Processamento da Aba VENDAS (Exemplo: Calcular total vendido por SKU) ---
        # Adaptar conforme a estrutura real da aba 'VENDAS'
        df_alertas_full = pd.DataFrame() # Inicializa vazio, será preenchido se a aba existir e for processada
        try:
            vendas_df = vendas_df_original.copy()
            # Exemplo: Supondo que 'VENDAS' tenha 'SKU' e 'Quantidade Vendida'
            col_sku_vendas = 'SKU' # Ajustar nome da coluna SKU na aba VENDAS
            col_qtd_vendas = 'Quantidade Vendida' # Ajustar nome da coluna Quantidade na aba VENDAS
            col_data_vendas = 'Data Venda' # Ajustar nome da coluna Data na aba VENDAS

            if col_sku_vendas in vendas_df.columns and col_qtd_vendas in vendas_df.columns and col_data_vendas in vendas_df.columns:
                vendas_df[col_data_vendas] = pd.to_datetime(vendas_df[col_data_vendas], errors='coerce')
                vendas_df.dropna(subset=[col_data_vendas], inplace=True)
                vendas_df[col_qtd_vendas] = pd.to_numeric(vendas_df[col_qtd_vendas], errors='coerce').fillna(0)

                # Filtrar vendas no período de análise
                vendas_df_datas_filtro = vendas_df[col_data_vendas].dt.date
                vendas_periodo = vendas_df[(vendas_df_datas_filtro >= data_inicio_analise_proc) & (vendas_df_datas_filtro <= data_fim_analise_proc)]

                # Calcular unidades vendidas por SKU no período
                unidades_vendidas = vendas_periodo.groupby(col_sku_vendas)[col_qtd_vendas].sum().reset_index()
                unidades_vendidas.columns = [COL_SKU_CUSTOS, 'Unidades_Vendidas_Periodo'] # Renomear SKU para bater com CUSTOS

                # Remover coluna antiga se existir e fazer merge
                df_final_com_estoque = df_final_com_estoque.drop('Unidades_Vendidas_Periodo', axis=1, errors='ignore')
                df_final_com_estoque = pd.merge(
                    df_final_com_estoque,
                    unidades_vendidas,
                    on=COL_SKU_CUSTOS,
                    how='left'
                )
                df_final_com_estoque['Unidades_Vendidas_Periodo'] = df_final_com_estoque['Unidades_Vendidas_Periodo'].fillna(0).astype(int)
            else:
                st.warning(f"Colunas '{col_sku_vendas}', '{col_qtd_vendas}' ou '{col_data_vendas}' não encontradas na aba 'VENDAS'. Cálculo de unidades vendidas no período não realizado.")
                if 'Unidades_Vendidas_Periodo' not in df_final_com_estoque.columns:
                     df_final_com_estoque['Unidades_Vendidas_Periodo'] = 0

            # --- NOVO: Processamento para Alerta de Estoque Full --- 
            # Tenta ler a aba 'Envio Full' (ou similar) se existir
            nome_aba_envio_full = next((key for key in abas_encontradas if key.upper() == 'ENVIO FULL'), None)
            if nome_aba_envio_full:
                df_envio_full = sheets_dict[nome_aba_envio_full].copy()
                # Colunas esperadas na aba 'Envio Full' (AJUSTAR NOMES CONFORME SUA PLANILHA)
                col_sku_full = "SKU" 
                col_data_envio_full = "Data Envio"
                col_qtd_enviada_full = "Qtd Enviada"
                col_qtd_atual_full = "Qtd Atual"

                if all(c in df_envio_full.columns for c in [col_sku_full, col_data_envio_full, col_qtd_enviada_full, col_qtd_atual_full]):
                    df_envio_full[col_data_envio_full] = pd.to_datetime(df_envio_full[col_data_envio_full], errors='coerce')
                    df_envio_full[col_qtd_enviada_full] = pd.to_numeric(df_envio_full[col_qtd_enviada_full], errors='coerce').fillna(0)
                    df_envio_full[col_qtd_atual_full] = pd.to_numeric(df_envio_full[col_qtd_atual_full], errors='coerce').fillna(0)
                    df_envio_full.dropna(subset=[col_data_envio_full, col_sku_full], inplace=True)

                    # Manter apenas a entrada mais recente por SKU (se houver múltiplas)
                    df_envio_full = df_envio_full.sort_values(by=col_data_envio_full, ascending=False)
                    df_envio_full = df_envio_full.drop_duplicates(subset=[col_sku_full], keep='first')

                    # Calcular dias desde o envio
                    hoje = datetime.now().date()
                    df_envio_full['Dias_Desde_Envio'] = (hoje - df_envio_full[col_data_envio_full].dt.date).dt.days

                    # Pegar vendas dos últimos 7 dias para previsão
                    data_7_dias_atras = hoje - timedelta(days=7)
                    vendas_7d = vendas_periodo[vendas_periodo[col_data_vendas].dt.date >= data_7_dias_atras]
                    vendas_7d_agg = vendas_7d.groupby(col_sku_vendas)[col_qtd_vendas].sum().reset_index()
                    vendas_7d_agg.columns = [col_sku_full, 'Vendas_7_Dias'] # Renomear SKU

                    # Juntar dados de envio com vendas 7d
                    df_alertas_full = pd.merge(df_envio_full, vendas_7d_agg, on=col_sku_full, how='left')
                    df_alertas_full['Vendas_7_Dias'] = df_alertas_full['Vendas_7_Dias'].fillna(0)

                    # Calcular dias restantes estimados
                    # Evitar divisão por zero e tratar casos sem vendas
                    df_alertas_full['Dias_Restantes_Estimados'] = np.where(
                        df_alertas_full['Vendas_7_Dias'] > 0,
                        (df_alertas_full[col_qtd_atual_full] / (df_alertas_full['Vendas_7_Dias'] / 7)).round(),
                        np.inf # Considerar infinito se não houve vendas
                    )
                    # Limitar dias restantes a um valor alto razoável (ex: 9999) para evitar infinitos na soma
                    df_alertas_full['Dias_Restantes_Estimados'] = df_alertas_full['Dias_Restantes_Estimados'].replace(np.inf, 9999)

                    # Calcular prazo total e filtrar alertas > 60 dias
                    df_alertas_full['Prazo_Total_Estimado'] = df_alertas_full['Dias_Desde_Envio'] + df_alertas_full['Dias_Restantes_Estimados']
                    df_alertas_full = df_alertas_full[df_alertas_full['Prazo_Total_Estimado'] > 60]

                    # Selecionar e renomear colunas para o alerta
                    df_alertas_full = df_alertas_full[[
                        col_sku_full, col_data_envio_full, 'Dias_Desde_Envio',
                        col_qtd_atual_full, 'Vendas_7_Dias', 'Dias_Restantes_Estimados',
                        'Prazo_Total_Estimado'
                    ]].rename(columns={
                        col_sku_full: "SKU",
                        col_data_envio_full: "Data Envio",
                        col_qtd_atual_full: "Qtd Atual Full"
                    })
                    st.success(f"Alerta de Estoque Full processado. {len(df_alertas_full)} SKUs em alerta.")
                else:
                    st.warning(f"Aba '{nome_aba_envio_full}' encontrada, mas colunas necessárias ({[col_sku_full, col_data_envio_full, col_qtd_enviada_full, col_qtd_atual_full]}) não estão presentes. Alerta de Estoque Full não calculado.")
                    df_alertas_full = None # Indicar que não foi calculado
            else:
                st.info("Aba 'Envio Full' não encontrada. Alerta de Prazo de Estoque Full não será calculado.")
                df_alertas_full = None # Indicar que não foi calculado

        except Exception as e_vendas_full:
            st.error(f"Erro ao processar aba VENDAS ou ENVIO FULL: {e_vendas_full}")
            st.error(traceback.format_exc())
            if 'Unidades_Vendidas_Periodo' not in df_final_com_estoque.columns:
                 df_final_com_estoque['Unidades_Vendidas_Periodo'] = 0
            df_alertas_full = None # Indicar falha
        # --- Fim do Processamento VENDAS e ENVIO FULL ---
        
        # Calcular Margem Líquida utilizando o tipo de margem selecionado
        if 'Valor de ADS' in df_final_com_estoque.columns and 'Unidades_Vendidas_Periodo' in df_final_com_estoque.columns:
            liquido_col = 'Liquido_Estrategico_Num' if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_proc else 'Liquido_Real_Num'
            df_final_com_estoque['_ads_sum'] = df_final_com_estoque.groupby(COL_SKU_CUSTOS)['Valor de ADS'].transform('sum')
            df_final_com_estoque['_unid_sum'] = df_final_com_estoque.groupby(COL_SKU_CUSTOS)['Unidades_Vendidas_Periodo'].transform('sum')
            df_final_com_estoque['_liq_val'] = df_final_com_estoque.groupby(COL_SKU_CUSTOS)[liquido_col].transform('mean')
            df_final_com_estoque['Margem_Liquida'] = np.where(
                df_final_com_estoque['_unid_sum'] > 0,
                (df_final_com_estoque['_ads_sum'] / df_final_com_estoque['_unid_sum']) - df_final_com_estoque['_liq_val'],
                -df_final_com_estoque['_liq_val']
            )
            df_final_com_estoque.drop(['_ads_sum', '_unid_sum', '_liq_val'], axis=1, inplace=True)
            df_final_com_estoque['Margem_Liquida_Original'] = df_final_com_estoque['Margem_Liquida'].apply(formatar_margem_para_exibicao_final)
        else:
            df_final_com_estoque['Margem_Liquida'] = 0.0
            df_final_com_estoque['Margem_Liquida_Original'] = "0,00%"

        # Adicionar coluna de tipo de venda (Marketplace, Atacado, Showroom)
        if COL_TIPO_VENDA not in df_final_com_estoque.columns:
            marketplaces_conhecidos = ["Mercado Livre", "Shopee", "Amazon", "Magalu", "Americanas", "Amazon Seller", "Amazon FBA", "Shein"]
            marketplaces_conhecidos_lower = [m.lower() for m in marketplaces_conhecidos]
            contas_atacado = ["ATACADO", "REVENDA"]
            contas_atacado_lower = [c.lower() for c in contas_atacado]
            contas_showroom = ["SHOWROOM"]
            contas_showroom_lower = [c.lower() for c in contas_showroom]

            def classificar_venda(row):
                conta = str(row[COL_CONTA_CUSTOS_ORIGINAL]).lower().strip()
                plataforma = str(row[COL_PLATAFORMA_CUSTOS]).lower().strip()

                if conta in contas_atacado_lower: return "Atacado"
                if conta in contas_showroom_lower: return "Showroom"
                if plataforma in marketplaces_conhecidos_lower: return "Marketplace"
                # Fallback: Se não for atacado/showroom e a plataforma não for conhecida, classificar como Marketplace
                # Ou pode ajustar para "Outros" se preferir
                return "Marketplace"

            df_final_com_estoque[COL_TIPO_VENDA] = df_final_com_estoque.apply(classificar_venda, axis=1)

        # Adicionar coluna de Estado (exemplo, pode precisar de lógica mais robusta)
        # Esta parte depende de como o estado é determinado (ex: da conta, da plataforma?)
        # Exemplo SIMPLES baseado na CONTA (AJUSTAR CONFORME NECESSÁRIO)
        if COL_ESTADO not in df_final_com_estoque.columns:
            def extrair_estado(conta):
                # Lógica de exemplo: tenta pegar as duas últimas letras se forem maiúsculas
                if isinstance(conta, str) and len(conta) >= 2 and conta[-2:].isupper():
                    # Adicionar validação se são siglas de estados válidos se necessário
                    return conta[-2:]
                return "Não Identificado" # Ou None
            df_final_com_estoque[COL_ESTADO] = df_final_com_estoque[COL_CONTA_CUSTOS_ORIGINAL].apply(extrair_estado)

        # Adicionar colunas de alerta finais
        if 'Margem_Num' in df_final_com_estoque.columns: df_final_com_estoque['Margem_Critica'] = df_final_com_estoque['Margem_Num'] < 10
        else: df_final_com_estoque['Margem_Critica'] = False
        if COL_ESTOQUE_TINY in df_final_com_estoque.columns: df_final_com_estoque['Estoque_Parado_Alerta'] = df_final_com_estoque[COL_ESTOQUE_TINY] > 10
        else: df_final_com_estoque['Estoque_Parado_Alerta'] = False

        st.success("Processamento inicial concluído.")
        # Retorna o DataFrame principal e o DataFrame de alertas de estoque full
        return df_final_com_estoque, df_alertas_full

    except FileNotFoundError:
        st.error("Erro: O arquivo da URL do Google Sheets não foi encontrado ou está inacessível.")
        st.error(f"Verifique a URL: {google_sheet_url}")
        return None, None
    except ValueError as ve:
        st.error(f"Erro de valor durante o processamento: {ve}")
        st.error(traceback.format_exc())
        return None, None
    except KeyError as ke:
        st.error(f"Erro: Coluna esperada não encontrada: {ke}. Verifique os nomes das colunas na planilha.")
        st.error(traceback.format_exc())
        return None, None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o processamento da planilha: {e}")
        st.error(traceback.format_exc())
        return None, None

# Função para ATUALIZAR a margem no DataFrame existente (sem reprocessar tudo)
@st.cache_data(ttl=600, show_spinner=False)
def atualizar_margem_sem_reprocessamento(df_existente, tipo_margem_selecionada_ui_atualizar):
    if df_existente is None or df_existente.empty:
        return df_existente # Retorna o DF vazio ou None se não houver dados

    df_atualizado = df_existente.copy()

    # Verifica se as colunas numéricas de margem existem
    col_estrategica_num = 'Margem_Estrategica_Num'
    col_real_num = 'Margem_Real_Num'
    col_estrategica_orig = 'Margem_Estrategica_Original'
    col_real_orig = 'Margem_Real_Original'

    if col_estrategica_num not in df_atualizado.columns or col_real_num not in df_atualizado.columns:
        st.warning("Colunas de margem numérica não encontradas no DataFrame para atualização. A margem não será alterada.")
        return df_existente # Retorna o original se as colunas base não existirem

    # Atualiza as colunas 'Margem_Num' e 'Margem_Original' com base na seleção
    if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_atualizar:
        df_atualizado['Margem_Num'] = df_atualizado[col_estrategica_num]
        df_atualizado['Margem_Original'] = df_atualizado[col_estrategica_orig]
    elif "Margem Real (M)" in tipo_margem_selecionada_ui_atualizar:
        df_atualizado['Margem_Num'] = df_atualizado[col_real_num]
        df_atualizado['Margem_Original'] = df_atualizado[col_real_orig]
    else: # Default para Estratégica se a seleção for inválida
        df_atualizado['Margem_Num'] = df_atualizado[col_estrategica_num]
        df_atualizado['Margem_Original'] = df_atualizado[col_estrategica_orig]

    # Recalcular Alerta de Margem Crítica com base na nova 'Margem_Num'
    if 'Margem_Num' in df_atualizado.columns:
        df_atualizado['Margem_Critica'] = df_atualizado['Margem_Num'] < 10
    else:
        df_atualizado['Margem_Critica'] = False

    # st.info("Margem atualizada no DataFrame.") # Opcional: feedback visual
    return df_atualizado

