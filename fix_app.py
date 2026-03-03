"""
fix_app.py — Corrige os 6 problemas encontrados no app.py
==========================================================
Uso: python fix_app.py app.py
Gera: app_fixed.py

Problemas corrigidos:
  1. calculate_index: dead code apos return
  2. Tab 1: metrics_perc calculado mas nao exibido
  3. Tab 1: indentacao quebrada no ranking
  4. Tab 6: indentacao completamente quebrada no ranking
  5. Tab 6: else branch para metrica bruta sumiu
  6. Tab 7: calculate_index sem posicao na comparacao detalhada
"""
import sys, os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def apply_fix(code, old, new, label):
    if old in code:
        code = code.replace(old, new, 1)
        print(f"  [OK] {label}")
        return code, True
    else:
        print(f"  [SKIP] {label} - padrao nao encontrado")
        return code, False

def main():
    if len(sys.argv) < 2:
        print("Uso: python fix_app.py app.py")
        sys.exit(1)

    inp = sys.argv[1]
    if not os.path.exists(inp):
        print(f"Erro: {inp} nao encontrado")
        sys.exit(1)

    out = inp.replace('.py', '_fixed.py')
    code = read_file(inp)
    results = {}

    print(f"Corrigindo {inp} -> {out}\n{'='*50}")

    # ============================================
    # FIX 1: calculate_index dead code
    # ============================================
    print("\n1. calculate_index: remover dead code")
    OLD_1 = """def calculate_index(player_row, metrics, df_all):
    # Delega para weighted - retrocompatível
    return calculate_weighted_index(player_row, metrics, df_all, position=None)
    percentiles = []
    for metric in metrics:
        try:
            if metric in player_row.index and metric in df_all.columns:
                val = safe_float(player_row[metric])
                if val is not None:
                    perc = calculate_percentile(val, df_all[metric])
                    if pd.notna(perc):
                        if 'Faltas/90' in metric or 'Cartões' in metric or 'sofridos' in metric.lower():
                            perc = 100 - perc
                        percentiles.append(float(perc))
        except:
            continue
    if percentiles:
        return float(np.nanmean(percentiles))
    return 50.0"""

    NEW_1 = """def calculate_index(player_row, metrics, df_all):
    # Delega para weighted - retrocompativel
    return calculate_weighted_index(player_row, metrics, df_all, position=None)"""

    code, ok = apply_fix(code, OLD_1, NEW_1, "calculate_index dead code")
    results['fix1_dead_code'] = ok

    # ============================================
    # FIX 2: Tab 1 metrics_perc - adicionar grafico
    # ============================================
    print("\n2. Tab 1: exibir grafico de metrics_perc")
    OLD_2 = """                with col2:
                    # Métricas individuais mais importantes para a posição
                    st.markdown(create_section_title("📈", "Métricas Principais"), unsafe_allow_html=True)
                    
                    # Pegar as métricas mais relevantes
                    metrics_perc = calculate_metric_percentiles(ws_match, posicao_categoria, wyscout_percentil_t1, top_n=12)"""

    NEW_2 = """                with col2:
                    st.markdown(create_section_title("📈", "Métricas Principais"), unsafe_allow_html=True)
                    metrics_perc = calculate_metric_percentiles(ws_match, posicao_categoria, wyscout_percentil_t1, top_n=12)
                    if metrics_perc:
                        st.plotly_chart(create_bar_chart(metrics_perc, "Top Métricas (Percentil)"), width='stretch', config={'displayModeBar': False}, key="bar_metrics_t1")"""

    code, ok = apply_fix(code, OLD_2, NEW_2, "Tab 1 metrics_perc chart")
    results['fix2_metrics_chart'] = ok

    # ============================================
    # FIX 3: Tab 1 ranking - indentacao
    # ============================================
    print("\n3. Tab 1: corrigir indentacao do ranking")
    OLD_3 = """                df_ranking_t1 = rank_players_weighted(
                wyscout_pos, posicao_categoria, wyscout_percentil_t1,
                indices_config=indices, min_minutes=0, include_indices=False
                )
                    ranking_data = []
                    if len(df_ranking_t1) > 0:
                        for _, row in df_ranking_t1.head(20).iterrows():
                            ranking_data.append({
                                'Jogador': row['Jogador'],
                                'Clube': row['Equipa'],
                                'Idade': safe_int(row.get('Idade')),
                                'Min': safe_int(row.get('Minutos jogados:')),
                                'Índice Médio': row['Score']
                            })"""

    NEW_3 = """                df_ranking_t1 = rank_players_weighted(
                    wyscout_pos, posicao_categoria, wyscout_percentil_t1,
                    indices_config=indices, min_minutes=0, include_indices=False
                )
                ranking_data = []
                if len(df_ranking_t1) > 0:
                    for _, row in df_ranking_t1.head(20).iterrows():
                        ranking_data.append({
                            'Jogador': row['Jogador'],
                            'Clube': row['Equipa'],
                            'Idade': safe_int(row.get('Idade')),
                            'Min': safe_int(row.get('Minutos jogados:')),
                            'Índice Médio': row['Score']
                        })"""

    code, ok = apply_fix(code, OLD_3, NEW_3, "Tab 1 ranking indent")
    results['fix3_tab1_indent'] = ok

    # ============================================
    # FIX 4: Tab 6 ranking - indentacao completa
    # ============================================
    print("\n4. Tab 6: corrigir indentacao do ranking inteiro")
    OLD_4 = """                with st.spinner(f'Calculando ranking ponderado para {len(df_rank_limited)} jogadores...'):
    df_ranked = rank_players_weighted(
        df_rank_limited,
        posicao_calc,
        wyscout_percentil,
        indices_config=indices_cfg,
        min_minutes=0,
        include_indices=True
    )

if len(df_ranked) > 0:
    # Montar df_resultado
    sc_lookup = create_skillcorner_lookup(skillcorner)

    ranking_data = []
    for _, row in df_ranked.iterrows():
        entry = {
            'Jogador': row['Jogador'],
            'Clube': row.get('Equipa', row.get('Team', '-')),
            'Idade': safe_int(row.get('Idade')),
            'Min': safe_int(row.get('Minutos jogados:')),
            'Score': row['Score'],
        }
        # Indices compostos (já calculados por rank_players_weighted)
        for idx_name in indices_cfg.keys():
            if idx_name in row.index and pd.notna(row[idx_name]):
                entry[idx_name] = row[idx_name]

        # SkillCorner
        nome_jogador = normalize_name(row['Jogador'])
        sc_data = sc_lookup.get(nome_jogador, {})
        if sc_data and posicao_calc in SKILLCORNER_INDICES:
            for sc_idx in SKILLCORNER_INDICES[posicao_calc]:
                short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                if short_name in sc_data:
                    entry[f'SC: {short_name}'] = sc_data[short_name]

        ranking_data.append(entry)

    if ranking_data:
        df_resultado = pd.DataFrame(ranking_data)

        # Ordenação
        if ordenar_por == '🎯 Índice Geral':
            sort_col = 'Score'
        else:
            sort_col = ordenar_por.replace('📊 ', '').replace(' (índice)', '')

        if sort_col in df_resultado.columns:
            df_resultado = df_resultado.sort_values(sort_col, ascending=False)
        else:
            df_resultado = df_resultado.sort_values('Score', ascending=False)

        df_resultado = df_resultado.head(100)
        df_resultado.insert(0, '#', range(1, len(df_resultado) + 1))

        # Column config
        column_config = {
            '#': st.column_config.NumberColumn(width='small'),
            'Score': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        }
        for col in df_resultado.columns:
            if col in list(indices_cfg.keys()):
                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
            elif col.startswith('SC:'):
                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")

        st.dataframe(df_resultado, width='stretch', height=600, hide_index=True, column_config=column_config)"""

    NEW_4 = """                with st.spinner(f'Calculando ranking ponderado para {len(df_rank_limited)} jogadores...'):
                    df_ranked = rank_players_weighted(
                        df_rank_limited,
                        posicao_calc,
                        wyscout_percentil,
                        indices_config=indices_cfg,
                        min_minutes=0,
                        include_indices=True
                    )

                if len(df_ranked) > 0:
                    sc_lookup = create_skillcorner_lookup(skillcorner)

                    ranking_data = []
                    for _, row in df_ranked.iterrows():
                        entry = {
                            'Jogador': row['Jogador'],
                            'Clube': row.get('Equipa', row.get('Team', '-')),
                            'Idade': safe_int(row.get('Idade')),
                            'Min': safe_int(row.get('Minutos jogados:')),
                            'Score': row['Score'],
                        }
                        for idx_name in indices_cfg.keys():
                            if idx_name in row.index and pd.notna(row[idx_name]):
                                entry[idx_name] = row[idx_name]

                        nome_jogador = normalize_name(row['Jogador'])
                        sc_data = sc_lookup.get(nome_jogador, {})
                        if sc_data and posicao_calc in SKILLCORNER_INDICES:
                            for sc_idx in SKILLCORNER_INDICES[posicao_calc]:
                                short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                                if short_name in sc_data:
                                    entry[f'SC: {short_name}'] = sc_data[short_name]

                        ranking_data.append(entry)

                    if ranking_data:
                        df_resultado = pd.DataFrame(ranking_data)

                        if ordenar_por == '🎯 Índice Geral':
                            sort_col = 'Score'
                        else:
                            sort_col = ordenar_por.replace('📊 ', '').replace(' (índice)', '')

                        if sort_col in df_resultado.columns:
                            df_resultado = df_resultado.sort_values(sort_col, ascending=False)
                        else:
                            df_resultado = df_resultado.sort_values('Score', ascending=False)

                        df_resultado = df_resultado.head(100)
                        df_resultado.insert(0, '#', range(1, len(df_resultado) + 1))

                        column_config = {
                            '#': st.column_config.NumberColumn(width='small'),
                            'Score': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                        }
                        for col in df_resultado.columns:
                            if col in list(indices_cfg.keys()):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                            elif col.startswith('SC:'):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")

                        st.dataframe(df_resultado, width='stretch', height=600, hide_index=True, column_config=column_config)

            else:
                # Ordenacao por metrica bruta (nao-indice)
                sort_col = ordenar_por
                if sort_col in df_rank.columns:
                    df_rank_sorted = df_rank.sort_values(sort_col, ascending=False).head(100)

                    show_cols = ['Jogador']
                    if equipa_col and equipa_col in df_rank_sorted.columns:
                        show_cols.append(equipa_col)
                    for c in ['Idade', 'Minutos jogados:', sort_col]:
                        if c in df_rank_sorted.columns and c not in show_cols:
                            show_cols.append(c)

                    df_resultado = df_rank_sorted[show_cols].copy()
                    df_resultado.insert(0, '#', range(1, len(df_resultado) + 1))
                    st.dataframe(df_resultado, width='stretch', height=600, hide_index=True)
                else:
                    st.warning(f"Coluna '{sort_col}' nao encontrada nos dados")"""

    code, ok = apply_fix(code, OLD_4, NEW_4, "Tab 6 ranking indent + else branch")
    results['fix4_tab6_indent'] = ok

    # ============================================
    # FIX 5: Tab 7 - calculate_all_indices
    # ============================================
    print("\n5. Tab 7: usar calculate_all_indices na comparacao")
    OLD_5 = """                                indices_ref_vals = {idx_name: calculate_index(row_ref, metrics, base_calc_sim) 
                                                   for idx_name, metrics in indices_cfg_sim.items()}
                                indices_sim_vals = {idx_name: calculate_index(row_similar, metrics, base_calc_sim) 
                                                   for idx_name, metrics in indices_cfg_sim.items()}"""

    NEW_5 = """                                indices_ref_vals = calculate_all_indices(row_ref, indices_cfg_sim, base_calc_sim, categoria_sim)
                                indices_sim_vals = calculate_all_indices(row_similar, indices_cfg_sim, base_calc_sim, categoria_sim)"""

    code, ok = apply_fix(code, OLD_5, NEW_5, "Tab 7 calculate_all_indices")
    results['fix5_tab7'] = ok

    # ============================================
    # RESULTADO
    # ============================================
    write_file(out, code)

    applied = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"RESULTADO: {applied}/{total} fixes aplicados")
    for k, v in results.items():
        print(f"  [{'OK' if v else 'SKIP'}] {k}")
    print(f"\nOutput: {out} ({len(code)} chars)")

    if applied < total:
        print("\nFixes nao aplicados: o texto exato nao foi encontrado.")
        print("Pode ser diferenca de espacos/tabs ou o codigo ja foi modificado.")
        print("Aplique manualmente os fixes restantes.")

    # Validacao basica
    print("\nValidacao:")
    # Check no indent-0 code outside functions
    lines = code.split('\n')
    problems = []
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped and not stripped.startswith(('#', 'import ', 'from ', 'def ', 'class ', '@', 'if __name__', 'COLORS', 'COUNTRY_FLAGS', 'CLUB_LOGOS', 'LEAGUE_LOGOS', 'INDICES_CONFIG', 'POSICAO_MAP', 'POSICOES_DISPLAY', 'SKILLCORNER_INDICES', 'SERIE_B_TEAMS', 'GOOGLE_SHEET_ID')):
            # Check if it's a continuation or dict/list
            if not stripped.startswith(("'", '"', "}", "]", ")", "{", "[", "(")) and not stripped.startswith(('st.', 'POSICAO_ALIAS')):
                problems.append(f"  L{i}: '{stripped[:60]}'")

    if problems:
        print(f"  AVISO: {len(problems)} linhas com indent=0 suspeitas:")
        for p in problems[:10]:
            print(p)
    else:
        print("  OK - nenhuma linha indent=0 suspeita")


if __name__ == '__main__':
    main()
