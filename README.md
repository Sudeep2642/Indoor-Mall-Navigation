# 🏬 MallNav — Indoor Navigation Platform

Complete Django-based indoor navigation system for shopping malls.
Visitors scan a QR code → see they are here → search destination → get floor-by-floor route.

---

## ⚡ Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database tables
python manage.py makemigrations
python manage.py migrate

# 3. Seed demo mall (Orion Mall, Bangalore — 3 floors, 50+ locations)
python manage.py seed_demo

# 4. Start server
python manage.py runserver
```

---

## 🔗 Key URLs

| URL | What it is |
|-----|-----------|
| `http://localhost:8000/` | Homepage — all malls |
| `http://localhost:8000/navigate/orion-mall/` | Browse map, pick start & destination |
| `http://localhost:8000/navigate/orion-mall/GF_LIFT_A/` | Simulate QR scan at Lift A GF |
| `http://localhost:8000/navigate/orion-mall/MAIN_ENTRANCE/` | Simulate QR scan at Main Entrance |
| `http://localhost:8000/login/` | Admin login (admin / admin123) |
| `http://localhost:8000/dashboard/` | Manage malls |
| `http://localhost:8000/admin/` | Django admin |

---

## 📱 How QR Navigation Works

1. **Admin prints QR codes** — each location gets a unique QR  
   QR URL = `https://yourdomain.com/navigate/<mall-slug>/<location-code>/`

2. **QR codes are placed** at physical locations in the mall  
   (Entrances, lifts, escalators, junctions, info desks)

3. **Visitor scans QR** with phone camera — opens browser (no app needed)

4. **"You are here" appears** — green banner shows current location + floor

5. **Visitor picks destination** — search or use quick buttons (Restroom, Food, Exit, ATM...)

6. **Route appears instantly**:
   - Animated dotted path on interactive floor map
   - Step-by-step directions in sidebar
   - Floor-by-floor instructions (which lift/escalator to take)
   - Time estimate

7. **Visitor follows steps** — tap each step to see that floor on the map

---

## 🏗 Project Structure

```
mallnav/
├── manage.py
├── requirements.txt
├── Procfile                    ← Railway/Render deployment
├── mallnav/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── navigation/
│   ├── models.py               ← Mall, Floor, Location, Edge, ScanLog
│   ├── engine.py               ← Dijkstra pathfinding (networkx)
│   ├── views.py                ← All views + REST API
│   ├── urls.py
│   ├── qr_generator.py         ← QR code generation
│   ├── admin.py
│   └── management/commands/
│       └── seed_demo.py        ← Demo data seeder
└── templates/navigation/
    ├── navigate.html           ← Main visitor navigation page
    ├── home.html
    ├── dashboard.html
    ├── mall_admin.html
    ├── add_mall.html
    ├── add_location.html
    ├── edit_location.html
    ├── add_edge.html
    └── login.html
```

---

## 🗺 Admin Workflow (Adding a New Mall)

### Step 1 — Create mall
Dashboard → Add Mall → Fill name, city, floors

### Step 2 — Add locations
For each location (shop, lift, entrance, junction, restroom...):
- Give it a unique Code (e.g. GF_ZARA, F1_LIFT_A)
- Set X/Y percentage position on floor map
- Use Junction type for corridor intersections

### Step 3 — Add connections
Connect every location to its neighbors:
- Same-floor shops → junction → corridor
- Cross-floor: lift on floor 0 → lift on floor 1 (type=lift)

### Step 4 — Generate QR codes
Dashboard → your mall → Generate QR → Download each QR → Print & place in mall

### Step 5 — Upload floor maps (optional)
Upload images of floor plans → shown as background on navigation map

---

## 🔌 API

```
GET /api/route/<mall-slug>/?from=CODE&to=CODE
```

Returns:
```json
{
  "ok": true,
  "from_name": "Main Entrance",
  "to_name": "KFC",
  "total_steps": 8,
  "est_minutes": 4,
  "floors_visited": [0, 2],
  "steps": [
    {"code": "GF_MAIN_ENT", "name": "Main Entrance", "floor_number": 0,
     "floor_label": "Ground Floor", "instruction": "Start at Main Entrance on Ground Floor.",
     "walk_type": "walk", "is_floor_change": false, "x_pct": 50, "y_pct": 95},
    ...
  ]
}
```

---

## 🚀 Deployment

### Railway (Recommended)
1. Push to GitHub
2. Railway → New → Deploy from GitHub
3. Add PostgreSQL database
4. Set env vars: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=.railway.app`, `DATABASE_URL`
5. Run: `python manage.py migrate && python manage.py seed_demo`

### Render
Same as Railway — uses Procfile automatically.

### PythonAnywhere
Clone repo, pip install, set WSGI config, collectstatic.

---

## 🔁 Multi-Mall

Same engine powers all malls. Each mall has:
- Independent location graph
- Own floor maps
- Own QR codes (encode mall-specific URLs)
- Own analytics

To add another mall: repeat Steps 1–4 above. No code changes needed.
