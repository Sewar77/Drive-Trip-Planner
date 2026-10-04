import EldLog from "./EldLog";

export default function DailyLogs({ logs }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div><span className="eyebrow">DAILY LOG SHEETS</span><h2>Generated driver logs</h2></div>
        <p>{logs.length} sheet{logs.length === 1 ? "" : "s"} generated</p>
      </div>
      <div className="logs-stack">
        {logs.map((log) => <EldLog key={log.date} log={log} />)}
      </div>
    </section>
  );
}
