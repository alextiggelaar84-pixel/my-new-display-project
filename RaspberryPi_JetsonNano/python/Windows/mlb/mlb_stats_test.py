import statsapi
# Pretty-prints the entire dictionary structure cleanly
##pprint(standings)
leagues = [103, 104]  # 103 for AL, 104 for NL

for league_id in leagues:
    standings = statsapi.standings_data(leagueId=league_id)
    for division_id, division in standings.items():
        div_name = division.get('div_name')
        print(div_name)
        for team in division.get('teams', []):
            team_name = team.get('name')
            wins = team.get('w')
            losses = team.get('l')
            gb = team.get('gb')

            pct = wins/(wins + losses) if (wins + losses) > 0 else 0
            print(f"{team_name}: {wins}-{losses}, PCT: {pct:.3f}, GB: {gb}")
        print(f"\n")


    
    