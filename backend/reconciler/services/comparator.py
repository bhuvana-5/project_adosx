from collections import defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from .normalizer import normalize_reference, safe_parse_decimal


MISSING_IN_SYSTEM_B = "MISSING_IN_SYSTEM_B"
ORPHAN_IN_SYSTEM_B = "ORPHAN_IN_SYSTEM_B"
DUPLICATE_IN_SYSTEM_B = "DUPLICATE_IN_SYSTEM_B"
VALUE_MISMATCH = "VALUE_MISMATCH"


@dataclass
class Discrepancy:
    reason: str
    record_id: str
    location_id: str | None
    org_id: str
    val_a: str | None
    val_b: str | None
    sort_value: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _raw_value(record: dict, field: str = "value") -> str | None:
    value = record.get(field)

    if value is None:
        return None

    return str(value)


def _normalized_value(record: dict) -> Decimal | None:
    """
    Prefer a pre-normalized value when the caller supplies one.
    Otherwise normalize the raw value.
    """
    normalized = record.get("normalized_value")

    if normalized is not None:
        if isinstance(normalized, Decimal):
            return normalized

        try:
            return Decimal(str(normalized))
        except Exception:
            pass

    return safe_parse_decimal(record.get("value"))


def _sort_value(
    value_a: Decimal | None,
    value_b: Decimal | None,
) -> float | None:
    value = value_a if value_a is not None else value_b

    if value is None:
        return None

    return float(value)


def reconcile_records(
    records_a: list[dict],
    records_b: list[dict],
    location_org_map: dict[str, str],
) -> list[Discrepancy]:
    """
    Reconcile System A and System B.

    Four explicit passes are represented:

    1. Group System B by normalized reference and detect duplicates.
    2. Find System A records missing from System B.
    3. Find System B references that have no System A parent.
    4. Compare values for one-to-one matches.

    Tenant filtering is intentionally performed by the API before
    this function is called.
    """

    discrepancies: list[Discrepancy] = []

    # ---------------------------------------------------------
    # Pass 1: Group System B by normalized reference.
    # ---------------------------------------------------------
    b_by_ref: dict[str, list[dict]] = defaultdict(list)

    for entry in records_b:
        normalized_ref = normalize_reference(entry.get("record_ref"))
        b_by_ref[normalized_ref].append(entry)

    # ---------------------------------------------------------
    # Build System A lookup.
    # ---------------------------------------------------------
    a_by_ref: dict[str, dict] = {}

    for record in records_a:
        normalized_id = normalize_reference(record.get("record_id"))

        if normalized_id:
            a_by_ref[normalized_id] = record

    matched_b_refs: set[str] = set()

    # ---------------------------------------------------------
    # Pass 2 + Pass 4:
    # Iterate through System A.
    # ---------------------------------------------------------
    for record_a in records_a:
        record_id = str(record_a.get("record_id", ""))
        normalized_id = normalize_reference(record_id)

        location_id = record_a.get("location_id")
        org_id = location_org_map.get(location_id, "UNKNOWN")

        b_entries = b_by_ref.get(normalized_id, [])

        # Pass 2: Missing in System B.
        if not b_entries:
            value_a = _raw_value(record_a)
            normalized_a = _normalized_value(record_a)

            discrepancies.append(
                Discrepancy(
                    reason=MISSING_IN_SYSTEM_B,
                    record_id=record_id,
                    location_id=location_id,
                    org_id=org_id,
                    val_a=value_a,
                    val_b=None,
                    sort_value=_sort_value(normalized_a, None),
                )
            )
            continue

        # Pass 1: Duplicate System B entries.
        if len(b_entries) > 1:
            matched_b_refs.add(normalized_id)

            values_b = [
                _raw_value(entry) for entry in b_entries
            ]

            normalized_a = _normalized_value(record_a)

            discrepancies.append(
                Discrepancy(
                    reason=DUPLICATE_IN_SYSTEM_B,
                    record_id=record_id,
                    location_id=location_id,
                    org_id=org_id,
                    val_a=_raw_value(record_a),
                    val_b="; ".join(
                        value if value is not None else ""
                        for value in values_b
                    ),
                    sort_value=_sort_value(normalized_a, None),
                )
            )
            continue

        # Pass 4: One-to-one value comparison.
        matched_b_refs.add(normalized_id)

        record_b = b_entries[0]

        normalized_a = _normalized_value(record_a)
        normalized_b = _normalized_value(record_b)

        if normalized_a != normalized_b:
            discrepancies.append(
                Discrepancy(
                    reason=VALUE_MISMATCH,
                    record_id=record_id,
                    location_id=location_id,
                    org_id=org_id,
                    val_a=_raw_value(record_a),
                    val_b=_raw_value(record_b),
                    sort_value=_sort_value(normalized_a, normalized_b),
                )
            )

    # ---------------------------------------------------------
    # Pass 3: Find orphan System B records.
    # ---------------------------------------------------------
    for normalized_ref, b_entries in b_by_ref.items():
        if not normalized_ref:
            continue

        if normalized_ref in a_by_ref:
            continue

        for orphan in b_entries:
            location_id = orphan.get("location_id")
            org_id = location_org_map.get(
                location_id,
                "UNKNOWN",
            )

            normalized_b = _normalized_value(orphan)

            discrepancies.append(
                Discrepancy(
                    reason=ORPHAN_IN_SYSTEM_B,
                    record_id=str(
                        orphan.get("record_ref", "")
                    ),
                    location_id=location_id,
                    org_id=org_id,
                    val_a=None,
                    val_b=_raw_value(orphan),
                    sort_value=_sort_value(None, normalized_b),
                )
            )

    return discrepancies
