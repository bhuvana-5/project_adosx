async function getJson(url) {
  const response = await fetch(url);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();

      if (body.error) {
        message = body.error;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export async function fetchOrganizations() {
  return getJson("/api/organizations/");
}


export async function fetchDiscrepancies(
  orgId,
  reason = "ALL"
) {
  const params = new URLSearchParams({
    org_id: orgId,
    reason
  });

  return getJson(
    `/api/discrepancies/?${params.toString()}`
  );
}
