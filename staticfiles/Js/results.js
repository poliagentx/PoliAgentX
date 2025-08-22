document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById("plots-container");

    // Prepare data
    const indicatorData = {};
    rawData.forEach(row => {
        const timeKeys = Object.keys(row).filter(k => /^\d+$/.test(k)).map(k => parseInt(k));
        indicatorData[row.indicator_label] = {
            row,
            x: timeKeys,
            y: timeKeys.map(k => row[k]),
            goal: timeKeys.map(() => row.goal)
        };
    });
    const allIndicators = Object.keys(indicatorData);
    const selectEl = document.getElementById('indicator-select');

    // Render plots
    function renderPlots(selectedIndicators) {
        container.innerHTML = '';
        if (selectedIndicators.length === 1) {
            const label = selectedIndicators[0];
            const dataObj = indicatorData[label];
            const div = document.createElement('div');
            div.className = "col-span-1 md:col-span-2 bg-white shadow-lg rounded-xl p-6 h-[600px]";
            div.id = `plot-${label}`;
            container.appendChild(div);
            Plotly.newPlot(div, [
                { x: dataObj.x, y: dataObj.y, mode: 'lines+markers', name: label, line: { color: dataObj.row.color, width: 3 } },
                { x: dataObj.x, y: dataObj.goal, mode: 'lines', name: 'Goal', line: { color: '#000', dash: 'dash' } }
            ]);
        } else {
            const div = document.createElement('div');
            div.className = "col-span-1 md:col-span-2 bg-white shadow-lg rounded-xl p-6 h-[600px]";
            div.id = "combined-plot";
            container.appendChild(div);

            const traces = [];
            selectedIndicators.forEach(label => {
                const dataObj = indicatorData[label];
                traces.push({ x: dataObj.x, y: dataObj.y, mode: 'lines+markers', name: label, line: { color: dataObj.row.color } });
            });
            Plotly.newPlot(div, traces, { title: "Selected Indicators" });
        }
        renderTable(selectedIndicators, indicatorData);
    }

    // Initial
    renderPlots(allIndicators);

    // Dropdown
    selectEl.addEventListener('change', () => {
        if (selectEl.value === 'all') renderPlots(allIndicators);
        else renderPlots([selectEl.value]);
    });

    // Compare
    document.getElementById('compare-submit').addEventListener('click', () => {
        const checked = Array.from(document.querySelectorAll('.compare-checkbox:checked')).map(c => c.value);
        if (checked.length > 0) renderPlots(checked);
        document.getElementById('compareModal').classList.add('hidden');
    });
});
