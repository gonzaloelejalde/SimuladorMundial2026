from itertools import combinations
import random

# =========================
# TABLAS
# =========================

def empty_table(teams):
    return {
        t: {"pj": 0, "pts": 0, "gf": 0, "gc": 0}
        for t in teams
    }


def apply_result(table, t1, t2, g1, g2):
    table[t1]["pj"] += 1
    table[t2]["pj"] += 1

    table[t1]["gf"] += g1
    table[t1]["gc"] += g2
    table[t2]["gf"] += g2
    table[t2]["gc"] += g1

    if g1 > g2:
        table[t1]["pts"] += 3
    elif g2 > g1:
        table[t2]["pts"] += 3
    else:
        table[t1]["pts"] += 1
        table[t2]["pts"] += 1


def sort_table(table):
    return sorted(
        table.items(),
        key=lambda x: (
            x[1]["pts"],
            x[1]["gf"] - x[1]["gc"],
            x[1]["gf"]
        ),
        reverse=True
    )


def group_matches(teams):
    return list(combinations(teams, 2))


def groups_finished(groups, played):
    for g, teams in groups.items():
        if len(played[g]) != len(list(combinations(teams, 2))):
            return False
    return True


# =========================
# CLASIFICADOS
# =========================

def rank_teams(tables):
    firsts = {}
    seconds = {}
    thirds = []

    for g, table in tables.items():
        ranked = sort_table(table)

        firsts[g] = ranked[0][0]
        seconds[g] = ranked[1][0]

        team, s = ranked[2]
        thirds.append({
            "team": team,
            "pts": s["pts"],
            "dg": s["gf"] - s["gc"],
            "gf": s["gf"]
        })

    thirds.sort(
        key=lambda x: (x["pts"], x["dg"], x["gf"]),
        reverse=True
    )

    return firsts, seconds, thirds


# =========================
# FIXTURE OFICIAL 16AVOS
# =========================

OFFICIAL_16AVOS = [
    ("2A", "2B"),
    ("1E", "3"),
    ("1F", "2C"),
    ("1D", "2F"),
    ("1I", "3"),
    ("2E", "2I"),
    ("1A", "3"),
    ("1L", "3"),
    ("1D", "3"),
    ("1G", "3"),
    ("2K", "2L"),
    ("1H", "2J"),
    ("1B", "3"),
    ("1J", "2H"),
    ("1K", "3"),
    ("2D", "2G"),
]


def resolve_slot(code, firsts, seconds):
    pos = code[0]
    group = code[1]

    if pos == "1":
        return firsts[group]
    if pos == "2":
        return seconds[group]

    raise ValueError(f"Slot inválido: {code}")


def resolve_third_random(thirds, used):
    disponibles = [t["team"] for t in thirds if t["team"] not in used]

    if not disponibles:
        raise ValueError("No quedan terceros disponibles")

    return random.choice(disponibles)


def build_16avos(firsts, seconds, thirds):
    bracket = []
    used = set()

    for a, b in OFFICIAL_16AVOS:
        team_a = resolve_slot(a, firsts, seconds)
        used.add(team_a)

        if b == "3":
            team_b = resolve_third_random(thirds, used)
        else:
            team_b = resolve_slot(b, firsts, seconds)

        if team_b in used:
            team_b = resolve_third_random(thirds, used)

        used.add(team_b)
        bracket.append((team_a, team_b))

    return bracket


# =========================
# SIGUIENTE RONDA
# =========================

def next_round(prev):
    winners = [m["winner"] for m in prev]
    return [
        {"a": winners[i], "b": winners[i + 1]}
        for i in range(0, len(winners), 2)
    ]
