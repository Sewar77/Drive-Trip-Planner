const ROW = { off_duty: 0, sleeper: 1, driving: 2, on_duty: 3 };
const LABEL = { off_duty: "OFF DUTY", sleeper: "SLEEPER BERTH", driving: "DRIVING", on_duty: "ON DUTY (NOT DRIVING)" };

function hourOfDay(iso) {
  const d = new Date(iso);
  return d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
}

function makePath(events, width, top, rowH) {
  const x = (h) => (h / 24) * width;
  const y = (status) => top + ROW[status] * rowH + rowH / 2;
  let path = "";
  events.forEach((e, i) => {
    let start = hourOfDay(e.start);
    let end = hourOfDay(e.end);
    if (new Date(e.end).getUTCDate() !== new Date(e.start).getUTCDate()) end = 24;
    if (i === 0) path += `M ${x(start)} ${y(e.status)}`;
    else path += ` V ${y(e.status)}`;
    path += ` H ${x(end)}`;
  });
  return path;
}

export default function EldLog({ log }) {
  const width = 960, top = 62, rowH = 46, gridH = rowH * 4;
  const path = makePath(log.events, width, top, rowH);
  const total = Object.values(log.totals).reduce((a, b) => a + b, 0);

  return (
    <article className="eld-sheet">
      <div className="eld-header">
        <div><span>DRIVER'S DAILY LOG</span><strong>{log.date}</strong></div>
        <div><span>TOTAL MILES</span><strong>{log.total_miles}</strong></div>
        <div><span>24-HOUR TOTAL</span><strong>{total.toFixed(2)}</strong></div>
      </div>

      <div className="eld-scroll">
        <div className="eld-chart">
          <div className="eld-labels">
            {Object.values(LABEL).map((x) => <div key={x}>{x}</div>)}
          </div>
          <svg viewBox={`0 0 ${width} ${top + gridH + 8}`} role="img" aria-label={`ELD graph for ${log.date}`}>
            {[0,1,2,3,4].map((r) => <line key={`r${r}`} x1="0" x2={width} y1={top+r*rowH} y2={top+r*rowH} className="grid-major" />)}
            {Array.from({ length: 97 }).map((_, i) => {
              const xx = (i / 96) * width;
              return <line key={i} x1={xx} x2={xx} y1={top} y2={top+gridH} className={i%4===0 ? "grid-major" : "grid-minor"} />;
            })}
            {Array.from({ length: 25 }).map((_, i) => (
              <text key={`t${i}`} x={(i/24)*width} y="42" textAnchor={i===0 ? "start" : i===24 ? "end" : "middle"}>{i}</text>
            ))}
            <path d={path} className="duty-path" />
          </svg>
        </div>
      </div>

      <div className="eld-totals">
        {Object.entries(LABEL).map(([key, label]) => (
          <div key={key}><span>{label}</span><strong>{log.totals[key].toFixed(2)} h</strong></div>
        ))}
      </div>

      <div className="remarks">
        <strong>Remarks / duty changes</strong>
        {log.events.filter(e => e.label !== "Off Duty").map((e, i) => (
          <p key={i}>{new Date(e.start).toISOString().slice(11,16)} — {e.label}{e.location ? ` — ${e.location}` : ""}</p>
        ))}
      </div>
    </article>
  );
}
