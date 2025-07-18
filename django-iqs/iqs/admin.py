from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from .models import GeoLayer, Attribute, AttributeType, AttributeValue, GeometryType, OgcRelationType, AttributePriorityLevel


class AttributeInline(admin.TabularInline):
    model = Attribute
    show_change_link = True
    extra = 3

class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    show_change_link = True
    extra = 3


class AttributePriorityLevelAdmin(admin.ModelAdmin):
    fields = [f.name for f in AttributePriorityLevel._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields


class AttributeAdmin(admin.ModelAdmin):
    fields = [f.name for f in Attribute._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields
    inlines = [AttributeValueInline]


class GeoLayerAdmin(admin.ModelAdmin):
    fields = [f.name for f in GeoLayer._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields
    inlines = [AttributeInline]

class AttributeTypeAdmin(admin.ModelAdmin):
    fields = [f.name for f in AttributeType._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields


class AttributeValueAdmin(admin.ModelAdmin):
    fields = [f.name for f in AttributeValue._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields
    show_change_link = True

class GeometryTypeAdmin(admin.ModelAdmin):
    fields = [f.name for f in GeometryType._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields


class OgcRelationTypeAdmin(admin.ModelAdmin):
    fields = [f.name for f in OgcRelationType._meta.fields if f.name != 'id']
    list_filter = list_display = search_fields = fields


# Register the admin models classes
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(GeoLayer, GeoLayerAdmin)
admin.site.register(AttributeType, AttributeTypeAdmin)
admin.site.register(AttributeValue, AttributeValueAdmin)
admin.site.register(GeometryType, GeometryTypeAdmin)
admin.site.register(OgcRelationType, OgcRelationTypeAdmin)
admin.site.register(AttributePriorityLevel, AttributePriorityLevelAdmin)

