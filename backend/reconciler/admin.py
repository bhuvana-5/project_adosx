from django.contrib import admin

from .models import ImportIssue, Location, SystemARecord, SystemBEntry


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("location_id", "org_id")


@admin.register(SystemARecord)
class SystemARecordAdmin(admin.ModelAdmin):
    list_display = (
        "record_id",
        "location",
        "raw_value",
        "normalized_value",
        "imported_row_number",
    )
    search_fields = ("record_id",)


@admin.register(SystemBEntry)
class SystemBEntryAdmin(admin.ModelAdmin):
    list_display = (
        "record_ref",
        "normalized_record_ref",
        "location",
        "raw_value",
        "normalized_value",
        "imported_row_number",
    )
    search_fields = ("record_ref", "normalized_record_ref")


@admin.register(ImportIssue)
class ImportIssueAdmin(admin.ModelAdmin):
    list_display = ("source", "row_number", "message")
    search_fields = ("source", "message")
