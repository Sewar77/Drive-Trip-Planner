import { useState } from "react";
import { planTrip } from "./api";
import TripForm from "./components/TripForm";
import SummaryCards from "./components/SummaryCards";
import RouteMap from "./components/RouteMap";
import Timeline from "./components/Timeline";
import DailyLogs from "./components/DailyLogs";

export default function App() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handlePlan(values) {
    setLoading(true);
    setError("");
    setPlan(null);
    try {
      setPlan(await planTrip(values));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <span className="eyebrow">FULL-STACK HOS PLANNER</span>
          <h1>Driver Trip Planner</h1>
          <p>Plan a compliant property-carrying trip, visualize the route, and generate daily ELD log sheets.</p>
        </div>
        <div className="rule-chip">70 hrs / 8 days</div>
      </header>

      <TripForm onSubmit={handlePlan} loading={loading} />
      {error && <div className="error-box">{error}</div>}

      {plan && (
        <>
          <SummaryCards summary={plan.summary} />
          <section className="panel">
            <div className="section-heading">
              <div><span className="eyebrow">ROUTE</span><h2>Trip overview</h2></div>
            </div>
            <RouteMap plan={plan} />
          </section>
          <Timeline events={plan.events} />
          <DailyLogs logs={plan.daily_logs} />
          <section className="panel assumptions">
            <span className="eyebrow">IMPLEMENTATION NOTES</span>
            <h2>Planner assumptions</h2>
            <ul>{plan.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
          </section>
        </>
      )}
    </main>
  );
}
