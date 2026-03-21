"""
statsbomb_open.py — StatsBomb Open Data Integration
=====================================================
Fetches free, open-source match data from StatsBomb's GitHub repository.
Used for historical match analysis and event-level scouting insights.

Data source: https://github.com/statsbomb/open-data (public, free to use)
"""

import logging
from typing import Any, Dict, List, Optional
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# In-memory cache for fetched data
_cache: Dict[str, Any] = {}


def _fetch_json(path: str) -> Any:
    """Fetch JSON from StatsBomb open-data GitHub repo with caching."""
    if path in _cache:
        return _cache[path]

    url = f"{_BASE}/{path}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        _cache[path] = data
        return data
    except requests.RequestException as e:
        logger.error("StatsBomb fetch failed for %s: %s", url, e)
        return None


def clear_cache():
    """Clear the in-memory cache."""
    _cache.clear()


# ── Competitions ─────────────────────────────────────────────────────

def get_competitions() -> List[Dict[str, Any]]:
    """Return all available competitions with seasons."""
    raw = _fetch_json("competitions.json")
    if not raw:
        return []

    # Group by competition
    comp_map: Dict[int, Dict[str, Any]] = {}
    for entry in raw:
        cid = entry.get("competition_id")
        if cid not in comp_map:
            comp_map[cid] = {
                "competition_id": cid,
                "competition_name": entry.get("competition_name", ""),
                "country_name": entry.get("country_name", ""),
                "seasons": [],
            }
        comp_map[cid]["seasons"].append({
            "season_id": entry.get("season_id"),
            "season_name": entry.get("season_name", ""),
        })

    # Sort seasons within each competition
    for comp in comp_map.values():
        comp["seasons"].sort(key=lambda s: s.get("season_name", ""), reverse=True)

    result = sorted(comp_map.values(), key=lambda c: c.get("competition_name", ""))
    return result


# ── Matches ──────────────────────────────────────────────────────────

def get_matches(competition_id: int, season_id: int) -> List[Dict[str, Any]]:
    """Return all matches for a competition/season."""
    raw = _fetch_json(f"matches/{competition_id}/{season_id}.json")
    if not raw:
        return []

    matches = []
    for m in raw:
        home = m.get("home_team", {})
        away = m.get("away_team", {})
        matches.append({
            "match_id": m.get("match_id"),
            "match_date": m.get("match_date"),
            "kick_off": m.get("kick_off"),
            "home_team": home.get("home_team_name", ""),
            "away_team": away.get("away_team_name", ""),
            "home_score": m.get("home_score"),
            "away_score": m.get("away_score"),
            "competition_stage": m.get("competition_stage", {}).get("name", ""),
            "stadium": m.get("stadium", {}).get("name", "") if m.get("stadium") else "",
            "referee": m.get("referee", {}).get("name", "") if m.get("referee") else "",
        })

    matches.sort(key=lambda x: x.get("match_date", ""), reverse=True)
    return matches


# ── Events ───────────────────────────────────────────────────────────

def get_match_events(match_id: int) -> List[Dict[str, Any]]:
    """Return all events for a match."""
    raw = _fetch_json(f"events/{match_id}.json")
    if not raw:
        return []
    return raw


def get_match_summary(match_id: int) -> Dict[str, Any]:
    """Compute a summary of match events: goals, shots, passes, cards, etc."""
    events = get_match_events(match_id)
    if not events:
        return {"error": "No events found"}

    # Determine teams
    teams: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        team = ev.get("team", {}).get("name", "Unknown")
        if team not in teams:
            teams[team] = {
                "team": team,
                "goals": 0,
                "shots": 0,
                "shots_on_target": 0,
                "passes": 0,
                "passes_completed": 0,
                "tackles": 0,
                "interceptions": 0,
                "fouls": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "corners": 0,
                "dribbles": 0,
                "dribbles_completed": 0,
                "xg_total": 0.0,
            }

        t = teams[team]
        ev_type = ev.get("type", {}).get("name", "")

        if ev_type == "Shot":
            t["shots"] += 1
            shot = ev.get("shot", {})
            outcome = shot.get("outcome", {}).get("name", "")
            if outcome == "Goal":
                t["goals"] += 1
            if outcome in ("Goal", "Saved", "Saved To Post"):
                t["shots_on_target"] += 1
            xg = shot.get("statsbomb_xg", 0)
            if xg:
                t["xg_total"] += float(xg)

        elif ev_type == "Pass":
            t["passes"] += 1
            pass_data = ev.get("pass", {})
            outcome = pass_data.get("outcome")
            if outcome is None:  # None means completed
                t["passes_completed"] += 1
            pass_type = pass_data.get("type", {}).get("name", "")
            if pass_type == "Corner":
                t["corners"] += 1

        elif ev_type == "Duel":
            duel = ev.get("duel", {})
            duel_type = duel.get("type", {}).get("name", "")
            if duel_type == "Tackle":
                t["tackles"] += 1

        elif ev_type == "Interception":
            t["interceptions"] += 1

        elif ev_type == "Foul Committed":
            t["fouls"] += 1
            card = ev.get("foul_committed", {}).get("card", {}).get("name", "")
            if "Yellow" in card:
                t["yellow_cards"] += 1
            elif "Red" in card or "Second Yellow" in card:
                t["red_cards"] += 1

        elif ev_type == "Dribble":
            t["dribbles"] += 1
            outcome = ev.get("dribble", {}).get("outcome", {}).get("name", "")
            if outcome == "Complete":
                t["dribbles_completed"] += 1

    # Round xG
    for t in teams.values():
        t["xg_total"] = round(t["xg_total"], 2)
        t["pass_accuracy"] = round(
            t["passes_completed"] / t["passes"] * 100 if t["passes"] > 0 else 0, 1
        )

    return {
        "match_id": match_id,
        "teams": list(teams.values()),
    }


# ── Lineups ──────────────────────────────────────────────────────────

def get_lineups(match_id: int) -> List[Dict[str, Any]]:
    """Return lineups for a match."""
    raw = _fetch_json(f"lineups/{match_id}.json")
    if not raw:
        return []

    lineups = []
    for team_data in raw:
        team_name = team_data.get("team_name", "")
        players = []
        for p in team_data.get("lineup", []):
            positions = p.get("positions", [])
            pos_name = positions[0].get("position", "") if positions else ""
            players.append({
                "player_id": p.get("player_id"),
                "player_name": p.get("player_name", ""),
                "player_nickname": p.get("player_nickname"),
                "jersey_number": p.get("jersey_number"),
                "position": pos_name,
                "country": p.get("country", {}).get("name", "") if p.get("country") else "",
            })
        lineups.append({
            "team": team_name,
            "players": players,
        })

    return lineups


# ── Player match events ─────────────────────────────────────────────

def get_player_match_stats(match_id: int, player_name: str) -> Dict[str, Any]:
    """Extract stats for a specific player from match events."""
    events = get_match_events(match_id)
    if not events:
        return {"error": "No events found"}

    player_events = [
        e for e in events
        if e.get("player", {}).get("name", "").lower() == player_name.lower()
    ]

    if not player_events:
        return {"error": f"Player '{player_name}' not found in match"}

    team = player_events[0].get("team", {}).get("name", "")
    stats = {
        "player": player_name,
        "team": team,
        "match_id": match_id,
        "passes": 0,
        "passes_completed": 0,
        "shots": 0,
        "shots_on_target": 0,
        "goals": 0,
        "assists": 0,
        "xg": 0.0,
        "xa": 0.0,
        "tackles": 0,
        "interceptions": 0,
        "dribbles": 0,
        "dribbles_completed": 0,
        "fouls_committed": 0,
        "fouls_won": 0,
        "ball_recoveries": 0,
        "duels_won": 0,
        "aerial_won": 0,
        "touches": len(player_events),
        "key_passes": 0,
        "crosses": 0,
        "long_balls": 0,
        "through_balls": 0,
    }

    for ev in player_events:
        ev_type = ev.get("type", {}).get("name", "")

        if ev_type == "Pass":
            stats["passes"] += 1
            pass_data = ev.get("pass", {})
            if pass_data.get("outcome") is None:
                stats["passes_completed"] += 1
            if pass_data.get("goal_assist"):
                stats["assists"] += 1
            xa = pass_data.get("shot_assist") or pass_data.get("goal_assist")
            if xa:
                stats["key_passes"] += 1
            if pass_data.get("cross"):
                stats["crosses"] += 1
            if pass_data.get("length", 0) > 32:
                stats["long_balls"] += 1
            if pass_data.get("through_ball"):
                stats["through_balls"] += 1

        elif ev_type == "Shot":
            stats["shots"] += 1
            shot = ev.get("shot", {})
            outcome = shot.get("outcome", {}).get("name", "")
            if outcome == "Goal":
                stats["goals"] += 1
            if outcome in ("Goal", "Saved", "Saved To Post"):
                stats["shots_on_target"] += 1
            xg = shot.get("statsbomb_xg", 0)
            if xg:
                stats["xg"] += float(xg)

        elif ev_type == "Duel":
            duel = ev.get("duel", {})
            duel_type = duel.get("type", {}).get("name", "")
            outcome = duel.get("outcome", {}).get("name", "")
            if duel_type == "Tackle":
                stats["tackles"] += 1
            if "Won" in outcome or "Success" in outcome:
                stats["duels_won"] += 1
            if duel_type == "Aerial Lost" or "Aerial" in duel_type:
                if "Won" in outcome:
                    stats["aerial_won"] += 1

        elif ev_type == "Interception":
            stats["interceptions"] += 1

        elif ev_type == "Dribble":
            stats["dribbles"] += 1
            outcome = ev.get("dribble", {}).get("outcome", {}).get("name", "")
            if outcome == "Complete":
                stats["dribbles_completed"] += 1

        elif ev_type == "Foul Committed":
            stats["fouls_committed"] += 1

        elif ev_type == "Foul Won":
            stats["fouls_won"] += 1

        elif ev_type == "Ball Recovery":
            stats["ball_recoveries"] += 1

    stats["xg"] = round(stats["xg"], 3)
    stats["pass_accuracy"] = round(
        stats["passes_completed"] / stats["passes"] * 100 if stats["passes"] > 0 else 0, 1
    )
    stats["dribble_success"] = round(
        stats["dribbles_completed"] / stats["dribbles"] * 100 if stats["dribbles"] > 0 else 0, 1
    )

    return stats


# ── Shot map data ────────────────────────────────────────────────────

def get_shot_map(match_id: int) -> List[Dict[str, Any]]:
    """Extract all shots from a match with location and xG for visualization."""
    events = get_match_events(match_id)
    if not events:
        return []

    shots = []
    for ev in events:
        if ev.get("type", {}).get("name") != "Shot":
            continue

        shot = ev.get("shot", {})
        location = ev.get("location", [])
        end_location = shot.get("end_location", [])

        shots.append({
            "player": ev.get("player", {}).get("name", ""),
            "team": ev.get("team", {}).get("name", ""),
            "minute": ev.get("minute", 0),
            "second": ev.get("second", 0),
            "location_x": location[0] if len(location) > 0 else None,
            "location_y": location[1] if len(location) > 1 else None,
            "end_x": end_location[0] if len(end_location) > 0 else None,
            "end_y": end_location[1] if len(end_location) > 1 else None,
            "xg": round(float(shot.get("statsbomb_xg", 0)), 3),
            "outcome": shot.get("outcome", {}).get("name", ""),
            "technique": shot.get("technique", {}).get("name", ""),
            "body_part": shot.get("body_part", {}).get("name", ""),
            "shot_type": shot.get("type", {}).get("name", ""),
        })

    return shots


# ── Pass network data ────────────────────────────────────────────────

def get_pass_network(match_id: int, team_name: str) -> Dict[str, Any]:
    """Build pass network data for a team in a match."""
    events = get_match_events(match_id)
    if not events:
        return {"error": "No events found"}

    # Filter passes for the team
    passes = [
        e for e in events
        if e.get("type", {}).get("name") == "Pass"
        and e.get("team", {}).get("name", "").lower() == team_name.lower()
    ]

    if not passes:
        return {"error": f"No passes found for team '{team_name}'"}

    # Build adjacency: passer → receiver
    player_positions: Dict[str, Dict[str, Any]] = {}
    connections: Dict[str, int] = {}  # "from|to" → count

    for p in passes:
        passer = p.get("player", {}).get("name", "")
        receiver = p.get("pass", {}).get("recipient", {}).get("name", "")
        location = p.get("location", [])

        if passer and passer not in player_positions:
            player_positions[passer] = {"x_sum": 0, "y_sum": 0, "count": 0}

        if passer:
            player_positions[passer]["x_sum"] += location[0] if len(location) > 0 else 0
            player_positions[passer]["y_sum"] += location[1] if len(location) > 1 else 0
            player_positions[passer]["count"] += 1

        if passer and receiver and p.get("pass", {}).get("outcome") is None:
            key = f"{passer}|{receiver}"
            connections[key] = connections.get(key, 0) + 1

    # Average positions
    nodes = []
    for name, pos in player_positions.items():
        if pos["count"] > 0:
            nodes.append({
                "player": name,
                "avg_x": round(pos["x_sum"] / pos["count"], 1),
                "avg_y": round(pos["y_sum"] / pos["count"], 1),
                "total_passes": pos["count"],
            })

    # Edges (minimum 3 passes to show connection)
    edges = []
    for key, count in connections.items():
        if count >= 3:
            parts = key.split("|")
            edges.append({
                "from": parts[0],
                "to": parts[1],
                "passes": count,
            })

    edges.sort(key=lambda e: e["passes"], reverse=True)

    return {
        "team": team_name,
        "match_id": match_id,
        "nodes": sorted(nodes, key=lambda n: n["total_passes"], reverse=True),
        "edges": edges[:30],  # top 30 connections
    }


# ── Season Insights (aggregated) ──────────────────────────────────

def get_season_insights(competition_id: int, season_id: int) -> Dict[str, Any]:
    """Aggregate match-level data across an entire season for insights."""
    matches = get_matches(competition_id, season_id)
    if not matches:
        return {"error": "No matches found"}

    # Limit to avoid extremely long processing (StatsBomb open data)
    match_ids = [m["match_id"] for m in matches]

    # Aggregate structures
    team_agg: Dict[str, Dict[str, Any]] = {}
    player_goals: Dict[str, Dict[str, Any]] = {}
    player_xg: Dict[str, Dict[str, Any]] = {}
    player_assists: Dict[str, Dict[str, Any]] = {}
    player_key_passes: Dict[str, Dict[str, Any]] = {}
    all_shots: List[Dict[str, Any]] = []
    total_goals = 0
    total_xg = 0.0
    matches_processed = 0

    for mid in match_ids:
        try:
            summary = get_match_summary(mid)
            if "error" in summary:
                continue

            matches_processed += 1

            for t in summary.get("teams", []):
                name = t["team"]
                if name not in team_agg:
                    team_agg[name] = {
                        "team": name,
                        "matches": 0,
                        "goals": 0,
                        "goals_against": 0,
                        "xg_total": 0.0,
                        "xg_against": 0.0,
                        "shots": 0,
                        "shots_on_target": 0,
                        "passes": 0,
                        "passes_completed": 0,
                        "tackles": 0,
                        "interceptions": 0,
                        "fouls": 0,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "corners": 0,
                        "dribbles": 0,
                        "dribbles_completed": 0,
                        "wins": 0,
                        "draws": 0,
                        "losses": 0,
                    }

                ta = team_agg[name]
                ta["matches"] += 1
                ta["goals"] += t["goals"]
                ta["xg_total"] += t["xg_total"]
                ta["shots"] += t["shots"]
                ta["shots_on_target"] += t["shots_on_target"]
                ta["passes"] += t["passes"]
                ta["passes_completed"] += t["passes_completed"]
                ta["tackles"] += t["tackles"]
                ta["interceptions"] += t["interceptions"]
                ta["fouls"] += t["fouls"]
                ta["yellow_cards"] += t["yellow_cards"]
                ta["red_cards"] += t["red_cards"]
                ta["corners"] += t["corners"]
                ta["dribbles"] += t["dribbles"]
                ta["dribbles_completed"] += t["dribbles_completed"]
                total_goals += t["goals"]
                total_xg += t["xg_total"]

            # Compute goals against and W/D/L
            teams_in_match = summary.get("teams", [])
            if len(teams_in_match) == 2:
                t0, t1 = teams_in_match[0], teams_in_match[1]
                team_agg[t0["team"]]["goals_against"] += t1["goals"]
                team_agg[t0["team"]]["xg_against"] += t1["xg_total"]
                team_agg[t1["team"]]["goals_against"] += t0["goals"]
                team_agg[t1["team"]]["xg_against"] += t0["xg_total"]

                if t0["goals"] > t1["goals"]:
                    team_agg[t0["team"]]["wins"] += 1
                    team_agg[t1["team"]]["losses"] += 1
                elif t0["goals"] < t1["goals"]:
                    team_agg[t1["team"]]["wins"] += 1
                    team_agg[t0["team"]]["losses"] += 1
                else:
                    team_agg[t0["team"]]["draws"] += 1
                    team_agg[t1["team"]]["draws"] += 1

            # Collect shots for player-level aggregation
            shots = get_shot_map(mid)
            for s in shots:
                all_shots.append(s)
                pname = s.get("player", "")
                team = s.get("team", "")
                xg_val = s.get("xg", 0)
                is_goal = s.get("outcome") == "Goal"

                if pname:
                    if pname not in player_xg:
                        player_xg[pname] = {"player": pname, "team": team, "xg": 0.0, "shots": 0}
                    player_xg[pname]["xg"] += xg_val
                    player_xg[pname]["shots"] += 1

                    if is_goal:
                        if pname not in player_goals:
                            player_goals[pname] = {"player": pname, "team": team, "goals": 0, "xg": 0.0}
                        player_goals[pname]["goals"] += 1
                        player_goals[pname]["xg"] += xg_val

        except Exception as e:
            logger.warning("Failed to process match %s: %s", mid, e)
            continue

    # Finalize team aggregations
    team_list = []
    for ta in team_agg.values():
        m_count = ta["matches"]
        ta["xg_total"] = round(ta["xg_total"], 2)
        ta["xg_against"] = round(ta["xg_against"], 2)
        ta["xg_diff"] = round(ta["goals"] - ta["xg_total"], 2)
        ta["pass_accuracy"] = round(
            ta["passes_completed"] / ta["passes"] * 100 if ta["passes"] > 0 else 0, 1
        )
        ta["shot_accuracy"] = round(
            ta["shots_on_target"] / ta["shots"] * 100 if ta["shots"] > 0 else 0, 1
        )
        ta["points"] = ta["wins"] * 3 + ta["draws"]
        ta["goal_diff"] = ta["goals"] - ta["goals_against"]
        ta["avg_goals"] = round(ta["goals"] / m_count, 2) if m_count > 0 else 0
        ta["avg_xg"] = round(ta["xg_total"] / m_count, 2) if m_count > 0 else 0
        ta["defensive_actions"] = ta["tackles"] + ta["interceptions"]
        ta["avg_defensive"] = round(ta["defensive_actions"] / m_count, 1) if m_count > 0 else 0
        team_list.append(ta)

    team_list.sort(key=lambda t: (t["points"], t["goal_diff"], t["goals"]), reverse=True)

    # Top scorers
    top_scorers = sorted(player_goals.values(), key=lambda p: (p["goals"], p["xg"]), reverse=True)[:15]
    for p in top_scorers:
        p["xg"] = round(p["xg"], 2)
        p["xg_diff"] = round(p["goals"] - p["xg"], 2)

    # Top xG (including non-scorers with high xG)
    top_xg = sorted(player_xg.values(), key=lambda p: p["xg"], reverse=True)[:15]
    for p in top_xg:
        p["xg"] = round(p["xg"], 2)
        p["goals"] = player_goals.get(p["player"], {}).get("goals", 0)
        p["xg_diff"] = round(p["goals"] - p["xg"], 2)

    # xG overperformers/underperformers (teams)
    xg_analysis = []
    for ta in team_list:
        xg_analysis.append({
            "team": ta["team"],
            "goals": ta["goals"],
            "xg": ta["xg_total"],
            "diff": ta["xg_diff"],
            "goals_against": ta["goals_against"],
            "xg_against": ta["xg_against"],
        })
    xg_analysis.sort(key=lambda x: x["diff"], reverse=True)

    # Tactical patterns: most possession, most aggressive pressing, best passing
    tactical = {
        "most_possession": sorted(team_list, key=lambda t: t["passes"], reverse=True)[:5],
        "most_pressing": sorted(team_list, key=lambda t: t["avg_defensive"], reverse=True)[:5],
        "best_passing": sorted(team_list, key=lambda t: t["pass_accuracy"], reverse=True)[:5],
        "most_shots": sorted(team_list, key=lambda t: t["shots"], reverse=True)[:5],
    }

    # Format tactical data (lighter)
    for key in tactical:
        tactical[key] = [
            {"team": t["team"], "value": t["passes"] if key == "most_possession"
             else t["avg_defensive"] if key == "most_pressing"
             else t["pass_accuracy"] if key == "best_passing"
             else t["shots"],
             "matches": t["matches"]}
            for t in tactical[key]
        ]

    return {
        "competition_id": competition_id,
        "season_id": season_id,
        "matches_total": len(matches),
        "matches_processed": matches_processed,
        "total_goals": total_goals // 2 if total_goals > 0 else 0,  # goals counted twice (both teams)
        "total_xg": round(total_xg / 2, 2) if total_xg > 0 else 0,
        "avg_goals_per_match": round(total_goals / (2 * matches_processed), 2) if matches_processed > 0 else 0,
        "avg_xg_per_match": round(total_xg / (2 * matches_processed), 2) if matches_processed > 0 else 0,
        "teams": team_list,
        "top_scorers": top_scorers,
        "top_xg": top_xg,
        "xg_analysis": xg_analysis,
        "tactical": tactical,
    }
