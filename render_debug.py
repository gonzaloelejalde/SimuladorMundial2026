from app import app, tables, played, groups as GROUPS
from itertools import combinations

# Mark every group match as played with dummy scores so 'finished' becomes True
for g, teams in GROUPS.items():
	played[g] = {}
	for t1, t2 in combinations(teams, 2):
		key = '||'.join(sorted([t1, t2]))
		played[g][key] = {"t1": t1, "t2": t2, "g1": 1, "g2": 0}

app.testing = True
c = app.test_client()
resp = c.get('/groups')
html = resp.get_data(as_text=True)
start = html.find('<h1>Playoffs')
print(html[start:start+3000])
