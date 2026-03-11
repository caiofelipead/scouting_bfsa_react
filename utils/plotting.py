"""
utils/plotting.py — Funções de visualização Plotly para o Scouting Dashboard.

Extraído do monolito app.py. Todas as funções retornam go.Figure.
"""

import numpy as np
import plotly.graph_objects as go

from config.mappings import COLORS


def get_color(value: float) -> str:
    """Retorna cor CSS baseada no percentil."""
    if value >= 90:
        return COLORS['elite']
    elif value >= 65:
        return COLORS['above']
    elif value >= 36:
        return COLORS['average']
    return COLORS['below']


def create_legend_html() -> str:
    """Cria legenda de cores HTML."""
    return f"""
    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin: 25px 0; padding: 18px 24px; background: {COLORS['card']}; border-radius: 12px; border: 2px solid {COLORS['border']};">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['elite']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Elite (90+)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['above']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Acima (65-89)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['average']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Média (36-64)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['below']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Abaixo (0-35)</span>
        </div>
    </div>
    """


def create_section_title(icon: str, title: str) -> str:
    """Cria título de seção com fundo estilizado."""
    return f"""
    <div style="display: flex; align-items: center; gap: 12px; margin: 30px 0 20px 0; padding: 12px 16px; background: {COLORS['card']}; border-left: 4px solid {COLORS['accent']}; border-radius: 0 8px 8px 0;">
        <span style="font-size: 22px;">{icon}</span>
        <span style="color: #ffffff; font-size: 18px; font-weight: 700;">{title}</span>
    </div>
    """


def create_wyscout_radar(metrics_dict: dict) -> go.Figure:
    """Cria radar chart estilizado WyScout com setores coloridos por percentil."""
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    n = len(categories)

    if n == 0:
        return go.Figure()

    fig = go.Figure()

    # Círculos de fundo
    for r in [25, 50, 75, 100]:
        theta = list(range(0, 361, 1))
        fig.add_trace(go.Scatterpolar(
            r=[r] * len(theta), theta=theta, mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1),
            showlegend=False, hoverinfo='skip'
        ))

    # Linhas radiais
    for i in range(n):
        angle = i * (360 / n)
        fig.add_trace(go.Scatterpolar(
            r=[0, 105], theta=[angle, angle], mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1),
            showlegend=False, hoverinfo='skip'
        ))

    # Setores coloridos
    for i, (cat, val) in enumerate(zip(categories, values)):
        color = get_color(val)
        angle_center = i * (360 / n)
        half_width = (360 / n) / 2 - 2

        theta_points = np.linspace(angle_center - half_width, angle_center + half_width, 30)
        r_points = [val] * len(theta_points)

        theta_full = [angle_center] + list(theta_points) + [angle_center]
        r_full = [0] + r_points + [0]

        fig.add_trace(go.Scatterpolar(
            r=r_full, theta=theta_full, fill='toself',
            fillcolor=color, line=dict(color=color, width=1),
            opacity=0.85, showlegend=False,
            hovertemplate=f'<b>{cat}</b><br>{val:.0f}<extra></extra>'
        ))

    # Labels externos
    for i, (cat, val) in enumerate(zip(categories, values)):
        angle = i * (360 / n)
        fig.add_trace(go.Scatterpolar(
            r=[128], theta=[angle], mode='text',
            text=[f"<b>{cat}</b>"], textfont=dict(size=12, color='white'),
            showlegend=False, hoverinfo='skip'
        ))
        if val > 15:
            fig.add_trace(go.Scatterpolar(
                r=[val * 0.5], theta=[angle], mode='text',
                text=[f'<b>{val:.0f}</b>'], textfont=dict(size=14, color='white'),
                showlegend=False, hoverinfo='skip'
            ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 150]),
            angularaxis=dict(visible=False, direction='clockwise'),
            bgcolor=COLORS['bg']
        ),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        margin=dict(l=100, r=100, t=60, b=60),
        height=420,
        showlegend=False
    )

    return fig


def create_bar_chart(metrics_dict: dict, title: str = "") -> go.Figure:
    """Cria gráfico de barras horizontais com cores por percentil."""
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    colors = [get_color(v) for v in values]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories, x=values, orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{v:.0f}' for v in values],
        textposition='inside',
        textfont=dict(color='white', size=14, weight=700),
        hovertemplate='<b>%{y}</b><br>Percentil: %{x:.0f}<extra></extra>'
    ))

    for x in [25, 50, 75]:
        fig.add_vline(x=x, line_dash="dot", line_color="rgba(255,255,255,0.3)")

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16, color='white')),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        xaxis=dict(
            range=[0, 100],
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white', size=12),
            title=dict(text='<b>Percentil</b>', font=dict(color='white', size=13))
        ),
        yaxis=dict(
            tickfont=dict(color='white', size=13),
            categoryorder='total ascending'
        ),
        margin=dict(l=180, r=40, t=60, b=60),
        height=max(320, len(categories) * 50 + 120)
    )

    return fig


def create_comparison_radar(p1_data: dict, p2_data: dict, p1_name: str, p2_name: str) -> go.Figure:
    """Cria radar de comparação entre dois jogadores."""
    categories = list(p1_data.keys())
    vals1 = list(p1_data.values()) + [list(p1_data.values())[0]]
    vals2 = list(p2_data.values()) + [list(p2_data.values())[0]]
    theta = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=theta, fill='toself',
        fillcolor='rgba(220, 38, 38, 0.3)',
        line=dict(color=COLORS['accent'], width=2),
        name=p1_name
    ))

    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=theta, fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line=dict(color='#3b82f6', width=2),
        name=p2_name
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.15)', tickfont=dict(color='white', size=11)),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.15)', tickfont=dict(color='white', size=12, weight=500)),
            bgcolor=COLORS['bg']
        ),
        paper_bgcolor=COLORS['card'],
        legend=dict(
            orientation='h', yanchor='bottom', y=1.1, xanchor='center', x=0.5,
            font=dict(color='white', size=14, weight=600),
            bgcolor=COLORS['card'],
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        margin=dict(l=80, r=80, t=100, b=40),
        height=480
    )

    return fig


def create_scatter_plot(df, x_col: str, y_col: str, highlight: str | None = None, title: str = "") -> go.Figure:
    """Cria scatter plot com quadrantes e highlight de jogador."""
    df_valid = df.dropna(subset=[x_col, y_col])
    if len(df_valid) == 0:
        return go.Figure()

    x_mean, y_mean = df_valid[x_col].mean(), df_valid[y_col].mean()
    x_max, y_max = df_valid[x_col].max() * 1.1, df_valid[y_col].max() * 1.1
    x_min, y_min = df_valid[x_col].min() * 0.9, df_valid[y_col].min() * 0.9

    fig = go.Figure()

    # Quadrantes
    fig.add_shape(type="rect", x0=x_mean, y0=y_mean, x1=x_max, y1=y_max,
                  fillcolor="rgba(34,197,94,0.15)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_min, y0=y_min, x1=x_mean, y1=y_mean,
                  fillcolor="rgba(239,68,68,0.15)", line=dict(width=0))

    fig.add_hline(y=y_mean, line_dash="dot", line_color="rgba(255,255,255,0.4)")
    fig.add_vline(x=x_mean, line_dash="dot", line_color="rgba(255,255,255,0.4)")

    # Usar JogadorDisplay para hover
    display_col = 'JogadorDisplay' if 'JogadorDisplay' in df_valid.columns else 'Jogador' if 'Jogador' in df_valid.columns else 'player_name'
    name_col = 'Jogador' if 'Jogador' in df_valid.columns else 'player_name'

    fig.add_trace(go.Scatter(
        x=df_valid[x_col], y=df_valid[y_col],
        mode='markers',
        marker=dict(size=7, color='#6b7280', opacity=0.5),
        text=df_valid[display_col],
        hovertemplate='<b>%{text}</b><br>%{x:.2f} | %{y:.2f}<extra></extra>',
        showlegend=False
    ))

    if highlight:
        if display_col in df_valid.columns and highlight in df_valid[display_col].values:
            p = df_valid[df_valid[display_col] == highlight].iloc[0]
            label = p[name_col].split()[0] if name_col in p else highlight.split()[0]
        elif name_col in df_valid.columns and highlight in df_valid[name_col].values:
            p = df_valid[df_valid[name_col] == highlight].iloc[0]
            label = highlight.split()[0]
        else:
            p = None
            label = None

        if p is not None:
            fig.add_trace(go.Scatter(
                x=[p[x_col]], y=[p[y_col]],
                mode='markers+text',
                marker=dict(size=16, color=COLORS['accent'], line=dict(width=3, color='white')),
                text=[label],
                textposition='top center',
                textfont=dict(color='white', size=13, weight=700),
                showlegend=False
            ))

    x_label = x_col.replace('/90', ' /90').replace(', %', ' %')
    y_label = y_col.replace('/90', ' /90').replace(', %', ' %')

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=17, color='white')),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        xaxis=dict(
            title=dict(text=f"<b>{x_label}</b>", font=dict(color='white', size=14)),
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white', size=11),
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text=f"<b>{y_label}</b>", font=dict(color='white', size=14)),
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white', size=11),
            zeroline=False
        ),
        margin=dict(l=90, r=40, t=80, b=90),
        height=460
    )

    return fig
