from flask import Flask, render_template, request, redirect
from data import groups
from logic import (
    empty_table, apply_result, sort_table,
    group_matches, groups_finished, rank_teams,
    build_16avos, next_round, OFFICIAL_16AVOS
)
import copy

app = Flask(__name__)

# =====================
# ESTADO GLOBAL
# =====================

tables = {g: empty_table(t) for g, t in groups.items()}
played = {g: {} for g in groups}

# Inicializar playoffs con placeholders (ej. '1A', '2B', '3') para que siempre se muestren
playoff_state = {
    "rounds": [[{"a": a, "b": b} for a, b in OFFICIAL_16AVOS]]
}

# =====================
# RUTAS
# =====================

@app.route("/")
def index():
    return redirect("/groups")


@app.route("/groups", methods=["GET", "POST"])
def groups_view():
    global tables

    # ---------------------
    # GUARDAR RESULTADO
    # ---------------------
    if request.method == "POST":
        group = request.form["group"]
        t1 = request.form["t1"]
        t2 = request.form["t2"]
        g1 = int(request.form["g1"])
        g2 = int(request.form["g2"])

        key = "||".join(sorted([t1, t2]))

        played[group][key] = {
            "t1": t1,
            "t2": t2,
            "g1": g1,
            "g2": g2
        }

        # ⚠️ si cambian resultados, reinicio playoffs
        playoff_state["rounds"] = []

    # ---------------------
    # RECONSTRUIR TABLAS
    # ---------------------
    tables = {g: empty_table(teams) for g, teams in groups.items()}

    for g in played:
        for m in played[g].values():
            apply_result(
                tables[g],
                m["t1"], m["t2"],
                m["g1"], m["g2"]
            )

    # ---------------------
    # DATA PARA TEMPLATE
    # ---------------------
    group_data = {
        g: {
            "teams": teams,
            "matches": group_matches(teams),
            "table": sort_table(tables[g])
        }
        for g, teams in groups.items()
    }

    finished = groups_finished(groups, played)

    # ---------------------
    # INICIALIZAR PLAYOFFS
    # ---------------------
    # Cuando los grupos ya estén completos, resolver placeholders a nombres reales
    if finished:
        firsts, seconds, thirds = rank_teams(tables)
        initial = build_16avos(firsts, seconds, thirds)

        # Guardar copia previa para mapear selecciones antiguas a nombres reales
        prev_rounds = copy.deepcopy(playoff_state.get("rounds", []))

        # Reemplazar la primera ronda preservando cualquier 'winner' previamente elegido
        new_round = []
        old_round = prev_rounds[0] if prev_rounds else []

        for i, (a_name, b_name) in enumerate(initial):
            old = old_round[i] if i < len(old_round) else {}
            new_match = {"a": a_name, "b": b_name}

            if "winner" in old:
                w = old["winner"]
                if w == old.get("a"):
                    new_match["winner"] = a_name
                elif w == old.get("b"):
                    new_match["winner"] = b_name
                else:
                    new_match["winner"] = w

            new_round.append(new_match)

        # Establecer la primera ronda resuelta
        if playoff_state.get("rounds"):
            playoff_state["rounds"][0] = new_round
        else:
            playoff_state["rounds"] = [new_round]

        # Construir un diccionario de mapeo de valores antiguos -> nombres reales
        mapping = {}
        for i, old in enumerate(old_round):
            if not old:
                continue
            if "a" in old:
                mapping[old["a"]] = new_round[i]["a"]
            if "b" in old:
                mapping[old["b"]] = new_round[i]["b"]

        # Aplicar mapeo a rondas siguientes (si existen), preservando winners
        for r_idx in range(1, len(prev_rounds)):
            if r_idx >= len(playoff_state.get("rounds", [])):
                # si no hay esa ronda en el estado actual, conservar la previa (mapeada)
                playoff_state["rounds"].append(prev_rounds[r_idx])

            for m_idx, old_match in enumerate(prev_rounds[r_idx]):
                # asegurar que exista la entrada actual
                if m_idx >= len(playoff_state["rounds"][r_idx]):
                    playoff_state["rounds"][r_idx].append(copy.deepcopy(old_match))

                cur_match = playoff_state["rounds"][r_idx][m_idx]

                # mapear campos 'a', 'b', 'winner' si estaban apuntando a placeholders
                for key in ("a", "b", "winner"):
                    if key in old_match and old_match[key] in mapping:
                        cur_match[key] = mapping[old_match[key]]

    return render_template(
        "groups.html",
        group_data=group_data,
        played=played,
        finished=finished,
        playoff_state=playoff_state
    )


@app.route("/pick_winner", methods=["POST"])
def pick_winner():
    r = int(request.form["round"])
    m = int(request.form["match"])
    winner = request.form["winner"]

    playoff_state["rounds"][r][m]["winner"] = winner

    if all("winner" in x for x in playoff_state["rounds"][r]):
        if len(playoff_state["rounds"][r]) > 1:
            playoff_state["rounds"].append(
                next_round(playoff_state["rounds"][r])
            )

    return redirect("/groups")


if __name__ == "__main__":
    app.run(debug=True)
