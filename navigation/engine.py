"""
Navigation Engine — mall-agnostic shortest-path finder.
Builds a graph per mall from the Edge table, then runs Dijkstra.

Polygon obstacle avoidance:
  Locations with an area_polygon (shops, restaurants, etc.) act as obstacles.
  Any edge whose straight-line segment crosses through an obstacle polygon
  gets a very high weight penalty, forcing Dijkstra to route around it.
  The start and destination nodes are always exempt (you need to enter them).
"""

import networkx as nx
from .models import Location, Edge


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

def _on_segment(p, q, r):
    return (min(p[0],r[0]) <= q[0] <= max(p[0],r[0]) and
            min(p[1],r[1]) <= q[1] <= max(p[1],r[1]))

def _segments_intersect(p1, p2, p3, p4):
    """Return True if line segment p1-p2 intersects p3-p4."""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    if d1 == 0 and _on_segment(p3, p1, p4): return True
    if d2 == 0 and _on_segment(p3, p2, p4): return True
    if d3 == 0 and _on_segment(p1, p3, p2): return True
    if d4 == 0 and _on_segment(p1, p4, p2): return True
    return False

def _point_in_polygon(px, py, polygon):
    """Ray-casting point-in-polygon test."""
    n = len(polygon)
    inside = False
    x, y = px, py
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj-xi)*(y-yi)/(yj-yi)+xi):
            inside = not inside
        j = i
    return inside

def _edge_blocked_by_polygon(ax, ay, bx, by, polygon):
    """
    Returns True if segment A→B is blocked by the polygon obstacle.
    Blocked means: the segment crosses any polygon edge AND neither
    endpoint is inside the polygon (endpoints inside = entering/leaving the shop,
    which is allowed).
    """
    if len(polygon) < 3:
        return False
    a_inside = _point_in_polygon(ax, ay, polygon)
    b_inside = _point_in_polygon(bx, by, polygon)
    # If both endpoints are inside the same obstacle it's fine (e.g. intra-shop edge)
    if a_inside and b_inside:
        return False
    # If exactly one endpoint is inside, allow — they're entering/leaving
    if a_inside or b_inside:
        return False
    # Both outside — check if the segment still punches through the polygon
    n = len(polygon)
    for i in range(n):
        px1, py1 = polygon[i]
        px2, py2 = polygon[(i+1) % n]
        if _segments_intersect((ax,ay),(bx,by),(px1,py1),(px2,py2)):
            return True
    return False


# ── Graph builder ─────────────────────────────────────────────────────────────

# Weight multiplier applied to edges that cross an obstacle polygon.
# High enough that Dijkstra always prefers going around.
OBSTACLE_PENALTY = 1_000_000

def build_graph(mall):
    """Build NetworkX graph for a mall from DB, respecting polygon obstacles."""
    G = nx.Graph()

    locations = Location.objects.filter(mall=mall, is_active=True).select_related('floor')
    loc_map = {}
    for loc in locations:
        G.add_node(loc.code, obj=loc)
        loc_map[loc.code] = loc

    # Collect obstacle polygons: only shop/restaurant/etc that have a drawn polygon
    # Exclude junction/lift/stairs/escalator types — those are corridor elements
    OBSTACLE_TYPES = {'shop', 'restaurant', 'restroom', 'atm', 'parking', 'info', 'emergency'}
    obstacles = []
    for loc in loc_map.values():
        if loc.area_polygon and len(loc.area_polygon) >= 3 and loc.loc_type in OBSTACLE_TYPES:
            obstacles.append({
                'code': loc.code,
                'polygon': loc.area_polygon,   # list of [x_pct, y_pct]
                'floor': loc.floor.number,
            })

    edges = Edge.objects.filter(mall=mall).select_related('from_loc', 'to_loc')
    for e in edges:
        a = e.from_loc
        b = e.to_loc
        base_weight = e.weight

        # Only check obstacles on same floor (cross-floor edges use lifts etc.)
        extra = 0
        if a.floor.number == b.floor.number:
            for obs in obstacles:
                # Skip if this edge connects to/from the obstacle's own node
                if obs['floor'] != a.floor.number:
                    continue
                if obs['code'] in (a.code, b.code):
                    continue
                if _edge_blocked_by_polygon(
                    a.x_pct, a.y_pct,
                    b.x_pct, b.y_pct,
                    obs['polygon']
                ):
                    extra = max(extra, OBSTACLE_PENALTY)

        G.add_edge(
            a.code, b.code,
            weight=base_weight + extra,
            walk_type=e.walk_type,
            blocked=(extra > 0),
        )

    return G


# ── Route finder ──────────────────────────────────────────────────────────────

def find_route(mall, from_code, to_code):
    """
    Find shortest route between two location codes.

    Returns dict:
    {
        'ok': True/False,
        'error': str or None,
        'from': Location obj,
        'to': Location obj,
        'steps': [ {name, floor_number, floor_label, instruction,
                    walk_type, x_pct, y_pct, code} ],
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
            'ok': True, 'error': None,
            'from': loc, 'to': loc,
            'steps': [{
                'code': loc.code, 'name': loc.name,
                'floor_number': loc.floor.number,
                'floor_label': loc.floor.label,
                'x_pct': loc.x_pct, 'y_pct': loc.y_pct,
                'loc_type': loc.loc_type, 'walk_type': 'walk',
                'instruction': 'You are already here!',
                'is_floor_change': False,
            }],
            'floors_visited': [loc.floor.number],
            'total_steps': 1, 'est_minutes': 0,
        }

    try:
        path_codes = nx.shortest_path(G, from_code, to_code, weight='weight')
    except nx.NetworkXNoPath:
        return {'ok': False, 'error': 'No path found. The map may not be fully connected yet.'}
    except nx.NodeNotFound as e:
        return {'ok': False, 'error': str(e)}

    steps = []
    floors_visited = []

    for i, code in enumerate(path_codes):
        loc = G.nodes[code]['obj']
        floor_num = loc.floor.number

        if not floors_visited or floors_visited[-1] != floor_num:
            floors_visited.append(floor_num)

        walk_type = 'walk'
        is_floor_change = False
        if i > 0:
            edge_data = G.edges[path_codes[i-1], code]
            walk_type = edge_data.get('walk_type', 'walk')
            prev_loc = G.nodes[path_codes[i-1]]['obj']
            is_floor_change = prev_loc.floor.number != floor_num

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
            instruction = "Continue through the corridor."
        else:
            instruction = f"Pass {loc.name}."

        steps.append({
            'code': loc.code, 'name': loc.name,
            'floor_number': floor_num, 'floor_label': loc.floor.label,
            'x_pct': loc.x_pct, 'y_pct': loc.y_pct,
            'loc_type': loc.loc_type, 'walk_type': walk_type,
            'instruction': instruction, 'is_floor_change': is_floor_change,
        })

    floor_changes = sum(1 for s in steps if s['is_floor_change'])
    est_minutes = max(1, round(len(steps) * 0.5 + floor_changes * 0.5))

    return {
        'ok': True, 'error': None,
        'from': G.nodes[from_code]['obj'],
        'to': G.nodes[to_code]['obj'],
        'steps': steps,
        'floors_visited': floors_visited,
        'total_steps': len(steps),
        'est_minutes': est_minutes,
    }


# ── JSON helpers ──────────────────────────────────────────────────────────────

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
            'area_polygon': loc.area_polygon or [],
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
