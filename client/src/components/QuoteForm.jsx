import { useState, useEffect } from "react";
import { submitQuoteRequest } from "../services/api.js";

export default function QuoteForm({ prefilledService = "WHITE_LABEL_DATA_PROCESSING", prefilledEstimate = 20000 }) {
  const [formData, setFormData] = useState({
    fullName: "",
    companyName: "",
    email: "",
    phone: "",
    serviceType: prefilledService,
    location: "",
    estimatedValueINR: prefilledEstimate,
    projectNotes: "",
  });

  const [status, setStatus] = useState({ loading: false, error: "", referenceId: "" });

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      serviceType: prefilledService,
      estimatedValueINR: prefilledEstimate,
    }));
  }, [prefilledService, prefilledEstimate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ loading: true, error: "", referenceId: "" });
    try {
      const res = await submitQuoteRequest(formData);
      setStatus({ loading: false, error: "", referenceId: res.referenceId });
      setFormData({
        fullName: "",
        companyName: "",
        email: "",
        phone: "",
        serviceType: prefilledService,
        location: "",
        estimatedValueINR: prefilledEstimate,
        projectNotes: "",
      });
    } catch (err) {
      setStatus({ loading: false, error: err.message, referenceId: "" });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xl font-bold text-white">Request Commercial Quote / Dataset Upload</h3>
          <p className="text-xs text-slate-400 mt-1">24-hour engineering turnaround for industrial audits &amp; photogrammetry.</p>
        </div>
        <span className="font-mono text-xs px-2.5 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          EST: ₹{Number(formData.estimatedValueINR).toLocaleString("en-IN")}
        </span>
      </div>

      {status.referenceId && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 text-sm">
          Quote logged under Reference ID <span className="font-mono font-bold">{status.referenceId}</span>.
        </div>
      )}

      {status.error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-300 text-sm">
          {status.error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">FULL NAME *</label>
          <input
            type="text"
            name="fullName"
            required
            value={formData.fullName}
            onChange={handleChange}
            placeholder="Rajesh Sharma"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">COMPANY / PLANT NAME *</label>
          <input
            type="text"
            name="companyName"
            required
            value={formData.companyName}
            onChange={handleChange}
            placeholder="Steel / Survey / Solar Corp"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">WORK EMAIL *</label>
          <input
            type="email"
            name="email"
            required
            value={formData.email}
            onChange={handleChange}
            placeholder="ops@company.in"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">PHONE / WHATSAPP *</label>
          <input
            type="tel"
            name="phone"
            required
            value={formData.phone}
            onChange={handleChange}
            placeholder="+91 98XXXXXXXX"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">SERVICE MODULE *</label>
          <select
            name="serviceType"
            value={formData.serviceType}
            onChange={handleChange}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          >
            <option value="WHITE_LABEL_DATA_PROCESSING">White-Label Aerial Data Processing (24h)</option>
            <option value="MINING_STOCKPILE_3D">Mining Stockpile Volumetric &amp; 3D DEM</option>
            <option value="THERMAL_SOLAR_AUDIT">Thermal / Solar Hotspot &amp; Defect Audit</option>
            <option value="CONFINED_SPACE_INSPECTION">Confined-Space Boiler / Silo Inspection</option>
            <option value="CUSTOM_UAV_RND">Custom UAV &amp; Autonomous Payload R&amp;D</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">SITE LOCATION</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="Bhilai / Raipur / Korba"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-mono text-slate-400 mb-1">PROJECT SCOPE / IMAGE COUNT / DRIVE LINK</label>
        <textarea
          name="projectNotes"
          rows="3"
          value={formData.projectNotes}
          onChange={handleChange}
          placeholder="Specify acreage, stockpile count, boiler dimensions, or paste raw dataset link..."
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-cyan-400 outline-none"
        />
      </div>

      <button
        type="submit"
        disabled={status.loading}
        className="w-full bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-lg transition cursor-pointer"
      >
        {status.loading ? "TRANSMITTING TELEMETRY..." : "SUBMIT QUOTE REQUEST"}
      </button>
    </form>
  );
}