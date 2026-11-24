import { useState } from "react";
import { Shield, Cpu, Layers, ArrowRight, CheckCircle2, Radio } from "lucide-react";
import QuoteForm from "../components/QuoteForm.jsx";

export default function Home() {
  const [activeTab, setActiveTab] = useState("data");
  const [acres, setAcres] = useState(100);
  const [selectedService, setSelectedService] = useState("WHITE_LABEL_DATA_PROCESSING");

  const estimatedPrice = Math.max(15000, acres * 200);
  const traditionalCost = Math.round(estimatedPrice * 3.4);

  const contactEmail = import.meta.env.VITE_CONTACT_EMAIL || "ops@vayugrid.in";
  const contactPhone = import.meta.env.VITE_CONTACT_PHONE || "Contact via Quote Form";
  const companyLocation = import.meta.env.VITE_COMPANY_LOCATION || "Bhilai - Raipur Industrial Corridor, Chhattisgarh";

  const scrollToQuote = (serviceKey) => {
    setSelectedService(serviceKey);
    document.getElementById("quote-section")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100">
      <header className="sticky top-0 z-40 bg-[#070B14]/90 backdrop-blur border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono font-bold text-lg tracking-wider">
            <Radio className="w-5 h-5 text-cyan-400" />
            <span>VAYUGRID<span className="text-cyan-400">.AERO</span></span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-slate-300">
            <a href="#services" className="hover:text-cyan-400">Capabilities</a>
            <a href="#platforms" className="hover:text-cyan-400">UAV Systems</a>
            <a href="#estimator" className="hover:text-cyan-400">Cost Estimator</a>
          </nav>
          <button
            onClick={() => scrollToQuote("WHITE_LABEL_DATA_PROCESSING")}
            className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-mono font-bold px-4 py-2 rounded-lg cursor-pointer"
          >
            GET QUOTE
          </button>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 py-20 md:py-28">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs mb-6">
          <span>INDIGENOUS AERIAL INTELLIGENCE &amp; CONFINED-SPACE UAVs</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight max-w-4xl">
          Turn Raw Drone Imagery Into <span className="text-cyan-400">Engineering-Grade Audits</span> in 24 Hours.
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mt-6 leading-relaxed">
          High-precision 3D stockpile volumetrics, thermal defect mapping, and collision-tolerant indoor UAV inspection systems engineered for heavy steel, power, and mining infrastructure.
        </p>
        <div className="flex flex-wrap gap-4 mt-8">
          <button
            onClick={() => scrollToQuote("WHITE_LABEL_DATA_PROCESSING")}
            className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3.5 rounded-lg inline-flex items-center gap-2 cursor-pointer"
          >
            Upload Dataset / Request Quote <ArrowRight className="w-4 h-4" />
          </button>
          <a
            href="#platforms"
            className="border border-slate-700 hover:border-slate-500 px-6 py-3.5 rounded-lg font-medium text-slate-200"
          >
            Explore UAV Platforms
          </a>
        </div>
      </section>

      <section id="services" className="max-w-6xl mx-auto px-6 py-16 border-t border-slate-800/80">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-10">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold">Operational Capabilities</h2>
            <p className="text-slate-400 text-sm mt-1">Select your operational profile below.</p>
          </div>
          <div className="inline-flex bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab("data")}
              className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition cursor-pointer ${
                activeTab === "data" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-white"
              }`}
            >
              PILOT &amp; SURVEY PARTNERS
            </button>
            <button
              onClick={() => setActiveTab("plant")}
              className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition cursor-pointer ${
                activeTab === "plant" ? "bg-amber-500 text-slate-950" : "text-slate-400 hover:text-white"
              }`}
            >
              INDUSTRIAL PLANTS
            </button>
          </div>
        </div>

        {activeTab === "data" ? (
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title: "2D Orthomosaic & Contours",
                price: "From ₹15,000",
                desc: "Sub-centimeter GeoTIFF maps, DXF contour lines, and CAD overlays delivered within 24 hours of flight.",
                key: "WHITE_LABEL_DATA_PROCESSING",
              },
              {
                title: "3D Stockpile Volumetrics",
                price: "From ₹25,000",
                desc: "Cut/fill terrain models and certified tonnage volume reports for coal, iron ore, and cement quarries.",
                key: "MINING_STOCKPILE_3D",
              },
              {
                title: "Solar & Thermal Fault PDF",
                price: "From ₹20,000",
                desc: "Automated hotspot classification, string-level anomaly tagging, and executive maintenance reports.",
                key: "THERMAL_SOLAR_AUDIT",
              },
            ].map((item) => (
              <div key={item.title} className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <span className="font-mono text-xs text-cyan-400">{item.price}</span>
                  <h3 className="text-xl font-bold mt-2">{item.title}</h3>
                  <p className="text-sm text-slate-400 mt-3 leading-relaxed">{item.desc}</p>
                </div>
                <button
                  onClick={() => scrollToQuote(item.key)}
                  className="mt-6 text-xs font-mono font-bold text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1 cursor-pointer"
                >
                  SELECT SERVICE <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-slate-900/70 border border-amber-500/30 rounded-2xl p-6">
              <span className="font-mono text-xs text-amber-400">ZERO SCAFFOLDING DOWNTIME</span>
              <h3 className="text-xl font-bold mt-2">Confined-Space Boiler &amp; Silo Inspection</h3>
              <p className="text-sm text-slate-400 mt-3 leading-relaxed">
                Collision-tolerant caged UAV deployment for offline boilers, chimneys, ducts, and storage silos—eliminating multi-day scaffolding costs and human entry hazards.
              </p>
              <button
                onClick={() => scrollToQuote("CONFINED_SPACE_INSPECTION")}
                className="mt-6 text-xs font-mono font-bold text-amber-400 inline-flex items-center gap-1 cursor-pointer"
              >
                BOOK SITE AUDIT <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
              <span className="font-mono text-xs text-cyan-400">PREVENTIVE MAINTENANCE</span>
              <h3 className="text-xl font-bold mt-2">Plant-Wide Thermal &amp; Structural Digital Twin</h3>
              <p className="text-sm text-slate-400 mt-3 leading-relaxed">
                Periodic aerial thermography and high-resolution structural crack tracking across steel plants, power stations, and conveyor networks.
              </p>
              <button
                onClick={() => scrollToQuote("THERMAL_SOLAR_AUDIT")}
                className="mt-6 text-xs font-mono font-bold text-cyan-400 inline-flex items-center gap-1 cursor-pointer"
              >
                REQUEST ANNUAL AMC <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </section>

      <section id="platforms" className="max-w-6xl mx-auto px-6 py-16 border-t border-slate-800/80">
        <h2 className="text-2xl md:text-3xl font-bold mb-8">Indigenous UAV R&amp;D Roadmap</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <Shield className="w-7 h-7 text-amber-400 mb-4" />
            <div className="font-mono text-xs text-amber-400">PROTOTYPE // INDOOR</div>
            <h3 className="text-lg font-bold mt-1">VG-CAGE Mk.I</h3>
            <p className="text-sm text-slate-400 mt-2">
              Impact-absorbing carbon-polymer geodesic cage engineered for GPS-denied steel boilers, culverts, and industrial ducts.
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <Cpu className="w-7 h-7 text-cyan-400 mb-4" />
            <div className="font-mono text-xs text-cyan-400">SUB-250G // DGCA NANO</div>
            <h3 className="text-lg font-bold mt-1">VG-NANO X1</h3>
            <p className="text-sm text-slate-400 mt-2">
              Ducted micro-reconnaissance platform under 250g AUW for rapid indoor room clearing, pipe scouting, and low-light telemetry.
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <Layers className="w-7 h-7 text-emerald-400 mb-4" />
            <div className="font-mono text-xs text-emerald-400">DEFENCE R&amp;D // DUAL-USE</div>
            <h3 className="text-lg font-bold mt-1">AEGIS Autonomy Stack</h3>
            <p className="text-sm text-slate-400 mt-2">
              Edge-AI visual navigation and resilient telemetry architecture built for autonomous perimeter surveillance and tactical UAVs.
            </p>
          </div>
        </div>
      </section>

      <section id="estimator" className="max-w-6xl mx-auto px-6 py-16 border-t border-slate-800/80">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-10 grid md:grid-cols-2 gap-8 items-center">
          <div>
            <span className="font-mono text-xs text-cyan-400">INSTANT PROCESSING ESTIMATOR</span>
            <h2 className="text-2xl font-bold mt-2">Calculate Your Survey Processing Cost</h2>
            <p className="text-sm text-slate-400 mt-2">
              Adjust survey area (acres) to compare VayuGrid 24-hour processing against traditional enterprise software &amp; manual CAD teams.
            </p>
            <div className="mt-6">
              <div className="flex justify-between font-mono text-sm mb-2">
                <span>Survey Area</span>
                <span className="text-cyan-400 font-bold">{acres} Acres</span>
              </div>
              <input
                type="range"
                min="25"
                max="500"
                step="25"
                value={acres}
                onChange={(e) => setAcres(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Traditional Processing / Scaffolding</span>
              <span className="font-mono line-through text-slate-500">₹{traditionalCost.toLocaleString("en-IN")}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="font-semibold">VayuGrid Turnkey Fee</span>
              <span className="font-mono text-3xl font-bold text-cyan-400">₹{estimatedPrice.toLocaleString("en-IN")}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Estimated Savings: ₹{(traditionalCost - estimatedPrice).toLocaleString("en-IN")}</span>
            </div>
            <button
              onClick={() => scrollToQuote("WHITE_LABEL_DATA_PROCESSING")}
              className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-2.5 rounded-lg text-sm cursor-pointer"
            >
              Lock This Estimate in Quote Form
            </button>
          </div>
        </div>
      </section>

      <section id="quote-section" className="max-w-3xl mx-auto px-6 py-16">
        <QuoteForm prefilledService={selectedService} prefilledEstimate={estimatedPrice} />
      </section>

      <footer className="border-t border-slate-800 py-10 px-6 text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between gap-4">
          <div>
            <span className="font-mono font-bold text-slate-300">VAYUGRID AEROSPACE</span>
            <p className="mt-1">{companyLocation}</p>
          </div>
          <div className="font-mono space-y-1 md:text-right">
            <p>EMAIL: {contactEmail}</p>
            <p>OPS DESK: {contactPhone}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}