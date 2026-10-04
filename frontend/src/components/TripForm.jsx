import { useState } from "react";

const initial = {
  current_location: "",
  pickup_location: "",
  dropoff_location: "",
  current_cycle_used: 0,
};

export default function TripForm({ onSubmit, loading }) {
  const [values, setValues] = useState(initial);

  function update(e) {
    setValues((v) => ({ ...v, [e.target.name]: e.target.value }));
  }

  function submit(e) {
    e.preventDefault();
    onSubmit({ ...values, current_cycle_used: Number(values.current_cycle_used) });
  }

  return (
    <section className="panel form-panel">
      <div className="section-heading">
        <div><span className="eyebrow">TRIP INPUTS</span><h2>Where are you heading?</h2></div>
        <p>U.S. addresses or city/state combinations work best.</p>
      </div>
      <form className="trip-form" onSubmit={submit}>
        <label>Current location
          <input required name="current_location" value={values.current_location} onChange={update} placeholder="Chicago, IL" />
        </label>
        <label>Pickup location
          <input required name="pickup_location" value={values.pickup_location} onChange={update} placeholder="Indianapolis, IN" />
        </label>
        <label>Dropoff location
          <input required name="dropoff_location" value={values.dropoff_location} onChange={update} placeholder="Atlanta, GA" />
        </label>
        <label>Current cycle used (hrs)
          <input required type="number" min="0" max="70" step="0.25" name="current_cycle_used" value={values.current_cycle_used} onChange={update} />
        </label>
        <button disabled={loading}>{loading ? "Calculating route…" : "Plan trip"}</button>
      </form>
    </section>
  );
}
