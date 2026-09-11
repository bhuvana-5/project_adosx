import { useEffect, useState } from "react";
import { fetchDiscrepancies, fetchOrganizations } from "./api";
import FilterBar from "./components/FilterBar";
import DiscrepancyTable from "./components/DiscrepancyTable";

function App() {
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState("");
  const [reason, setReason] = useState("");
  const [discrepancies, setDiscrepancies] = useState([]);

  const [loadingOrganizations, setLoadingOrganizations] = useState(true);
  const [loadingDiscrepancies, setLoadingDiscrepancies] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadOrganizations() {
      try {
        setLoadingOrganizations(true);
        const data = await fetchOrganizations();

        setOrganizations(data.organizations || []);

        if (data.organizations?.length > 0) {
          setSelectedOrg(data.organizations[0].org_id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingOrganizations(false);
      }
    }

    loadOrganizations();
  }, []);

  useEffect(() => {
    if (!selectedOrg) {
      return;
    }

    async function loadDiscrepancies() {
      try {
        setLoadingDiscrepancies(true);
        setError("");

        const data = await fetchDiscrepancies(selectedOrg, reason);

        setDiscrepancies(data.discrepancies || []);
      } catch (err) {
        setError(err.message);
        setDiscrepancies([]);
      } finally {
        setLoadingDiscrepancies(false);
      }
    }

    loadDiscrepancies();
  }, [selectedOrg, reason]);

  return (
    <div className="app">
      <header className="page-header">
        <div>
          <h1>System Reconciliation</h1>
          <p>
            Review disagreements between System A and System B.
          </p>
        </div>
      </header>

      <main className="container">
        {loadingOrganizations ? (
          <div className="status-card">
            Loading organizations...
          </div>
        ) : (
          <>
            <FilterBar
              organizations={organizations}
              selectedOrg={selectedOrg}
              setSelectedOrg={setSelectedOrg}
              reason={reason}
              setReason={setReason}
            />

            {error && (
              <div className="error-card">
                {error}
              </div>
            )}

            {loadingDiscrepancies ? (
              <div className="status-card">
                Loading discrepancies...
              </div>
            ) : (
              <DiscrepancyTable
                discrepancies={discrepancies}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
