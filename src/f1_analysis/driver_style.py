"""Race-specific F1 feed colours and stable teammate line styles."""
import re
from collections import defaultdict


def driver_styles(drivers):
    teams=defaultdict(list)
    for row in drivers:teams[row.get('team_name') or str(row['driver_number'])].append(row)
    styles={}
    for team,rows in teams.items():
        rows=sorted(rows,key=lambda row:row['driver_number'])
        colors=[r.get('team_colour','').lstrip('#') for r in rows]
        color=next(('#'+c.upper() for c in colors if re.fullmatch('[0-9a-fA-F]{6}',c)), '#B3BECE')
        for i,row in enumerate(rows):
            number=row['driver_number'];code=row.get('name_acronym') or str(number)
            styles[number]={'color':color,'linestyle':'-' if i==0 else ':','marker':'o' if i==0 else 's',
                            'label':f'{number} {code}','number':number,'team':team,
                            'color_source':'OpenF1 drivers.team_colour voor de gekozen racesessie'}
    return styles
