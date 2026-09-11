import React from "react";


const REASONS = [
  {
    value: "ALL",
    label: "All discrepancies"
  },
  {
    value: "MISSING_IN_SYSTEM_B",
    label: "Missing in System B"
  },
  {
    value: "ORPHAN_IN_SYSTEM_B",
    label: "Orphan in System B"
  },
  {
    value: "DUPLICATE_IN_SYSTEM_B",
    label: "Duplicate in System B"
  },
  {
    value: "VALUE_MISMATCH",
    label: "Value mismatch"
  }
];


export default function FilterBar({
  organizations,
  selectedOrg,
  selectedReason,
  onOrgChange,
  onReasonChange
}) {
  return (
    <section className="filter-bar">
      <div className="filter-field">
        <label htmlFor="organization">
          Organization
        </label>

        <select
          id="organization"
          value={selectedOrg}
          onChange={(event) =>
            onOrgChange(event.target.value)
          }
        >
          {organizations.map((orgId) => (
            <option
              key={orgId}
              value={orgId}
            >
              {orgId}
            </option>
          ))}
        </select>
      </div>


      <div className="filter-field">
        <label htmlFor="reason">
          Discrepancy reason
        </label>

        <select
          id="reason"
          value={selectedReason}
          onChange={(event) =>
            onReasonChange(event.target.value)
          }
        >
          {REASONS.map((reason) => (
            <option
              key={reason.value}
              value={reason.value}
            >
              {reason.label}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
