import React, { useMemo, useState } from "react";


const REASON_LABELS = {
  MISSING_IN_SYSTEM_B: "Missing in System B",
  ORPHAN_IN_SYSTEM_B: "Orphan in System B",
  DUPLICATE_IN_SYSTEM_B: "Duplicate in System B",
  VALUE_MISMATCH: "Value mismatch"
};


function formatReason(reason) {
  return (
    REASON_LABELS[reason] ||
    reason
  );
}


function formatValue(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return value;
}


export default function DiscrepancyTable({
  items
}) {
  const [
    sortAscending,
    setSortAscending
  ] = useState(true);


  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      const valueA =
        a.sort_value === null ||
        a.sort_value === undefined
          ? Number.POSITIVE_INFINITY
          : Number(a.sort_value);

      const valueB =
        b.sort_value === null ||
        b.sort_value === undefined
          ? Number.POSITIVE_INFINITY
          : Number(b.sort_value);

      if (valueA === valueB) {
        return a.record_id.localeCompare(
          b.record_id
        );
      }

      return sortAscending
        ? valueA - valueB
        : valueB - valueA;
    });
  }, [items, sortAscending]);


  if (items.length === 0) {
    return (
      <div className="empty-state">
        No discrepancies found for the selected
        filters.
      </div>
    );
  }


  return (
    <section className="table-section">
      <div className="table-toolbar">
        <strong>
          {items.length} discrepancy
          {items.length === 1 ? "" : "ies"}
        </strong>

        <button
          type="button"
          onClick={() =>
            setSortAscending(
              (current) => !current
            )
          }
        >
          Sort by value{" "}
          {sortAscending ? "↑" : "↓"}
        </button>
      </div>


      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Record</th>
              <th>Location</th>
              <th>Tenant</th>
              <th>Reason</th>
              <th>System A</th>
              <th>System B</th>
            </tr>
          </thead>

          <tbody>
            {sortedItems.map((item, index) => (
              <tr
                key={`${item.record_id}-${item.reason}-${index}`}
              >
                <td className="record-cell">
                  {item.record_id}
                </td>

                <td>
                  {item.location_id || "—"}
                </td>

                <td>
                  {item.org_id}
                </td>

                <td>
                  <span
                    className={`reason reason-${item.reason.toLowerCase()}`}
                  >
                    {formatReason(item.reason)}
                  </span>
                </td>

                <td>
                  {formatValue(item.val_a)}
                </td>

                <td>
                  {formatValue(item.val_b)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
