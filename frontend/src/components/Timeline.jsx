function fmt(iso) {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "UTC" }) + " UTC";
}

export default function Timeline({ events }) {
  return (
    <section className="panel">
      <span className="eyebrow">HOS SCHEDULE</span>
      <h2>Route instructions & required stops</h2>
      <div className="timeline">
        {events.map((event, i) => (
          <article className={`timeline-item status-${event.status}`} key={`${event.start}-${i}`}>
            <div className="timeline-dot" />
            <div>
              <div className="timeline-top"><strong>{event.label}</strong><span>{event.hours.toFixed(2)} hrs</span></div>
              <p>{fmt(event.start)} → {fmt(event.end)}{event.miles ? ` • ${event.miles} mi` : ""}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
