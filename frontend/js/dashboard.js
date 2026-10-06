(async () => {
  const s = await api("/dashboard/stats");
  document.getElementById("source").textContent =
    `Aggregate view of ${s.population} ${s.source}. Assessments saved by this app so far: ${s.stored_assessments}.`;
  document.getElementById("disc").textContent = s.disclaimer;

  const cards = [
    ["Overall risk score (avg)", s.average_overall_score], ["Risk level (avg)", s.average_level],
    ["High-risk categories", `${s.high_risk_categories} / 10`], ["Avg findings per profile", s.average_findings],
    ["Security controls enabled (avg)", `${s.average_controls_enabled} / ${s.total_controls}`],
  ];
  const box = document.getElementById("cards");
  cards.forEach(([t, v]) => box.append(el("div", { className: "card" }, el("h3", { textContent: t }), el("div", { className: "big", textContent: v }))));

  const labels = Object.keys(s.category_averages).map((k) => s.category_labels[k]);
  const catVals = Object.values(s.category_averages);
  const colors = (vals) => vals.map((v) => LEVEL_COLOR[levelOf(v)]);
  const bar = (id, labs, data, opts = {}) => new Chart(document.getElementById(id), {
    type: "bar", data: { labels: labs, datasets: [{ data, backgroundColor: opts.colors || "#38e1b0" }] },
    options: { maintainAspectRatio: false, indexAxis: opts.horizontal ? "y" : "x", plugins: { legend: { display: false } },
               scales: { [opts.horizontal ? "x" : "y"]: { min: 0, max: 100 } } },
  });
  bar("c1", labels, catVals, { colors: colors(catVals), horizontal: true });
  new Chart(document.getElementById("c2"), {
    type: "doughnut", data: { labels: Object.keys(s.risk_distribution), datasets: [{ data: Object.values(s.risk_distribution),
      backgroundColor: Object.keys(s.risk_distribution).map((l) => LEVEL_COLOR[l]), borderColor: "#141a24" }] },
    options: { maintainAspectRatio: false },
  });
  bar("c3", s.top_weaknesses.map((w) => w.label), s.top_weaknesses.map((w) => w.percent), { horizontal: true, colors: "#ff8a3d" });
  bar("c4", s.controls_enabled.map((c) => c.control), s.controls_enabled.map((c) => c.percent_enabled), { horizontal: true, colors: "#38e1b0" });
  const fp = s.digital_footprint.map((d) => d.avg_risk);
  bar("c5", s.digital_footprint.map((d) => d.label), fp, { colors: colors(fp) });
  const imp = s.improvement_comparison;
  bar("c6", ["Current", "Fix IMMEDIATE", "Fix IMMEDIATE + IMPORTANT", "Fix all"],
      [imp.current, imp.after_immediate, imp.after_immediate_important, imp.after_all], { colors: ["#ff4d5e", "#ff8a3d", "#f4c542", "#2fd47a"] });
})();
