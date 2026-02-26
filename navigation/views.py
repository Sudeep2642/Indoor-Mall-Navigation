import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.db.models import Count

from .models import Mall, Floor, Location, Edge, ScanLog, NavSearch
from .engine import find_route, get_all_locations_json, get_all_edges_json
from .qr_generator import generate_for_location


# ──────────────────────────────────────────────────────────────
# PUBLIC — Visitor-facing navigation
# ──────────────────────────────────────────────────────────────

def home(request):
    malls = Mall.objects.filter(is_active=True)
    return render(request, 'navigation/home.html', {'malls': malls})


def navigate(request, mall_slug, from_code=None):
    """
    Main visitor navigation page.
    URL:  /navigate/<mall_slug>/              → browse map, pick start + destination
    URL:  /navigate/<mall_slug>/<from_code>/  → QR scan — "you are here" is set
    """
    mall   = get_object_or_404(Mall, slug=mall_slug, is_active=True)
    floors = Floor.objects.filter(mall=mall).order_by('number')

    # Resolve current location from QR scan
    current_loc = None
    if from_code:
        try:
            current_loc = Location.objects.select_related('floor').get(
                mall=mall, code=from_code.upper(), is_active=True
            )
            # Log QR scan
            ScanLog.objects.create(
                location=current_loc,
                ip=_get_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
            )
        except Location.DoesNotExist:
            messages.error(request, f"QR code location '{from_code}' not found in {mall.name}.")

    locations_data = get_all_locations_json(mall)
    edges_data     = get_all_edges_json(mall)

    context = {
        'mall': mall,
        'floors': floors,
        'current_loc': current_loc,
        'locations_json': json.dumps(locations_data),
        'edges_json':     json.dumps(edges_data),
        'floors_json':    json.dumps([
            {
                'number': f.number, 'label': f.label,
                'has_map': bool(f.map_image),
                'map_img_url': f.map_image.url if f.map_image else None,
            }
            for f in floors
        ]),
    }
    return render(request, 'navigation/navigate.html', context)


def route_api(request, mall_slug):
    """
    JSON API:  GET /api/route/<mall_slug>/?from=CODE&to=CODE
    Returns full route data consumed by the frontend.
    """
    mall     = get_object_or_404(Mall, slug=mall_slug, is_active=True)
    from_code = request.GET.get('from', '').upper()
    to_code   = request.GET.get('to', '').upper()

    if not from_code or not to_code:
        return JsonResponse({'ok': False, 'error': 'Both from= and to= are required.'})

    result = find_route(mall, from_code, to_code)

    # Log search
    if result['ok']:
        from_obj = result['from']
        to_obj   = result['to']
        NavSearch.objects.create(
            mall=mall,
            from_loc=from_obj,
            to_loc=to_obj,
            found=True,
            steps=result['total_steps'],
        )
    else:
        NavSearch.objects.create(mall=mall, found=False)

    # Serialise (Location objects aren't JSON-serialisable)
    if result['ok']:
        payload = {
            'ok': True,
            'from_name': result['from'].name,
            'from_floor': result['from'].floor.label,
            'to_name': result['to'].name,
            'to_floor': result['to'].floor.label,
            'total_steps': result['total_steps'],
            'est_minutes': result['est_minutes'],
            'floors_visited': result['floors_visited'],
            'steps': result['steps'],   # already plain dicts
        }
    else:
        payload = {'ok': False, 'error': result['error']}

    return JsonResponse(payload)


def floor_map_view(request, floor_id):
    """Serve floor map image (used as canvas background)."""
    floor = get_object_or_404(Floor, pk=floor_id)
    if floor.map_image:
        return HttpResponse(floor.map_image.read(), content_type='image/png')
    return HttpResponse(status=404)


# ──────────────────────────────────────────────────────────────
# ADMIN dashboard
# ──────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    malls = Mall.objects.annotate(
        loc_count=Count('locations', distinct=True),
        scan_count=Count('locations__scans', distinct=True),
    )
    if not request.user.is_staff:
        malls = malls.filter(created_by=request.user)
    return render(request, 'navigation/dashboard.html', {
        'malls': malls,
        'total_malls': malls.count(),
        'total_scans': ScanLog.objects.filter(location__mall__in=malls).count(),
    })


@login_required
def mall_admin(request, mall_slug):
    mall    = get_object_or_404(Mall, slug=mall_slug)
    floors  = Floor.objects.filter(mall=mall).annotate(loc_count=Count('locations'))
    locations = Location.objects.filter(mall=mall).select_related('floor').order_by('floor__number', 'name')
    edges   = Edge.objects.filter(mall=mall).select_related('from_loc__floor', 'to_loc__floor')
    top_dest = (NavSearch.objects
                .filter(mall=mall, found=True, to_loc__isnull=False)
                .values('to_loc__name')
                .annotate(n=Count('id'))
                .order_by('-n')[:8])
    recent_scans = ScanLog.objects.filter(location__mall=mall).select_related('location')[:10]

    from django.conf import settings as django_settings
    server_has_key = bool(getattr(django_settings, 'ANTHROPIC_API_KEY', ''))

    return render(request, 'navigation/mall_admin.html', {
        'mall': mall,
        'floors': floors,
        'locations': locations,
        'edges': edges,
        'top_dest': top_dest,
        'recent_scans': recent_scans,
        'total_scans': ScanLog.objects.filter(location__mall=mall).count(),
        'total_searches': NavSearch.objects.filter(mall=mall).count(),
        'locations_json': json.dumps(get_all_locations_json(mall)),
        'edges_json':     json.dumps(get_all_edges_json(mall)),
        'floors_json':    json.dumps([
            {'number': f.number, 'label': f.label} for f in floors
        ]),
        'server_has_key': server_has_key,
    })


@login_required
def add_mall(request):
    if request.method == 'POST':
        try:
            mall = Mall.objects.create(
                name=request.POST['name'],
                slug=request.POST['slug'].lower().replace(' ', '-'),
                city=request.POST['city'],
                address=request.POST.get('address', ''),
                total_floors=int(request.POST.get('total_floors', 1)),
                created_by=request.user,
            )
            if request.FILES.get('logo'):
                mall.logo = request.FILES['logo']
                mall.save()
            # Auto-create floors
            for i in range(int(request.POST.get('total_floors', 1))):
                label = 'Ground Floor' if i == 0 else f'Floor {i}'
                Floor.objects.create(mall=mall, number=i, label=label)
            messages.success(request, f"'{mall.name}' created! Now add locations and connections.")
            return redirect('mall_admin', mall_slug=mall.slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'navigation/add_mall.html')


@login_required
def add_location(request, mall_slug):
    mall   = get_object_or_404(Mall, slug=mall_slug)
    floors = Floor.objects.filter(mall=mall)
    if request.method == 'POST':
        try:
            floor = get_object_or_404(Floor, pk=request.POST['floor_id'])
            loc = Location.objects.create(
                mall=mall,
                floor=floor,
                code=request.POST['code'].upper().replace(' ', '_'),
                name=request.POST['name'],
                loc_type=request.POST['loc_type'],
                description=request.POST.get('description', ''),
                x_pct=float(request.POST.get('x_pct', 50)),
                y_pct=float(request.POST.get('y_pct', 50)),
            )
            # Auto-generate QR
            try:
                base = request.build_absolute_uri('/').rstrip('/')
                generate_for_location(loc, base)
            except Exception:
                pass
            messages.success(request, f"Location '{loc.name}' added.")
            return redirect('mall_admin', mall_slug=mall.slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    # Build existing locations per floor for map reference
    existing = Location.objects.filter(mall=mall).select_related('floor')
    existing_by_floor = {}
    for loc in existing:
        fid = str(loc.floor_id)
        if fid not in existing_by_floor:
            existing_by_floor[fid] = []
        existing_by_floor[fid].append({
            'name': loc.name, 'type': loc.loc_type,
            'x_pct': loc.x_pct, 'y_pct': loc.y_pct,
        })
    return render(request, 'navigation/add_location.html', {
        'mall': mall, 'floors': floors,
        'type_choices': Location.TYPE_CHOICES,
        'existing_locs_json': json.dumps(existing_by_floor),
    })




@login_required
def ai_floor_setup(request, floor_id):
    """Render the AI floor setup page for a specific floor."""
    floor = get_object_or_404(Floor, pk=floor_id)
    return render(request, 'navigation/ai_floor_setup.html', {
        'floor': floor,
        'mall': floor.mall,
    })

@login_required
def ai_analyse_floor(request, floor_id):
    """
    POST: Accepts a floor map image + Anthropic API key.
    Calls Claude Vision to detect shops, lifts, entrances, corridors.
    Returns JSON list of detected locations + suggested edges.
    """
    import base64, urllib.request, urllib.error
    floor = get_object_or_404(Floor, pk=floor_id)
    mall  = floor.mall

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})

    from django.conf import settings as django_settings
    api_key = request.POST.get('api_key', '').strip()
    # Fall back to server-configured key if user didn't provide one
    if not api_key:
        api_key = getattr(django_settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return JsonResponse({'ok': False, 'error': 'Anthropic API key required'})

    # Get image — either uploaded file or existing floor map
    img_b64 = None
    img_type = 'image/jpeg'
    if request.FILES.get('image'):
        f_obj = request.FILES['image']
        img_b64 = base64.b64encode(f_obj.read()).decode()
        img_type = f_obj.content_type or 'image/jpeg'
    elif floor.map_image:
        with open(floor.map_image.path, 'rb') as fh:
            img_b64 = base64.b64encode(fh.read()).decode()
        img_type = 'image/png'
    else:
        return JsonResponse({'ok': False, 'error': 'No image provided and no floor map uploaded yet.'})

    prompt = """You are analyzing a shopping mall floor plan image. 
Extract ALL visible locations and return ONLY a JSON object with this exact structure:

{
  "locations": [
    {
      "name": "Store/Location Name",
      "type": "shop|restaurant|restroom|lift|escalator|stairs|entrance|atm|parking|info|emergency|junction",
      "x_pct": 45.5,
      "y_pct": 32.0,
      "description": "brief note"
    }
  ],
  "edges": [
    {"from": 0, "to": 1, "walk_type": "walk|lift|escalator|stairs"}
  ],
  "notes": "any important observations"
}

Rules for x_pct and y_pct:
- x_pct: 0 = left edge, 100 = right edge of the image
- y_pct: 0 = top edge, 100 = bottom edge of the image
- Be precise — estimate the CENTER of each shop/location

Location type rules:
- Named retail brands → shop
- Food outlets, cafes, restaurants → restaurant  
- WC/toilet/washroom → restroom
- Lift/elevator symbols → lift
- Escalator arrows/symbols → escalator
- Stairs symbols → stairs
- Entry/exit gates → entrance
- Bank/ATM → atm
- Parking → parking
- Information/help desk → info
- Emergency exit → emergency
- Corridor intersections (no specific shop) → junction

For edges: connect adjacent locations that a person can walk between directly.
Index refers to position in the locations array (0-based).
Cross-floor connections (lift-to-lift, escalator-to-escalator) should NOT be included — those are added separately.

Return ONLY the JSON, no explanation text."""

    payload = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img_type,
                        "data": img_b64
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            return JsonResponse({'ok': False, 'error': err.get('error', {}).get('message', body)})
        except Exception:
            return JsonResponse({'ok': False, 'error': f'API error {e.code}: {body[:200]}'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})

    # Parse Claude response
    try:
        raw_text = result['content'][0]['text']
        # Strip markdown code fences if present
        raw_text = raw_text.strip()
        if raw_text.startswith('```'):
            raw_text = raw_text.split('\n', 1)[1]
            if raw_text.endswith('```'):
                raw_text = raw_text.rsplit('```', 1)[0]
        detected = json.loads(raw_text)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Could not parse AI response: {str(e)}', 'raw': result.get('content', [{}])[0].get('text', '')[:500]})

    return JsonResponse({'ok': True, 'floor_id': floor_id, 'floor_label': floor.label, 'data': detected})


@login_required
def ai_save_locations(request, floor_id):
    """
    POST JSON: Save AI-detected locations (and edges) to the database.
    Body: { locations: [...], edges: [...], api_key: '...' }
    """
    floor = get_object_or_404(Floor, pk=floor_id)
    mall  = floor.mall

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON body'})

    locs_data  = body.get('locations', [])
    edges_data = body.get('edges', [])

    created_locs = []
    idx_to_loc   = {}  # map submitted index → Location obj

    for i, ld in enumerate(locs_data):
        if not ld.get('name') or ld.get('skip'):
            idx_to_loc[i] = None
            continue
        # Generate unique code
        base_code = f"F{floor.number}_{ld['name'].upper().replace(' ', '_')[:12]}"
        code = base_code
        suffix = 1
        while Location.objects.filter(mall=mall, code=code).exists():
            code = f"{base_code}_{suffix}"
            suffix += 1

        loc = Location.objects.create(
            mall=mall,
            floor=floor,
            code=code,
            name=ld['name'],
            loc_type=ld.get('type', 'shop'),
            description=ld.get('description', ''),
            x_pct=float(ld.get('x_pct', 50)),
            y_pct=float(ld.get('y_pct', 50)),
        )
        idx_to_loc[i] = loc
        created_locs.append(loc)

        # Auto-generate QR
        try:
            base = request.build_absolute_uri('/').rstrip('/')
            generate_for_location(loc, base)
        except Exception:
            pass

    # Create edges
    edge_count = 0
    for ed in edges_data:
        fl = idx_to_loc.get(ed.get('from'))
        tl = idx_to_loc.get(ed.get('to'))
        if not fl or not tl or fl == tl:
            continue
        wt = ed.get('walk_type', 'walk')
        w  = 2.0 if wt in ('lift', 'escalator', 'stairs') else 1.0
        Edge.objects.get_or_create(from_loc=fl, to_loc=tl, defaults={'mall': mall, 'walk_type': wt, 'weight': w})
        Edge.objects.get_or_create(from_loc=tl, to_loc=fl, defaults={'mall': mall, 'walk_type': wt, 'weight': w})
        edge_count += 1

    return JsonResponse({
        'ok': True,
        'created': len(created_locs),
        'edges': edge_count,
        'redirect': f'/dashboard/{mall.slug}/'
    })


@login_required
def edit_location(request, loc_id):
    loc    = get_object_or_404(Location, pk=loc_id)
    floors = Floor.objects.filter(mall=loc.mall)
    if request.method == 'POST':
        try:
            loc.name      = request.POST['name']
            loc.loc_type  = request.POST['loc_type']
            loc.floor     = get_object_or_404(Floor, pk=request.POST['floor_id'])
            loc.x_pct     = float(request.POST.get('x_pct', loc.x_pct))
            loc.y_pct     = float(request.POST.get('y_pct', loc.y_pct))
            loc.description = request.POST.get('description', '')
            loc.save()
            messages.success(request, f"'{loc.name}' updated.")
            return redirect('mall_admin', mall_slug=loc.mall.slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'navigation/edit_location.html', {
        'loc': loc, 'mall': loc.mall, 'floors': floors,
        'type_choices': Location.TYPE_CHOICES,
    })


@login_required
def delete_location(request, loc_id):
    loc = get_object_or_404(Location, pk=loc_id)
    slug = loc.mall.slug
    if request.method == 'POST':
        loc.delete()
        messages.success(request, "Location deleted.")
    return redirect('mall_admin', mall_slug=slug)


@login_required
def add_edge(request, mall_slug):
    mall = get_object_or_404(Mall, slug=mall_slug)
    locations = Location.objects.filter(mall=mall, is_active=True).select_related('floor')
    if request.method == 'POST':
        try:
            fl = get_object_or_404(Location, pk=request.POST['from_loc'])
            tl = get_object_or_404(Location, pk=request.POST['to_loc'])
            if fl == tl:
                messages.error(request, "From and To cannot be the same location.")
            else:
                Edge.objects.get_or_create(
                    from_loc=fl, to_loc=tl,
                    defaults={
                        'mall': mall,
                        'walk_type': request.POST.get('walk_type', 'walk'),
                        'weight': float(request.POST.get('weight', 1.0)),
                    }
                )
                # Bidirectional: also create reverse
                Edge.objects.get_or_create(
                    from_loc=tl, to_loc=fl,
                    defaults={
                        'mall': mall,
                        'walk_type': request.POST.get('walk_type', 'walk'),
                        'weight': float(request.POST.get('weight', 1.0)),
                    }
                )
                messages.success(request, f"Connection: {fl.code} ↔ {tl.code}")
                return redirect('mall_admin', mall_slug=mall.slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'navigation/add_edge.html', {
        'mall': mall, 'locations': locations,
        'walk_type_choices': Edge.WALK_TYPE,
    })


@login_required
def delete_edge(request, edge_id):
    edge = get_object_or_404(Edge, pk=edge_id)
    slug = edge.mall.slug
    if request.method == 'POST':
        # Delete both directions
        Edge.objects.filter(from_loc=edge.from_loc, to_loc=edge.to_loc).delete()
        Edge.objects.filter(from_loc=edge.to_loc, to_loc=edge.from_loc).delete()
        messages.success(request, "Connection deleted.")
    return redirect('mall_admin', mall_slug=slug)


@login_required
def upload_floor_map(request, floor_id):
    floor = get_object_or_404(Floor, pk=floor_id)
    if request.method == 'POST' and request.FILES.get('map_image'):
        floor.map_image = request.FILES['map_image']
        floor.save()
        messages.success(request, f"Map uploaded for {floor.label}.")
    return redirect('mall_admin', mall_slug=floor.mall.slug)


@login_required
def delete_floor_map(request, floor_id):
    """Delete ONLY the background map image — locations and edges are untouched."""
    floor = get_object_or_404(Floor, pk=floor_id)
    if request.method == 'POST':
        if floor.map_image:
            import os
            try:
                image_path = floor.map_image.path
                floor.map_image.delete(save=False)
                floor.map_image = None
                floor.save()
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception:
                floor.map_image = None
                floor.save()
            messages.success(request, f"Map image removed from {floor.label}. All locations and connections are intact.")
        else:
            messages.info(request, "No map image to delete.")
    return redirect('mall_admin', mall_slug=floor.mall.slug)


@login_required
def update_floor_label(request, floor_id):
    floor = get_object_or_404(Floor, pk=floor_id)
    if request.method == 'POST':
        floor.label = request.POST.get('label', floor.label)
        floor.save()
        messages.success(request, "Floor label updated.")
    return redirect('mall_admin', mall_slug=floor.mall.slug)


@login_required
def generate_qr_all(request, mall_slug):
    mall = get_object_or_404(Mall, slug=mall_slug)
    base = request.build_absolute_uri('/').rstrip('/')
    locs = Location.objects.filter(mall=mall, is_active=True)
    count = 0
    for loc in locs:
        try:
            generate_for_location(loc, base)
            count += 1
        except Exception:
            pass
    messages.success(request, f"Generated {count} QR codes.")
    return redirect('mall_admin', mall_slug=mall_slug)


@login_required
def download_qr(request, loc_id):
    loc = get_object_or_404(Location, pk=loc_id)
    if loc.qr_image:
        response = HttpResponse(loc.qr_image.read(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="QR_{loc.code}.png"'
        return response
    messages.error(request, "No QR generated yet.")
    return redirect('mall_admin', mall_slug=loc.mall.slug)


# ──────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, "Invalid username or password.")
    return render(request, 'navigation/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ──────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────

def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
