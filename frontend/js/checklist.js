(async () => {
  const { items } = await api("/privacy-checklist");
  const list = document.getElementById("list");
  items.forEach((text, i) => {
    const box = el("input", { type: "checkbox", id: "c" + i });
    list.append(el("li", {}, el("label", { htmlFor: "c" + i }, box, " " + text)));
  });
  document.getElementById("print").addEventListener("click", () => window.print());
})();
