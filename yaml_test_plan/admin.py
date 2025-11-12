from django.contrib import admin
from .models import TestPlanYaml


@admin.register(TestPlanYaml)
class TestPlanYamlAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_name', 'validation_status', 'create_user', 'create_time')
    list_filter = ('validation_status', 'create_time')
    search_fields = ('file_name', 'plan_name')
    readonly_fields = ('create_time',)

