export default function SummaryCards({ summary }) {
  const cards = [
    ["Distance", `${summary.distance_miles.toLocaleString()} mi`],
    ["Drive time", `${summary.estimated_driving_hours} hrs`],
    ["Cycle used", `${summary.current_cycle_used} hrs`],
    ["Daily logs", summary.number_of_daily_logs],
  ];
  return (
    <section className="summary-grid">
      {cards.map(([label, value]) => (
        <article className="summary-card" key={label}>
          <span>{label}</span><strong>{value}</strong>
        </article>
      ))}
    </section>
  );
}
