
document.addEventListener('DOMContentLoaded', () => {
    const rawData = JSON.parse("{{ df_output_json|escapejs }}");
    const container = document.getElementById("plots-container");

    // Prepare structured data
    const indicatorData = {};
    rawData.forEach(row => {
        const timeKeys = Object.keys(row)
            .filter(k => /^\d+$/.test(k))
            .sort((a, b) => parseInt(a) - parseInt(b));
        indicatorData[row.indicator_label] = {
            row: row,
            x: timeKeys.map(k => parseInt(k)),
            y: timeKeys.map(k => row[k]),
            goal: Array(timeKeys.length).fill(row.goal)
        };
    });

    const allIndicators = Object.keys(indicatorData);
    const selectEl = document.getElementById('indicator-select');

    // Render plots
    function renderPlots(selectedIndicators) {
        container.innerHTML = '';
        if(selectedIndicators.length === allIndicators.length) {
            const combinedX = indicatorData[allIndicators[0]].x;
            const combinedY = combinedX.map((_, t) => allIndicators.reduce((sum, label) => sum + indicatorData[label].y[t], 0));
            const combinedGoals = combinedX.map((_, t) => allIndicators.reduce((sum, label) => sum + indicatorData[label].goal[t], 0));

            const plotWrapper = document.createElement('div');
            plotWrapper.className = 'col-span-1 md:col-span-2 bg-white shadow-lg rounded-xl p-6';
            const plotDiv = document.createElement('div');
            plotDiv.id = `plot-all`;
            plotDiv.style.height = '500px';
            plotWrapper.appendChild(plotDiv);
            container.appendChild(plotWrapper);

            Plotly.newPlot(plotDiv, [
                {x: combinedX, y: combinedY, mode: 'lines+markers', name: 'Combined Indicators', line: { color: '#1f77b4', width: 3 }},
                {x: combinedX, y: combinedGoals, mode: 'lines', name: 'Combined Goals', line: { color: '#000', width: 2, dash: 'dash' }}
            ], {title: 'All Indicators Combined', xaxis:{title:'Time'}, yaxis:{title:'Level'}, legend:{orientation:'h',y:-0.2}}, {responsive:true});
        } else {
            selectedIndicators.forEach(label => {
                const dataObj = indicatorData[label];
                const plotWrapper = document.createElement('div');
                plotWrapper.className = 'bg-white shadow-lg rounded-xl p-6';
                const badge = document.createElement('span');
                badge.className = 'inline-block px-3 py-1 text-xs font-semibold text-white rounded-full mb-2';
                badge.style.backgroundColor = dataObj.row.color;
                badge.textContent = 'SDG ' + dataObj.row.sdg;
                plotWrapper.appendChild(badge);

                const plotDiv = document.createElement('div');
                plotDiv.id = `plot-${label.replace(/[^a-zA-Z0-9-_]/g,'')}`;
                plotDiv.style.height = '400px';
                plotWrapper.appendChild(plotDiv);
                container.appendChild(plotWrapper);

                Plotly.newPlot(plotDiv, [
                    {x: dataObj.x, y: dataObj.y, mode:'lines+markers', name: label, line:{color:dataObj.row.color,width:3}},
                    {x: dataObj.x, y: dataObj.goal, mode:'lines', name:'Goal', line:{color:'#000', width:2,dash:'dash'}}
                ], {title:`Indicator: ${label}`, xaxis:{title:'Time'}, yaxis:{title:'Level'}, legend:{orientation:'h',y:-0.2}}, {responsive:true});
            });
        }
    }

    // Render table with SDG color-coding and tooltips
    function renderTable(selectedIndicators) {
        const thead = document.getElementById('table-head');
        const tbody = document.getElementById('table-body');
        thead.innerHTML = '';
        tbody.innerHTML = '';

        if(selectedIndicators.length === allIndicators.length) {
            const combinedX = indicatorData[allIndicators[0]].x;
            const headerRow = ['Time', ...allIndicators];
            thead.innerHTML = `<tr class="bg-gray-100">${headerRow.map(h => `<th scope="col" class="px-6 py-3">${h}</th>`).join('')}</tr>`;

            combinedX.forEach((t, idx) => {
                const row = [t, ...allIndicators.map(l => indicatorData[l].y[idx])];
                tbody.innerHTML += `<tr class="bg-white border-b hover:bg-gray-50">${row.map((v, colIdx) => {
                    if(colIdx===0) return `<td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${v}</td>`;
                    const label = allIndicators[colIdx-1];
                    const color = indicatorData[label].row.color;
                    const sdg = indicatorData[label].row.sdg;
                    return `<td class="px-6 py-4" style="background-color:${color};color:white;" title="SDG ${sdg}: ${v.toFixed(4)}">${v.toFixed(4)}</td>`;
                }).join('')}</tr>`;
            });
        } else if(selectedIndicators.length>1) {
            const firstX = indicatorData[selectedIndicators[0]].x;
            const headerRow = ['Time'];
            selectedIndicators.forEach(label => headerRow.push(`${label} Value`, `${label} Goal`));
            thead.innerHTML = `<tr class="bg-gray-100">${headerRow.map(h=>`<th scope="col" class="px-6 py-3">${h}</th>`).join('')}</tr>`;

            firstX.forEach((t, idx) => {
                const row = [t];
                selectedIndicators.forEach(label => {
                    const dataObj = indicatorData[label];
                    row.push({value:dataObj.y[idx], color:dataObj.row.color, sdg:dataObj.row.sdg}, dataObj.goal[idx]);
                });
                tbody.innerHTML += `<tr class="bg-white border-b hover:bg-gray-50">${row.map((cell, colIdx)=>{
                    if(colIdx===0) return `<td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${cell}</td>`;
                    if(typeof cell==='object') return `<td class="px-6 py-4" style="background-color:${cell.color};color:white;" title="SDG ${cell.sdg}: ${cell.value.toFixed(4)}">${cell.value.toFixed(4)}</td>`;
                    return `<td class="px-6 py-4" title="Goal: ${cell.toFixed(4)}">${cell.toFixed(4)}</td>`;
                }).join('')}</tr>`;
            });
        } else {
            const label = selectedIndicators[0];
            const dataObj = indicatorData[label];
            thead.innerHTML = `<tr class="bg-gray-100"><th scope="col" class="px-6 py-3">Time</th><th scope="col" class="px-6 py-3">Value</th><th scope="col" class="px-6 py-3">Goal</th></tr>`;
            dataObj.x.forEach((t, idx) => {
                const value = dataObj.y[idx];
                const goal = dataObj.goal[idx];
                const color = dataObj.row.color;
                const sdg = dataObj.row.sdg;
                tbody.innerHTML += `<tr class="bg-white border-b hover:bg-gray-50">
                    <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${t}</td>
                    <td class="px-6 py-4" style="background-color:${color};color:white;" title="SDG ${sdg}: ${value.toFixed(4)}">${value.toFixed(4)}</td>
                    <td class="px-6 py-4" title="Goal: ${goal.toFixed(4)}">${goal.toFixed(4)}</td>
                </tr>`;
            });
        }
    }

    // Initial render
    renderPlots(allIndicators);
    renderTable(allIndicators);

    // Dropdown change
    selectEl.addEventListener('change', () => {
        if(selectEl.value==='all'){
            renderPlots(allIndicators);
            renderTable(allIndicators);
        } else {
            renderPlots([selectEl.value]);
            renderTable([selectEl.value]);
        }
    });

    // Compare Modal Submit
    document.getElementById('compare-submit').addEventListener('click', () => {
        const checked = Array.from(document.querySelectorAll('.compare-checkbox:checked')).map(c=>c.value);
        if(checked.length>0){
            renderPlots(checked);
            renderTable(checked);
            // Hide the modal manually since Bootstrap JS is removed
            document.getElementById('compareModal').classList.add('hidden');
        }
    });
});
