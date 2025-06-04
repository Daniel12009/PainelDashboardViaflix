import streamlit as st
import pandas as pd
import numpy as np

# --- Definir Constantes de Colunas Usadas Internamente ---
# (Estas são as colunas esperadas no DataFrame *antes* da renomeação final)
COL_SKU_CUSTOS = 'SKU PRODUTOS'
COL_ID_PRODUTO_CUSTOS = 'ID DO PRODUTO'
COL_CONTA_CUSTOS_ORIGINAL = 'CONTAS'
COL_PLATAFORMA_CUSTOS = 'PLATAFORMA'
COL_VALOR_PRODUTO_PLANILHA_CUSTOS = 'PREÇO UND'
NOME_PADRAO_TIPO_ANUNCIO = 'Tipo de Anúncio' # Nome padrão usado internamente no DF
COL_TIPO_VENDA = 'TIPO DE VENDA'

# Nomes das colunas APÓS renomeação no app_corrigido.py (usados para filtro e formatação)
COL_MARKETPLACE_RENAMED = 'Marketplace'
COL_SKU_RENAMED = 'SKU'
COL_CONTA_RENAMED = 'Conta'
COL_MARGEM_RENAMED = 'Margem'
COL_PRECO_RENAMED = 'Preço Unit.' # Corrigido para corresponder à renomeação no app
COL_VALOR_PEDIDO_RENAMED = 'Valor Pedido' # Adicionar se esta coluna for usada

def format_currency_safe(x):
    """Formata valor como moeda BRL, tratando erros e não numéricos, retornando R$ 0,00 em caso de falha."""
    if pd.isna(x):
        return "R$ 0,00" # Alterado de "R$ -" para "R$ 0,00"
    try:
        # Tenta converter para float
        float_x = float(x)
        # Formata se for um número
        return f"R$ {float_x:_.2f}".replace('.', '#').replace(',', '.').replace('#', ',').replace('_', '.')
    except (ValueError, TypeError):
        # Se não for numérico ou a conversão falhar, retorna placeholder
        return "R$ 0,00" # Alterado de "R$ -" para "R$ 0,00"

def personalizar_tabela_por_marketplace(df, marketplace_selecionado, tipo_margem):
    """
    Personaliza a tabela de produtos com base no marketplace selecionado.
    Versão otimizada para resposta rápida ao alternar tipos de margem.
    
    Args:
        df: DataFrame com os dados JÁ RENOMEADOS para exibição (ex: 'Marketplace', 'SKU')
        marketplace_selecionado: Marketplace selecionado no filtro ("Todos" ou um específico)
        tipo_margem: Tipo de margem selecionada (Estratégica ou Real) - Usado para formatação?
        
    Returns:
        DataFrame: DataFrame personalizado para exibição (ou Styler)
    """
    
    # Verificar se df é um DataFrame ou uma Series
    if isinstance(df, pd.Series):
        df = pd.DataFrame([df]) # Converter Series para DataFrame
        
    df_personalizado = df.copy()

    # Filtrar por marketplace se necessário (usando a coluna JÁ RENOMEADA)
    if marketplace_selecionado != "Todos":
        if COL_MARKETPLACE_RENAMED in df_personalizado.columns:
            df_personalizado = df_personalizado[df_personalizado[COL_MARKETPLACE_RENAMED] == marketplace_selecionado]
        else:
            # Se a coluna renomeada não existe, algo está errado no fluxo anterior
            # st.warning(f"Coluna '{COL_MARKETPLACE_RENAMED}' não encontrada para filtro.")
            return pd.DataFrame(columns=df.columns) # Retorna DF vazio
    
    # Verificar se o DataFrame está vazio após filtro
    if df_personalizado.empty:
        # Retorna um DataFrame vazio com as colunas esperadas para evitar erros
        return pd.DataFrame(columns=df.columns)

    # A seleção e renomeação de colunas agora é feita ANTES de chamar esta função
    # Esta função foca na formatação e estilização

    # Exemplo de estilização (pode ser expandido)
    def highlight_margem(s):
        # Assume que a coluna 'Margem (%)' contém strings como '15.50%'
        try:
            # Tenta extrair o valor numérico da string formatada
            val_str = str(s).replace('%', '').replace(',', '.')
            val = float(val_str)
            if val < 10:
                return 'color: red; font-weight: bold;'
            elif val < 16:
                return 'color: orange;'
            else:
                return 'color: green;'
        except:
            return '' # Retorna estilo vazio se a conversão falhar

    # Aplicar formatação/estilização
    styler = df_personalizado.style
    
    # Aplicar highlight na coluna de Margem (já formatada como string % no app_corrigido)
    col_margem_display = "Margem (%)" # Nome da coluna após renomeação e formatação
    if col_margem_display in df_personalizado.columns:
         styler = styler.applymap(highlight_margem, subset=[col_margem_display])
         
    # Formatar colunas numéricas como moeda usando a função segura
    # Certifique-se que os nomes das colunas aqui correspondem aos nomes NO DATAFRAME 'df_personalizado'
    # ANTES da formatação ser aplicada (ou seja, os nomes após a renomeação no app_corrigido)
    cols_currency = [COL_PRECO_RENAMED] # Adicionar COL_VALOR_PEDIDO_RENAMED se existir e precisar ser formatado
    
    format_dict = {}
    for col in cols_currency:
        if col in df_personalizado.columns:
            format_dict[col] = format_currency_safe
            
    if format_dict:
        styler = styler.format(format_dict)

    # Ocultar índice
    styler = styler.hide(axis="index")

    return styler

# Função para atualizar a tabela quando o tipo de margem é alterado
# Esta função pode não ser mais necessária se a lógica de margem for tratada antes
@st.cache_data(ttl=600, show_spinner=False)
def atualizar_tabela_com_nova_margem(df_tabela, tipo_margem):
    """
    Atualiza a tabela de produtos com o novo tipo de margem selecionado.
    
    Args:
        df_tabela: DataFrame com a tabela personalizada
        tipo_margem: Tipo de margem selecionada (Estratégica ou Real)
        
    Returns:
        DataFrame: DataFrame atualizado com a nova margem
    """
    # Esta função pode precisar ser reavaliada dependendo de como a coluna 'Margem'
    # é preparada antes de chamar personalizar_tabela_por_marketplace
    return df_tabela # Por enquanto, retorna o DF sem modificação

