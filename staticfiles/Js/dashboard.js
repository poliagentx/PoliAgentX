function renderDashboard(label, dataObj) {
    const dashboard = document.getElementById("indicator-dashboard");
    const container = document.getElementById("dashboard-content");
    container.innerHTML = "";

    if (!label || !dataObj) {
        dashboard.classList.add("hidden");
        return;
    }

    dashboard.classList.remove("hidden");

    const first = dataObj.y[0];
    const last = dataObj.y[dataObj.y.length - 1];
    const growth = (((last - first) / first) * 100).toFixed(2);

    const cards = [
        { title: "Indicator", value: label },
        { title: "Initial Value", value: first.toFixed(2) },
        { title: "Final Value", value: last.toFixed(2) },
        { title: "Growth Rate", value: `${growth}%` }
    ];

    cards.forEach(c => {
        const div = document.createElement("div");
        div.className = "p-4 bg-gray-100 rounded-lg shadow";
        div.innerHTML = `<p class="text-sm text-gray-600">${c.title}</p>
                         <p class="text-lg font-bold text-gray-900">${c.value}</p>`;
        container.appendChild(div);
    });
}

function renderTable(selectedIndicators, indicatorData) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    if (selectedIndicators.length === 0) return;

    if (selectedIndicators.length === 1) {
        const label = selectedIndicators[0];
        const dataObj = indicatorData[label];
        thead.innerHTML = `<tr><th>Time</th><th>Value</th><th>Goal</th></tr>`;
        dataObj.x.forEach((t, idx) => {
            tbody.innerHTML += `<tr><td>${t}</td><td>${dataObj.y[idx].toFixed(2)}</td><td>${dataObj.goal[idx].toFixed(2)}</td></tr>`;
        });
        renderDashboard(label, dataObj);
    } else {
        renderDashboard(null, null);
    }
}
