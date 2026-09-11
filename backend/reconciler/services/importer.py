import csv
from pathlib import Path
from typing import Iterable

from django.db import transaction

from reconciler.models import (
    ImportIssue,
    Location,
    SystemARecord,
    SystemBEntry,
)

from .normalizer import normalize_reference, safe_parse_decimal


REQUIRED_LOCATION_COLUMNS = {
    "location_id",
    "org_id",
}

REQUIRED_A_COLUMNS = {
    "record_id",
    "location_id",
    "value",
}

REQUIRED_B_COLUMNS = {
    "record_ref",
    "location_id",
    "value",
}


def _clean_row(row: dict) -> dict:
    return {
        str(key).strip(): (
            value if value is not None else ""
        )
        for key, value in row.items()
    }


def _record_issue(
    source: str,
    row_number: int,
    message: str,
    raw_data: dict,
) -> None:
    ImportIssue.objects.create(
        source=source,
        row_number=row_number,
        message=message,
        raw_data=raw_data,
    )


def _read_csv(path: Path) -> Iterable[tuple[int, dict]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"{path.name} does not contain a CSV header."
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            yield row_number, _clean_row(row)


@transaction.atomic
def import_all(
    data_dir: Path,
    clear_existing: bool = True,
) -> dict:
    """
    Import all three CSV files.

    The importer preserves raw values and does not enforce a foreign
    key from System B to System A. This is important because orphan
    B records are a required reconciliation case.
    """

    locations_path = data_dir / "locations.csv"
    system_a_path = data_dir / "system_a.csv"
    system_b_path = data_dir / "system_b.csv"

    for path in (
        locations_path,
        system_a_path,
        system_b_path,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required CSV file not found: {path}"
            )

    if clear_existing:
        ImportIssue.objects.all().delete()
        SystemBEntry.objects.all().delete()
        SystemARecord.objects.all().delete()
        Location.objects.all().delete()

    location_count = 0
    system_a_count = 0
    system_b_count = 0
    issue_count = 0

    # ---------------------------------------------------------
    # Locations first because they establish tenant ownership.
    # ---------------------------------------------------------
    for row_number, row in _read_csv(locations_path):
        missing = REQUIRED_LOCATION_COLUMNS - set(row)

        if missing:
            _record_issue(
                "locations.csv",
                row_number,
                f"Missing columns: {sorted(missing)}",
                row,
            )
            issue_count += 1
            continue

        location_id = row.get("location_id", "").strip()
        org_id = row.get("org_id", "").strip()

        if not location_id or not org_id:
            _record_issue(
                "locations.csv",
                row_number,
                "Location ID and org ID are required.",
                row,
            )
            issue_count += 1
            continue

        Location.objects.update_or_create(
            location_id=location_id,
            defaults={
                "org_id": org_id,
            },
        )

        location_count += 1

    location_map = {
        location.location_id: location
        for location in Location.objects.all()
    }

    # ---------------------------------------------------------
    # System A
    # ---------------------------------------------------------
    for row_number, row in _read_csv(system_a_path):
        missing = REQUIRED_A_COLUMNS - set(row)

        if missing:
            _record_issue(
                "system_a.csv",
                row_number,
                f"Missing columns: {sorted(missing)}",
                row,
            )
            issue_count += 1
            continue

        record_id = row.get("record_id", "").strip()
        location_id = row.get("location_id", "").strip()
        raw_value = row.get("value", "")

        if not record_id:
            _record_issue(
                "system_a.csv",
                row_number,
                "record_id is required.",
                row,
            )
            issue_count += 1
            continue

        location = location_map.get(location_id)

        if location is None:
            _record_issue(
                "system_a.csv",
                row_number,
                f"Unknown location: {location_id}",
                row,
            )
            issue_count += 1

        SystemARecord.objects.update_or_create(
            record_id=record_id,
            defaults={
                "location": location,
                "raw_value": str(raw_value),
                "normalized_value": safe_parse_decimal(
                    raw_value
                ),
                "imported_row_number": row_number,
            },
        )

        system_a_count += 1

    # ---------------------------------------------------------
    # System B
    #
    # IMPORTANT:
    # Do NOT use record_ref as a foreign key.
    # Orphan B entries must survive ingestion.
    # ---------------------------------------------------------
    for row_number, row in _read_csv(system_b_path):
        missing = REQUIRED_B_COLUMNS - set(row)

        if missing:
            _record_issue(
                "system_b.csv",
                row_number,
                f"Missing columns: {sorted(missing)}",
                row,
            )
            issue_count += 1
            continue

        record_ref = row.get("record_ref", "")
        location_id = row.get("location_id", "").strip()
        raw_value = row.get("value", "")

        location = location_map.get(location_id)

        if location is None:
            _record_issue(
                "system_b.csv",
                row_number,
                f"Unknown location: {location_id}",
                row,
            )
            issue_count += 1

        SystemBEntry.objects.create(
            record_ref=str(record_ref),
            normalized_record_ref=normalize_reference(
                record_ref
            ),
            location=location,
            raw_value=str(raw_value),
            normalized_value=safe_parse_decimal(
                raw_value
            ),
            imported_row_number=row_number,
        )

        system_b_count += 1

    return {
        "locations": location_count,
        "system_a": system_a_count,
        "system_b": system_b_count,
        "issues": issue_count,
    }
