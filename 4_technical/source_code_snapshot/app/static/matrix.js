const year = new Date().getFullYear();

function getLevel(value) {
  if (!value || value === 0) return 0;
  if (value < 1) return 1;
  if (value < 3) return 2;
  if (value < 6) return 3;
  return 4;
}

async function buildMatrix() {
  const res = await fetch("/get_yearly_savings");
  const data = await res.json();
  const savings = data.savings || {};

  const matrix = document.getElementById("matrix");
  const months = document.getElementById("months");

  const start = new Date(`${year}-01-01`);
  const end = new Date(`${year}-12-31`);

  while (start.getDay() !== 1) start.setDate(start.getDate() - 1);

  let currentMonth = -1;
  let column = 0;

  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const day = document.createElement("div");
    day.className = "day";

    const dateKey = d.toISOString().split("T")[0];
    const saving = savings[dateKey] || 0;
    const level = getLevel(saving);

    if (level > 0) day.dataset.level = level;

    day.title = `${d.toDateString()} — ${
      saving ? saving.toFixed(2) + " kg CO₂e saved" : "No activity"
    }`;

    matrix.appendChild(day);

    if (d.getFullYear() === year && d.getMonth() !== currentMonth) {
      currentMonth = d.getMonth();
      const label = document.createElement("div");
      label.style.gridColumn = column + 1;
      label.textContent = d.toLocaleString("default", { month: "short" });
      months.appendChild(label);
    }

    if (d.getDay() === 0) column++;
  }
}

buildMatrix();
