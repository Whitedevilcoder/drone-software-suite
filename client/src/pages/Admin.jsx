import { useState, useEffect } from "react";
import { adminLogin, fetchAllQuotes, updateQuoteStatus } from "../services/api";

const STATUS_OPTIONS = ["NEW", "CONTACTED", "PROPOSAL_SENT", "WON", "LOST"];

export default function AdminDashboard() {
  const [token, setToken] = useState(localStorage.getItem("vg_admin_token") || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [quotes, setQuotes] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (token) {
      fetchAllQuotes(token)
        .then(setQuotes)
        .catch(() => {
          localStorage.removeItem("vg_admin_token");
          setToken("");
        });
    }
  }, [token]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const jwt = await adminLogin(email, password);
      localStorage.setItem("vg_admin_token", jwt);
      setToken(jwt);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    const updated = await updateQuoteStatus(token, id, { status: newStatus });
    setQuotes((prev) => prev.map((q) => (q._id === id ? updated : q)));
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <form onSubmit={handleLogin} className="w-full max-w-sm bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <h2 className="text-xl font-bold text-cyan-400">VayuGrid Lead Command</h2>
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <input
            type="email"
            placeholder="Admin Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm"
            required
          />
          <button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2 rounded">
            Authenticate
          </button>
        </form>
      </div>
    );
  }

  const pipelineTotal = quotes
    .filter((q) => q.status !== "LOST")
    .reduce((sum, q) => sum + (q.estimatedValueINR || 0), 0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-cyan-400">B2B Quote Pipeline</h1>
            <p className="text-sm text-slate-400">
              Active Pipeline Value: <span className="text-amber-400 font-mono font-bold">₹{pipelineTotal.toLocaleString("en-IN")}</span>
            </p>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem("vg_admin_token");
              setToken("");
            }}
            className="text-xs border border-slate-700 px-3 py-1.5 rounded hover:bg-slate-800"
          >
            Logout
          </button>
        </div>

        <div className="overflow-x-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400 font-mono text-xs uppercase">
              <tr>
                <th className="p-3">Ref ID</th>
                <th className="p-3">Company / Contact</th>
                <th className="p-3">Service</th>
                <th className="p-3">Est. Value</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {quotes.map((q) => (
                <tr key={q._id} className="hover:bg-slate-900/50">
                  <td className="p-3 font-mono text-cyan-400">{q.referenceId}</td>
                  <td className="p-3">
                    <div className="font-semibold">{q.companyName}</div>
                    <div className="text-xs text-slate-400">{q.fullName} • {q.phone}</div>
                  </td>
                  <td className="p-3 text-xs font-mono">{q.serviceType}</td>
                  <td className="p-3 font-mono text-amber-400">₹{q.estimatedValueINR.toLocaleString("en-IN")}</td>
                  <td className="p-3">
                    <select
                      value={q.status}
                      onChange={(e) => handleStatusChange(q._id, e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs font-mono"
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}