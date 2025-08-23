
document.addEventListener('DOMContentLoaded', () => {
    const rawData = JSON.parse("{{ df_output_json|escapejs }}");
    const container = document.getElementById("plots-container");

    // --- Preprocess Data ---
    const firstRow = rawData[0];
    const timeKeys = Object.keys(firstRow)
        .filter(k => /^\d+$/.test(k))
        .sort((a, b) => parseInt(a) - parseInt(b));

    const indicatorData = {};
    rawData.forEach(row => {
        indicatorData[row.indicator_label] = {
            row,
            x: timeKeys.map(k => parseInt(k)),
            y: timeKeys.map(k => row[k]),
            goal: Array(timeKeys.length).fill(row.goal)
        };
    });

    const allIndicators = Object.keys(indicatorData);
    const selectEl = document.getElementById('indicator-select');

    // --- Helpers ---
    function makePlotWrapper(id) {
        const plotWrapper = document.createElement('div');
        plotWrapper.className = 'col-span-1 md:col-span-2 bg-white shadow-lg rounded-xl p-6 h-[600px]';
        const plotDiv = document.createElement('div');
        plotDiv.id = id;
        plotDiv.style.height = '100%';
        plotWrapper.appendChild(plotDiv);
        container.appendChild(plotWrapper);
        return plotDiv;
    }

    // --- Plots ---
    function renderPlots(selectedIndicators) {
        container.innerHTML = '';

        if (selectedIndicators.length === 1) {
            const label = selectedIndicators[0];
            const dataObj = indicatorData[label];
            const plotDiv = makePlotWrapper(`plot-${label.replace(/[^a-zA-Z0-9-_]/g,'')}`);

            // Add SDG badge
            const badge = document.createElement('span');
            badge.className = 'inline-block px-3 py-1 text-xs font-semibold text-white rounded-full mb-2';
            badge.style.backgroundColor = dataObj.row.color;
            badge.textContent = 'SDG ' + dataObj.row.sdg;
            plotDiv.parentNode.insertBefore(badge, plotDiv);

            Plotly.newPlot(plotDiv, [
                { x: dataObj.x, y: dataObj.y, mode: 'lines+markers', name: label, line: { color: dataObj.row.color, width: 3 } },
                { x: dataObj.x, y: dataObj.goal, mode: 'lines', name: 'Goal', line: { color: '#000', width: 2, dash: 'dash' } }
            ], {
                title: `Indicator: ${label}`,
                xaxis: { title: 'Time' },
                yaxis: { title: 'Indicator Level' },
                legend: { orientation: 'h', y: -0.2 }
            }, { responsive: true });

        } else {
            const plotDiv = makePlotWrapper('combined-plot');
            const traces = selectedIndicators.flatMap(label => {
                const d = indicatorData[label];
                return [
                    { x: d.x, y: d.y, mode: 'lines+markers', name: label, line: { color: d.row.color, width: 3 } },
                    { x: d.x, y: d.goal, mode: 'lines', name: `${label} Goal`, line: { color: d.row.color, width: 2, dash: 'dot' } }
                ];
            });

            Plotly.newPlot(plotDiv, traces, {
                title: 'Selected Indicators Comparison',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Indicator Level' },
                legend: { orientation: 'h', y: -0.2 }
            }, { responsive: true });
        }
    }

    // --- Table ---
    function renderTable(selectedIndicators) {
        const thead = document.getElementById('table-head');
        const tbody = document.getElementById('table-body');
        thead.innerHTML = '';
        tbody.innerHTML = '';

        let html = '';
        if (selectedIndicators.length === allIndicators.length) {
            const headerRow = ['Time', ...allIndicators];
            thead.innerHTML = `<tr class="bg-gray-100">${headerRow.map(h => `<th class="px-6 py-3">${h}</th>`).join('')}</tr>`;

            indicatorData[allIndicators[0]].x.forEach((t, idx) => {
                html += `<tr class="bg-white border-b hover:bg-gray-50"><td class="px-6 py-4 font-medium">${t}</td>` +
                        allIndicators.map(label => {
                            const { y, row } = indicatorData[label];
                            return `<td class="px-6 py-4" style="background:${row.color};color:white;" title="SDG ${row.sdg}: ${y[idx].toFixed(4)}">${y[idx].toFixed(4)}</td>`;
                        }).join('') + `</tr>`;
            });
        } else if (selectedIndicators.length > 1) {
            const headerRow = ['Time', ...selectedIndicators.flatMap(l => [`${l} Value`, `${l} Goal`])];
            thead.innerHTML = `<tr class="bg-gray-100">${headerRow.map(h => `<th class="px-6 py-3">${h}</th>`).join('')}</tr>`;

            indicatorData[selectedIndicators[0]].x.forEach((t, idx) => {
                html += `<tr class="bg-white border-b hover:bg-gray-50"><td class="px-6 py-4 font-medium">${t}</td>` +
                        selectedIndicators.map(label => {
                            const { y, goal, row } = indicatorData[label];
                            return `<td class="px-6 py-4" style="background:${row.color};color:white;" title="SDG ${row.sdg}: ${y[idx].toFixed(4)}">${y[idx].toFixed(4)}</td>` +
                                   `<td class="px-6 py-4" title="Goal: ${goal[idx].toFixed(4)}">${goal[idx].toFixed(4)}</td>`;
                        }).join('') + `</tr>`;
            });
        } else {
            const label = selectedIndicators[0];
            const { x, y, goal, row } = indicatorData[label];
            thead.innerHTML = `<tr class="bg-gray-100"><th class="px-6 py-3">Time</th><th class="px-6 py-3">Value</th><th class="px-6 py-3">Goal</th></tr>`;
            x.forEach((t, idx) => {
                html += `<tr class="bg-white border-b hover:bg-gray-50">
                    <td class="px-6 py-4 font-medium">${t}</td>
                    <td class="px-6 py-4" style="background:${row.color};color:white;" title="SDG ${row.sdg}: ${y[idx].toFixed(4)}">${y[idx].toFixed(4)}</td>
                    <td class="px-6 py-4" title="Goal: ${goal[idx].toFixed(4)}">${goal[idx].toFixed(4)}</td>
                </tr>`;
            });
        }
        tbody.innerHTML = html;
    }

    // --- Initial render ---
    renderPlots(allIndicators);
    renderTable(allIndicators);

    // Dropdown
    selectEl.addEventListener('change', () => {
        const val = selectEl.value;
        if (val === 'all') {
            renderPlots(allIndicators);
            renderTable(allIndicators);
        } else {
            renderPlots([val]);
            renderTable([val]);
        }
    });

    // Compare Modal
    document.getElementById('compare-submit').addEventListener('click', () => {
        const checked = [...document.querySelectorAll('.compare-checkbox:checked')].map(c => c.value);
        if (checked.length > 0) {
            renderPlots(checked);
            renderTable(checked);
            document.getElementById('compareModal').classList.add('hidden');
        }
    });
});
