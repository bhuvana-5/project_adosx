import React, {
  useEffect,
  useState
} from "react";

import {
  fetchDiscrepancies,
  fetchOrganizations
} from "./api";

import FilterBar from "./components/FilterBar";
import DiscrepancyTable from "./components/DiscrepancyTable";


export default function App() {
  const [
    organizations,
    setOrganizations
  ] = useState([]);

  const [
    selectedOrg,
    setSelectedOrg
  ] = useState("");

  const [
    selectedReason,
    setSelectedReason
  ] = useState("ALL");

  const [
    discrepancies,
    setDiscrepancies
  ] = useState([]);

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    error,
    setError
  ] = useState("");


  useEffect(() => {
    async function loadOrganizations() {
      try {
        setLoading(true);
        setError("");

        const data =
          await fetchOrganizations();

        setOrganizations(
          data.results || []
        );

        if (
          data.results &&
          data.results.length > 0
        ) {
          setSelectedOrg(
            data.results[0]
          );
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadOrganizations();
  }, []);


  useEffect(() => {
    if (!selectedOrg) {
      setDiscrepancies([]);
      return;
    }

    async function loadDiscrepancies() {
      try {
        setLoading(true);
        setError("");

        const data =
          await fetchDiscrepancies(
            selectedOrg,
            selectedReason
          );

        setDiscrepancies(
          data.results || []
        );
      } catch (err) {
        setError(err.message);
        setDiscrepancies([]);
      } finally {
        setLoading(false);
      }
    }

    loadDiscrepancies();
  }, [
    selectedOrg,
    selectedReason
  ]);


  return (
    <main className="app">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            AdosX Engineering Assessment
          </p>

          <h1>
            Cross-System Reconciliation
          </h1>

          <p className="subtitle">
            Review discrepancies between
            System A and System B.
          </p>
        </div>
      </header>


      {organizations.length > 0 && (
        <FilterBar
          organizations={organizations}
          selectedOrg={selectedOrg}
          selectedReason={selectedReason}
          onOrgChange={setSelectedOrg}
          onReasonChange={setSelectedReason}
        />
      )}


      {error && (
        <div className="error">
          <strong>Error:</strong>{" "}
          {error}
        </div>
      )}


      {loading ? (
        <div className="loading">
          Loading...
        </div>
      ) : (
        <DiscrepancyTable
          items={discrepancies}
        />
      )}
    </main>
  );
}
