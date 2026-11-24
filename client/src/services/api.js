const RAW_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
const API_BASE = RAW_BASE.replace(/\/+$/, "");

async function parseResponse(res) {
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Invalid server response (HTTP ${res.status}) from ${API_BASE}`);
  }
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

export async function submitQuoteRequest(payload) {
  const res = await fetch(`${API_BASE}/quotes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(res);
}

export async function adminLogin(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await parseResponse(res);
  return data.token;
}

export async function fetchAllQuotes(token) {
  const res = await fetch(`${API_BASE}/quotes`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseResponse(res);
}

export async function updateQuoteStatus(token, id, updates) {
  const res = await fetch(`${API_BASE}/quotes/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  return parseResponse(res);
}