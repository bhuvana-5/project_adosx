from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=100, unique=True)
    org_id = models.CharField(max_length=100)

    class Meta:
        ordering = ["location_id"]

    def __str__(self):
        return f"{self.location_id} ({self.org_id})"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="system_a_records",
    )
    raw_value = models.CharField(max_length=255, blank=True)
    normalized_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    imported_row_number = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["record_id"]

    def __str__(self):
        return self.record_id


class SystemBEntry(models.Model):
    record_ref = models.CharField(max_length=255, blank=True)
    normalized_record_ref = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="system_b_entries",
    )
    raw_value = models.CharField(max_length=255, blank=True)
    normalized_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    imported_row_number = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.record_ref


class ImportIssue(models.Model):
    source = models.CharField(max_length=100)
    row_number = models.PositiveIntegerField()
    message = models.TextField()
    raw_data = models.JSONField(default=dict)

    class Meta:
        ordering = ["source", "row_number"]

    def __str__(self):
        return f"{self.source} row {self.row_number}: {self.message}"
