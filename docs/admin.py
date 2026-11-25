from django.contrib import admin
from .models import *
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
 list_display=("title","category","status","version","uploaded_by","uploaded_at","view_count","download_count")
 list_filter=("status","category","uploaded_at")
 search_fields=("title","description","tags__name","uploaded_by__username")
 filter_horizontal=("tags",)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): list_display=("name","parent","created_at");search_fields=("name",)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin): search_fields=("name",)
for model in (DocumentVersion,DocumentPermission,DocumentAuditLog,DocumentShare,DocumentFavorite,DocumentComment):
 admin.site.register(model)
