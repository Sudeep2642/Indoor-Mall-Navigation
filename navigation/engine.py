"""
Navigation Engine — mall-agnostic shortest-path finder.
Builds a graph per mall from the Edge table, then runs Dijkstra.
Returns structured step-by-step directions including floor changes.
"""

import networkx as nx
from .models import Location, Edge


def build_graph(mall):
    """Build NetworkX graph for a mall from DB."""
    G = nx.Graph()

    locations = Location.objects.filter(mall=mall, is_active=True).select_related('floor')
    for loc in locations:
        G.add_node(loc.code, obj=loc)

    edges = Edge.objects.filter(mall=mall).select_related('from_loc', 'to_loc')
    for e in edges:
        G.add_edge(e.from_loc.code, e.to_loc.code, weight=e.weight, walk_type=e.walk_type)

    return G


def find_route(mall, from_code, to_code):
    """
    Find shortest route between two location codes.

    Returns dict:
    {
        'ok': True/False,
        'error': str or None,
        'from': Location obj,
        'to': Location obj,
        'steps': [ {name, floor_number, floor_label, instruction, walk_type, x_pct, y_pct, code} ],
        'floors_visited': [floor numbers in order],
        'total_steps': int,
        'est_minutes': int,
    }
    """
    G = build_graph(mall)

    if from_code not in G:
        return {'ok': False, 'error': f'Start location "{from_code}" not found.'}
    if to_code not in G:
        return {'ok': False, 'error': f'Destination "{to_code}" not found.'}

    if from_code == to_code:
        loc = G.nodes[from_code]['obj']
        return {
            'ok': True,
            'error': None,
            'from': loc,
            'to': loc,
            'steps': [{
                'code': loc.code,
                'name': loc.name,
                'floor_number': loc.floor.number,
                'floor_label': loc.floor.label,
                'x_pct': loc.x_pct,
                'y_pct': loc.y_pct,
                'loc_type': loc.loc_type,
                'walk_type': 'walk',
                'instruction': 'You are already here!',
                'is_floor_change': False,
            }],
            'floors_visited': [loc.floor.number],
            'total_steps': 1,
            'est_minutes': 0,
        }

    try:
        path_codes = nx.shortest_path(G, from_code, to_code, weight='weight')
    except nx.NetworkXNoPath:
        return {'ok': False, 'error': 'No path found. The map may not be fully connected yet.'}
    except nx.NodeNotFound as e:
        return {'ok': False, 'error': str(e)}

    # Build step list
    steps = []
    floors_visited = []

    for i, code in enumerate(path_codes):
        loc = G.nodes[code]['obj']
        floor_num = loc.floor.number

        if not floors_visited or floors_visited[-1] != floor_num:
            floors_visited.append(floor_num)

        # Determine walk_type from edge
        walk_type = 'walk'
        is_floor_change = False
        if i > 0:
            edge_data = G.edges[path_codes[i-1], code]
            walk_type = edge_data.get('walk_type', 'walk')
            prev_loc = G.nodes[path_codes[i-1]]['obj']
            is_floor_change = prev_loc.floor.number != floor_num

        # Build human-readable instruction
        if i == 0:
            instruction = f"Start at {loc.name} on {loc.floor.label}."
        elif i == len(path_codes) - 1:
            instruction = f"Arrive at {loc.name} — your destination!"
        elif is_floor_change:
            prev = G.nodes[path_codes[i-1]]['obj']
            direction = "up" if floor_num > prev.floor.number else "down"
            if walk_type == 'lift':
                instruction = f"Take the lift {direction} to {loc.floor.label}."
            elif walk_type == 'escalator':
                instruction = f"Take the escalator {direction} to {loc.floor.label}."
            elif walk_type == 'stairs':
                instruction = f"Use the stairs {direction} to {loc.floor.label}."
            else:
                instruction = f"Go {direction} to {loc.floor.label}."
        elif loc.loc_type == 'junction':
            instruction = f"Continue through the corridor."
        elif loc.loc_type in ('lift', 'escalator', 'stairs'):
            instruction = f"Pass {loc.name}."
        else:
            instruction = f"Pass {loc.name}."

        steps.append({
            'code': loc.code,
            'name': loc.name,
            'floor_number': floor_num,
            'floor_label': loc.floor.label,
            'x_pct': loc.x_pct,
            'y_pct': loc.y_pct,
            'loc_type': loc.loc_type,
            'walk_type': walk_type,
            'instruction': instruction,
            'is_floor_change': is_floor_change,
        })

    # Estimate: ~1 min per 2 steps + 1 min per floor change
    floor_changes = sum(1 for s in steps if s['is_floor_change'])
    est_minutes = max(1, round(len(steps) * 0.5 + floor_changes * 0.5))

    from_obj = G.nodes[from_code]['obj']
    to_obj   = G.nodes[to_code]['obj']

    return {
        'ok': True,
        'error': None,
        'from': from_obj,
        'to': to_obj,
        'steps': steps,
        'floors_visited': floors_visited,
        'total_steps': len(steps),
        'est_minutes': est_minutes,
    }


def get_all_locations_json(mall):
    """Return all active locations as a list of dicts for JS."""
    locs = Location.objects.filter(mall=mall, is_active=True).select_related('floor')
    result = []
    for loc in locs:
        result.append({
            'code': loc.code,
            'name': loc.name,
            'floor_number': loc.floor.number,
            'floor_label': loc.floor.label,
            'loc_type': loc.loc_type,
            'area_size': loc.area_size,
            'x_pct': loc.x_pct,
            'y_pct': loc.y_pct,
        })
    return result


def get_all_edges_json(mall):
    """Return all edges as list of dicts for JS map drawing."""
    edges = Edge.objects.filter(mall=mall).select_related('from_loc__floor', 'to_loc__floor')
    result = []
    for e in edges:
        result.append({
            'from_code': e.from_loc.code,
            'to_code': e.to_loc.code,
            'from_floor': e.from_loc.floor.number,
            'to_floor': e.to_loc.floor.number,
            'walk_type': e.walk_type,
        })
    return result
