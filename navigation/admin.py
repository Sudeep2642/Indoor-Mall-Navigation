from django.contrib import admin
from .models import Mall, Floor, Location, Edge, ScanLog, NavSearch

@admin.register(Mall)
class MallAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'total_floors', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('mall', 'number', 'label')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'loc_type', 'mall', 'floor', 'is_active')
    list_filter = ('mall', 'loc_type', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ('from_loc', 'to_loc', 'walk_type', 'weight')
    list_filter = ('mall', 'walk_type')

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ('location', 'scanned_at', 'ip')
    readonly_fields = ('scanned_at',)

@admin.register(NavSearch)
class NavSearchAdmin(admin.ModelAdmin):
    list_display = ('mall', 'from_loc', 'to_loc', 'found', 'searched_at')
