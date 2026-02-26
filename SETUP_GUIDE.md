# 🏬 MallNav — Complete Admin Setup Guide

---

## PART 1 — FIRST TIME SETUP

### Run the app
```bash
cd mallnav
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo      # creates Orion Mall demo + admin user
python manage.py runserver 0.0.0.0:8000
```

Login at: `http://localhost:8000/login/`  
Username: `admin` | Password: `admin123`

---

## PART 2 — ADDING A NEW MALL (Step by Step)

### Step 1 — Create the Mall
1. Go to `http://localhost:8000/dashboard/`
2. Click **+ Add Mall**
3. Fill in:
   - **Mall Name** → e.g. "Phoenix Marketcity"
   - **URL Slug** → auto-filled as `phoenix-marketcity` (lowercase, hyphens)
   - **City** → Bangalore
   - **Total Floors** → 4
   - **Logo** → optional image
4. Click **Create Mall**
5. Floors are created automatically (Ground Floor, Floor 1, Floor 2, Floor 3)

---

### Step 2 — Set Up the Map

You have 4 options depending on what floor map material you have:

---

#### OPTION A — You have NO floor map at all (most common)

**This is perfectly fine.** MallNav works without any floor images.
The map shows dots (locations) connected by lines (corridors) on a dark grid background.

**What to do:**
- Skip the floor map upload entirely
- Go straight to adding locations (Step 3)
- The navigation still works 100% — visitors see dots and route lines

**The map will look like this:**
```
  ·  [Main Entrance]
  |
  ·  [Info Desk]
  |
  ●——●——[Lift A]——●——●
  |              |
[Zara]       [H&M]
```
Clean, functional, no images needed.

---

#### OPTION B — You have a floor map image (clear photo or PDF export)

**Best case scenario.**

1. Dashboard → your mall → **Floors & Maps** tab
2. For each floor, click **Choose File** under "Upload Floor Map"
3. Upload a JPG or PNG of the floor plan
4. Click **Upload**

The image appears as a **faded background** (22% opacity) behind the dots.
This helps visitors correlate the dots with real physical space.

**Tips for best results:**
- Crop the image to just the mall outline (remove borders/legends)
- Landscape orientation works best
- File size under 2MB per floor

---

#### OPTION C — You have a blurred or hand-drawn map

**Still usable!** Even a rough sketch works.

1. Take a photo of the hand-drawn sketch with your phone
2. Open in any image editor (even MS Paint or Google Photos)
3. Adjust brightness/contrast so lines are clear
4. Upload as described in Option B

**For blurred maps:**
- Use Google Photos' "Enhance" feature to sharpen
- Or use remove.bg or Canva to clean it up
- Even a blurry map is better than nothing as a reference

**Alternative — Draw your own in 10 minutes:**
1. Go to **draw.io** (free, no signup): `https://app.diagrams.net`
2. Draw rectangles for shops, lines for corridors
3. Export as PNG
4. Upload to MallNav

---

#### OPTION D — You want to place shop dots manually on the map

This is how all maps are built in MallNav — you place X/Y percentages for each location.

**How X% and Y% work:**
```
(0,0) ─────────────── (100,0)
  │                      │
  │    Your floor map    │
  │                      │
(0,100) ──────────── (100,100)
```

- X=0 → left edge, X=100 → right edge
- Y=0 → top edge, Y=100 → bottom edge
- X=50, Y=50 → exact center of the map

**Method 1 — Estimate by eye (quickest)**

Look at a floor plan and estimate:
- Main entrance at bottom center → X=50, Y=95
- Lift in upper-left quadrant → X=25, Y=30
- Shop in top-right corner → X=80, Y=15

**Method 2 — Use the Map Preview to fine-tune**

1. Add a location with your best X/Y guess
2. Go to Dashboard → your mall → **Map Preview** tab
3. See where the dot landed
4. Go back and edit the location (click Edit button in Locations table)
5. Adjust X/Y and save
6. Refresh Map Preview to check

**Method 3 — Get exact percentages from an image**

1. Open your floor map image in MS Paint (Windows) or Preview (Mac)
2. Hover mouse over a shop's center
3. Note the pixel coordinates shown at the bottom
4. Divide by image width/height × 100 = percentage

Example: Image is 1000×700px. Shop is at pixel (350, 210).
- X% = 350/1000 × 100 = **35**
- Y% = 210/700 × 100 = **30**

---

### Step 3 — Add Locations

Every point on the map is a "Location". You need to add:
- All shops and restaurants
- All lifts (one per floor!)
- All escalators (one per floor!)
- All restrooms
- Entrances/exits
- ATMs, info desk, parking
- **Junction nodes** for corridor intersections (invisible waypoints)

**Go to:** Dashboard → your mall → **+ Location**

For each location, fill:
| Field | What to put |
|-------|------------|
| Name | "Zara", "Lift A", "Gents Restroom" |
| Code | Auto-generated: F1_ZARA, F1_LIFT_A |
| Type | Choose from dropdown |
| Floor | Ground Floor / First Floor etc. |
| X % | Horizontal position (0=left, 100=right) |
| Y % | Vertical position (0=top, 100=bottom) |

**Junction nodes** — these are invisible waypoints for corridors:
- Name them "Junction North", "Corridor Center" etc.
- Type = Junction
- Place them at corridor crossings
- You must connect shops → junction → junction → destination

---

### Step 4 — Add Connections

Connections define which locations are physically walkable to each other.

**Go to:** Dashboard → your mall → **+ Connection**

**Rules:**
- All connections are bidirectional (A→B automatically creates B→A)
- Same floor: use type **Walk**, weight 1–3
- Cross floor (lift): use type **Lift**, weight 2
- Cross floor (escalator): use type **Escalator**, weight 2
- Long corridors: weight 3–5
- Short walks: weight 1

**Pattern for a simple floor:**
```
Main Entrance → Central Junction
Central Junction → Lift A
Central Junction → Escalator Up
Central Junction → Zara
Central Junction → H&M
Central Junction → Restroom
```

**Cross-floor connections (lifts/escalators):**
```
GF_LIFT_A → F1_LIFT_A  (type=Lift)
F1_LIFT_A → F2_LIFT_A  (type=Lift)
GF_ESC_UP → F1_ESC_DOWN  (type=Escalator)
```

---

### Step 5 — Generate QR Codes

1. Dashboard → your mall → click **📱 Generate QR** button
2. All locations get QR codes instantly
3. In the Locations table, click **⬇ QR** next to each location
4. Download the PNG
5. Print and laminate
6. Place physically in the mall

**What each QR contains:**
```
https://yoursite.com/navigate/phoenix-marketcity/GF_LIFT_A/
```
When a visitor scans → page opens → "You are here: Lift A, Ground Floor" → they pick destination → route appears.

---

## PART 3 — TESTING YOUR MALL

### Test navigation in browser
Open: `http://localhost:8000/navigate/phoenix-marketcity/`
- Try searching for a shop
- Try Quick Find buttons
- Check that routes appear with steps

### Simulate a QR scan
Open: `http://localhost:8000/navigate/phoenix-marketcity/GF_LIFT_A/`
This simulates a visitor scanning the QR at Lift A, Ground Floor.
You should see "📍 You are here: Lift A — Ground Floor"

### Test from your phone
```bash
# Find your laptop's IP
ipconfig   # Windows
ifconfig   # Mac/Linux

# Run server accessible from phone
python manage.py runserver 0.0.0.0:8000

# On your phone, open:
http://192.168.x.x:8000/navigate/phoenix-marketcity/GF_LIFT_A/
```

### Common issues and fixes

**"No route found" error:**
- Check that both locations exist and are connected via edges
- Use Map Preview → check that locations appear as dots
- Open Django Admin (`/admin/`) → check the Edge table

**Location dot in wrong place:**
- Edit the location, adjust X% and Y%
- Check Map Preview to see new position

**QR code opens wrong URL:**
- Go to Dashboard → Generate QR again after deploying to production
- QR codes encode your server's URL — regenerate after changing domain

---

## PART 4 — ADDING MORE MALLS ALONGSIDE ORION MALL

You can have unlimited malls. Here's how to add a second one while Orion Mall continues working.

### Example: Adding "Phoenix Marketcity, Whitefield"

1. **Dashboard → + Add Mall**
   - Name: Phoenix Marketcity
   - Slug: phoenix-whitefield  ← must be unique
   - City: Bangalore
   - Floors: 3

2. **Add locations for Phoenix** (same process as above)
   - Each mall has completely separate locations
   - Same location codes can exist in different malls (they're scoped per mall)

3. **Add connections for Phoenix**

4. **Generate QR codes for Phoenix**
   - These QR codes encode `/navigate/phoenix-whitefield/LOCATION_CODE/`
   - Completely separate from Orion Mall QRs

5. **Both malls are live simultaneously:**
   - `http://yoursite.com/navigate/orion-mall/` → Orion Mall map
   - `http://yoursite.com/navigate/phoenix-whitefield/` → Phoenix Mall map
   - Homepage shows both malls as cards

**Each mall is fully independent:**
- Own floor maps
- Own QR codes
- Own analytics (scan counts, popular destinations)
- Own admin management

---

## PART 5 — QUICK REFERENCE

### Location Types
| Type | Use for |
|------|---------|
| entrance | Mall doors, gates |
| shop | Retail stores |
| restaurant | Food outlets, food court stalls |
| restroom | Toilets |
| lift | Elevator (add on EVERY floor!) |
| escalator | Moving stairs (add on EVERY floor!) |
| stairs | Regular stairs |
| atm | ATM machines |
| parking | Parking entrance/exit |
| info | Information desk |
| emergency | Emergency exits |
| junction | **Corridor intersections (invisible)** |

### Minimum locations needed
For a basic working mall (1 floor):
- 1 entrance
- 1 junction (corridor center)
- Your shops (5–10 to start)
- 1 restroom
- 1 lift or escalator (if multi-floor)

### URL patterns
| URL | What it does |
|-----|-------------|
| `/navigate/<slug>/` | Browse map, pick start manually |
| `/navigate/<slug>/<CODE>/` | QR scan — "you are here" is set |
| `/api/route/<slug>/?from=X&to=Y` | JSON route API |
| `/dashboard/` | Admin dashboard |
| `/dashboard/<slug>/` | Manage a specific mall |
