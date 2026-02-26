"""
python manage.py seed_demo

Creates:
  - superuser: admin / admin123
  - Orion Mall, Bangalore — 3 floors, 40+ locations, all connections
  - QR codes for every location
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from navigation.models import Mall, Floor, Location, Edge


class Command(BaseCommand):
    help = 'Seed a complete demo mall (Orion Mall, Bangalore)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding demo mall...'))

        # ── Superuser ──────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@mallnav.com', 'admin123')
            self.stdout.write('  Created admin user')
        admin_user = User.objects.get(username='admin')

        # ── Mall ───────────────────────────────────────────────
        mall, _ = Mall.objects.get_or_create(
            slug='orion-mall',
            defaults=dict(
                name='Orion Mall',
                city='Bangalore',
                address='Dr. Rajkumar Road, Rajajinagar, Bangalore 560055',
                total_floors=3,
                created_by=admin_user,
            )
        )

        # ── Floors ─────────────────────────────────────────────
        f0, _ = Floor.objects.get_or_create(mall=mall, number=0, defaults={'label': 'Ground Floor'})
        f1, _ = Floor.objects.get_or_create(mall=mall, number=1, defaults={'label': 'First Floor'})
        f2, _ = Floor.objects.get_or_create(mall=mall, number=2, defaults={'label': 'Second Floor'})

        floors = {0: f0, 1: f1, 2: f2}

        # ── Locations ──────────────────────────────────────────
        # (code, name, type, floor, x%, y%)
        raw = [
            # Ground Floor — Entrances & services
            ('GF_MAIN_ENT',   'Main Entrance',         'entrance',   0, 50, 95),
            ('GF_WEST_ENT',   'West Entrance',         'entrance',   0, 8,  70),
            ('GF_EAST_ENT',   'East Entrance',         'entrance',   0, 92, 70),
            ('GF_INFO',       'Information Desk',      'info',       0, 50, 78),
            ('GF_ATM',        'ATM',                   'atm',        0, 18, 82),
            ('GF_PARKING',    'Parking Entrance',      'parking',    0, 50, 98),
            ('GF_RESTROOM_M', 'Gents Restroom GF',     'restroom',   0, 10, 45),
            ('GF_RESTROOM_F', 'Ladies Restroom GF',    'restroom',   0, 90, 45),
            ('GF_LIFT_A',     'Lift A (Ground)',        'lift',       0, 32, 55),
            ('GF_LIFT_B',     'Lift B (Ground)',        'lift',       0, 68, 55),
            ('GF_ESC_UP',     'Escalator Up (GF)',     'escalator',  0, 50, 55),
            ('GF_JN_C',       'Central Junction GF',   'junction',   0, 50, 68),
            ('GF_JN_W',       'West Corridor GF',      'junction',   0, 22, 55),
            ('GF_JN_E',       'East Corridor GF',      'junction',   0, 78, 55),
            # Ground Floor — Shops
            ('GF_FOODWORLD',  'FoodWorld',             'shop',       0, 20, 30),
            ('GF_RELIANCE',   'Reliance Fresh',        'shop',       0, 80, 30),
            ('GF_MCDONALD',   "McDonald's",            'restaurant', 0, 30, 18),
            ('GF_STARBUCKS',  'Starbucks',             'restaurant', 0, 70, 18),
            ('GF_ZARA',       'Zara',                  'shop',       0, 50, 22),
            ('GF_EMERGENCY',  'Emergency Exit GF',     'emergency',  0, 5,  50),

            # First Floor
            ('F1_LIFT_A',     'Lift A (First)',         'lift',       1, 32, 55),
            ('F1_LIFT_B',     'Lift B (First)',         'lift',       1, 68, 55),
            ('F1_ESC_UP',     'Escalator Up (F1)',      'escalator',  1, 50, 55),
            ('F1_ESC_DOWN',   'Escalator Down (F1)',    'escalator',  1, 45, 58),
            ('F1_JN_C',       'Central Junction F1',   'junction',   1, 50, 65),
            ('F1_JN_W',       'West Corridor F1',      'junction',   1, 22, 55),
            ('F1_JN_E',       'East Corridor F1',      'junction',   1, 78, 55),
            ('F1_RESTROOM_M', 'Gents Restroom F1',     'restroom',   1, 10, 45),
            ('F1_RESTROOM_F', 'Ladies Restroom F1',    'restroom',   1, 90, 45),
            ('F1_HM',         'H&M',                   'shop',       1, 20, 28),
            ('F1_LEVIS',      "Levi's",                'shop',       1, 80, 28),
            ('F1_MNS',        'Marks & Spencer',       'shop',       1, 35, 22),
            ('F1_PANTALOONS', 'Pantaloons',            'shop',       1, 65, 22),
            ('F1_ADIDAS',     'Adidas',                'shop',       1, 22, 75),
            ('F1_NIKE',       'Nike',                  'shop',       1, 78, 75),
            ('F1_FC_ENT',     'Food Court Entrance',   'restaurant', 1, 50, 80),

            # Second Floor — Food & Entertainment
            ('F2_LIFT_A',     'Lift A (Second)',        'lift',       2, 32, 55),
            ('F2_LIFT_B',     'Lift B (Second)',        'lift',       2, 68, 55),
            ('F2_ESC_DOWN',   'Escalator Down (F2)',   'escalator',  2, 50, 55),
            ('F2_JN_C',       'Central Junction F2',   'junction',   2, 50, 65),
            ('F2_RESTROOM',   'Restroom F2',           'restroom',   2, 90, 45),
            ('F2_FOOD_COURT', 'Food Court',            'restaurant', 2, 50, 35),
            ('F2_BURGER',     'Burger King',           'restaurant', 2, 22, 22),
            ('F2_KFC',        'KFC',                   'restaurant', 2, 38, 18),
            ('F2_PIZZA',      'Pizza Hut',             'restaurant', 2, 50, 15),
            ('F2_SUBWAY',     'Subway',                'restaurant', 2, 62, 18),
            ('F2_DOMINOS',    "Domino's",              'restaurant', 2, 78, 22),
            ('F2_PVR',        'PVR Cinemas',           'shop',       2, 25, 80),
            ('F2_TIMEZONE',   'Time Zone Gaming',      'shop',       2, 75, 80),
            ('F2_EMERGENCY',  'Emergency Exit F2',     'emergency',  2, 5,  50),
        ]

        locs = {}
        for code, name, ltype, flr, x, y in raw:
            loc, _ = Location.objects.get_or_create(
                mall=mall, code=code,
                defaults=dict(floor=floors[flr], name=name, loc_type=ltype, x_pct=x, y_pct=y)
            )
            locs[code] = loc

        self.stdout.write(f'  {len(locs)} locations ready')

        # ── Edges (bidirectional — we insert both directions) ──
        def connect(a, b, wtype='walk', w=1.0):
            al, bl = locs.get(a), locs.get(b)
            if not al or not bl:
                return
            Edge.objects.get_or_create(from_loc=al, to_loc=bl,
                defaults={'mall': mall, 'walk_type': wtype, 'weight': w})
            Edge.objects.get_or_create(from_loc=bl, to_loc=al,
                defaults={'mall': mall, 'walk_type': wtype, 'weight': w})

        # Ground Floor connections
        connect('GF_MAIN_ENT',  'GF_INFO')
        connect('GF_INFO',      'GF_JN_C')
        connect('GF_JN_C',      'GF_ATM',       w=1.5)
        connect('GF_WEST_ENT',  'GF_JN_W',      w=1.5)
        connect('GF_EAST_ENT',  'GF_JN_E',      w=1.5)
        connect('GF_JN_W',      'GF_JN_C')
        connect('GF_JN_E',      'GF_JN_C')
        connect('GF_JN_C',      'GF_LIFT_A')
        connect('GF_JN_C',      'GF_LIFT_B')
        connect('GF_JN_C',      'GF_ESC_UP')
        connect('GF_JN_W',      'GF_RESTROOM_M',w=1.5)
        connect('GF_JN_E',      'GF_RESTROOM_F',w=1.5)
        connect('GF_JN_W',      'GF_FOODWORLD', w=1.5)
        connect('GF_JN_E',      'GF_RELIANCE',  w=1.5)
        connect('GF_JN_C',      'GF_ZARA',      w=2)
        connect('GF_JN_W',      'GF_MCDONALD',  w=2)
        connect('GF_JN_E',      'GF_STARBUCKS', w=2)
        connect('GF_MAIN_ENT',  'GF_PARKING',   w=0.5)
        connect('GF_JN_W',      'GF_EMERGENCY', w=2)

        # First Floor connections
        connect('F1_JN_C',      'F1_LIFT_A')
        connect('F1_JN_C',      'F1_LIFT_B')
        connect('F1_JN_C',      'F1_ESC_UP')
        connect('F1_JN_C',      'F1_ESC_DOWN')
        connect('F1_JN_W',      'F1_JN_C')
        connect('F1_JN_E',      'F1_JN_C')
        connect('F1_JN_W',      'F1_RESTROOM_M',w=1.5)
        connect('F1_JN_E',      'F1_RESTROOM_F',w=1.5)
        connect('F1_JN_W',      'F1_HM',        w=1.5)
        connect('F1_JN_E',      'F1_LEVIS',     w=1.5)
        connect('F1_JN_W',      'F1_MNS',       w=2)
        connect('F1_JN_E',      'F1_PANTALOONS',w=2)
        connect('F1_JN_W',      'F1_ADIDAS',    w=2)
        connect('F1_JN_E',      'F1_NIKE',      w=2)
        connect('F1_JN_C',      'F1_FC_ENT',    w=2)

        # Second Floor connections
        connect('F2_JN_C',      'F2_LIFT_A')
        connect('F2_JN_C',      'F2_LIFT_B')
        connect('F2_JN_C',      'F2_ESC_DOWN')
        connect('F2_JN_C',      'F2_RESTROOM',  w=1.5)
        connect('F2_JN_C',      'F2_FOOD_COURT',w=1.5)
        connect('F2_FOOD_COURT','F2_BURGER',    w=1.5)
        connect('F2_FOOD_COURT','F2_KFC',       w=1.5)
        connect('F2_FOOD_COURT','F2_PIZZA',     w=1.5)
        connect('F2_FOOD_COURT','F2_SUBWAY',    w=1.5)
        connect('F2_FOOD_COURT','F2_DOMINOS',   w=1.5)
        connect('F2_JN_C',      'F2_PVR',       w=2)
        connect('F2_JN_C',      'F2_TIMEZONE',  w=2)
        connect('F2_JN_C',      'F2_EMERGENCY', w=3)

        # Cross-floor via LIFTS
        connect('GF_LIFT_A',    'F1_LIFT_A',    'lift',      2)
        connect('GF_LIFT_B',    'F1_LIFT_B',    'lift',      2)
        connect('F1_LIFT_A',    'F2_LIFT_A',    'lift',      2)
        connect('F1_LIFT_B',    'F2_LIFT_B',    'lift',      2)

        # Cross-floor via ESCALATORS
        connect('GF_ESC_UP',    'F1_ESC_DOWN',  'escalator', 2)
        connect('F1_ESC_UP',    'F2_ESC_DOWN',  'escalator', 2)

        # Food court direct path
        connect('F1_FC_ENT',    'F2_JN_C',      'stairs',    2)

        edge_count = Edge.objects.filter(mall=mall).count()
        self.stdout.write(f'  {edge_count} edges ready')

        # ── QR codes ───────────────────────────────────────────
        try:
            from navigation.qr_generator import generate_for_location
            base = 'http://localhost:8000'
            count = 0
            for loc in Location.objects.filter(mall=mall):
                try:
                    generate_for_location(loc, base)
                    count += 1
                except Exception:
                    pass
            self.stdout.write(f'  {count} QR codes generated')
        except Exception as e:
            self.stdout.write(f'  QR generation skipped: {e}')

        self.stdout.write(self.style.SUCCESS("""
╔══════════════════════════════════════════════════════╗
║  ✅  DEMO MALL SEEDED SUCCESSFULLY                   ║
╠══════════════════════════════════════════════════════╣
║  Mall:     Orion Mall, Bangalore                     ║
║  Floors:   3  (Ground, First, Second)                ║
║  Admin:    admin / admin123                          ║
╠══════════════════════════════════════════════════════╣
║  URLs:                                               ║
║  Home:      http://localhost:8000/                   ║
║  Map:       http://localhost:8000/navigate/orion-mall/
║  Admin:     http://localhost:8000/login/             ║
║                                                      ║
║  Test QR scan (simulates scanning at Lift A GF):     ║
║  http://localhost:8000/navigate/orion-mall/GF_LIFT_A/║
╚══════════════════════════════════════════════════════╝
        """))
