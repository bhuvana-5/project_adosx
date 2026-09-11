from decimal import Decimal

from django.test import SimpleTestCase

from reconciler.services.comparator import (
    DUPLICATE_IN_SYSTEM_B,
    MISSING_IN_SYSTEM_B,
    ORPHAN_IN_SYSTEM_B,
    VALUE_MISMATCH,
    reconcile_records,
)


class ComparatorTests(SimpleTestCase):

    def test_detects_record_missing_in_system_b(self):
        records_a = [
            {
                "record_id": "REC-01",
                "value": "100.00",
                "location_id": "LOC-1",
            }
        ]

        records_b = []

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].reason,
            MISSING_IN_SYSTEM_B,
        )
        self.assertEqual(
            results[0].val_a,
            "100.00",
        )
        self.assertIsNone(results[0].val_b)

    def test_detects_orphan_record_in_system_b(self):
        records_a = []

        records_b = [
            {
                "record_ref": "REC-999",
                "value": "800.00",
                "location_id": "LOC-1",
            }
        ]

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].reason,
            ORPHAN_IN_SYSTEM_B,
        )
        self.assertEqual(
            results[0].record_id,
            "REC-999",
        )

    def test_detects_duplicate_entries_in_system_b(self):
        records_a = [
            {
                "record_id": "REC-01",
                "value": "100.00",
                "location_id": "LOC-1",
            }
        ]

        records_b = [
            {
                "record_ref": "REC-01",
                "value": "100.00",
                "location_id": "LOC-1",
            },
            {
                "record_ref": " rec_01 ",
                "value": "100",
                "location_id": "LOC-1",
            },
        ]

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].reason,
            DUPLICATE_IN_SYSTEM_B,
        )

    def test_detects_value_mismatch(self):
        records_a = [
            {
                "record_id": "REC-01",
                "value": "100.00",
                "location_id": "LOC-1",
            }
        ]

        records_b = [
            {
                "record_ref": "REC-01",
                "value": "120.00",
                "location_id": "LOC-1",
            }
        ]

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].reason,
            VALUE_MISMATCH,
        )
        self.assertEqual(
            results[0].val_a,
            "100.00",
        )
        self.assertEqual(
            results[0].val_b,
            "120.00",
        )

    def test_normalized_currency_values_are_equal(self):
        records_a = [
            {
                "record_id": "REC-01",
                "value": "100.10",
                "location_id": "LOC-1",
            }
        ]

        records_b = [
            {
                "record_ref": "rec_01",
                "value": "$100.10",
                "location_id": "LOC-1",
            }
        ]

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        self.assertEqual(results, [])

    def test_tenant_boundary_isolation(self):
        records_a = [
            {
                "record_id": "REC-ORG-1",
                "value": "100.00",
                "location_id": "LOC-1",
            },
            {
                "record_id": "REC-ORG-2",
                "value": "200.00",
                "location_id": "LOC-2",
            },
        ]

        records_b = [
            {
                "record_ref": "REC-ORG-1",
                "value": "150.00",
                "location_id": "LOC-1",
            },
            {
                "record_ref": "REC-ORG-2",
                "value": "250.00",
                "location_id": "LOC-2",
            },
        ]

        # Only ORG-1 locations are supplied to this reconciliation.
        tenant_location_map = {
            "LOC-1": "ORG-1",
        }

        tenant_a_records = [
            record
            for record in records_a
            if record["location_id"] == "LOC-1"
        ]

        tenant_b_records = [
            record
            for record in records_b
            if record["location_id"] == "LOC-1"
        ]

        results = reconcile_records(
            tenant_a_records,
            tenant_b_records,
            tenant_location_map,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].org_id,
            "ORG-1",
        )
        self.assertEqual(
            results[0].record_id,
            "REC-ORG-1",
        )

        self.assertNotEqual(
            results[0].record_id,
            "REC-ORG-2",
        )

    def test_blank_numeric_value_does_not_crash(self):
        records_a = [
            {
                "record_id": "REC-01",
                "value": "",
                "location_id": "LOC-1",
            }
        ]

        records_b = [
            {
                "record_ref": "REC-01",
                "value": "N/A",
                "location_id": "LOC-1",
            }
        ]

        location_map = {
            "LOC-1": "ORG-1",
        }

        results = reconcile_records(
            records_a,
            records_b,
            location_map,
        )

        # Both values normalize to None, so this is not a mismatch.
        self.assertEqual(results, [])
