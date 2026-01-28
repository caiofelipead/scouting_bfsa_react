import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ============================================
# CONFIGURAÇÃO
# ============================================
st.set_page_config(
    page_title="Scouting Dashboard | Botafogo-SP",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CORES
# ============================================
COLORS = {
    'bg': '#0f0f13',
    'card': '#1a1a22',
    'accent': '#dc2626',
    'text': '#ffffff',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280',
    'border': 'rgba(255,255,255,0.1)',
    'elite': '#22c55e',
    'above': '#eab308',
    'average': '#f97316',
    'below': '#ef4444',
}

# ============================================
# CSS LIMPO
# ============================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .main {{
        background: {COLORS['bg']};
        font-family: 'Inter', sans-serif;
    }}
    
    [data-testid="stSidebar"] {{
        background: #0d0d11;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background: {COLORS['card']};
        border-radius: 10px;
        padding: 4px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: {COLORS['text_muted']};
        font-weight: 500;
        border-radius: 8px;
        padding: 8px 16px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {COLORS['accent']} !important;
        color: white !important;
    }}
    
    [data-testid="stMetric"] {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 16px;
    }}
    
    [data-testid="stMetric"] label {{
        color: {COLORS['text_muted']} !important;
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {COLORS['text']} !important;
        font-weight: 700 !important;
    }}
    
    h1, h2, h3 {{ 
        font-family: 'Inter', sans-serif; 
        color: {COLORS['text']} !important;
    }}
    
    p {{ 
        font-family: 'Inter', sans-serif;
        color: {COLORS['text_secondary']};
    }}
    
    .stSubheader {{
        color: {COLORS['text']} !important;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Forçar cor branca nos títulos */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: white !important;
    }}
    
    [data-testid="stSubheader"] {{
        color: white !important;
    }}
    
    /* Labels dos selectbox */
    .stSelectbox label {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Radio buttons */
    .stRadio label {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    .stRadio div[role="radiogroup"] label {{
        color: {COLORS['text']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNÇÕES
# ============================================

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file:
        xlsx = pd.ExcelFile(uploaded_file)
    else:
        xlsx = pd.ExcelFile('Banco_de_Dados___Jogadores-2.xlsx')
    
    analises = pd.read_excel(xlsx, sheet_name='Análises')
    central = pd.read_excel(xlsx, sheet_name='Central de Dados')
    oferecidos = pd.read_excel(xlsx, sheet_name='Oferecidos')
    return analises, central, oferecidos


def get_color(value):
    """Cor baseada no percentil"""
    if value >= 90:
        return COLORS['elite']
    elif value >= 65:
        return COLORS['above']
    elif value >= 36:
        return COLORS['average']
    return COLORS['below']


def create_wyscout_radar(metrics_dict):
    """Radar estilo Wyscout com setores coloridos"""
    
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    n = len(categories)
    
    fig = go.Figure()
    
    # Círculos de fundo
    for r in [25, 50, 75, 100]:
        theta = list(range(0, 361, 1))
        fig.add_trace(go.Scatterpolar(
            r=[r] * len(theta),
            theta=theta,
            mode='lines',
            line=dict(color='rgba(255,255,255,0.08)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Linhas radiais
    for i in range(n):
        angle = i * (360 / n)
        fig.add_trace(go.Scatterpolar(
            r=[0, 105],
            theta=[angle, angle],
            mode='lines',
            line=dict(color='rgba(255,255,255,0.08)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Setores coloridos para cada métrica
    for i, (cat, val) in enumerate(zip(categories, values)):
        color = get_color(val)
        angle_center = i * (360 / n)
        half_width = (360 / n) / 2 - 2  # pequeno gap entre setores
        
        # Criar setor como polígono
        theta_points = np.linspace(angle_center - half_width, angle_center + half_width, 30)
        r_points = [val] * len(theta_points)
        
        # Fechar o setor (ir até o centro e voltar)
        theta_full = [angle_center] + list(theta_points) + [angle_center]
        r_full = [0] + r_points + [0]
        
        fig.add_trace(go.Scatterpolar(
            r=r_full,
            theta=theta_full,
            fill='toself',
            fillcolor=color,
            line=dict(color=color, width=1),
            opacity=0.85,
            name=cat,
            showlegend=False,
            hovertemplate=f'<b>{cat}</b><br>{val:.0f}<extra></extra>'
        ))
    
    # Labels das categorias (fora do gráfico)
    for i, (cat, val) in enumerate(zip(categories, values)):
        angle = i * (360 / n)
        
        fig.add_trace(go.Scatterpolar(
            r=[115],
            theta=[angle],
            mode='text',
            text=[cat],
            textfont=dict(size=11, color=COLORS['text_secondary']),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Valor dentro do setor
        if val > 20:
            fig.add_trace(go.Scatterpolar(
                r=[val * 0.6],
                theta=[angle],
                mode='text',
                text=[f'{val:.0f}'],
                textfont=dict(size=11, color='white', weight=600),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 130]),
            angularaxis=dict(visible=False, direction='clockwise'),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=60, t=30, b=30),
        height=350,
        showlegend=False
    )
    
    return fig


def create_comparison_radar(p1_data, p2_data, p1_name, p2_name):
    """Radar de comparação"""
    
    categories = ['Técnica', 'Físico', 'Tática', 'Mental']
    
    vals1 = [p1_data.get(c, 0) or 0 for c in categories] + [p1_data.get('Técnica', 0) or 0]
    vals2 = [p2_data.get(c, 0) or 0 for c in categories] + [p2_data.get('Técnica', 0) or 0]
    theta = categories + [categories[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=theta,
        fill='toself',
        fillcolor='rgba(220, 38, 38, 0.3)',
        line=dict(color=COLORS['accent'], width=2),
        name=p1_name
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=theta,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line=dict(color='#3b82f6', width=2),
        name=p2_name
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5, font=dict(color='white')),
        margin=dict(l=60, r=60, t=50, b=30),
        height=400
    )
    
    return fig


def create_scatter_plot(df, x_col, y_col, highlight=None):
    """Scatter com quadrantes"""
    
    x_mean, y_mean = df[x_col].mean(), df[y_col].mean()
    x_max, y_max = df[x_col].max() * 1.1, df[y_col].max() * 1.1
    x_min, y_min = df[x_col].min() * 0.9, df[y_col].min() * 0.9
    
    fig = go.Figure()
    
    # Quadrantes
    fig.add_shape(type="rect", x0=x_mean, y0=y_mean, x1=x_max, y1=y_max,
                  fillcolor="rgba(34,197,94,0.1)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_min, y0=y_min, x1=x_mean, y1=y_mean,
                  fillcolor="rgba(239,68,68,0.1)", line=dict(width=0))
    
    fig.add_hline(y=y_mean, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig.add_vline(x=x_mean, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode='markers',
        marker=dict(size=10, color=COLORS['text_muted'], opacity=0.5),
        text=df['Nome'],
        hovertemplate='<b>%{text}</b><br>%{x:.1f} | %{y:.1f}<extra></extra>',
        showlegend=False
    ))
    
    if highlight and highlight in df['Nome'].values:
        p = df[df['Nome'] == highlight].iloc[0]
        fig.add_trace(go.Scatter(
            x=[p[x_col]], y=[p[y_col]],
            mode='markers+text',
            marker=dict(size=16, color=COLORS['accent'], line=dict(width=2, color='white')),
            text=[highlight.split()[0]],
            textposition='top center',
            textfont=dict(color='white', size=11),
            showlegend=False
        ))
    
    fig.add_annotation(x=x_max*0.95, y=y_max*0.95, text="COMPLETO", showarrow=False,
                      font=dict(color=COLORS['elite'], size=11, weight=700))
    fig.add_annotation(x=x_min*1.02, y=y_min*1.02, text="LIMITADO", showarrow=False,
                      font=dict(color=COLORS['below'], size=11, weight=700))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title=x_col, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color=COLORS['text_muted'])),
        yaxis=dict(title=y_col, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color=COLORS['text_muted'])),
        margin=dict(l=60, r=40, t=40, b=60),
        height=480
    )
    
    return fig


# ============================================
# MAIN
# ============================================

def main():
    # SIDEBAR
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0;">
            <div style="color: #dc2626; font-size: 11px; letter-spacing: 3px; font-weight: 600;">SCOUTING</div>
            <div style="color: white; font-size: 26px; font-weight: 800; letter-spacing: -1px;">BOTAFOGO</div>
            <div style="color: #6b7280; font-size: 10px; letter-spacing: 2px;">RIBEIRÃO PRETO</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        uploaded = st.file_uploader("📂 Carregar Planilha", type=['xlsx'])
        
        try:
            analises, central, oferecidos = load_data(uploaded)
        except:
            st.error("⚠️ Faça upload do Excel")
            return
        
        st.divider()
        
        st.caption("FILTROS")
        
        posicoes = ['Todas'] + sorted([str(p) for p in analises['Posição'].dropna().unique()])
        posicao = st.selectbox("Posição", posicoes)
        
        df = analises if posicao == 'Todas' else analises[analises['Posição'] == posicao]
        
        jogadores = sorted([str(j) for j in df['Nome'].dropna().unique()])
        if not jogadores:
            st.warning("Nenhum jogador")
            return
        
        jogador = st.selectbox("Jogador", jogadores)
        
        st.divider()
        st.caption(f"📊 {len(analises)} jogadores | 🏃 {len(central)} com dados físicos")
    
    # MAIN CONTENT
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Perfil", "📈 Comparativo", "🏃 Físico", "📋 Dados"])
    
    # ===== TAB 1: PERFIL =====
    with tab1:
        if jogador:
            p = df[df['Nome'] == jogador].iloc[0]
            
            # Header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 12px; padding: 24px; border: 1px solid {COLORS['border']};">
                    <div style="color: {COLORS['accent']}; font-size: 12px; font-weight: 600; letter-spacing: 1px;">{p['Posição'] or 'JOGADOR'}</div>
                    <div style="color: white; font-size: 32px; font-weight: 800; margin: 4px 0;">{p['Nome']}</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px;">
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Idade</div>
                            <div style="color: white; font-size: 14px;">{int(p['Idade']) if pd.notna(p['Idade']) else '-'} anos ({int(p['Ano']) if pd.notna(p['Ano']) else '-'})</div>
                        </div>
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Clube</div>
                            <div style="color: white; font-size: 14px;">{p['Clube'] or '-'}</div>
                        </div>
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Liga</div>
                            <div style="color: white; font-size: 14px;">{p['Liga'] or '-'}</div>
                        </div>
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Perfil</div>
                            <div style="color: white; font-size: 14px;">{p['Perfil'] or '-'}</div>
                        </div>
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Contrato</div>
                            <div style="color: white; font-size: 14px;">{str(p['Contrato']).split(' ')[0] if pd.notna(p['Contrato']) else '-'}</div>
                        </div>
                        <div>
                            <div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Agente</div>
                            <div style="color: white; font-size: 14px;">{p['Agente'] if pd.notna(p.get('Agente')) else '-'}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if pd.notna(p['Nota_Desempenho']):
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {COLORS['accent']}, #b91c1c); border-radius: 12px; padding: 20px; text-align: center; height: 100%;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 10px; letter-spacing: 1px;">NOTA GERAL</div>
                        <div style="color: white; font-size: 42px; font-weight: 800;">{p['Nota_Desempenho']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if pd.notna(p.get('Link_TM')):
                    st.link_button("🔗 Transfermarkt", p['Link_TM'], use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Radars
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Atributos")
                
                attrs = {
                    'Técnica': (p['Técnica'] / 5 * 100) if pd.notna(p['Técnica']) else 50,
                    'Físico': (p['Físico'] / 5 * 100) if pd.notna(p['Físico']) else 50,
                    'Tática': (p['Tática'] / 5 * 100) if pd.notna(p['Tática']) else 50,
                    'Mental': (p['Mental'] / 5 * 100) if pd.notna(p['Mental']) else 50,
                }
                
                fig = create_wyscout_radar(attrs)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                st.subheader("Percentile Rankings")
                
                perc = {
                    'Técnica': (p['Técnica'] / 5 * 100) if pd.notna(p['Técnica']) else 50,
                    'Físico': (p['Físico'] / 5 * 100) if pd.notna(p['Físico']) else 50,
                    'Tática': (p['Tática'] / 5 * 100) if pd.notna(p['Tática']) else 50,
                    'Mental': (p['Mental'] / 5 * 100) if pd.notna(p['Mental']) else 50,
                    'Potencial': (p['Potencial'] / 5 * 100) if pd.notna(p.get('Potencial')) else 50,
                }
                
                fig2 = create_wyscout_radar(perc)
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            
            # Legenda
            st.markdown(f"""
            <div style="display: flex; justify-content: center; gap: 24px; margin: 10px 0 20px 0;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 12px; height: 12px; background: {COLORS['elite']}; border-radius: 2px;"></div>
                    <span style="color: {COLORS['text_muted']}; font-size: 11px;">Elite (90+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 12px; height: 12px; background: {COLORS['above']}; border-radius: 2px;"></div>
                    <span style="color: {COLORS['text_muted']}; font-size: 11px;">Acima (65-89)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 12px; height: 12px; background: {COLORS['average']}; border-radius: 2px;"></div>
                    <span style="color: {COLORS['text_muted']}; font-size: 11px;">Média (36-64)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 12px; height: 12px; background: {COLORS['below']}; border-radius: 2px;"></div>
                    <span style="color: {COLORS['text_muted']}; font-size: 11px;">Abaixo (0-35)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Análise
            if pd.notna(p.get('Análise')):
                st.divider()
                st.subheader("Análise Qualitativa")
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-left: 4px solid {COLORS['accent']}; border-radius: 0 8px 8px 0; padding: 20px;">
                    <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0;">{p['Análise']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ===== TAB 2: COMPARATIVO =====
    with tab2:
        df_plot = df.dropna(subset=['Técnica', 'Físico', 'Tática', 'Mental']).copy()
        
        if len(df_plot) > 0:
            df_plot['Finalização'] = (df_plot['Técnica'] + df_plot['Físico']) / 2 * 20
            df_plot['Criação'] = (df_plot['Tática'] + df_plot['Mental']) / 2 * 20
            
            st.subheader(f"Perfil: Finalização x Criação ({len(df_plot)} jogadores)")
            fig = create_scatter_plot(df_plot, 'Finalização', 'Criação', jogador)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.divider()
        
        st.subheader("Comparar Jogadores")
        
        c1, c2 = st.columns(2)
        with c1:
            j1 = st.selectbox("Jogador 1", jogadores, key='c1')
        with c2:
            j2 = st.selectbox("Jogador 2", jogadores, index=min(1, len(jogadores)-1), key='c2')
        
        if j1 and j2 and j1 != j2:
            p1 = df[df['Nome'] == j1].iloc[0]
            p2 = df[df['Nome'] == j2].iloc[0]
            
            d1 = {c: p1[c] for c in ['Técnica', 'Físico', 'Tática', 'Mental']}
            d2 = {c: p2[c] for c in ['Técnica', 'Físico', 'Tática', 'Mental']}
            
            fig = create_comparison_radar(d1, d2, j1, j2)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== TAB 3: FÍSICO =====
    with tab3:
        if len(central) > 0:
            jf_list = sorted([str(j) for j in central['Nome'].dropna().unique()])
            jf = st.selectbox("Jogador", jf_list, key='phys')
            
            if jf:
                pf = central[central['Nome'] == jf].iloc[0]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Distância/90", f"{pf['distance_per_90']:.0f}m" if pd.notna(pf['distance_per_90']) else "N/A")
                c2.metric("Sprints/90", f"{pf['sprint_count_per_90']:.1f}" if pd.notna(pf['sprint_count_per_90']) else "N/A")
                c3.metric("HI Dist/90", f"{pf['hi_distance_per_90']:.0f}m" if pd.notna(pf['hi_distance_per_90']) else "N/A")
                c4.metric("Top Speed", f"{pf['avg_psv99']:.1f} km/h" if pd.notna(pf['avg_psv99']) else "N/A")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Rankings Físicos")
                    
                    def safe_rank(v):
                        return max(0, min(100, 100 - v)) if pd.notna(v) else 50
                    
                    phys_metrics = {
                        'Distância': safe_rank(pf.get('distance_per_90_rank')),
                        'Sprints': safe_rank(pf.get('sprint_count_per_90_rank')),
                        'HI Runs': safe_rank(pf.get('hi_count_per_90_rank')),
                        'Velocidade': safe_rank(pf.get('avg_psv99_rank')),
                        'Acelerações': safe_rank(pf.get('explacceltosprint_count_per_90_rank')),
                    }
                    
                    fig = create_wyscout_radar(phys_metrics)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                with col2:
                    st.subheader("Velocidade x Volume")
                    
                    df_phys = central.dropna(subset=['avg_psv99', 'distance_per_90'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_phys['avg_psv99'], y=df_phys['distance_per_90'],
                        mode='markers',
                        marker=dict(size=10, color=COLORS['text_muted'], opacity=0.4),
                        text=df_phys['Nome'],
                        hovertemplate='<b>%{text}</b><br>%{x:.1f} km/h | %{y:.0f}m<extra></extra>',
                        showlegend=False
                    ))
                    
                    if jf in df_phys['Nome'].values:
                        pr = df_phys[df_phys['Nome'] == jf].iloc[0]
                        fig.add_trace(go.Scatter(
                            x=[pr['avg_psv99']], y=[pr['distance_per_90']],
                            mode='markers+text',
                            marker=dict(size=16, color=COLORS['accent'], line=dict(width=2, color='white')),
                            text=[jf.split()[0]],
                            textposition='top center',
                            textfont=dict(color='white', size=11),
                            showlegend=False
                        ))
                    
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(title='Velocidade (km/h)', gridcolor='rgba(255,255,255,0.05)'),
                        yaxis=dict(title='Distância/90 (m)', gridcolor='rgba(255,255,255,0.05)'),
                        margin=dict(l=60, r=40, t=20, b=60),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem dados físicos")
    
    # ===== TAB 4: DADOS =====
    with tab4:
        source = st.radio("", ['Análises', 'Dados Físicos', 'Oferecidos'], horizontal=True)
        
        if source == 'Análises':
            cols = ['Nome', 'Posição', 'Idade', 'Clube', 'Liga', 'Perfil', 'Nota_Desempenho']
            df_show = df[[c for c in cols if c in df.columns]]
        elif source == 'Dados Físicos':
            cols = ['Nome', 'Clube', 'Posição', 'distance_per_90', 'sprint_count_per_90', 'avg_psv99']
            df_show = central[[c for c in cols if c in central.columns]]
        else:
            df_show = oferecidos
        
        st.dataframe(df_show, use_container_width=True, height=500)
        st.download_button("📥 Exportar CSV", df_show.to_csv(index=False).encode('utf-8'), f"{source.lower()}.csv")


if __name__ == "__main__":
    main()
