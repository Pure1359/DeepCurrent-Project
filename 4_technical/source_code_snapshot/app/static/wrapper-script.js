// This script fetches category statistics from the server and renders a donut chart along with a legend.
async function fetchData() {
  try {
    const res = await fetch("/user_access/get_category_stats", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(`HTTP error: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error("Failed to fetch category stats:", error);
    return [];
  }
}
//-----------------------------------------------

const cx = 200,
  cy = 200,
  R = 180,
  r = 126,
  gap = 0.025;
const ns = "http://www.w3.org/2000/svg";

function polar(cx, cy, radius, angle) {
  return [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)];
}

function arcPath(cx, cy, R, r, startAngle, endAngle) {
  const [x1, y1] = polar(cx, cy, R, startAngle);
  const [x2, y2] = polar(cx, cy, R, endAngle);
  const [x3, y3] = polar(cx, cy, r, endAngle);
  const [x4, y4] = polar(cx, cy, r, startAngle);
  const large = endAngle - startAngle > Math.PI ? 1 : 0;
  return `M ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2} L ${x3} ${y3} A ${r} ${r} 0 ${large} 0 ${x4} ${y4} Z`;
}

function buildLegend(cats) {
  const legend = document.getElementById("legend");
  legend.innerHTML = "";
  cats.forEach((cat) => {
    const item = document.createElement("span");
    item.className = "legend-item";
    item.innerHTML = `
      <span class="legend-dot" style="background:${cat.color};"></span>
      <span class="cat-label">${cat.label}</span>
    `;
    legend.appendChild(item);
  });
}

function drawChart(cats) {
  const svg = document.getElementById("donut");
  svg.innerHTML = "";

  const total = cats.reduce((s, c) => s + c.pct, 0);
  let start = -Math.PI / 2;

  cats.forEach((cat) => {
    if (cat.pct <= 0) return;

    const sweep = (cat.pct / total) * 2 * Math.PI - gap;
    const end = start + sweep;
    const mid = start + sweep / 2;

    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", arcPath(cx, cy, R, r, start, end));
    path.setAttribute("fill", cat.color);
    svg.appendChild(path);

    // Label sits in the middle of the arc thickness
    const labelRadius = (R + r) / 2;
    const [lx, ly] = polar(cx, cy, labelRadius, mid);

    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", lx);
    text.setAttribute("y", ly);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "middle");
    text.setAttribute("font-size", "11");
    text.setAttribute("font-weight", "600");
    text.setAttribute("fill", "#fff");
    text.textContent = cat.pct + "%";
    svg.appendChild(text);

    start = end + gap;
  });

  // Center total
  const centerLabel = document.createElementNS(ns, "text");
  centerLabel.setAttribute("x", cx);
  centerLabel.setAttribute("y", cy - 8);
  centerLabel.setAttribute("text-anchor", "middle");
  centerLabel.setAttribute("font-size", "22");
  centerLabel.setAttribute("font-weight", "500");
  centerLabel.setAttribute("fill", "#111");
  centerLabel.textContent = total + "%";
  svg.appendChild(centerLabel);

  const centerSub = document.createElementNS(ns, "text");
  centerSub.setAttribute("x", cx);
  centerSub.setAttribute("y", cy + 14);
  centerSub.setAttribute("text-anchor", "middle");
  centerSub.setAttribute("font-size", "12");
  centerSub.setAttribute("fill", "#888");
  centerSub.textContent = "Total";
  svg.appendChild(centerSub);
}

// Initialize the chart by fetching data and rendering the legend and chart
async function init() {
  const data = await fetchData();
  buildLegend(data);
  drawChart(data);
}

init();
