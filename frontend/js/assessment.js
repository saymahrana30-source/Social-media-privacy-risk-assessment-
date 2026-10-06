// Questionnaire UI. Answers live only in this tab (sessionStorage) and in the request to /api/assessment.
(async () => {
  const { categories, total_questions } = await api("/questionnaire");
  const answers = {};
  let step = 0;
  const label = (v) => v.replaceAll("_", " ");

  const section = document.getElementById("section"), stepper = document.getElementById("stepper");
  const bar = document.getElementById("bar"), err = document.getElementById("err");
  const next = document.getElementById("next"), prev = document.getElementById("prev");

  function counts(cat) { const n = cat.questions.filter((q) => answers[q.id]).length; return [n, cat.questions.length]; }

  function render() {
    stepper.replaceChildren();
    categories.forEach((cat, i) => {
      const [n, total] = counts(cat);
      const b = el("button", { type: "button", textContent: `${cat.letter}. ${cat.title}` });
      if (i === step) b.classList.add("active");
      if (n === total) b.classList.add("done");
      b.addEventListener("click", () => { step = i; render(); });
      stepper.append(b);
    });
    const cat = categories[step];
    section.replaceChildren(el("h3", { textContent: `Category ${cat.letter}: ${cat.title}` }));
    for (const q of cat.questions) {
      const opts = el("div", { className: "options", role: "radiogroup" });
      for (const o of q.options) {
        const input = el("input", { type: "radio", name: q.id, value: o, checked: answers[q.id] === o });
        input.addEventListener("change", () => { answers[q.id] = o; updateProgress(); markStepper(); });
        opts.append(el("label", {}, input, label(o)));
      }
      section.append(el("div", { className: "question" }, el("p", { textContent: q.text }), opts));
    }
    next.textContent = step === categories.length - 1 ? "Calculate my privacy risk" : "Next";
    prev.disabled = step === 0;
    updateProgress();
    err.textContent = "";
  }

  function markStepper() {
    [...stepper.children].forEach((b, i) => b.classList.toggle("done", counts(categories[i])[0] === counts(categories[i])[1]));
  }
  function updateProgress() {
    const n = Object.keys(answers).length;
    bar.style.width = (100 * n / total_questions) + "%";
    document.getElementById("count").textContent = `${n} / ${total_questions} answered`;
  }

  async function submit() {
    const missing = categories.flatMap((c) => c.questions).filter((q) => !answers[q.id]);
    if (missing.length) {
      const idx = categories.findIndex((c) => c.questions.some((q) => !answers[q.id]));
      step = idx; render();
      err.textContent = `Please answer all questions (${missing.length} remaining).`;
      return;
    }
    next.disabled = true;
    try {
      const result = await api("/assessment", { method: "POST", body: { answers } });
      sessionStorage.setItem("pm_answers", JSON.stringify(answers));            // for the simulator only
      sessionStorage.setItem("pm_delete_" + result.assessment_id, result.delete_token);
      sessionStorage.setItem("pm_result_" + result.assessment_id, JSON.stringify(result));
      location.href = "/results.html?id=" + encodeURIComponent(result.assessment_id);
    } catch (e) { err.textContent = e.message; next.disabled = false; }
  }

  next.addEventListener("click", () => (step < categories.length - 1 ? (step++, render(), window.scrollTo(0, 0)) : submit()));
  prev.addEventListener("click", () => { if (step > 0) { step--; render(); window.scrollTo(0, 0); } });
  document.getElementById("demo").addEventListener("click", async () => {
    const demo = await api("/demo-profile");
    Object.assign(answers, demo.answers);
    sessionStorage.setItem("pm_demo_fix", JSON.stringify(demo.fix_ids));
    render();
  });
  if (new URLSearchParams(location.search).get("demo")) document.getElementById("demo").click(); else render();
})();
