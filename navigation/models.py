from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Mall(models.Model):
    name         = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True)
    city         = models.CharField(max_length=100)
    address      = models.TextField(blank=True)
    logo         = models.ImageField(upload_to='logos/', blank=True, null=True)
    total_floors = models.IntegerField(default=1)
    is_active    = models.BooleanField(default=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Floor(models.Model):
    mall         = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='floors')
    number       = models.IntegerField()          # 0 = Ground, 1 = First, etc.
    label        = models.CharField(max_length=80) # "Ground Floor", "First Floor"
    map_image    = models.ImageField(upload_to='floor_maps/', blank=True, null=True)
    map_width_px = models.IntegerField(default=1000)
    map_height_px= models.IntegerField(default=700)
    show_map_to_visitors = models.BooleanField(default=True, help_text="When OFF, visitors see only nodes/connections — the floor plan image is hidden.")

    class Meta:
        unique_together = ('mall', 'number')
        ordering = ['number']

    def __str__(self):
        return f"{self.mall.name} — {self.label}"


class Location(models.Model):
    TYPE_CHOICES = [
        ('entrance',  'Entrance / Exit'),
        ('shop',      'Shop / Store'),
        ('restaurant','Restaurant / Food'),
        ('restroom',  'Restroom'),
        ('lift',      'Lift / Elevator'),
        ('escalator', 'Escalator'),
        ('stairs',    'Stairs'),
        ('atm',       'ATM'),
        ('parking',   'Parking'),
        ('info',      'Information Desk'),
        ('emergency', 'Emergency Exit'),
        ('junction',  'Corridor / Junction'),
    ]

    mall          = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='locations')
    floor         = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='locations')
    code          = models.CharField(max_length=60)   # e.g. GF_ZARA, F1_LIFT_A
    name          = models.CharField(max_length=200)
    loc_type      = models.CharField(max_length=20, choices=TYPE_CHOICES, default='shop')
    description   = models.TextField(blank=True)
    # Position on map as percentage 0-100
    x_pct         = models.FloatField(default=50)
    y_pct         = models.FloatField(default=50)
    qr_image      = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    AREA_SIZE_CHOICES = [
        ('xs',  'XS — Tiny (kiosk / ATM)'),
        ('sm',  'Small (≤ 200 sq ft)'),
        ('md',  'Medium (200–600 sq ft)'),
        ('lg',  'Large (600–1500 sq ft)'),
        ('xl',  'XL — Anchor (1500 sq ft +)'),
    ]
    area_size     = models.CharField(max_length=4, choices=AREA_SIZE_CHOICES, default='md')
    # Polygon boundary: list of [x_pct, y_pct] points drawn by admin on the map
    # e.g. [[10.5, 20.0], [30.2, 20.0], [30.2, 45.1], [10.5, 45.1]]
    area_polygon  = models.JSONField(default=list, blank=True)
    is_active     = models.BooleanField(default=True)

    class Meta:
        unique_together = ('mall', 'code')
        ordering = ['floor__number', 'name']

    def __str__(self):
        return f"{self.name} [{self.code}] — {self.floor.label}"

    def qr_url_data(self, base_url):
        """Data encoded in QR code — full URL visitor opens when scanning."""
        return f"{base_url}/navigate/{self.mall.slug}/{self.code}/"


class Edge(models.Model):
    """Walkable connection between two locations (undirected graph edge)."""
    WALK_TYPE = [
        ('walk',      'Walk'),
        ('lift',      'Lift'),
        ('escalator', 'Escalator'),
        ('stairs',    'Stairs'),
    ]
    mall        = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='edges')
    from_loc    = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='edges_from')
    to_loc      = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='edges_to')
    walk_type   = models.CharField(max_length=20, choices=WALK_TYPE, default='walk')
    weight      = models.FloatField(default=1.0)

    class Meta:
        unique_together = ('from_loc', 'to_loc')

    def __str__(self):
        return f"{self.from_loc.code} ↔ {self.to_loc.code} ({self.walk_type})"


class ScanLog(models.Model):
    """Analytics: every QR scan."""
    location   = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='scans')
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip         = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return f"Scan: {self.location.code} @ {self.scanned_at}"


class NavSearch(models.Model):
    """Analytics: every navigation search."""
    mall       = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='searches')
    from_loc   = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='nav_from')
    to_loc     = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='nav_to')
    searched_at= models.DateTimeField(auto_now_add=True)
    found      = models.BooleanField(default=True)
    steps      = models.IntegerField(default=0)

    class Meta:
        ordering = ['-searched_at']
