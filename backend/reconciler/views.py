from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Location, SystemARecord, SystemBEntry
from .services.comparator import reconcile_records


REASON_CHOICES = [
    "MISSING_IN_SYSTEM_B",
    "ORPHAN_IN_SYSTEM_B",
    "DUPLICATE_IN_SYSTEM_B",
    "VALUE_MISMATCH",
]


def _location_org_map():
    return {
        location.location_id: location.org_id
        for location in Location.objects.all()
    }


def _serialize_a_record(record):
    return {
        "record_id": record.record_id,
        "location_id": (
            record.location.location_id
            if record.location
            else None
        ),
        "value": record.raw_value,
        "normalized_value": (
            str(record.normalized_value)
            if record.normalized_value is not None
            else None
        ),
    }


def _serialize_b_entry(entry):
    return {
        "record_ref": entry.record_ref,
        "normalized_record_ref": (
            entry.normalized_record_ref
        ),
        "location_id": (
            entry.location.location_id
            if entry.location
            else None
        ),
        "value": entry.raw_value,
        "normalized_value": (
            str(entry.normalized_value)
            if entry.normalized_value is not None
            else None
        ),
    }


@require_GET
def organizations(request):
    """
    Return available organizations.

    This endpoint is intentionally simple because the assessment
    does not require authentication.
    """

    org_ids = (
        Location.objects
        .values_list("org_id", flat=True)
        .distinct()
        .order_by("org_id")
    )

    return JsonResponse(
        {
            "results": list(org_ids),
        }
    )


@require_GET
def discrepancies(request):
    """
    Return discrepancies strictly scoped to the requested tenant.

    org_id is mandatory. No global/unscoped discrepancy endpoint
    is exposed.
    """

    org_id = request.GET.get("org_id", "").strip()
    reason = request.GET.get("reason", "").strip()

    if not org_id:
        return JsonResponse(
            {
                "error": "org_id query parameter is required"
            },
            status=400,
        )

    if reason and reason != "ALL":
        if reason not in REASON_CHOICES:
            return JsonResponse(
                {
                    "error": "Invalid discrepancy reason."
                },
                status=400,
            )

    location_ids = set(
        Location.objects
        .filter(org_id=org_id)
        .values_list("location_id", flat=True)
    )

    # ---------------------------------------------------------
    # Tenant filtering happens BEFORE reconciliation.
    # ---------------------------------------------------------
    records_a = [
        _serialize_a_record(record)
        for record in (
            SystemARecord.objects
            .select_related("location")
            .filter(location__org_id=org_id)
        )
    ]

    records_b = [
        _serialize_b_entry(entry)
        for entry in (
            SystemBEntry.objects
            .select_related("location")
            .filter(location__org_id=org_id)
        )
    ]

    location_map = _location_org_map()

    # Only pass tenant-owned locations into the comparison map.
    tenant_location_map = {
        location_id: location_map[location_id]
        for location_id in location_ids
        if location_id in location_map
    }

    results = reconcile_records(
        records_a=records_a,
        records_b=records_b,
        location_org_map=tenant_location_map,
    )

    if reason and reason != "ALL":
        results = [
            result
            for result in results
            if result.reason == reason
        ]

    return JsonResponse(
        {
            "results": [
                result.to_dict()
                for result in results
            ],
            "count": len(results),
            "org_id": org_id,
        }
    )
