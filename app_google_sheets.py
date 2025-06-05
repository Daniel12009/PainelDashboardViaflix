# Importações necessárias
import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
import io
import traceback
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import json
from streamlit_option_menu import option_menu # Importar option_menu

# --- ALTERADO: Importar a nova função de processamento do Google Sheets ---
from processar_planilha_google_sheets import processar_planilha_google_sheets, atualizar_margem_sem_reprocessamento

# Importar funções dos outros módulos (manter se ainda forem usadas)
from personalizar_tabela_melhorado import personalizar_tabela_por_marketplace, atualizar_tabela_com_nova_margem
from mapa_brasil_aprimorado import criar_mapa_brasil_interativo, calcular_valor_medio_pedido_atacado

# --- CONFIGURAÇÕES GLOBAIS ---
pd.set_option("styler.render.max_elements", 1500000)
HISTORICO_PATH = "historico.csv"; LOGO_PATH = "logo.png"; USUARIOS_PATH = "usuarios.json"
COL_SKU_CUSTOS = "SKU PRODUTOS"; 
COL_DATA_CUSTOS = "DIA DE VENDA"; 
COL_CONTA_CUSTOS_ORIGINAL = "CONTAS"
COL_PLATAFORMA_CUSTOS = "PLATAFORMA"; 
COL_MARGEM_ESTRATEGICA_PLANILHA_CUSTOS = "MARGEM ESTRATÉGICA"
COL_MARGEM_REAL_PLANILHA_CUSTOS = "MARGEM REAL"; 
COL_VALOR_PRODUTO_PLANILHA_CUSTOS = "PREÇO UND"
COL_ID_PRODUTO_CUSTOS = "ID DO PRODUTO"; 
COL_QUANTIDADE_CUSTOS_ABA_CUSTOS = "QUANTIDADE"
COL_VALOR_PEDIDO_CUSTOS = "VALOR DO PEDIDO"
COL_TIPO_ANUNCIO_ML_CUSTOS = "TIPO ANUNCIO ML" # Nome da coluna na planilha original
NOME_PADRAO_TIPO_ANUNCIO = "Tipo de Anúncio" # Nome padrão usado internamente no DF
NOME_PADRAO_TIPO_ENVIO = "Tipo de Envio" # Nome padrão usado internamente no DF
COL_TIPO_VENDA = "TIPO DE VENDA"  # Nova coluna para identificar Marketplace, Atacado ou Showroom
COL_ESTADO = "Estado" # Coluna de estado adicionada no processamento

# Novas colunas de estoque
COL_ESTOQUE_VF = "Estoque Full VF"
COL_ESTOQUE_GS = "Estoque Full GS"
COL_ESTOQUE_DK = "Estoque Full DK"
COL_ESTOQUE_TINY = "Estoque Tiny"
COL_ESTOQUE_TOTAL_FULL = "Estoque Total Full"

# --- ALTERADO: URL da Planilha Google Sheets --- 
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS2sAVvBiN31X0_MCOjkeYZsGfcf2VVf_gRkxu2S5SCMba0MV8sYURF614wDUnrq7d17f_JC6uR-Xno/pub?output=xlsx"

# Cores modernas
primary_color = "#1E3A8A"; secondary_color = "#3CCFCF"; accent_color = "#FF9500"
success_color = "#10B981"; warning_color = "#F59E0B"; danger_color = "#EF4444"
text_color_sidebar = "#FFFFFF"; background_sidebar = "#174F87"
text_color_main = "#374151"; background_main = "#F9FAFB"

st.set_page_config(page_title="ViaFlix Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- CSS Aprimorado (Integrado do app_corrigido.py) ---
st.markdown(f"""<style>
    @import url(			'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'			);
    html, body, [class*="css"] {{ font-family: 			'Inter'			, sans-serif; }}
    .main {{ background-color: {background_main}; color: {text_color_main}; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}

    [data-testid="stSidebar"] img {{
        display: block;
        margin-left: auto;
        margin-right: auto;
    }}
    .login-container img {{
        display: block;
        margin: auto;
    }}   
    /* Ajuste completo do sidebar para azul escuro */
    [data-testid="stSidebar"] {{ 
        background-color: {background_sidebar} !important; 
        padding-top: 1rem; /* Reduzir padding superior */
    }}
    
    /* Cor do texto principal dentro do sidebar (garantir contraste) */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] .stRadio label p /* Texto das opções do radio */
    {{ 
        color: {text_color_sidebar} !important; 
        opacity: 1 !important; /* Garantir opacidade total para leitura */
    }}

    /* Adicionado: Garantir cor escura para texto DENTRO dos inputs/selects no sidebar */
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] input,
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div[data-baseweb="selected-value"],
    [data-testid="stSidebar"] .stDateInput input
    {{ 
        color: #333 !important; /* Cor escura para o texto interno */
    }}

    /* Cor dos títulos e labels específicos */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] h5, 
    [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] .stRadio > label, /* Label do Radio */
    [data-testid="stSidebar"] .stSelectbox > label, /* Label do Selectbox */
    [data-testid="stSidebar"] .stDateInput > label, /* Label do DateInput */
    [data-testid="stSidebar"] .stFileUploader > label /* Label do FileUploader */
    {{ 
        color: {text_color_sidebar} !important; 
        font-weight: 500; 
    }}

    /* Estilos para textos e títulos personalizados no sidebar */
    .sidebar-text {{ 
        color: {text_color_sidebar} !important; 
        opacity: 0.9;
    }}
    
    .sidebar-title {{ 
        color: {text_color_sidebar} !important; 
        font-weight: bold; 
        font-size: 1.2rem; 
        margin-bottom: 1rem; 
        text-shadow: 0px 1px 2px rgba(0,0,0,0.3);
    }}
    
    /* Estilo dos botões no sidebar */
    [data-testid="stSidebar"] .stButton>button {{
        background-color: rgba(255,255,255,0.2); /* Fundo levemente transparente */
        color: {text_color_sidebar};
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%; /* Ocupar largura total */
    }}
    [data-testid="stSidebar"] .stButton>button:hover {{
        background-color: {secondary_color};
        color: {background_sidebar}; /* Texto escuro no hover */
        border-color: {secondary_color};
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}

    /* Estilos para streamlit-option-menu */
    .nav-link {{
        color: {text_color_sidebar} !important;
        transition: background-color 0.3s ease, color 0.3s ease;
        border-radius: 6px;
        margin: 2px 0;
        padding: 10px 15px !important;
    }}
    .nav-link:hover {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: {secondary_color} !important;
    }}
    .nav-link.active {{
        background-color: {secondary_color} !important;
        color: {background_sidebar} !important;
        font-weight: 600 !important;
    }}
    .nav-link.active i {{
        color: {background_sidebar} !important;
    }}
    .nav-link i {{
        color: {text_color_sidebar} !important;
        transition: color 0.3s ease;
    }}
    .nav-link:hover i {{
        color: {secondary_color} !important;
    }}

    /* Card de Métricas */
    .metric-card {{ 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        padding: 1.5rem; 
        text-align: center; 
        margin-bottom: 1.5rem; 
        border-left: 5px solid {primary_color}; 
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    .metric-card:hover {{ 
        transform: translateY(-5px); 
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }}
    .metric-card::after {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 30%;
        height: 5px;
        background: linear-gradient(90deg, transparent, {secondary_color});
    }}
    .metric-value {{ 
        font-size: 2.2rem; 
        font-weight: 700; 
        color: {primary_color}; 
        margin: 0.5rem 0; 
        background: linear-gradient(90deg, {primary_color}, {secondary_color});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 1px rgba(0,0,0,0.1);
    }}
    .metric-label {{ 
        color: #6C757D; 
        font-size: 0.9rem; 
        font-weight: 500; 
        text-transform: uppercase; 
        letter-spacing: 0.5px; 
    }}

    /* Abas */
    .stTabs [data-baseweb="tab-list"] {{ 
        gap: 2px; 
        background-color: #F1F5F9;
        border-radius: 10px;
        padding: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        border-radius: 8px;
        padding: 0px 20px;
        background-color: transparent;
        transition: all 0.3s ease;
        font-weight: 500;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: white !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border-bottom: 2px solid {primary_color};
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: rgba(255,255,255,0.7);
    }}

    /* Containers de Filtro e Gráfico */
    .custom-filter-container, .custom-chart-container {{
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    .custom-filter-container {{ border-top: 3px solid {secondary_color}; }}
    .custom-chart-container {{ border-top: 3px solid {primary_color}; }}

    /* Botões na área principal */
    .main .stButton>button {{
        background-color: {primary_color};
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    .main .stButton>button:hover {{
        background-color: {secondary_color};
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}

    /* Ícones e Tooltips */
    .category-icon {{ font-size: 1.5rem; margin-right: 10px; vertical-align: middle; }}
    .tooltip {{ position: relative; display: inline-block; }}
    .tooltip .tooltiptext {{ visibility: hidden; width: 200px; background-color: #333; color: #fff; text-align: center; border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -100px; opacity: 0; transition: opacity 0.3s; }}
    .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; }}

    /* Layout de Alertas (2 colunas) */
    .alert-filter-column {{ 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
        /* border-right: 1px solid #E5E7EB; */ /* Removido para usar st.columns */
    }}
    .alert-table-column {{ 
        /* padding-left: 20px; */ /* Removido para usar st.columns */
    }}

</style>""", unsafe_allow_html=True)
# --- FIM CSS ---

# --- INICIALIZAÇÃO DOS ESTADOS DA SESSÃO ---
default_states = {
    'authenticated': False,
    'app_state': "login", # Inicia no login
    'df_result': None, # DataFrame principal processado
    'df_alertas_full': None, # DataFrame de alertas de estoque full
    'data_inicio_analise_state': datetime.now().date() - timedelta(days=29),
    'data_fim_analise_state': datetime.now().date(),
    'periodo_selecionado': "30 dias",
    'conta_mae_selecionada_ui_state': "Todas", # Filtro Global Sidebar
    'tipo_margem_selecionada_state': "Margem Estratégica (L)",
    # Filtros Análise Detalhada SKU (agora na página)
    'det_marketplace_filter_state': "Todos", 
    'det_conta_filter_state': "Todos", # Novo filtro Conta
    'det_tipo_anuncio_filter_state': "Todos",
    'det_tipo_envio_filter_state': "Todos",
    'det_sku_text_filter_state': "",
    # --- REMOVIDO: Estados antigos de filtros movidos para página ---
    # 'marketplace_selecionado_state': "Todos", 
    # 'ml_tipo_anuncio_selecionado': "Todos", 
    # 'tipo_envio_selecionado': "Todos", 
    # 'tipo_venda_selecionado': "Todos", 
    # 'detailed_sku_filter': "", 
    # --- FIM REMOVIDO ---
    'ml_options_expanded': False,
    'selected_state': None,
    'admin_mode': False,
    'user_role': "user",
    'alert_sort_by': "Margem",
    'alert_sort_order': "Crescente",
    'dummy_rerun_counter': 0,
    'df_com_status_vendedores': None,
    'selected_page': "Dashboard",
    'data_loaded': False, # Novo estado para controlar se os dados foram carregados
    # Filtros de Alertas (serão widgets locais)
    'alert_tipo_alerta_filter': "Todos",
    'alert_marketplace_filter': "Todos",
    'alert_conta_filter': "Todos",
    'alert_sku_filter': "",
    'alert_ordenar_por': "Margem",
    'alert_ordem': "Crescente"
}
for key, value in default_states.items():
    if key not in st.session_state: st.session_state[key] = value

# --- FUNÇÕES AUXILIARES ---
def format_currency_brl(value):
    if pd.isna(value) or value == "-": return "R$ 0,00"
    try: float_value = float(value); formatted_value = f"{float_value:_.2f}".replace('.', '#').replace(',', '.').replace('#', ',').replace('_', '.'); return f"R$ {formatted_value}"
    except: return (value)

def format_integer(value):
    if pd.isna(value): return 0
    try: return int(value)
    except (ValueError, TypeError): return 0

def formatar_margem_para_exibicao_final(valor_numerico_percentual):
    if pd.isna(valor_numerico_percentual): return "0,00%"
    try: return f"{float(valor_numerico_percentual):.2f}".replace(".", ",") + "%"
    except (ValueError, TypeError): return str(valor_numerico_percentual)

def get_margin_color(margin_value_numeric):
    try:
        val = float(margin_value_numeric)
        if val < 10: return danger_color      # Vermelho para < 10
        elif val >= 10 and val < 17: return warning_color # Laranja para 10 <= valor < 17
        elif val >= 17: return success_color   # Verde para >= 17
        else: return primary_color # Cor padrão para outros casos (ex: NaN)
    except: return primary_color

def hash_password(password: str) -> str:
    """Retorna o hash SHA-256 de uma senha."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def carregar_usuarios():
    """Carrega os usuários do arquivo JSON usando senhas hasheadas."""
    default = {"admin": {"senha": hash_password("admin"), "role": "admin"}}
    if os.path.exists(USUARIOS_PATH):
        try:
            with open(USUARIOS_PATH, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else default
        except Exception:
            return default
    else:
        return default

def salvar_usuarios(usuarios):
    """Valida usuário comparando o hash da senha informada."""
    try:
        for info in usuarios.values():
            pwd = info.get("senha")
            if pwd and len(pwd) != 64:
                info["senha"] = hash_password(pwd)
        with open(USUARIOS_PATH, 'w') as f:
            json.dump(usuarios, f, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")

def authenticate(username, password):
    """Valida usuário comparando o hash da senha informada."""
    usuarios = carregar_usuarios()
    user_data = usuarios.get(username)
    if isinstance(user_data, dict):
        stored_hash = user_data.get("senha")
        if stored_hash and hash_password(password) == stored_hash:
            st.session_state.user_role = user_data.get("role", "user")
            return True
    return False

def display_login_screen():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.container(border=True):
            try:
                logo = Image.open(LOGO_PATH)
                st.markdown("<div class='login-container'>", unsafe_allow_html=True)
                st.image(logo, width=150)
                st.markdown("</div>", unsafe_allow_html=True) 
            except FileNotFoundError:
                st.markdown("## ViaFlix Login")
            except Exception as e:
                st.warning(f"Não foi possível carregar o logo: {e}")
                st.markdown("## ViaFlix Login")

            st.markdown("<h3 style='text-align: center;'>Acessar Dashboard</h3>", unsafe_allow_html=True)
            username = st.text_input("Usuário", key="login_user_gsheets", placeholder="seu_usuario")
            password = st.text_input("Senha", type="password", key="login_pass_gsheets", placeholder="********")
            if st.button("Entrar", key="login_btn_gsheets", use_container_width=True, type="primary"):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.app_state = "loading_data" # Mudar para estado de carregamento
                    st.rerun()
                else: st.error("Usuário ou senha inválidos.")

# --- FUNÇÃO PARA CARREGAR E PROCESSAR DADOS DO GOOGLE SHEETS --- 
def load_and_process_data():
    url = GOOGLE_SHEET_URL
    st.info(f"Carregando e processando dados de: {url}")
    df_processado, df_alertas = processar_planilha_google_sheets(
        google_sheet_url=url,
        tipo_margem_selecionada_ui_proc=st.session_state.tipo_margem_selecionada_state,
        data_inicio_analise_proc=st.session_state.data_inicio_analise_state,
        data_fim_analise_proc=st.session_state.data_fim_analise_state,
        col_margem_estrategica=COL_MARGEM_ESTRATEGICA_PLANILHA_CUSTOS,
        col_margem_real=COL_MARGEM_REAL_PLANILHA_CUSTOS,
        col_tipo_anuncio_ml_planilha_proc=COL_TIPO_ANUNCIO_ML_CUSTOS,
        _dummy_rerun_arg=st.session_state.dummy_rerun_counter
    )

    if df_processado is not None and not df_processado.empty:
        st.session_state.df_result = df_processado
        st.session_state.df_alertas_full = df_alertas # Armazena o DF de alertas
        st.session_state.data_loaded = True
        st.session_state.app_state = "dashboard"
        st.success("Dados carregados e processados com sucesso!")
        st.rerun()
    elif df_processado is not None and df_processado.empty:
        st.warning("Nenhum dado encontrado para o período selecionado após o processamento.")
        st.session_state.df_result = pd.DataFrame()
        st.session_state.df_alertas_full = pd.DataFrame()
        st.session_state.data_loaded = True
        st.session_state.app_state = "dashboard"
        st.rerun()
    else:
        st.session_state.data_loaded = False
        st.session_state.app_state = "error_loading"

# --- FUNÇÕES DE EXIBIÇÃO DO DASHBOARD --- 
def display_metrics(df, tipo_margem_selecionada_ui_metrics, categoria=None):
    if df is None or df.empty: return
    df_display = df.copy()
    if categoria and COL_TIPO_VENDA in df_display.columns: # Usar COL_TIPO_VENDA para filtrar por categoria
        df_display = df_display[df_display[COL_TIPO_VENDA] == categoria]
    if df_display.empty: 
        # Se a categoria não tiver dados, não mostrar nada para ela
        if categoria:
            st.info(f"Sem dados para a categoria: {categoria}")
        return

    total_pedidos = df_display[COL_VALOR_PEDIDO_CUSTOS].sum()
    margem_col_num = 'Margem_Num'
    if margem_col_num not in df_display.columns: margem_col_num = 'Margem_Estrategica_Num'
    
    if COL_VALOR_PEDIDO_CUSTOS in df_display.columns and margem_col_num in df_display.columns and df_display[COL_VALOR_PEDIDO_CUSTOS].sum() != 0:
        margem_media_pond = np.average(df_display[margem_col_num], weights=df_display[COL_VALOR_PEDIDO_CUSTOS])
    elif margem_col_num in df_display.columns:
        margem_media_pond = df_display[margem_col_num].mean()
    else:
        margem_media_pond = 0

    num_pedidos_unicos = df_display.shape[0]
    valor_medio_pedido = total_pedidos / num_pedidos_unicos if num_pedidos_unicos > 0 else 0
    
    margem_liquida_media = df_display['Margem_Liquida'].mean() if 'Margem_Liquida' in df_display.columns else 0
    
    # Define o label da métrica (Geral ou por Categoria)
    label_sufixo = f" {categoria}" if categoria else " Geral"
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Pedidos{label_sufixo}</div><div class='metric-value'>{format_currency_brl(total_pedidos)}</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Média{label_sufixo} ({tipo_margem_selecionada_ui_metrics[0]})</div><div class='metric-value' style='color:{get_margin_color(margem_media_pond)};'>{formatar_margem_para_exibicao_final(margem_media_pond)}</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Líquida Média{label_sufixo}</div><div class='metric-value' style='color:{get_margin_color(margem_liquida_media)};'>{formatar_margem_para_exibicao_final(margem_liquida_media)}</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Ticket Médio{label_sufixo}</div><div class='metric-value'>{format_currency_brl(valor_medio_pedido)}</div></div>", unsafe_allow_html=True)

def display_charts(df, tipo_margem_selecionada_ui_charts):
    if df is None or df.empty: return
    df_chart = df.copy()
    df_chart['MesAno'] = df_chart[COL_DATA_CUSTOS].dt.to_period('M').astype(str)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=False):
            st.markdown("<div class='custom-chart-container'>", unsafe_allow_html=True)
            st.subheader("📈 Performance Mensal")
            df_monthly = df_chart.groupby('MesAno').agg(
                Total_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'sum'),
                Margem_Media=('Margem_Num', 'mean') # Usar média simples aqui
            ).reset_index()
            fig_monthly = px.bar(df_monthly, x='MesAno', y='Total_Pedidos', title="Total de Pedidos por Mês", labels={'Total_Pedidos': 'Total Pedidos (R$)', 'MesAno': 'Mês'}, text_auto='.2s')
            fig_monthly.update_traces(marker_color=primary_color, textposition='outside')
            fig_monthly.update_layout(yaxis_title="Total Pedidos (R$)", xaxis_title="Mês", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_monthly, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.container(border=False):
            st.markdown("<div class='custom-chart-container'>", unsafe_allow_html=True)
            st.subheader("📊 Distribuição por Marketplace")
            df_marketplace = df_chart.groupby(COL_PLATAFORMA_CUSTOS).agg(
                Total_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'sum')
            ).reset_index().sort_values(by='Total_Pedidos', ascending=False)
            fig_pie = px.pie(df_marketplace, values='Total_Pedidos', names=COL_PLATAFORMA_CUSTOS, title="Distribuição de Pedidos por Marketplace", hole=0.4)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# --- ALTERADO: Função para exibir a Análise Detalhada (Layout e Tabela Ajustados v2) ---
def display_detailed_analysis_sku(df):
    st.markdown("## Análise Detalhada") # Título ajustado
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para exibir a análise detalhada.")
        return

    df_analysis = df.copy()

    # --- Filtros na Área Principal (Ajustados v2) ---
    st.markdown("<div class='custom-filter-container'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Filtro Marketplace
        marketplaces = ["Todos"] + sorted(df_analysis[COL_PLATAFORMA_CUSTOS].unique().tolist())
        marketplace_selecionado = st.selectbox(
            "Filtrar por Marketplace",
            options=marketplaces,
            key="det_marketplace_filter_widget", # Chave única para o widget
            index=marketplaces.index(st.session_state.det_marketplace_filter_state) # Usar estado específico
        )
        st.session_state.det_marketplace_filter_state = marketplace_selecionado # Atualizar estado específico

    with col2:
        # Filtro Conta (NOVO v2)
        contas = ["Todos"] + sorted(df_analysis[COL_CONTA_CUSTOS_ORIGINAL].unique().tolist())
        conta_selecionada = st.selectbox(
            "Filtrar por Conta",
            options=contas,
            key="det_conta_filter_widget", # Chave única
            index=contas.index(st.session_state.det_conta_filter_state) # Usar estado específico
        )
        st.session_state.det_conta_filter_state = conta_selecionada # Atualizar estado específico

    with col3:
        # Filtro Tipo de Anúncio
        if NOME_PADRAO_TIPO_ANUNCIO in df_analysis.columns:
            tipos_anuncio = ["Todos"] + sorted(df_analysis[NOME_PADRAO_TIPO_ANUNCIO].unique().tolist())
            tipo_anuncio_selecionado = st.selectbox(
                "Filtrar por Tipo Anúncio",
                options=tipos_anuncio,
                key="det_tipo_anuncio_filter_widget", # Chave única
                index=tipos_anuncio.index(st.session_state.det_tipo_anuncio_filter_state) # Usar estado específico
            )
            st.session_state.det_tipo_anuncio_filter_state = tipo_anuncio_selecionado # Atualizar estado específico
        else:
            st.markdown("Coluna Tipo Anúncio indisponível.")
            st.session_state.det_tipo_anuncio_filter_state = "Todos"

    with col4:
        # Filtro Tipo de Envio
        if NOME_PADRAO_TIPO_ENVIO in df_analysis.columns:
            tipos_envio = ["Todos"] + sorted(df_analysis[NOME_PADRAO_TIPO_ENVIO].unique().tolist())
            tipo_envio_selecionado = st.selectbox(
                "Filtrar por Tipo Envio",
                options=tipos_envio,
                key="det_tipo_envio_filter_widget", # Chave única
                index=tipos_envio.index(st.session_state.det_tipo_envio_filter_state) # Usar estado específico
            )
            st.session_state.det_tipo_envio_filter_state = tipo_envio_selecionado # Atualizar estado específico
        else:
            st.markdown("Coluna Tipo Envio indisponível.")
            st.session_state.det_tipo_envio_filter_state = "Todos"

    # Filtro SKU (ocupa a linha inteira)
    sku_filter = st.text_input(
        "Filtrar por SKU (parcial ou completo)",
        value=st.session_state.det_sku_text_filter_state, # Usar estado específico
        key="det_sku_text_filter_widget", # Chave única
        placeholder="Digite parte do SKU..."
    )
    st.session_state.det_sku_text_filter_state = sku_filter # Atualizar estado específico

    st.markdown("</div>", unsafe_allow_html=True)
    # --- Fim Filtros ---

    # Aplicar filtros (Ajustado v2)
    df_filtered = df_analysis.copy()
    if marketplace_selecionado != "Todos":
        df_filtered = df_filtered[df_filtered[COL_PLATAFORMA_CUSTOS] == marketplace_selecionado]
    if conta_selecionada != "Todos": # Usar filtro de conta
        df_filtered = df_filtered[df_filtered[COL_CONTA_CUSTOS_ORIGINAL] == conta_selecionada]
    if NOME_PADRAO_TIPO_ANUNCIO in df_filtered.columns and tipo_anuncio_selecionado != "Todos":
        df_filtered = df_filtered[df_filtered[NOME_PADRAO_TIPO_ANUNCIO] == tipo_anuncio_selecionado]
    if NOME_PADRAO_TIPO_ENVIO in df_filtered.columns and tipo_envio_selecionado != "Todos":
        df_filtered = df_filtered[df_filtered[NOME_PADRAO_TIPO_ENVIO] == tipo_envio_selecionado]
    if sku_filter:
        df_filtered = df_filtered[df_filtered[COL_SKU_CUSTOS].astype(str).str.contains(sku_filter, case=False, na=False)]

        # --- NOVO: Agrupamento por SKU, Conta e Marketplace --- 
    # Agrupa os dados para evitar duplicidade e agrega métricas.
    group_by_cols_orig = [COL_SKU_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL, COL_PLATAFORMA_CUSTOS]
    df_grouped = pd.DataFrame() # Inicializa vazio

    if not all(col in df_filtered.columns for col in group_by_cols_orig):
        st.warning("Colunas necessárias para agrupamento (SKU, Conta, Marketplace) não encontradas. Agrupamento não aplicado.")
        # Mantém df_filtered como está se não puder agrupar
    else:
        # Definir colunas para agregar e como agregar
        agg_dict = {
            # Nomes ORIGINAIS das colunas em df_filtered
            COL_QUANTIDADE_CUSTOS_ABA_CUSTOS: 'sum',
            COL_VALOR_PEDIDO_CUSTOS: 'sum',
            'Margem_Num': 'mean', # Média simples. Ponderada por VALOR_PEDIDO seria mais preciso.
            'Margem_Original': 'first', # Pega a primeira string formatada (para manter o formato)
            COL_VALOR_PRODUTO_PLANILHA_CUSTOS: 'first', # Média do preço unitário
            COL_ESTOQUE_VF: 'first',
            COL_ESTOQUE_GS: 'first',
            COL_ESTOQUE_DK: 'first',
            COL_ESTOQUE_TINY: 'first',
            COL_ESTOQUE_TOTAL_FULL: 'first',
            COL_ID_PRODUTO_CUSTOS: 'first', # Manter o ID do produto
            NOME_PADRAO_TIPO_ANUNCIO: 'first', # Manter o tipo de anúncio (pode variar, pegar o primeiro)
            "Valor de ADS": 'first' # Manter o valor de ADS (placeholder)
            # Adicione outras colunas e agregações conforme necessário
        }

        # Filtrar o agg_dict para incluir apenas colunas que existem em df_filtered
        agg_dict_existente = {k: v for k, v in agg_dict.items() if k in df_filtered.columns}
        cols_to_agg = list(agg_dict_existente.keys())

        # Verificar se há colunas para agregar
        if not cols_to_agg:
            st.warning("Nenhuma coluna numérica ou de agregação encontrada para o agrupamento.")
        else:
            try:
                # Selecionar colunas necessárias para o agrupamento
                df_to_group = df_filtered[group_by_cols_orig + cols_to_agg].copy()
                
                # Realizar o agrupamento
                df_grouped = df_to_group.groupby(group_by_cols_orig, as_index=False).agg(agg_dict_existente)
                st.success(f"Dados agrupados por SKU, Conta e Marketplace. {len(df_grouped)} linhas resultantes.")
                
                # --- IMPORTANTE: Reaplicar formatação nas colunas agregadas --- 
                # A coluna 'Margem_Original' já foi pega como 'first', então mantém o formato.
                # Precisamos reformatar as colunas numéricas agregadas.
                if COL_QUANTIDADE_CUSTOS_ABA_CUSTOS in df_grouped.columns:
                    df_grouped[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS] = df_grouped[COL_QUANTIDADE_CUSTOS_ABA_CUSTOS].apply(format_integer)
                if COL_VALOR_PEDIDO_CUSTOS in df_grouped.columns:
                    # Talvez não precise formatar o valor total do pedido aqui, mas sim o preço unitário médio?
                    pass # Deixar como número por enquanto
                if COL_VALOR_PRODUTO_PLANILHA_CUSTOS in df_grouped.columns:
                    df_grouped[COL_VALOR_PRODUTO_PLANILHA_CUSTOS] = df_grouped[COL_VALOR_PRODUTO_PLANILHA_CUSTOS].apply(format_currency_brl)
                # Estoques já são 'first', devem manter o formato original (int)
                # Margem_Num será usada para estilização, não precisa formatar para exibição.
                
                # Substituir o DataFrame filtrado pelo agrupado para a exibição
                df_filtered = df_grouped
                
            except Exception as e_group:
                st.error(f"Erro durante o agrupamento: {e_group}")
                st.error(traceback.format_exc())
                # Mantém df_filtered como estava antes do erro de agrupamento

    # --- Fim Agrupamento ---

    # --- Exibir Tabela Detalhada (COM Formatação Condicional de Margem) --- # (Título atualizado)
    # --- Exibir Tabela Detalhada (SEM Agregação - Ajustado v2) ---
    if not df_filtered.empty:
        
        # Colunas a serem exibidas e ordem desejada
        colunas_desejadas_map = {
            COL_SKU_CUSTOS: "SKU",
            COL_ID_PRODUTO_CUSTOS: "ID do Produto",
            COL_CONTA_CUSTOS_ORIGINAL: "Conta",
            COL_PLATAFORMA_CUSTOS: "Marketplace",
            "Margem_Original": "Margem", # Usar a coluna já formatada com %
            COL_QUANTIDADE_CUSTOS_ABA_CUSTOS: "Und Vendidas",
            COL_VALOR_PRODUTO_PLANILHA_CUSTOS: "Preço Vendido Und",
            COL_ESTOQUE_VF: "Estoque Full VF",
            COL_ESTOQUE_GS: "Estoque Full GS",
            COL_ESTOQUE_DK: "Estoque Full DK", # Adicionado v2
            COL_ESTOQUE_TINY: "Estoque Full Tiny", # Renomeado conforme pedido
            COL_ESTOQUE_TOTAL_FULL: "Estoque Total Full", # Renomeado conforme pedido
            # COL_VALOR_ADS: "Valor de ADS", # Coluna placeholder
            NOME_PADRAO_TIPO_ANUNCIO: "Tipo de Anúncio"
        }
        
        if "Valor de ADS" in df_filtered.columns:
            colunas_desejadas_map["Valor de ADS"] = "Valor de ADS"
        if "Margem_Liquida_Original" in df_filtered.columns:
            colunas_desejadas_map["Margem_Liquida_Original"] = "Margem Líquida"

        # Filtrar o DataFrame para conter apenas as colunas necessárias (na ordem original do df)
        colunas_originais_necessarias = [col for col in colunas_desejadas_map.keys() if col in df_filtered.columns]
        df_display_detalhada = df_filtered[colunas_originais_necessarias].copy()

        # Renomear colunas
        df_display_detalhada.rename(columns=colunas_desejadas_map, inplace=True)

        # Aplicar formatação
        # (Margem já vem formatada como string da coluna Margem_Original)
        if "Und Vendidas" in df_display_detalhada.columns: 
            df_display_detalhada["Und Vendidas"] = df_display_detalhada["Und Vendidas"].apply(format_integer)
        if "Preço Vendido Und" in df_display_detalhada.columns:
            df_display_detalhada["Preço Vendido Und"] = df_display_detalhada["Preço Vendido Und"].apply(format_currency_brl)
        if "Estoque Full VF" in df_display_detalhada.columns:
            df_display_detalhada["Estoque Full VF"] = df_display_detalhada["Estoque Full VF"].apply(format_integer)
        if "Estoque Full GS" in df_display_detalhada.columns:
            df_display_detalhada["Estoque Full GS"] = df_display_detalhada["Estoque Full GS"].apply(format_integer)
        if "Estoque Full DK" in df_display_detalhada.columns:
            df_display_detalhada["Estoque Full DK"] = df_display_detalhada["Estoque Full DK"].apply(format_integer)
        if "Estoque Full Tiny" in df_display_detalhada.columns:
            df_display_detalhada["Estoque Full Tiny"] = df_display_detalhada["Estoque Full Tiny"].apply(format_integer)
        if "Estoque Total Full" in df_display_detalhada.columns:
            df_display_detalhada["Estoque Total Full"] = df_display_detalhada["Estoque Total Full"].apply(format_integer)
        if "Valor de ADS" in df_display_detalhada.columns:
            df_display_detalhada["Valor de ADS"] = df_display_detalhada["Valor de ADS"].apply(format_currency_brl)
        if "Margem Líquida" in df_display_detalhada.columns:
            pass  # já está formatada    
        # ID do Produto e Tipo de Anúncio geralmente são strings, não precisam de formatação numérica
        # Conta e Marketplace também são strings
        # SKU é string
        # Valor de ADS é string "N/A"

        # Garantir a ordem final das colunas
        ordem_final_colunas = [
            "SKU", "ID do Produto", "Conta", "Marketplace", "Margem", "Und Vendidas",
            "Preço Vendido Und", "Estoque Full VF", "Estoque Full GS", "Estoque Full DK",
            "Estoque Full Tiny", "Estoque Total Full", "Valor de ADS", "Margem Líquida", "Tipo de Anúncio"
        ]
        # Filtrar a ordem pelas colunas que realmente existem em df_display_detalhada
        ordem_final_existente = [col for col in ordem_final_colunas if col in df_display_detalhada.columns]
        df_display_detalhada = df_display_detalhada[ordem_final_existente]

        # Exibir tabela
        st.dataframe(df_display_detalhada, use_container_width=True, hide_index=True)

        # --- Botão de Download CSV (Ajustado v2) --- 
        @st.cache_data
        def convert_df_to_csv_detalhado(df_to_convert):
            # Certificar que o DataFrame passado para conversão é o final formatado
            return df_to_convert.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

        csv_data = convert_df_to_csv_detalhado(df_display_detalhada) # Usar o df final
        st.download_button(
            label="📥 Baixar CSV Detalhado",
            data=csv_data,
            file_name=f"analise_detalhada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", # Nome do arquivo ajustado
            mime="text/csv",
            key="download_det_csv_v2" # Nova chave para evitar conflito
        )

    else:
        st.info("Nenhum resultado encontrado para os filtros selecionados.")
# --- FIM display_detailed_analysis_sku ---

# --- ALTERADO: Função para exibir a página de Alertas (Layout Ajustado) ---
def display_alerts(df_alertas_completo):
    st.markdown("## ⚠️ Alertas")

    if df_alertas_completo is None or df_alertas_completo.empty:
        st.info("Não há alertas de estoque para exibir.")
        return

    # Layout de duas colunas
    col_filtros, col_tabela = st.columns([1, 3]) # Coluna de filtros menor

    with col_filtros:
        st.markdown("<div class='alert-filter-column'>", unsafe_allow_html=True)
        st.subheader("Filtros de Alertas")

        # 1. Tipo de Alerta (Exemplo, adaptar conforme necessidade)
        #    Tipos podem vir de uma análise prévia ou serem fixos.
        #    Aqui, vamos usar tipos fixos como exemplo.
        tipos_alerta_opts = ["Todos", "Margens Críticas", "Estoque Parado", "Concorrência de Vendedores", "Alta Performance"]
        tipo_alerta_sel = st.radio(
            "Tipo de Alerta",
            options=tipos_alerta_opts,
            key="alert_tipo_alerta_filter_widget",
            index=tipos_alerta_opts.index(st.session_state.alert_tipo_alerta_filter)
        )
        st.session_state.alert_tipo_alerta_filter = tipo_alerta_sel

        # 2. Marketplace
        marketplaces_alert = ["Todos"] + sorted(df_alertas_completo[COL_PLATAFORMA_CUSTOS].unique().tolist())
        marketplace_alert_sel = st.selectbox(
            "Marketplace",
            options=marketplaces_alert,
            key="alert_marketplace_filter_widget",
            index=marketplaces_alert.index(st.session_state.alert_marketplace_filter)
        )
        st.session_state.alert_marketplace_filter = marketplace_alert_sel

        # 3. Conta
        contas_alert = ["Todos"] + sorted(df_alertas_completo[COL_CONTA_CUSTOS_ORIGINAL].unique().tolist())
        conta_alert_sel = st.selectbox(
            "Conta",
            options=contas_alert,
            key="alert_conta_filter_widget",
            index=contas_alert.index(st.session_state.alert_conta_filter)
        )
        st.session_state.alert_conta_filter = conta_alert_sel

        # 4. Buscar produto (SKU, ID ou nome)
        sku_alert_filter = st.text_input(
            "Buscar produto",
            value=st.session_state.alert_sku_filter,
            key="alert_sku_filter_widget",
            placeholder="SKU, ID ou nome..."
        )
        st.session_state.alert_sku_filter = sku_alert_filter

        st.divider()

        # 5. Ordenação
        st.subheader("Ordenação")
        # Colunas disponíveis para ordenar (ajustar conforme colunas reais em df_alertas_completo)
        # Usar nomes *antes* da renomeação final, se aplicável
        ordenar_por_opts = ["Margem", "Estoque Tiny", "Estoque Total Full", "SKU"]
        # Mapear nomes de exibição para nomes reais das colunas se necessário
        ordenar_por_map = {
            "Margem": "Margem_Num", # Usar a coluna numérica para ordenar
            "Estoque Tiny": COL_ESTOQUE_TINY,
            "Estoque Total Full": COL_ESTOQUE_TOTAL_FULL,
            "SKU": COL_SKU_CUSTOS
        }
        ordenar_por_sel = st.selectbox(
            "Ordenar por",
            options=ordenar_por_opts,
            key="alert_ordenar_por_widget",
            index=ordenar_por_opts.index(st.session_state.alert_ordenar_por)
        )
        st.session_state.alert_ordenar_por = ordenar_por_sel

        ordem_sel = st.radio(
            "Ordem",
            options=["Crescente", "Decrescente"],
            key="alert_ordem_widget",
            horizontal=True,
            index=["Crescente", "Decrescente"].index(st.session_state.alert_ordem)
        )
        st.session_state.alert_ordem = ordem_sel

        st.markdown("</div>", unsafe_allow_html=True)
        # --- Fim Coluna Filtros ---

    with col_tabela:
        st.markdown("<div class='alert-table-column'>", unsafe_allow_html=True)

        # --- Aplicar Filtros --- 
        df_alertas_filtrado = df_alertas_completo.copy()

        # Filtrar por Tipo de Alerta (Exemplo: Margens Críticas < 10%)
        if tipo_alerta_sel == "Margens Críticas":
            if 'Margem_Num' in df_alertas_filtrado.columns:
                df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Margem_Num'] < 10]
            else:
                st.warning("Coluna 'Margem_Num' necessária para filtro 'Margens Críticas' não encontrada.")
        # Adicionar lógica para outros tipos de alerta aqui...
        elif tipo_alerta_sel == "Estoque Parado":
             # Exemplo: Estoque total full = 0 e Estoque Tiny > 0 (ajustar lógica conforme regra real)
             if COL_ESTOQUE_TOTAL_FULL in df_alertas_filtrado.columns and COL_ESTOQUE_TINY in df_alertas_filtrado.columns:
                 df_alertas_filtrado = df_alertas_filtrado[
                     (df_alertas_filtrado[COL_ESTOQUE_TOTAL_FULL].fillna(0) == 0) & 
                     (df_alertas_filtrado[COL_ESTOQUE_TINY].fillna(0) > 0)
                 ]
             else:
                 st.warning("Colunas de estoque necessárias para filtro 'Estoque Parado' não encontradas.")
        # ... (outros filtros de tipo de alerta)

        # Filtrar por Marketplace
        if marketplace_alert_sel != "Todos":
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado[COL_PLATAFORMA_CUSTOS] == marketplace_alert_sel]
        
        # Filtrar por Conta
        if conta_alert_sel != "Todos":
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado[COL_CONTA_CUSTOS_ORIGINAL] == conta_alert_sel]

        # Filtrar por SKU/ID/Nome
        if sku_alert_filter:
            # Procurar em colunas relevantes (ajustar se necessário)
            mask_sku = df_alertas_filtrado[COL_SKU_CUSTOS].astype(str).str.contains(sku_alert_filter, case=False, na=False)
            mask_id = pd.Series(False, index=df_alertas_filtrado.index) # Inicializa com False
            if COL_ID_PRODUTO_CUSTOS in df_alertas_filtrado.columns:
                 mask_id = df_alertas_filtrado[COL_ID_PRODUTO_CUSTOS].astype(str).str.contains(sku_alert_filter, case=False, na=False)
            
            df_alertas_filtrado = df_alertas_filtrado[mask_sku | mask_id]

        # --- Ordenação --- 
        coluna_ordenacao = ordenar_por_map.get(ordenar_por_sel, COL_SKU_CUSTOS) # Usa SKU como fallback
        ascending_order = (ordem_sel == "Crescente")
        if coluna_ordenacao in df_alertas_filtrado.columns:
            # Tratar NaNs antes de ordenar, especialmente para colunas numéricas
            if pd.api.types.is_numeric_dtype(df_alertas_filtrado[coluna_ordenacao]):
                 df_alertas_filtrado = df_alertas_filtrado.sort_values(
                     by=coluna_ordenacao, 
                     ascending=ascending_order, 
                     na_position='last' # Coloca NaNs no final
                 )
            else: # Para colunas de texto
                 df_alertas_filtrado = df_alertas_filtrado.sort_values(
                     by=coluna_ordenacao, 
                     ascending=ascending_order, 
                     na_position='last'
                 )
        else:
             st.warning(f"Coluna de ordenação '{coluna_ordenacao}' não encontrada.")

        # --- Preparar para Exibição --- 
        if not df_alertas_filtrado.empty:
            # Selecionar e renomear colunas para exibição (conforme Imagem 3)
            cols_to_show_alert = {
                COL_SKU_CUSTOS: "SKU",
                COL_ID_PRODUTO_CUSTOS: "ID do Produto",
                COL_CONTA_CUSTOS_ORIGINAL: "Conta",
                COL_PLATAFORMA_CUSTOS: "Marketplace",
                "Margem_Original": "Margem", # Usar a margem já formatada
                COL_ESTOQUE_TINY: "Estoque Tiny",
                COL_ESTOQUE_TOTAL_FULL: "Estoque Total Full ML" # Nome da imagem
            }
            # Filtrar colunas que realmente existem no DataFrame
            cols_existentes = {k: v for k, v in cols_to_show_alert.items() if k in df_alertas_filtrado.columns}
            df_display_alert = df_alertas_filtrado[list(cols_existentes.keys())].copy()
            df_display_alert.rename(columns=cols_existentes, inplace=True)

            # Formatar colunas numéricas (estoque)
            if "Estoque Tiny" in df_display_alert.columns:
                df_display_alert["Estoque Tiny"] = df_display_alert["Estoque Tiny"].apply(format_integer)
            if "Estoque Total Full ML" in df_display_alert.columns:
                df_display_alert["Estoque Total Full ML"] = df_display_alert["Estoque Total Full ML"].apply(format_integer)
            
            # Adicionar coluna de ID do Produto se não existir, com valor padrão 'None'
            if "ID do Produto" not in df_display_alert.columns:
                df_display_alert.insert(1, "ID do Produto", "None") # Insere após SKU
                
            # Garantir a ordem das colunas como na imagem
            final_cols_order_alert = ["SKU", "ID do Produto", "Conta", "Marketplace", "Margem", "Estoque Tiny", "Estoque Total Full ML"]
            # Filtrar pelas colunas que realmente existem em df_display_alert
            final_cols_order_alert_existentes = [col for col in final_cols_order_alert if col in df_display_alert.columns]
            df_display_alert = df_display_alert[final_cols_order_alert_existentes]

            # Título da Tabela
            st.subheader(f"Tabela de Alertas ({len(df_display_alert)} itens)")
            # Exibir tabela
            st.dataframe(df_display_alert, use_container_width=True, hide_index=True)

            # --- Botão de Download CSV --- 
            @st.cache_data
            def convert_df_to_csv_alert(df_to_convert):
                return df_to_convert.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

            csv_data_alert = convert_df_to_csv_alert(df_display_alert)
            st.download_button(
                label="📥 Baixar Alertas Filtrados (CSV)",
                data=csv_data_alert,
                file_name=f"alertas_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_alert_csv"
            )
        else:
            st.info("Nenhum alerta encontrado para os filtros selecionados.")

        st.markdown("</div>", unsafe_allow_html=True)
        # --- Fim Coluna Tabela ---
# --- FIM display_alerts ---

def display_map(df):
    st.markdown("## 🗺️ Mapa de Vendas")
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para exibir o mapa.")
        return
    if COL_ESTADO not in df.columns:
        st.warning(f"Coluna '{COL_ESTADO}' necessária para o mapa não encontrada nos dados.")
        return

    with st.container(border=False):
        st.markdown("<div class='custom-chart-container'>", unsafe_allow_html=True)
        mapa_fig = criar_mapa_brasil_interativo(df, COL_ESTADO, COL_VALOR_PEDIDO_CUSTOS)
        if mapa_fig:
            st.plotly_chart(mapa_fig, use_container_width=True)
        else:
            st.warning("Não foi possível gerar o mapa.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL DA APLICAÇÃO ---
def main():
    # --- LOGIN --- 
    if not st.session_state.authenticated:
        display_login_screen()
        return

    # --- CARREGAMENTO INICIAL DOS DADOS --- 
    if st.session_state.app_state == "loading_data":
        with st.spinner("Processando dados... Por favor, aguarde."):
            load_and_process_data()
        # Se load_and_process_data mudar o estado para 'dashboard' ou 'error_loading',
        # o rerun cuidará de exibir a tela correta.
        # Se continuar em 'loading_data' (improvável), mostra a mensagem.
        if st.session_state.app_state == "loading_data":
            st.info("Aguardando o processamento dos dados.")
        return # Evita executar o resto do código enquanto carrega

    # --- ERRO NO CARREGAMENTO --- 
    if st.session_state.app_state == "error_loading":
        st.error("Ocorreu um erro ao carregar ou processar os dados. Verifique as mensagens acima.")
        # Adicionar um botão para tentar recarregar?
        if st.button("Tentar Recarregar Dados"):
            st.session_state.app_state = "loading_data"
            st.session_state.dummy_rerun_counter += 1 # Forçar re-execução do processamento
            st.rerun()
        return

    # --- DADOS NÃO CARREGADOS (ESTADO INICIAL APÓS LOGIN) --- 
    if not st.session_state.data_loaded:
         st.session_state.app_state = "loading_data"
         st.rerun() # Inicia o carregamento
         return

    # --- SIDEBAR (APÓS LOGIN E CARREGAMENTO) --- 
    with st.sidebar:
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=200,)
        except FileNotFoundError:
            st.markdown("<h1 class='sidebar-title'>ViaFlix</h1>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Erro ao carregar logo: {e}")
            st.markdown("<h1 class='sidebar-title'>ViaFlix</h1>", unsafe_allow_html=True)

        st.markdown("<p class='sidebar-text' style='text-align:center; font-size:20px; margin-bottom: 1rem;'>Painel Via Flix</p>", unsafe_allow_html=True)

        # Menu de Navegação
        selected = option_menu(
            menu_title="",
            options=["Dashboard", "Análise Detalhada", "Alertas", "Mapa", "Devolução", "Configurações"],
            icons=["house-door-fill", "search", "exclamation-triangle-fill", "map-fill", "arrow-left-right", "gear-fill"],
            menu_icon="speedometer2",
            default_index=["Dashboard", "Análise Detalhada", "Alertas", "Mapa", "Devolução", "Configurações"].index(st.session_state.selected_page),
            styles={
                "container": {"padding": "5px !important", "background-color": background_sidebar},
                "icon": {"color": "#ffffff", "font-size": "20px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin":"0px",
                    "--hover-color": "rgba(255,255,255,0.1)",
                    "color": text_color_sidebar # Forçar cor do texto aqui
                },
                "nav-link-selected": {
                    "background-color": secondary_color,
                    "color": background_sidebar, # Cor do texto quando selecionado (escuro)
                    "font-weight": "bold"
                },
            }
        )
        st.session_state.selected_page = selected # Atualiza a página selecionada

        st.divider()
        st.markdown("<h3 class='sidebar-title'>Filtros Globais</h3>", unsafe_allow_html=True)

        # Filtro de Período
        periodo_options = ["7 dias", "15 dias", "30 dias", "60 dias", "90 dias", "Personalizado"]
        periodo_selecionado = st.selectbox(
            "Período",
            periodo_options,
            key="period_selector_gsheets",
            index=periodo_options.index(st.session_state.periodo_selecionado)
        )

        today = datetime.now().date()
        data_inicio_analise = st.session_state.data_inicio_analise_state
        data_fim_analise = st.session_state.data_fim_analise_state

        periodo_changed = False
        if periodo_selecionado != st.session_state.periodo_selecionado:
            periodo_changed = True
            st.session_state.periodo_selecionado = periodo_selecionado
            if periodo_selecionado == "7 dias": data_inicio_analise = today - timedelta(days=6)
            elif periodo_selecionado == "15 dias": data_inicio_analise = today - timedelta(days=14)
            elif periodo_selecionado == "30 dias": data_inicio_analise = today - timedelta(days=29)
            elif periodo_selecionado == "60 dias": data_inicio_analise = today - timedelta(days=59)
            elif periodo_selecionado == "90 dias": data_inicio_analise = today - timedelta(days=89)
            data_fim_analise = today # Sempre atualiza data fim para hoje quando muda período pré-definido

        if periodo_selecionado == "Personalizado":
            date_cols = st.columns(2)
            with date_cols[0]:
                new_data_inicio = st.date_input("Data Início", value=data_inicio_analise, key="date_start_gsheets")
            with date_cols[1]:
                new_data_fim = st.date_input("Data Fim", value=data_fim_analise, key="date_end_gsheets")
            if new_data_inicio != data_inicio_analise or new_data_fim != data_fim_analise:
                periodo_changed = True
                data_inicio_analise = new_data_inicio
                data_fim_analise = new_data_fim
        else:
            # Exibe as datas selecionadas (não editáveis)
            date_cols = st.columns(2)
            with date_cols[0]:
                st.date_input("Data Início", value=data_inicio_analise, key="date_start_disp_gsheets", disabled=True)
            with date_cols[1]:
                st.date_input("Data Fim", value=data_fim_analise, key="date_end_disp_gsheets", disabled=True)

        # Filtro Conta Mãe (Filtro Global)
        df_result = st.session_state.df_result
        contas_mae = ["Todas"] + sorted(df_result[COL_CONTA_CUSTOS_ORIGINAL].unique().tolist()) if df_result is not None and not df_result.empty else ["Todas"]
        conta_mae_selecionada = st.selectbox(
            "Contas",
            contas_mae,
            key="account_selector_gsheets",
            index=contas_mae.index(st.session_state.conta_mae_selecionada_ui_state)
        )

        # Filtro Tipo de Margem
        tipo_margem_options = ["Margem Estratégica (L)", "Margem Real (M)"]
        tipo_margem_selecionada = st.radio(
            "Tipo de Margem",
            tipo_margem_options,
            key="margin_type_selector_gsheets",
            index=tipo_margem_options.index(st.session_state.tipo_margem_selecionada_state)
        )

        # --- Botão Recarregar Dados --- 
        st.divider()
        if st.button("🔄 Recarregar Dados da Planilha", key="reload_data_gsheets", use_container_width=True):
            st.session_state.app_state = "loading_data"
            st.session_state.dummy_rerun_counter += 1 # Força re-execução do processamento
            st.cache_data.clear() # Limpa o cache para garantir leitura fresca
            st.rerun()

        st.divider()
        if st.button("Logout", key="logout_button_gsheets", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.app_state = "login"
            # Limpar outros estados relevantes ao fazer logout
            for key in default_states:
                 if key not in ['authenticated', 'app_state']: # Não resetar auth/app_state aqui
                     st.session_state[key] = default_states[key]
            st.cache_data.clear()
            st.rerun()

    # --- Lógica de Atualização e Filtragem --- 
    reprocess_needed = False
    if periodo_changed:
        st.session_state.data_inicio_analise_state = data_inicio_analise
        st.session_state.data_fim_analise_state = data_fim_analise
        reprocess_needed = True

    if tipo_margem_selecionada != st.session_state.tipo_margem_selecionada_state:
        st.session_state.tipo_margem_selecionada_state = tipo_margem_selecionada
        # Tentar atualizar margem sem reprocessar tudo
        if st.session_state.df_result is not None:
            st.session_state.df_result = atualizar_margem_sem_reprocessamento(
                st.session_state.df_result,
                tipo_margem_selecionada
            )
            # Atualizar também df_alertas_full se ele existir e tiver margens
            if st.session_state.df_alertas_full is not None and not st.session_state.df_alertas_full.empty:
                 st.session_state.df_alertas_full = atualizar_margem_sem_reprocessamento(
                     st.session_state.df_alertas_full,
                     tipo_margem_selecionada,
                     COL_MARGEM_ESTRATEGICA_PLANILHA_CUSTOS,
                     COL_MARGEM_REAL_PLANILHA_CUSTOS
                 )
        else:
            reprocess_needed = True # Se df_result for None, precisa reprocessar

    if conta_mae_selecionada != st.session_state.conta_mae_selecionada_ui_state:
        st.session_state.conta_mae_selecionada_ui_state = conta_mae_selecionada
        # A filtragem por conta mãe global é feita diretamente na exibição, não precisa reprocessar

    # Se o período mudou, forçar reprocessamento completo
    if reprocess_needed:
        st.session_state.app_state = "loading_data"
        st.session_state.dummy_rerun_counter += 1
        st.rerun()

    # Aplicar filtro de conta mãe global para exibição
    df_display = st.session_state.df_result
    df_alertas_display = st.session_state.df_alertas_full
    if df_display is not None and not df_display.empty and st.session_state.conta_mae_selecionada_ui_state != "Todas":
        df_display = df_display[df_display[COL_CONTA_CUSTOS_ORIGINAL] == st.session_state.conta_mae_selecionada_ui_state]
    if df_alertas_display is not None and not df_alertas_display.empty and st.session_state.conta_mae_selecionada_ui_state != "Todas":
        df_alertas_display = df_alertas_display[df_alertas_display[COL_CONTA_CUSTOS_ORIGINAL] == st.session_state.conta_mae_selecionada_ui_state]

    # --- EXIBIÇÃO DA PÁGINA SELECIONADA (Dashboard Corrigido v2) --- 
    if selected == "Dashboard":
        st.markdown("## Dashboard Geral")
        if df_display is not None and not df_display.empty:
            # Exibir métricas gerais UMA VEZ
            display_metrics(df_display, st.session_state.tipo_margem_selecionada_state)
            
            st.divider()
            display_charts(df_display, st.session_state.tipo_margem_selecionada_state)
        else:
            st.info("Não há dados suficientes para exibir o dashboard.")

    elif selected == "Análise Detalhada":
        # Chama a função com layout e tabela ajustados v2
        display_detailed_analysis_sku(df_display)

    elif selected == "Alertas":
        # Chama a função com layout ajustado
        display_alerts(df_alertas_display)

    elif selected == "Mapa":
        display_map(df_display)

    elif selected == "Devolução":
        st.markdown("## 🔄 Devolução")
        st.info("Página de Devolução em construção.")
        # Adicionar conteúdo da página de devolução aqui

    elif selected == "Configurações":
        st.markdown("## ⚙️ Configurações")
        st.info("Página de Configurações em construção.")
        # Adicionar conteúdo da página de configurações aqui

# --- PONTO DE ENTRADA --- 
if __name__ == "__main__":
    main()

