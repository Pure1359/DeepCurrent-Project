const year = 2025;

const start = new Date(`${year}-01-01`);
const end = new Date(`${year}-12-31`);

while (start.getDay() !== 1) start.setDate(start.getDate() - 1);

let currentMonth = -1;
let column = 0;

for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
  const day = document.createElement("div");
  day.className = "day";

  const level = Math.floor(Math.random() * 5);
  if (level > 0) day.dataset.level = level;

  day.title = d.toDateString();

  matrix.appendChild(day);

  // 👉 Only label months when inside the target year
  if (d.getFullYear() === year && d.getMonth() !== currentMonth) {
    currentMonth = d.getMonth();

    const label = document.createElement("div");
    label.style.gridColumn = column + 1;
    label.textContent = d.toLocaleString("default", { month: "short" });

    months.appendChild(label);
  }

  if (d.getDay() === 0) column++;
}
