from django.urls import path
from . import views

urlpatterns = [
    # ── Public / Visitor ──
    path('', views.home, name='home'),

    # QR scan lands here: /navigate/<mall>/<location_code>/
    path('navigate/<slug:mall_slug>/<str:from_code>/', views.navigate, name='navigate_from'),

    # Browse map without QR
    path('navigate/<slug:mall_slug>/', views.navigate, name='navigate'),

    # Route API
    path('api/route/<slug:mall_slug>/', views.route_api, name='route_api'),

    # ── Admin ──
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/<slug:mall_slug>/', views.mall_admin, name='mall_admin'),
    path('dashboard/mall/add/', views.add_mall, name='add_mall'),

    path('dashboard/<slug:mall_slug>/location/add/', views.add_location, name='add_location'),
    path('dashboard/location/<int:loc_id>/edit/', views.edit_location, name='edit_location'),
    path('dashboard/location/<int:loc_id>/delete/', views.delete_location, name='delete_location'),
    path('dashboard/location/<int:loc_id>/qr/', views.download_qr, name='download_qr'),

    path('dashboard/<slug:mall_slug>/edge/add/', views.add_edge, name='add_edge'),
    path('dashboard/edge/<int:edge_id>/delete/', views.delete_edge, name='delete_edge'),

    path('dashboard/floor/<int:floor_id>/upload/', views.upload_floor_map, name='upload_floor_map'),
    path('dashboard/floor/<int:floor_id>/delete-map/', views.delete_floor_map, name='delete_floor_map'),
    path('dashboard/floor/<int:floor_id>/toggle-map-visibility/', views.toggle_floor_map_visibility, name='toggle_floor_map_visibility'),
    path('dashboard/floor/<int:floor_id>/ai-setup/', views.ai_floor_setup, name='ai_floor_setup'),
    path('dashboard/floor/<int:floor_id>/ai-analyse/', views.ai_analyse_floor, name='ai_analyse_floor'),
    path('dashboard/floor/<int:floor_id>/ai-save/', views.ai_save_locations, name='ai_save_locations'),
    path('dashboard/floor/<int:floor_id>/label/', views.update_floor_label, name='update_floor_label'),
    path('dashboard/<slug:mall_slug>/qr/generate/', views.generate_qr_all, name='generate_qr_all'),

    # ── Auth ──
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
