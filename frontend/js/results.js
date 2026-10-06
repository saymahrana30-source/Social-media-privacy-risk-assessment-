(async () => {
  const id = new URLSearchParams(location.search).get("id");
  let data;
  try { data = JSON.parse(sessionStorage.getItem("pm_result_" + id)) || (await api("/assessment/" + encodeURIComponent(id))); }
  catch (e) { document.getElementById("loading").textContent = "Could not load this assessment: " + e.message; return; }
  const fresh = !!data.top_risks;                      // full result from POST (has safe answers + recommendations)
  const score = data.overall_score, level = data.risk_level, labels = data.category_labels;
  document.getElementById("loading").hidden = true;
  document.getElementById("content").hidden = false;

  const s = document.getElementById("score");
  s.className = "big c-" + LEVEL_CLASS[level]; s.append(String(score), el("small", { textContent: " / 100" }));
  document.getElementById("level").append(el("span", { className: "badge " + LEVEL_CLASS[level], textContent: level }));
  const highCats = Object.entries(data.category_scores).filter(([, v]) => v >= 41).map(([k]) => labels[k]);
  document.getElementById("hrc").textContent = highCats.length ? "High-risk categories: " + highCats.join(", ") : "No category scores HIGH or worse.";
  const controls = Object.values(data.controls_enabled || {});
  document.getElementById("controls").textContent = `${controls.filter(Boolean).length} / ${controls.length}`;
  document.getElementById("disclaimer").textContent = data.disclaimer;
  renderBars(document.getElementById("bars"), data.category_scores, labels);

  new Chart(document.getElementById("radar"), {
    type: "radar",
    data: { labels: Object.values(labels), datasets: [{ label: "Risk (higher = worse)", data: Object.values(data.category_scores),
      backgroundColor: "rgba(255,77,94,.22)", borderColor: "#ff4d5e", pointBackgroundColor: "#ff4d5e" }] },
    options: { maintainAspectRatio: false, scales: { r: { min: 0, max: 100, ticks: { stepSize: 20, backdropColor: "transparent" } } },
               plugins: { legend: { display: false } } },
  });

  const findings = data.findings || [];
  const fbox = document.getElementById("findings");
  if (!findings.length) fbox.append(el("p", { textContent: "No findings - all assessed items were reported as low risk." }));
  (data.top_risks || findings.slice(0, 5)).forEach((f, i) =>
    fbox.append(el("div", { className: "finding " + f.severity }, el("span", { className: "tag", textContent: f.severity }),
      `${i + 1}. ${f.description}`)));

  const rbox = document.getElementById("recs");
  const grouped = fresh ? data.recommendations.grouped : null;
  if (grouped) {
    for (const [prio, items] of Object.entries(grouped)) {
      if (!items.length) continue;
      rbox.append(el("h3", { textContent: prio }));
      items.forEach((r) => rbox.append(el("div", { className: "finding" }, el("small", { textContent: r.category_label }), el("br"), r.recommendation)));
    }
    data.recommendations.awareness.forEach((a) => rbox.append(el("div", { className: "notice", textContent: `${a.label}: ${a.tip}` })));
  } else {
    const recs = await api(`/assessment/${encodeURIComponent(id)}/recommendations`);
    for (const [prio, items] of Object.entries(recs.grouped)) {
      if (!items.length) continue;
      rbox.append(el("h3", { textContent: prio }));
      items.forEach((r) => rbox.append(el("div", { className: "finding", textContent: r.recommendation })));
    }
  }

  // ---- improvement simulator (needs the answers, which exist only in this browser tab) ----
  const answers = JSON.parse(sessionStorage.getItem("pm_answers") || "null");
  const checks = document.getElementById("simchecks"), out = document.getElementById("simout");
  const simBtns = [document.getElementById("simrun"), document.getElementById("simall")];
  if (!answers || !fresh) {
    simBtns.forEach((b) => (b.disabled = true));
    checks.append(el("p", { className: "lead", textContent: "The simulator needs the answers from your current browser session (they are never stored on the server)." }));
  } else {
    findings.forEach((f) => checks.append(el("label", {}, el("input", { type: "checkbox", value: f.question_id }), " " + f.fix)));
    const run = async (body) => {
      const r = await api("/assessment/simulate-improvement", { method: "POST", body: { answers, ...body } });
      out.replaceChildren(
        el("div", {}, "Current", el("div", { className: "big c-" + LEVEL_CLASS[r.before.level], textContent: r.before.score }), r.before.level),
        el("div", { className: "big", textContent: "\u2192" }),
        el("div", {}, "Simulated", el("div", { className: "big c-" + LEVEL_CLASS[r.after.level], textContent: r.after.score }), r.after.level),
        el("div", {}, "Risk reduction", el("div", { className: "big c-low", textContent: r.risk_reduction + " pts" })),
        el("p", { className: "lead", textContent: r.disclaimer }));
    };
    document.getElementById("simrun").addEventListener("click", () => {
      const ids = [...checks.querySelectorAll("input:checked")].map((i) => i.value);
      if (ids.length) run({ fix_ids: ids }); else out.textContent = "Select at least one fix.";
    });
    document.getElementById("simall").addEventListener("click", () => { checks.querySelectorAll("input").forEach((i) => (i.checked = true)); run({ apply: "all" }); });
  }

  const report = document.getElementById("report");
  report.href = `/api/assessment/${encodeURIComponent(id)}/report`;
  document.getElementById("delete").addEventListener("click", async () => {
    const token = sessionStorage.getItem("pm_delete_" + id);
    const msg = document.getElementById("deleteMsg");
    if (!token) { msg.textContent = "The delete token is only available in the browser session that created this result."; return; }
    try {
      await api("/assessment/" + encodeURIComponent(id), { method: "DELETE", headers: { "X-Delete-Token": token } });
      ["pm_answers", "pm_result_" + id, "pm_delete_" + id].forEach((k) => sessionStorage.removeItem(k));
      msg.textContent = "Deleted from the server. The printable report link no longer works.";
    } catch (e) { msg.textContent = e.message; }
  });
})();
