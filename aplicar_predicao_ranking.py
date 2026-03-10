#!/usr/bin/env python3
"""
aplicar_predicao_ranking.py
============================
Aplica 6 patches no app.py para integrar P(Sucesso) ao Tab 6 (Ranking).

Uso:
    python aplicar_predicao_ranking.py

Entrada: app.py (mesmo diretório)
Saída:   app.py (sobrescrito, backup em app_backup_pred.py)

Patches:
  P1: WYSCOUT_LEAGUE_MAP + resolve_league_to_tier()
  P2: Checkbox + seletor Liga Alvo
  P3: Cálculo P(Sucesso) no loop de ranking
  P4: Column config para P(Sucesso)
  P5: Opção P(Sucesso) no selectbox de ordenação
  P6: Sort logic para P(Sucesso)
"""

import os
import sys
import shutil


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def apply(code, old, new, label):
    if old in code:
        code = code.replace(old, new, 1)
        print(f'  [\033[92mOK\033[0m] {label}')
        return code, True
    print(f'  [\033[91mFAIL\033[0m] {label} — padrão não encontrado')
    return code, False


def main():
    src = 'app.py'
    if not os.path.exists(src):
        print(f'ERRO: {src} não encontrado no diretório atual.')
        print(f'Coloque este script no mesmo diretório do app.py e rode novamente.')
        sys.exit(1)

    # Backup
    bkp = 'app_backup_pred.py'
    shutil.copy2(src, bkp)
    print(f'Backup: {bkp}')

    code = read_file(src)
    ok_count = 0

    print(f'\nAplicando patches em {src} ({len(code)} chars)...\n')

    # =================================================================
    # PATCH 1: WYSCOUT_LEAGUE_MAP + resolve_league_to_tier()
    # Inserido ANTES de def is_serie_b_team()
    # =================================================================
    P1_ANCHOR = 'def is_serie_b_team(team_name):'

    P1_INSERT = r'''
# ============================================
# MAPEAMENTO LIGA WYSCOUT → LEAGUE_TIERS
# ============================================
WYSCOUT_LEAGUE_MAP = {
    # Brasil
    'Brasil | 1': 'Serie A Brasil', 'Brasil | 2': 'Serie B Brasil',
    'Brasil | 3': 'Serie C Brasil', 'Brasil | 4': 'Serie D Brasil',
    'Série A': 'Serie A Brasil', 'Serie A': 'Serie A Brasil',
    'Série B': 'Serie B Brasil', 'Serie B': 'Serie B Brasil',
    'Brasileirão': 'Serie A Brasil',
    # Europa Top 5
    'England | 1': 'Premier League', 'Inglaterra | 1': 'Premier League',
    'Premier League': 'Premier League',
    'England | 2': 'Championship', 'Championship': 'Championship',
    'Spain | 1': 'La Liga', 'Espanha | 1': 'La Liga', 'La Liga': 'La Liga',
    'LaLiga': 'La Liga', 'Spain | 2': 'La Liga 2',
    'Italy | 1': 'Serie A Italia', 'Itália | 1': 'Serie A Italia',
    'Italy | 2': 'Serie B Italia',
    'Germany | 1': 'Bundesliga', 'Alemanha | 1': 'Bundesliga',
    'Bundesliga': 'Bundesliga', 'Germany | 2': '2. Bundesliga',
    'France | 1': 'Ligue 1', 'França | 1': 'Ligue 1', 'Ligue 1': 'Ligue 1',
    'France | 2': 'Ligue 2',
    # Europa Tier 2
    'Portugal | 1': 'Liga Portugal', 'Liga Portugal': 'Liga Portugal',
    'Primeira Liga': 'Liga Portugal', 'Portugal | 2': 'Liga Portugal 2',
    'Netherlands | 1': 'Eredivisie', 'Holanda | 1': 'Eredivisie',
    'Eredivisie': 'Eredivisie',
    'Belgium | 1': 'Belgian Pro League', 'Bélgica | 1': 'Belgian Pro League',
    'Turkey | 1': 'Super Lig', 'Turquia | 1': 'Super Lig',
    'Scotland | 1': 'Scottish Premiership',
    'Russia | 1': 'Russian Premier League', 'Rússia | 1': 'Russian Premier League',
    'Austria | 1': 'Austrian Bundesliga', 'Áustria | 1': 'Austrian Bundesliga',
    'Switzerland | 1': 'Swiss Super League', 'Suíça | 1': 'Swiss Super League',
    'Denmark | 1': 'Danish Superliga', 'Dinamarca | 1': 'Danish Superliga',
    'Greece | 1': 'Greek Super League', 'Grécia | 1': 'Greek Super League',
    'Ukraine | 1': 'Ukrainian Premier League',
    'Czech Republic | 1': 'Czech First League',
    'Croatia | 1': 'Croatian First League',
    'Serbia | 1': 'Serbian Super Liga',
    'Poland | 1': 'Polish Ekstraklasa',
    'Romania | 1': 'Romanian Liga I',
    'Norway | 1': 'Norwegian Eliteserien',
    'Sweden | 1': 'Swedish Allsvenskan',
    'Israel | 1': 'Israeli Premier League',
    'Bulgaria | 1': 'Bulgarian First League',
    'Cyprus | 1': 'Cypriot First Division',
    # Américas
    'Argentina | 1': 'Liga Argentina', 'Liga Profesional': 'Liga Argentina',
    'Argentina | 2': 'Liga Argentina B',
    'USA | 1': 'MLS', 'MLS': 'MLS',
    'Mexico | 1': 'Liga MX', 'Liga MX': 'Liga MX',
    'Colombia | 1': 'Liga Colombia', 'Chile | 1': 'Liga Chile',
    'Uruguay | 1': 'Liga Uruguai', 'Peru | 1': 'Liga Peru',
    'Ecuador | 1': 'Liga Equador', 'Paraguay | 1': 'Liga Paraguai',
    'Bolivia | 1': 'Liga Bolivia', 'Venezuela | 1': 'Liga Venezuela',
    # Ásia
    'Japan | 1': 'J1 League', 'Japão | 1': 'J1 League', 'Japan | 2': 'J2 League',
    'Korea | 1': 'K-League 1', 'Coreia | 1': 'K-League 1', 'K League 1': 'K-League 1',
    'Saudi Arabia | 1': 'Saudi Pro League', 'Arábia Saudita | 1': 'Saudi Pro League',
    'Qatar | 1': 'Qatar Stars League', 'UAE | 1': 'UAE Pro League',
    'China | 1': 'Chinese Super League', 'India | 1': 'Indian Super League',
    # África / Oceania
    'Egypt | 1': 'Egyptian Premier League', 'South Africa | 1': 'South African Premier',
    'Morocco | 1': 'Moroccan Botola', 'Tunisia | 1': 'Tunisian Ligue 1',
    'Australia | 1': 'A-League',
    # Estaduais / Copas Brasil
    'Paulista A1': 'Paulista A1', 'Paulista A2': 'Paulista A2', 'Paulista A3': 'Paulista A3',
    'Carioca A1': 'Carioca A1', 'Gaúcho A1': 'Gaucho A1', 'Gaucho A1': 'Gaucho A1',
    'Mineiro A1': 'Mineiro A1', 'Paranaense A1': 'Paranaense A1',
    'Cearense A1': 'Cearense A1', 'Pernambucano A1': 'Pernambucano A1',
    'Baiano A1': 'Baiano A1',
    'Copa do Brasil': 'Copa do Brasil', 'Copa do Nordeste': 'Copa do Nordeste',
    'Copa Libertadores': 'Copa Libertadores', 'Copa Sudamericana': 'Copa Sudamericana',
}


def resolve_league_to_tier(league_name, team_name=None):
    """Resolve nome de liga WyScout para chave do ContractSuccessPredictor.LEAGUE_TIERS."""
    if league_name is None:
        if team_name is None:
            return None
    elif pd.notna(league_name):
        league_str = str(league_name).strip()
        if league_str in WYSCOUT_LEAGUE_MAP:
            return WYSCOUT_LEAGUE_MAP[league_str]
        for key, val in WYSCOUT_LEAGUE_MAP.items():
            if key.lower() in league_str.lower() or league_str.lower() in key.lower():
                return val
    if team_name is not None:
        try:
            if pd.notna(team_name) and str(team_name).strip() in SERIE_B_TEAMS:
                return 'Serie B Brasil'
        except Exception:
            pass
    return None


''' + P1_ANCHOR

    code, ok = apply(code, P1_ANCHOR, P1_INSERT, 'P1: WYSCOUT_LEAGUE_MAP + resolve_league_to_tier()')
    if ok: ok_count += 1

    # =================================================================
    # PATCH 2: Checkbox "Incluir P(Sucesso)" + seletor Liga Alvo
    # Inserido ANTES de "# ===== APLICAR FILTROS ====="
    # Idempotente: não aplica se o bloco já existir no código
    # =================================================================
    P2_ANCHOR = '        # ===== APLICAR FILTROS =====\n        df_rank = wyscout.copy()'
    P2_GUARD = "key=f'inc_pred_rank_{posicao_rank}'"

    P2_INSERT = """        # ===== FILTRO: LIGA ALVO (predição de sucesso) =====
        if HAS_PREDICTIVE:
            col_pred1, col_pred2 = st.columns([1, 3])
            with col_pred1:
                incluir_predicao = st.checkbox("\U0001f3af Incluir P(Sucesso)", value=False, key=f'inc_pred_rank_{posicao_rank}',
                                                help="Calcula probabilidade de sucesso contratual para cada jogador")
            with col_pred2:
                if incluir_predicao:
                    ligas_alvo_ranking = [
                        'Serie B Brasil', 'Serie A Brasil', 'Serie C Brasil',
                        'Liga Portugal', 'Liga Portugal 2', 'MLS',
                        'Liga Argentina', 'J1 League', 'Saudi Pro League',
                        'Premier League', 'La Liga', 'Bundesliga',
                        'Serie A Italia', 'Ligue 1', 'Eredivisie',
                        'Championship', 'Belgian Pro League', 'Super Lig',
                        'Liga MX', 'Liga Colombia', 'Liga Chile',
                        'K-League 1', 'A-League',
                    ]
                    liga_alvo_rank = st.selectbox("Liga Alvo (contratação)", ligas_alvo_ranking,
                                                   index=0, key=f'liga_alvo_rank_{posicao_rank}')
                else:
                    liga_alvo_rank = 'Serie B Brasil'
        else:
            incluir_predicao = False
            liga_alvo_rank = 'Serie B Brasil'

        """ + P2_ANCHOR

    if P2_GUARD in code:
        print(f'  [\033[93mSKIP\033[0m] P2: Checkbox + seletor Liga Alvo — já aplicado (idempotente)')
        ok_count += 1
    else:
        code, ok = apply(code, P2_ANCHOR, P2_INSERT, 'P2: Checkbox + seletor Liga Alvo')
        if ok: ok_count += 1
    if ok: ok_count += 1

    # =================================================================
    # PATCH 3: Cálculo de P(Sucesso) no loop de ranking_data
    # Inserido ANTES de "ranking_data.append(entry)" no Tab 6
    # =================================================================
    P3_OLD = """                        nome_jogador = normalize_name(row['Jogador'])
                        sc_data = sc_lookup.get(nome_jogador, {})
                        if sc_data and posicao_calc in SKILLCORNER_INDICES:
                            for sc_idx in SKILLCORNER_INDICES[posicao_calc]:
                                short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                                if short_name in sc_data:
                                    entry[f'SC: {short_name}'] = sc_data[short_name]

                        ranking_data.append(entry)"""

    P3_NEW = """                        nome_jogador = normalize_name(row['Jogador'])
                        sc_data = sc_lookup.get(nome_jogador, {})
                        if sc_data and posicao_calc in SKILLCORNER_INDICES:
                            for sc_idx in SKILLCORNER_INDICES[posicao_calc]:
                                short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                                if short_name in sc_data:
                                    entry[f'SC: {short_name}'] = sc_data[short_name]

                        # P(Sucesso) — predição de contratação
                        if HAS_PREDICTIVE and incluir_predicao:
                            _age = safe_float(row.get('Idade'), 25)
                            _mins = safe_float(row.get('Minutos jogados:'), 0)
                            _ssp = entry['Score']
                            _liga_ws = row.get(liga_col) if liga_col and liga_col in row.index else None
                            _equipa = row.get('Equipa', row.get('Team'))
                            _liga_origin = resolve_league_to_tier(_liga_ws, _equipa)
                            if _liga_origin is None:
                                _liga_origin = liga_alvo_rank
                            try:
                                _pred = ContractSuccessPredictor().predict_success_unsupervised(
                                    ssp_score=_ssp, age=_age,
                                    league_origin=_liga_origin,
                                    league_target=liga_alvo_rank,
                                    minutes=_mins,
                                )
                                entry['P(Sucesso)'] = round(_pred['success_probability'] * 100, 1)
                                entry['Risco'] = _pred['risk_level'].capitalize()
                                entry['Gap Liga'] = round(_pred.get('league_gap', 0), 1)
                            except Exception:
                                entry['P(Sucesso)'] = None
                                entry['Risco'] = '-'
                                entry['Gap Liga'] = None

                        ranking_data.append(entry)"""

    code, ok = apply(code, P3_OLD, P3_NEW, 'P3: P(Sucesso) no loop de ranking')
    if ok: ok_count += 1

    # =================================================================
    # PATCH 4: Column config para P(Sucesso), Risco, Gap Liga
    # =================================================================
    P4_OLD = """                        for col in df_resultado.columns:
                            if col in list(indices_cfg.keys()):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                            elif col.startswith('SC:'):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")

                        st.dataframe(df_resultado, width='stretch', height=600, hide_index=True, column_config=column_config)"""

    P4_NEW = """                        for col in df_resultado.columns:
                            if col in list(indices_cfg.keys()):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                            elif col.startswith('SC:'):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                        # Colunas de predição de sucesso contratual
                        if 'P(Sucesso)' in df_resultado.columns:
                            column_config['P(Sucesso)'] = st.column_config.ProgressColumn(
                                label="P(Sucesso) %", min_value=0, max_value=100, format="%.1f%%"
                            )
                        if 'Gap Liga' in df_resultado.columns:
                            column_config['Gap Liga'] = st.column_config.NumberColumn(format="%.1f")

                        st.dataframe(df_resultado, width='stretch', height=600, hide_index=True, column_config=column_config)"""

    code, ok = apply(code, P4_OLD, P4_NEW, 'P4: Column config P(Sucesso)')
    if ok: ok_count += 1

    # =================================================================
    # PATCH 5: Adicionar P(Sucesso) às opções de ordenação
    # =================================================================
    P5_OLD = """            ordenar_por = st.selectbox("\U0001f4c8 Ordenar por", metricas_ord, key='ordenar_ranking')"""

    P5_NEW = """            # Adicionar P(Sucesso) como opção de ordenação (requer motor preditivo)
            if HAS_PREDICTIVE:
                metricas_ord.append('\U0001f3af P(Sucesso)')
            ordenar_por = st.selectbox("\U0001f4c8 Ordenar por", metricas_ord, key='ordenar_ranking')"""

    code, ok = apply(code, P5_OLD, P5_NEW, 'P5: P(Sucesso) no selectbox de ordenação')
    if ok: ok_count += 1

    # =================================================================
    # PATCH 6: Sort logic para P(Sucesso)
    # =================================================================
    P6_OLD = """                        if ordenar_por == '\U0001f3af Índice Geral':
                            sort_col = 'Score'
                        else:
                            sort_col = ordenar_por.replace('\U0001f4ca ', '').replace(' (índice)', '')"""

    P6_NEW = """                        if ordenar_por == '\U0001f3af Índice Geral':
                            sort_col = 'Score'
                        elif ordenar_por == '\U0001f3af P(Sucesso)':
                            sort_col = 'P(Sucesso)'
                        else:
                            sort_col = ordenar_por.replace('\U0001f4ca ', '').replace(' (índice)', '')"""

    code, ok = apply(code, P6_OLD, P6_NEW, 'P6: Sort logic P(Sucesso)')
    if ok: ok_count += 1

    # =================================================================
    # RESULTADO
    # =================================================================
    write_file(src, code)

    print(f'\n{"="*60}')
    print(f'RESULTADO: {ok_count}/6 patches aplicados')
    print(f'Arquivo: {src} ({len(code)} chars)')
    print(f'Backup:  {bkp}')

    if ok_count < 6:
        print(f'\n\033[93mAVISO: {6-ok_count} patches falharam.\033[0m')
        print('Possíveis causas:')
        print('  - O app.py já foi modificado (indentação/espaços diferentes)')
        print('  - Versão do app.py diferente da esperada')
        print('  - Patches já aplicados anteriormente')
        print('\nSoluções:')
        print('  1. Verifique se o app.py é a versão original (com Tab 8 Predição + Tab 9 Clusters)')
        print('  2. Se patches já foram aplicados, restaure o backup e rode novamente')
        print('  3. Aplique manualmente consultando INTEGRACAO_PREDICAO_RANKING.md')
    else:
        print(f'\n\033[92mTodos os patches aplicados com sucesso!\033[0m')
        print('Novas features no Tab 6 (Ranking):')
        print('  • Checkbox "Incluir P(Sucesso)" para ativar predição')
        print('  • Seletor de Liga Alvo (default: Serie B Brasil)')
        print('  • Colunas: P(Sucesso) %, Risco, Gap Liga')
        print('  • Ordenação por P(Sucesso) disponível')

    return ok_count


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result == 6 else 1)
