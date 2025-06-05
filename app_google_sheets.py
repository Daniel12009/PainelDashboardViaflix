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
from processar_planilha_google_sheets import processar_planilha_google_sheets

# Importar funções dos outros módulos (manter se ainda forem usadas)
from personalizar_tabela_melhorado import personalizar_tabela_por_marketplace
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

# Colunas numéricas usadas no cálculo da Margem Líquida (nomes após processamento)
COL_LIQUIDO_REAL_NUM = "Liquido_Real_Num"
COL_LIQUIDO_ESTRATEGICO_NUM = "Liquido_Estrategico_Num"
COL_VALOR_ADS_NUM = "Valor de ADS" # Assumindo que esta coluna já é numérica após processamento
COL_FATURAMENTO_BRUTO_NUM = "Faturamento_Bruto"

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
    'tipo_margem_selecionada_state': "Margem Estratégica (L)", # Default para Estratégica
    # Filtros Análise Detalhada SKU (agora na página)
    'det_marketplace_filter_state': "Todos", 
    'det_conta_filter_state': "Todos", # Novo filtro Conta
    'det_tipo_anuncio_filter_state': "Todos",
    'det_tipo_envio_filter_state': "Todos",
    'det_sku_text_filter_state': "",
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
    except: return str(value) # Retorna como string se não puder formatar

def format_integer(value):
    if pd.isna(value): return 0
    try: return int(value)
    except (ValueError, TypeError): return 0

# CORRIGIDO: Função para formatar margem com 2 casas decimais para exibição
def formatar_margem_para_exibicao_final(valor_numerico_percentual):
    """Converte a margem numérica em string com 2 casas decimais e %."""
    if pd.isna(valor_numerico_percentual):
        return "0,00%"
    try:
        # Arredonda para 2 casas decimais ANTES de converter para string
        valor_arredondado = round(float(valor_numerico_percentual), 2)
        # Formata como string com vírgula e %
        return f"{valor_arredondado:.2f}%".replace('.', ',')
    except (ValueError, TypeError):
        # Fallback para valores não numéricos
        return str(valor_numerico_percentual)

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
            # Garante que a senha padrão do admin esteja hasheada se o arquivo existir mas estiver vazio/inválido
            if not isinstance(data, dict) or "admin" not in data or "senha" not in data["admin"]:
                 data = default
            elif len(data["admin"]["senha"]) != 64:
                 data["admin"]["senha"] = hash_password("admin") # Refaz o hash se estiver incorreto
            return data
        except Exception:
            return default
    else:
        return default

def salvar_usuarios(usuarios):
    """Salva usuários, garantindo que as senhas estejam hasheadas."""
    try:
        usuarios_hashed = usuarios.copy()
        for user, info in usuarios_hashed.items():
            pwd = info.get("senha")
            # Faz o hash apenas se a senha não parecer já ser um hash SHA-256
            if pwd and (not isinstance(pwd, str) or len(pwd) != 64):
                info["senha"] = hash_password(str(pwd))
        with open(USUARIOS_PATH, 'w') as f:
            json.dump(usuarios_hashed, f, indent=4)
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
                st.image(logo, width=150)
            except FileNotFoundError:
                st.markdown("## ViaFlix Login")
            except Exception as e:
                st.warning(f"Não foi possível carregar o logo: {e}")
                st.markdown("## ViaFlix Login")

            st.markdown("<h3 style='text-align: center;'>Acessar Dashboard</h3>", unsafe_allow_html=True)
            username = st.text_input("Usuário", key="login_user_gsheets", placeholder="seu_usuario")
            password = st.text_input("Senha", type="password", key="login_pass_gsheets", placeholder="********")
            if st.button("Entrar", key="login_button_gsheets", use_container_width=True):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.app_state = "dashboard" # Muda para o dashboard
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

# --- FUNÇÕES DE CARREGAMENTO E PROCESSAMENTO DE DADOS ---
@st.cache_data(ttl=600, show_spinner="Carregando e processando dados da planilha...")
def load_and_process_data(url, tipo_margem, data_inicio, data_fim, col_margem_estr, col_margem_real, col_tipo_anuncio, _dummy_rerun):
    return processar_planilha_google_sheets(
        google_sheet_url=url,
        tipo_margem_selecionada_ui_proc=tipo_margem,
        data_inicio_analise_proc=data_inicio,
        data_fim_analise_proc=data_fim,
        col_margem_estrategica=col_margem_estr,
        col_margem_real=col_margem_real,
        col_tipo_anuncio_ml_planilha_proc=col_tipo_anuncio,
        _dummy_rerun_arg=_dummy_rerun
    )

# --- FUNÇÕES DE EXIBIÇÃO (Dashboard, Análise Detalhada, etc.) ---
def display_sidebar():
    with st.sidebar:
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=100)
        except FileNotFoundError:
            st.markdown("<h1 style='color: white; text-align: center;'>ViaFlix</h1>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Erro ao carregar logo: {e}")
            st.markdown("<h1 style='color: white; text-align: center;'>ViaFlix</h1>", unsafe_allow_html=True)
        
        st.markdown("<p class='sidebar-text' style='text-align: center;'>Dashboard de Análise de Vendas</p>", unsafe_allow_html=True)
        st.divider()

        # Menu de Navegação
        st.session_state.selected_page = option_menu(
            menu_title=None, # "Menu Principal",
            options=["Dashboard", "Análise Detalhada", "Alertas", "Mapa de Vendas"],
            icons=["bi-speedometer2", "bi-search", "bi-bell-fill", "bi-map-fill"], # Ícones Bootstrap
            menu_icon="cast", default_index=["Dashboard", "Análise Detalhada", "Alertas", "Mapa de Vendas"].index(st.session_state.selected_page),
            styles={
                "container": {"padding": "5px !important", "background-color": background_sidebar},
                "icon": {"color": text_color_sidebar, "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "rgba(255,255,255,0.1)"},
                "nav-link-selected": {"background-color": secondary_color, "color": background_sidebar, "font-weight": "bold"},
            }
        )
        st.divider()

        st.markdown("<h4 class='sidebar-title'>Filtros Globais</h4>", unsafe_allow_html=True)

        # Seleção de Período
        periodo = st.radio(
            "Período de Análise",
            ["7 dias", "15 dias", "30 dias", "60 dias", "90 dias", "Personalizado"],
            key="periodo_radio_gsheets",
            index=["7 dias", "15 dias", "30 dias", "60 dias", "90 dias", "Personalizado"].index(st.session_state.periodo_selecionado),
            horizontal=True
        )
        st.session_state.periodo_selecionado = periodo

        data_inicio_dt = st.session_state.data_inicio_analise_state
        data_fim_dt = st.session_state.data_fim_analise_state

        if periodo != "Personalizado":
            delta_map = {"7 dias": 6, "15 dias": 14, "30 dias": 29, "60 dias": 59, "90 dias": 89}
            data_fim_dt = datetime.now().date()
            data_inicio_dt = data_fim_dt - timedelta(days=delta_map[periodo])
        else:
            col1, col2 = st.columns(2)
            with col1:
                data_inicio_dt = st.date_input("Data Início", value=st.session_state.data_inicio_analise_state, key="date_start_gsheets")
            with col2:
                data_fim_dt = st.date_input("Data Fim", value=st.session_state.data_fim_analise_state, key="date_end_gsheets")

        # Atualizar estado apenas se houver mudança
        if data_inicio_dt != st.session_state.data_inicio_analise_state or data_fim_dt != st.session_state.data_fim_analise_state:
            st.session_state.data_inicio_analise_state = data_inicio_dt
            st.session_state.data_fim_analise_state = data_fim_dt
            st.session_state.data_loaded = False # Forçar recarregamento dos dados

        # Seleção de Conta Mãe (se df_result estiver carregado)
        contas_disponiveis = ["Todas"]
        if st.session_state.df_result is not None and not st.session_state.df_result.empty and COL_CONTA_CUSTOS_ORIGINAL in st.session_state.df_result.columns:
            contas_disponiveis.extend(sorted(st.session_state.df_result[COL_CONTA_CUSTOS_ORIGINAL].unique().tolist()))
        
        conta_selecionada = st.selectbox(
            "Filtrar por Conta",
            options=contas_disponiveis,
            key="conta_mae_select_gsheets",
            index=contas_disponiveis.index(st.session_state.conta_mae_selecionada_ui_state) if st.session_state.conta_mae_selecionada_ui_state in contas_disponiveis else 0
        )
        # Atualizar estado apenas se houver mudança
        if conta_selecionada != st.session_state.conta_mae_selecionada_ui_state:
            st.session_state.conta_mae_selecionada_ui_state = conta_selecionada
            # Não precisa recarregar dados, filtro é aplicado depois

        # Seleção do Tipo de Margem
        tipo_margem = st.radio(
            "Tipo de Margem para Análise",
            ["Margem Estratégica (L)", "Margem Real (M)"],
            key="tipo_margem_radio_gsheets",
            index=["Margem Estratégica (L)", "Margem Real (M)"].index(st.session_state.tipo_margem_selecionada_state)
        )
        # Atualizar estado e forçar recarregamento se houver mudança
        if tipo_margem != st.session_state.tipo_margem_selecionada_state:
            st.session_state.tipo_margem_selecionada_state = tipo_margem
            st.session_state.data_loaded = False # Forçar recarregamento dos dados

        st.divider()
        if st.button("Logout", key="logout_button_gsheets", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.app_state = "login"
            # Limpar dados ao sair
            st.session_state.df_result = None
            st.session_state.df_alertas_full = None
            st.session_state.data_loaded = False
            st.rerun()

def display_metrics(df, tipo_margem_selecionada_ui_metrics, categoria=None):
    if df is None or df.empty:
        st.warning(f"Sem dados para exibir métricas{f' para {categoria}' if categoria else ''}.")
        # Exibir cards zerados para manter layout
        cols = st.columns(4)
        label_sufixo = f" {categoria}" if categoria else " Geral"
        with cols[0]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Pedidos{label_sufixo}</div><div class='metric-value'>R$ 0,00</div></div>", unsafe_allow_html=True)
        with cols[1]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Média{label_sufixo} ({tipo_margem_selecionada_ui_metrics[0]})</div><div class='metric-value'>0,00%</div></div>", unsafe_allow_html=True)
        with cols[2]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Líquida Média{label_sufixo}</div><div class='metric-value'>0,00%</div></div>", unsafe_allow_html=True)
        with cols[3]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Ticket Médio{label_sufixo}</div><div class='metric-value'>R$ 0,00</div></div>", unsafe_allow_html=True)
        return

    df_display = df.copy()
    if categoria:
        if COL_PLATAFORMA_CUSTOS in df_display.columns:
            df_display = df_display[df_display[COL_PLATAFORMA_CUSTOS] == categoria]
        else:
            st.warning(f"Coluna '{COL_PLATAFORMA_CUSTOS}' não encontrada para filtrar por categoria '{categoria}'.")
            return # Ou exibe zerado como acima

    if df_display.empty:
        st.warning(f"Sem dados para exibir métricas para {categoria}.")
        # Exibir cards zerados
        cols = st.columns(4)
        label_sufixo = f" {categoria}" if categoria else " Geral"
        with cols[0]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Pedidos{label_sufixo}</div><div class='metric-value'>R$ 0,00</div></div>", unsafe_allow_html=True)
        with cols[1]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Média{label_sufixo} ({tipo_margem_selecionada_ui_metrics[0]})</div><div class='metric-value'>0,00%</div></div>", unsafe_allow_html=True)
        with cols[2]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Líquida Média{label_sufixo}</div><div class='metric-value'>0,00%</div></div>", unsafe_allow_html=True)
        with cols[3]: st.markdown(f"<div class='metric-card'><div class='metric-label'>Ticket Médio{label_sufixo}</div><div class='metric-value'>R$ 0,00</div></div>", unsafe_allow_html=True)
        return

    # Cálculos das métricas
    total_pedidos = df_display[COL_VALOR_PEDIDO_CUSTOS].sum()
    
    # Margem Média Ponderada pelo Valor do Pedido
    if 'Margem_Num' in df_display.columns and COL_VALOR_PEDIDO_CUSTOS in df_display.columns and df_display[COL_VALOR_PEDIDO_CUSTOS].sum() != 0:
        margem_media_pond = np.average(df_display['Margem_Num'], weights=df_display[COL_VALOR_PEDIDO_CUSTOS])
    else:
        margem_media_pond = df_display['Margem_Num'].mean() if 'Margem_Num' in df_display.columns else 0

    # --- CORREÇÃO: Calcular Margem Líquida Média CORRETAMENTE sobre os totais ---
    total_liquido = 0
    total_ads = 0
    total_faturamento = 0
    margem_liquida_calculada = 0.0

    # Determinar qual coluna de líquido usar
    liquido_col_num = COL_LIQUIDO_ESTRATEGICO_NUM if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_metrics else COL_LIQUIDO_REAL_NUM

    # Verificar se as colunas necessárias existem
    colunas_necessarias_margem_liq = [liquido_col_num, COL_VALOR_ADS_NUM, COL_FATURAMENTO_BRUTO_NUM]
    if all(col in df_display.columns for col in colunas_necessarias_margem_liq):
        # Garantir que as colunas são numéricas
        df_display[liquido_col_num] = pd.to_numeric(df_display[liquido_col_num], errors='coerce').fillna(0)
        df_display[COL_VALOR_ADS_NUM] = pd.to_numeric(df_display[COL_VALOR_ADS_NUM], errors='coerce').fillna(0)
        df_display[COL_FATURAMENTO_BRUTO_NUM] = pd.to_numeric(df_display[COL_FATURAMENTO_BRUTO_NUM], errors='coerce').fillna(0)
        
        # Calcular os totais
        total_liquido = df_display[liquido_col_num].sum()
        total_ads = df_display[COL_VALOR_ADS_NUM].sum()
        total_faturamento = df_display[COL_FATURAMENTO_BRUTO_NUM].sum()

        # Calcular a margem líquida sobre os totais
        if total_faturamento > 0:
            margem_liquida_calculada = ((total_liquido - total_ads) / total_faturamento) * 100
        else:
            margem_liquida_calculada = 0.0
    else:
        # st.warning(f"Colunas necessárias para Margem Líquida ({colunas_necessarias_margem_liq}) não encontradas. Usando 0.")
        margem_liquida_calculada = 0.0 # Ou None, ou algum indicador de erro
    # --- FIM CORREÇÃO ---

    num_pedidos_unicos = df_display.shape[0] # Ou usar df_display[COL_ID_PEDIDO].nunique() se tiver ID do pedido
    valor_medio_pedido = total_pedidos / num_pedidos_unicos if num_pedidos_unicos > 0 else 0
    
    # Define o label da métrica (Geral ou por Categoria)
    label_sufixo = f" {categoria}" if categoria else " Geral"
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Pedidos{label_sufixo}</div><div class='metric-value'>{format_currency_brl(total_pedidos)}</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Média{label_sufixo} ({tipo_margem_selecionada_ui_metrics[0]})</div><div class='metric-value' style='color:{get_margin_color(margem_media_pond)};'>{formatar_margem_para_exibicao_final(margem_media_pond)}</div></div>", unsafe_allow_html=True)
    with cols[2]:
        # Exibir a margem líquida calculada sobre os totais
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Margem Líquida Calculada{label_sufixo}</div><div class='metric-value' style='color:{get_margin_color(margem_liquida_calculada)};'>{formatar_margem_para_exibicao_final(margem_liquida_calculada)}</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Ticket Médio{label_sufixo}</div><div class='metric-value'>{format_currency_brl(valor_medio_pedido)}</div></div>", unsafe_allow_html=True)

def display_charts(df, tipo_margem_selecionada_ui_charts):
    if df is None or df.empty: return
    df_chart = df.copy()
    # Certificar que a coluna de data existe e é datetime
    if COL_DATA_CUSTOS not in df_chart.columns or not pd.api.types.is_datetime64_any_dtype(df_chart[COL_DATA_CUSTOS]):
        st.warning(f"Coluna '{COL_DATA_CUSTOS}' não encontrada ou não é do tipo data para gerar gráficos mensais.")
        df_chart['MesAno'] = 'N/A'
    else:
        df_chart['MesAno'] = df_chart[COL_DATA_CUSTOS].dt.to_period('M').astype(str)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=False):
            st.markdown("<div class='custom-chart-container'>", unsafe_allow_html=True)
            st.subheader("📈 Performance Mensal")
            # Verificar se colunas necessárias para agregação existem
            cols_agg_mensal = [COL_VALOR_PEDIDO_CUSTOS, 'Margem_Num']
            if all(c in df_chart.columns for c in cols_agg_mensal):
                df_monthly = df_chart.groupby('MesAno').agg(
                    Total_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'sum'),
                    Margem_Media=('Margem_Num', 'mean') # Usar média simples aqui
                ).reset_index()
                fig_monthly = px.bar(df_monthly, x='MesAno', y='Total_Pedidos', title="Total de Pedidos por Mês", labels={'Total_Pedidos': 'Total Pedidos (R$)', 'MesAno': 'Mês'}, text_auto='.2s')
                fig_monthly.update_traces(marker_color=primary_color, textposition='outside')
                fig_monthly.update_layout(yaxis_title="Total Pedidos (R$)", xaxis_title="Mês", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.warning(f"Colunas necessárias ({cols_agg_mensal}) para gráfico mensal não encontradas.")
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.container(border=False):
            st.markdown("<div class='custom-chart-container'>", unsafe_allow_html=True)
            st.subheader("📊 Distribuição por Marketplace")
            # Verificar se colunas necessárias existem
            if COL_PLATAFORMA_CUSTOS in df_chart.columns and COL_VALOR_PEDIDO_CUSTOS in df_chart.columns:
                df_marketplace = df_chart.groupby(COL_PLATAFORMA_CUSTOS).agg(
                    Total_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'sum')
                ).reset_index().sort_values(by='Total_Pedidos', ascending=False)
                fig_pie = px.pie(df_marketplace, values='Total_Pedidos', names=COL_PLATAFORMA_CUSTOS, title="Distribuição de Pedidos por Marketplace", hole=0.4)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning(f"Colunas necessárias ('{COL_PLATAFORMA_CUSTOS}', '{COL_VALOR_PEDIDO_CUSTOS}') para gráfico de marketplace não encontradas.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- CORRIGIDO: Função para exibir a Análise Detalhada com cálculo correto da margem líquida agregada ---
def display_detailed_analysis_sku(df, tipo_margem_selecionada_ui_detalhada):
    st.markdown("## Análise Detalhada por SKU") # Título ajustado
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
            index=marketplaces.index(st.session_state.det_marketplace_filter_state) if st.session_state.det_marketplace_filter_state in marketplaces else 0
        )
        st.session_state.det_marketplace_filter_state = marketplace_selecionado # Atualizar estado específico

    with col2:
        # Filtro Conta (NOVO v2)
        contas = ["Todos"] + sorted(df_analysis[COL_CONTA_CUSTOS_ORIGINAL].unique().tolist())
        conta_selecionada = st.selectbox(
            "Filtrar por Conta",
            options=contas,
            key="det_conta_filter_widget", # Chave única
            index=contas.index(st.session_state.det_conta_filter_state) if st.session_state.det_conta_filter_state in contas else 0
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
                index=tipos_anuncio.index(st.session_state.det_tipo_anuncio_filter_state) if st.session_state.det_tipo_anuncio_filter_state in tipos_anuncio else 0
            )
            st.session_state.det_tipo_anuncio_filter_state = tipo_anuncio_selecionado # Atualizar estado específico
        else:
            # st.markdown("Coluna Tipo Anúncio indisponível.")
            st.session_state.det_tipo_anuncio_filter_state = "Todos"

    with col4:
        # Filtro Tipo de Envio
        if NOME_PADRAO_TIPO_ENVIO in df_analysis.columns:
            tipos_envio = ["Todos"] + sorted(df_analysis[NOME_PADRAO_TIPO_ENVIO].unique().tolist())
            tipo_envio_selecionado = st.selectbox(
                "Filtrar por Tipo Envio",
                options=tipos_envio,
                key="det_tipo_envio_filter_widget", # Chave única
                index=tipos_envio.index(st.session_state.det_tipo_envio_filter_state) if st.session_state.det_tipo_envio_filter_state in tipos_envio else 0
            )
            st.session_state.det_tipo_envio_filter_state = tipo_envio_selecionado # Atualizar estado específico
        else:
            # st.markdown("Coluna Tipo Envio indisponível.")
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
        # Garantir que a coluna SKU é string para o contains
        if COL_SKU_CUSTOS in df_filtered.columns:
             df_filtered = df_filtered[df_filtered[COL_SKU_CUSTOS].astype(str).str.contains(sku_filter, case=False, na=False)]
        else:
             st.warning(f"Coluna '{COL_SKU_CUSTOS}' não encontrada para filtro de SKU.")
             df_filtered = pd.DataFrame() # Limpa o dataframe se não puder filtrar

    # --- CORREÇÃO: Agrupamento e Cálculo da Margem Líquida Agregada --- 
    df_grouped = pd.DataFrame() # Inicializa vazio

    if not df_filtered.empty:
        # Colunas para agrupar a exibição final
        group_by_cols_display = [COL_SKU_CUSTOS, COL_CONTA_CUSTOS_ORIGINAL, COL_PLATAFORMA_CUSTOS]
        
        # Verificar se colunas de agrupamento existem
        if not all(col in df_filtered.columns for col in group_by_cols_display):
            st.warning(f"Colunas de agrupamento ({group_by_cols_display}) não encontradas. Exibindo dados filtrados sem agrupar.")
            df_grouped = df_filtered # Usa o df filtrado diretamente se não puder agrupar
        else:
            # Colunas necessárias para o cálculo da margem líquida agregada
            liquido_col_num = COL_LIQUIDO_ESTRATEGICO_NUM if "Margem Estratégica (L)" in tipo_margem_selecionada_ui_detalhada else COL_LIQUIDO_REAL_NUM
            cols_calculo_margem = [liquido_col_num, COL_VALOR_ADS_NUM, COL_FATURAMENTO_BRUTO_NUM]
            
            # Colunas adicionais para agregar (somar ou pegar primeiro valor)
            cols_agg_adicionais = {
                COL_QUANTIDADE_CUSTOS_ABA_CUSTOS: 'sum',
                COL_VALOR_PEDIDO_CUSTOS: 'sum',
                'Margem_Num': 'mean', # Mantém a média da margem original (pode ser útil comparar)
                'Margem_Original': 'first', # Pega a string formatada original
                COL_VALOR_PRODUTO_PLANILHA_CUSTOS: 'first', # Pega o primeiro preço unitário
                COL_ESTOQUE_VF: 'first',
                COL_ESTOQUE_GS: 'first',
                COL_ESTOQUE_DK: 'first',
                COL_ESTOQUE_TINY: 'first',
                COL_ESTOQUE_TOTAL_FULL: 'first',
                COL_ID_PRODUTO_CUSTOS: 'first',
                NOME_PADRAO_TIPO_ANUNCIO: 'first'
            }

            # Verificar se todas as colunas necessárias existem
            colunas_necessarias_total = group_by_cols_display + cols_calculo_margem + list(cols_agg_adicionais.keys())
            colunas_faltantes = [col for col in colunas_necessarias_total if col not in df_filtered.columns]
            
            if colunas_faltantes:
                st.warning(f"Colunas necessárias para análise detalhada agrupada não encontradas: {colunas_faltantes}. Exibindo dados filtrados sem agrupar ou sem cálculo de margem líquida.")
                # Tenta exibir o df_filtered sem agrupar, mas pode faltar colunas na exibição
                df_grouped = df_filtered 
            else:
                # Construir o dicionário de agregação final
                agg_final = {
                    liquido_col_num: 'sum',
                    COL_VALOR_ADS_NUM: 'sum',
                    COL_FATURAMENTO_BRUTO_NUM: 'sum',
                    **{k: v for k, v in cols_agg_adicionais.items() if k in df_filtered.columns} # Adiciona as outras agregações
                }
                
                try:
                    # Garantir que colunas de cálculo são numéricas ANTES de agrupar
                    for col in cols_calculo_margem:
                        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)
                        
                    # Realizar o agrupamento
                    df_grouped = df_filtered.groupby(group_by_cols_display, as_index=False).agg(agg_final)
                    
                    # Calcular a Margem Líquida Agregada para cada grupo
                    df_grouped['Margem_Liquida_Calculada'] = np.where(
                        df_grouped[COL_FATURAMENTO_BRUTO_NUM] > 0,
                        ((df_grouped[liquido_col_num] - df_grouped[COL_VALOR_ADS_NUM]) / df_grouped[COL_FATURAMENTO_BRUTO_NUM]) * 100,
                        0.0
                    )
                    # st.success(f"Dados agrupados e Margem Líquida Calculada. {len(df_grouped)} linhas resultantes.")

                except Exception as e_group:
                    st.error(f"Erro durante o agrupamento ou cálculo da margem líquida agregada: {e_group}")
                    st.error(traceback.format_exc())
                    df_grouped = df_filtered # Fallback para dados filtrados se o agrupamento falhar

    # --- Fim Correção Agrupamento --- 

    # --- Exibir Tabela Detalhada --- 
    if not df_grouped.empty:
        
        # Colunas a serem exibidas e ordem desejada (usando df_grouped agora)
        colunas_desejadas_map = {
            COL_SKU_CUSTOS: "SKU",
            COL_ID_PRODUTO_CUSTOS: "ID do Produto",
            COL_CONTA_CUSTOS_ORIGINAL: "Conta",
            COL_PLATAFORMA_CUSTOS: "Marketplace",
            # 'Margem_Original': "Margem Lida (%)", # Margem original lida/formatada
            'Margem_Liquida_Calculada': "Margem Líquida Calc. (%)", # A NOVA MARGEM CALCULADA!
            COL_QUANTIDADE_CUSTOS_ABA_CUSTOS: "Und Vendidas Total",
            COL_VALOR_PEDIDO_CUSTOS: "Valor Pedido Total", # Soma dos pedidos do grupo
            COL_FATURAMENTO_BRUTO_NUM: "Faturamento Bruto Total", # Soma do faturamento do grupo
            liquido_col_num: "Líquido Total", # Soma do líquido do grupo
            COL_VALOR_ADS_NUM: "ADS Total", # Soma do ADS do grupo
            COL_VALOR_PRODUTO_PLANILHA_CUSTOS: "Preço Médio Und", # Primeiro preço encontrado
            COL_ESTOQUE_VF: "Estoque Full VF",
            COL_ESTOQUE_GS: "Estoque Full GS",
            COL_ESTOQUE_DK: "Estoque Full DK",
            COL_ESTOQUE_TINY: "Estoque Full Tiny",
            COL_ESTOQUE_TOTAL_FULL: "Estoque Total Full",
            NOME_PADRAO_TIPO_ANUNCIO: "Tipo de Anúncio"
        }

        # Filtrar o DataFrame agrupado para conter apenas as colunas necessárias
        colunas_originais_necessarias = [col for col in colunas_desejadas_map.keys() if col in df_grouped.columns]
        if not colunas_originais_necessarias:
             st.warning("Nenhuma coluna encontrada no DataFrame agrupado para exibição.")
             return 
             
        df_display_detalhada = df_grouped[colunas_originais_necessarias].copy()

        # Renomear colunas
        df_display_detalhada.rename(columns=colunas_desejadas_map, inplace=True)

        # Aplicar formatação às colunas renomeadas
        format_dict_detalhada = {}
        if "Margem Líquida Calc. (%)" in df_display_detalhada.columns:
            format_dict_detalhada["Margem Líquida Calc. (%)"] = formatar_margem_para_exibicao_final # Usa a função com 2 casas
        if "Und Vendidas Total" in df_display_detalhada.columns:
            format_dict_detalhada["Und Vendidas Total"] = format_integer
        if "Valor Pedido Total" in df_display_detalhada.columns:
            format_dict_detalhada["Valor Pedido Total"] = format_currency_brl
        if "Faturamento Bruto Total" in df_display_detalhada.columns:
            format_dict_detalhada["Faturamento Bruto Total"] = format_currency_brl
        if "Líquido Total" in df_display_detalhada.columns:
            format_dict_detalhada["Líquido Total"] = format_currency_brl
        if "ADS Total" in df_display_detalhada.columns:
            format_dict_detalhada["ADS Total"] = format_currency_brl
        if "Preço Médio Und" in df_display_detalhada.columns:
            format_dict_detalhada["Preço Médio Und"] = format_currency_brl
        if "Estoque Full VF" in df_display_detalhada.columns:
            format_dict_detalhada["Estoque Full VF"] = format_integer
        if "Estoque Full GS" in df_display_detalhada.columns:
            format_dict_detalhada["Estoque Full GS"] = format_integer
        if "Estoque Full DK" in df_display_detalhada.columns:
            format_dict_detalhada["Estoque Full DK"] = format_integer
        if "Estoque Full Tiny" in df_display_detalhada.columns:
            format_dict_detalhada["Estoque Full Tiny"] = format_integer
        if "Estoque Total Full" in df_display_detalhada.columns:
            format_dict_detalhada["Estoque Total Full"] = format_integer

        # Definir a ordem final das colunas para exibição
        ordem_final_colunas = [
            "SKU", "ID do Produto", "Conta", "Marketplace", 
            "Margem Líquida Calc. (%)", # Coluna principal de margem
            "Und Vendidas Total", "Valor Pedido Total", "Faturamento Bruto Total", 
            "Líquido Total", "ADS Total", "Preço Médio Und", 
            "Estoque Full VF", "Estoque Full GS", "Estoque Full DK", "Estoque Full Tiny", "Estoque Total Full",
            "Tipo de Anúncio"
        ]
        # Filtrar ordem final para colunas que realmente existem
        ordem_final_existente = [col for col in ordem_final_colunas if col in df_display_detalhada.columns]
        df_display_final = df_display_detalhada[ordem_final_existente]

        # Aplicar estilização (ex: cor da margem)
        styler = df_display_final.style
        if "Margem Líquida Calc. (%)" in df_display_final.columns:
            # Função para aplicar cor baseada no valor numérico ANTES da formatação final
            def highlight_margem_liquida(val):
                # Extrai o número da string formatada (ex: '9,74%')
                try:
                    num_str = str(val).replace('%','').replace(',','.')
                    num = float(num_str)
                    if num < 10: return f'color: {danger_color}; font-weight: bold;'
                    elif num < 17: return f'color: {warning_color};'
                    else: return f'color: {success_color};'
                except: return ''
            
            # Aplica o highlight e DEPOIS a formatação final
            styler = styler.apply(lambda col: col.map(highlight_margem_liquida), subset=["Margem Líquida Calc. (%)"])
            
        # Aplicar formatação numérica/moeda
        if format_dict_detalhada:
             styler = styler.format(format_dict_detalhada)

        # Ocultar índice
        styler = styler.hide(axis="index")

        st.dataframe(styler, use_container_width=True, height=600) # Aumentar altura
    else:
        st.info("Nenhum dado encontrado para os filtros selecionados na análise detalhada.")

# --- Função para Alertas (Placeholder) ---
def display_alerts(df_alertas):
    st.markdown("## Alertas de Estoque")
    if df_alertas is None or df_alertas.empty:
        st.info("Nenhum alerta de estoque Full com prazo estimado > 60 dias encontrado.")
        return

    st.dataframe(df_alertas, use_container_width=True)

# --- Função para Mapa (Placeholder) ---
def display_map(df):
    st.markdown("## Mapa de Vendas")
    if df is None or df.empty:
        st.warning("Dados insuficientes para gerar o mapa de vendas.")
        return
    
    # Verificar se a coluna de estado existe
    if COL_ESTADO not in df.columns:
        st.warning(f"Coluna '{COL_ESTADO}' necessária para o mapa não encontrada.")
        return
        
    # Calcular valor médio por estado (exemplo)
    df_mapa = df.groupby(COL_ESTADO).agg(
        Valor_Total_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'sum'),
        Num_Pedidos=(COL_VALOR_PEDIDO_CUSTOS, 'count') # Ou usar um ID de pedido único se disponível
    ).reset_index()
    df_mapa['Ticket_Medio'] = df_mapa['Valor_Total_Pedidos'] / df_mapa['Num_Pedidos']
    
    fig_mapa = criar_mapa_brasil_interativo(df_mapa, COL_ESTADO, 'Valor_Total_Pedidos', 'Ticket_Medio')
    if fig_mapa:
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.error("Erro ao gerar o mapa interativo.")

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---
if not st.session_state.authenticated:
    display_login_screen()
else:
    display_sidebar()

    # Carregar ou obter dados processados
    if not st.session_state.data_loaded:
        with st.spinner("Processando dados... Por favor, aguarde."):
            try:
                df_result_temp, df_alertas_temp = load_and_process_data(
                    url=GOOGLE_SHEET_URL,
                    tipo_margem=st.session_state.tipo_margem_selecionada_state,
                    data_inicio=st.session_state.data_inicio_analise_state,
                    data_fim=st.session_state.data_fim_analise_state,
                    col_margem_estr=COL_MARGEM_ESTRATEGICA_PLANILHA_CUSTOS,
                    col_margem_real=COL_MARGEM_REAL_PLANILHA_CUSTOS,
                    col_tipo_anuncio=COL_TIPO_ANUNCIO_ML_CUSTOS,
                    _dummy_rerun=st.session_state.dummy_rerun_counter # Para forçar recache
                )
                if df_result_temp is not None:
                    st.session_state.df_result = df_result_temp
                    st.session_state.df_alertas_full = df_alertas_temp
                    st.session_state.data_loaded = True
                    st.session_state.dummy_rerun_counter += 1 # Incrementar para próxima vez
                    # st.success("Dados carregados e processados!")
                else:
                    st.error("Falha ao carregar ou processar os dados. Verifique a planilha e os logs.")
                    st.session_state.df_result = None # Garantir que está None
                    st.session_state.df_alertas_full = None
                    st.session_state.data_loaded = False # Manter como não carregado

            except Exception as e:
                st.error(f"Erro inesperado durante o carregamento/processamento: {e}")
                st.error(traceback.format_exc())
                st.session_state.df_result = None
                st.session_state.df_alertas_full = None
                st.session_state.data_loaded = False

    # Filtrar dados com base na conta selecionada no sidebar
    df_filtered_global = st.session_state.df_result
    if st.session_state.df_result is not None and not st.session_state.df_result.empty:
        if st.session_state.conta_mae_selecionada_ui_state != "Todas":
            if COL_CONTA_CUSTOS_ORIGINAL in st.session_state.df_result.columns:
                df_filtered_global = st.session_state.df_result[
                    st.session_state.df_result[COL_CONTA_CUSTOS_ORIGINAL] == st.session_state.conta_mae_selecionada_ui_state
                ]
            else:
                st.warning(f"Coluna '{COL_CONTA_CUSTOS_ORIGINAL}' não encontrada para aplicar filtro global de conta.")
                df_filtered_global = pd.DataFrame() # Ou manter o DF original?

    # Exibir página selecionada
    if st.session_state.selected_page == "Dashboard":
        st.title("🚀 Dashboard Geral")
        st.markdown("Visão geral do desempenho de vendas.")
        display_metrics(df_filtered_global, st.session_state.tipo_margem_selecionada_state)
        display_charts(df_filtered_global, st.session_state.tipo_margem_selecionada_state)
        
        # Métricas por Marketplace
        if df_filtered_global is not None and not df_filtered_global.empty and COL_PLATAFORMA_CUSTOS in df_filtered_global.columns:
            st.divider()
            st.subheader("Desempenho por Marketplace")
            marketplaces_ativos = sorted(df_filtered_global[COL_PLATAFORMA_CUSTOS].unique().tolist())
            # Criar colunas dinamicamente para os marketplaces
            num_marketplaces = len(marketplaces_ativos)
            cols_marketplaces = st.columns(num_marketplaces if num_marketplaces <= 4 else 4) # Limitar a 4 colunas por linha
            col_idx = 0
            for mp in marketplaces_ativos:
                with cols_marketplaces[col_idx % len(cols_marketplaces)]:
                     display_metrics(df_filtered_global, st.session_state.tipo_margem_selecionada_state, categoria=mp)
                col_idx += 1

    elif st.session_state.selected_page == "Análise Detalhada":
        # Passar o tipo de margem selecionado para a função
        display_detailed_analysis_sku(df_filtered_global, st.session_state.tipo_margem_selecionada_state)

    elif st.session_state.selected_page == "Alertas":
        display_alerts(st.session_state.df_alertas_full)

    elif st.session_state.selected_page == "Mapa de Vendas":
        display_map(df_filtered_global)

