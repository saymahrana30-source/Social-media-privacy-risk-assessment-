// Shared helpers. NOTE: all user-visible text is inserted with textContent (never innerHTML) -> no XSS.
const NAV = [["index.html", "Home"], ["learn.html", "Learn"], ["assessment.html", "Assessment"],
             ["dashboard.html", "Dashboard"], ["checklist.html", "Checklist"]];

function renderNav() {
  const header = document.createElement("header");
  header.className = "nav";
  const brand = document.createElement("div");
  brand.className = "brand";
  brand.append("Privacy", Object.assign(document.createElement("span"), { textContent: "Shield" }), " Risk Framework");
  header.append(brand);
  const here = location.pathname.split("/").pop() || "index.html";
  for (const [href, label] of NAV) {
    const a = document.createElement("a");
    a.href = "/" + href; a.textContent = label;
    if (here === href) a.className = "active";
    header.append(a);
  }
  document.body.prepend(header);
  const footer = document.createElement("footer");
  footer.className = "site";
  footer.textContent = "Defensive cybersecurity & privacy education. Uses synthetic or voluntarily provided answers only - " +
    "it does not scrape, track or profile real social-media users. Educational model, not a guarantee of safety.";
  document.body.append(footer);
}

async function api(path, options = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" }, ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data.details && data.details.join("; ")) || data.error || res.statusText);
  return data;
}

const LEVEL_CLASS = { LOW: "low", MODERATE: "moderate", HIGH: "high", CRITICAL: "critical" };
const LEVEL_COLOR = { LOW: "#2fd47a", MODERATE: "#f4c542", HIGH: "#ff8a3d", CRITICAL: "#ff4d5e" };
function levelOf(score) { const s = Math.round(score); return s <= 20 ? "LOW" : s <= 40 ? "MODERATE" : s <= 70 ? "HIGH" : "CRITICAL"; }

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function renderBars(container, scores, labels) {
  container.replaceChildren();
  for (const [key, score] of Object.entries(scores)) {
    const fill = el("div", { className: "fill" });
    fill.style.width = score + "%"; fill.style.background = LEVEL_COLOR[levelOf(score)];
    container.append(el("div", { className: "bar" }, el("span", { textContent: labels[key] }),
      el("div", { className: "track" }, fill), el("span", { textContent: Math.round(score) })));
  }
}

if (window.Chart) { Chart.defaults.color = "#93a1ba"; Chart.defaults.borderColor = "#263146"; }
document.addEventListener("DOMContentLoaded", renderNav);
