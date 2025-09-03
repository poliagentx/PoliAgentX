document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById("plots-container");
    const selectEl = document.getElementById('indicator-select');
    const compareModal = document.getElementById('compareModal');
    const numStepsInput = document.getElementById('num-steps');
    const updateStepsBtn = document.getElementById('update-steps');

    // Prepare indicator data
    const indicatorData = {};
    rawData.forEach(row => {
        const timeKeys = Object.keys(row).filter(k => /^\d+$/.test(k)).map(k => parseInt(k)).sort((a,b)=>a-b);
        indicatorData[row.indicator_label] = {
            row,
            x: timeKeys,
            y: timeKeys.map(k => row[k]),
            goal: timeKeys.map(() => row.goal),
            budget: row.budget || []
        };
    });

    const allIndicators = Object.keys(indicatorData);

    // Render dashboard
    function renderDashboard(selectedLabels) {
        const dashboard = document.getElementById("indicator-dashboard");
        const container = document.getElementById("dashboard-content");
        container.innerHTML = "";

        if (!selectedLabels || selectedLabels.length !== 1) {
            // Summary for multiple/all indicators
            const summary = document.createElement("p");
            summary.innerText = `Displaying ${selectedLabels.length} indicators`;
            container.appendChild(summary);
            dashboard.classList.remove("hidden");
            return;
        }

        const label = selectedLabels[0];
        const dataObj = indicatorData[label];
        const first = dataObj.y[0];
        const last = dataObj.y[dataObj.y.length-1];
        const growth = (((last - first)/first)*100).toFixed(2);

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

        dashboard.classList.remove("hidden");
    }

    // Render plots
// Fixed plot rendering with proper sizing

    function renderPlots(selectedLabels) {
        container.innerHTML = "";
        if (!selectedLabels || selectedLabels.length === 0) return;

        if (selectedLabels.length === 1) {
            // Single indicator: indicator + budget
            const label = selectedLabels[0];
            const dataObj = indicatorData[label];

            // Indicator plot - Fixed height and responsive settings
            const plotDiv = document.createElement("div");
            plotDiv.className = "bg-white shadow-lg rounded-xl p-6 mb-6";
            plotDiv.style.height = "500px"; // Fixed height instead of Tailwind class
            plotDiv.style.minHeight = "400px"; // Minimum height
            container.appendChild(plotDiv);

            const plotlyConfig = {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                displaylogo: false
            };

            const plotlyLayout = {
                title: {
                    text: `Indicator: ${label}`,
                    font: { size: 18, weight: 'bold' }
                },
                xaxis: {
                    title: 'Time Steps',
                    showgrid: true,
                    gridcolor: '#f3f4f6'
                },
                yaxis: {
                    title: 'Value',
                    showgrid: true,
                    gridcolor: '#f3f4f6'
                },
                margin: {
                    l: 60,
                    r: 40,
                    t: 80,
                    b: 60
                },
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                autosize: true
            };

            Plotly.newPlot(plotDiv, [
                { 
                    x: dataObj.x, 
                    y: dataObj.y, 
                    mode: 'lines+markers', 
                    name: label, 
                    line: { color: dataObj.row.color, width: 3 },
                    marker: { size: 6 }
                },
                { 
                    x: dataObj.x, 
                    y: dataObj.goal, 
                    mode: 'lines', 
                    name: 'Goal', 
                    line: { color: '#000', dash: 'dash', width: 2 }
                }
            ], plotlyLayout, plotlyConfig);

            // Budget plot - Fixed height
            if (dataObj.budget && dataObj.budget.length > 0) {
                const budgetDiv = document.createElement("div");
                budgetDiv.className = "bg-white shadow-lg rounded-xl p-6 mb-6";
                budgetDiv.style.height = "300px"; // Fixed height
                budgetDiv.style.minHeight = "250px"; // Minimum height
                container.appendChild(budgetDiv);

                const budgetLayout = {
                    title: {
                        text: `Budget: ${label}`,
                        font: { size: 16, weight: 'bold' }
                    },
                    xaxis: {
                        title: 'Budget Value',
                        showgrid: true,
                        gridcolor: '#f3f4f6'
                    },
                    yaxis: {
                        title: 'Steps',
                        showgrid: false
                    },
                    margin: {
                        l: 100,  // More space for y-axis labels
                        r: 40,
                        t: 80,
                        b: 60
                    },
                    plot_bgcolor: 'white',
                    paper_bgcolor: 'white',
                    autosize: true
                };

                Plotly.newPlot(budgetDiv, [{
                    x: dataObj.budget,
                    y: dataObj.budget.map((_, i) => `Step ${i + 1}`),
                    type: 'bar',
                    orientation: 'h',
                    marker: { color: '#3b82f6' }
                }], budgetLayout, plotlyConfig);
            }

        } else {
            // Multiple indicators: combined plot
            const combinedDiv = document.createElement("div");
            combinedDiv.className = "bg-white shadow-lg rounded-xl p-6 mb-6";
            combinedDiv.style.height = "600px"; // Fixed height for multiple indicators
            combinedDiv.style.minHeight = "500px"; // Minimum height
            container.appendChild(combinedDiv);

            const traces = selectedLabels.map(label => {
                const dataObj = indicatorData[label];
                return { 
                    x: dataObj.x, 
                    y: dataObj.y, 
                    mode: 'lines+markers', 
                    name: label, 
                    line: { color: dataObj.row.color, width: 3 },
                    marker: { size: 6 }
                };
            });

            const combinedLayout = {
                title: {
                    text: "Selected Indicators",
                    font: { size: 18, weight: 'bold' }
                },
                xaxis: {
                    title: 'Time Steps',
                    showgrid: true,
                    gridcolor: '#f3f4f6'
                },
                yaxis: {
                    title: 'Value',
                    showgrid: true,
                    gridcolor: '#f3f4f6'
                },
                margin: {
                    l: 60,
                    r: 40,
                    t: 80,
                    b: 60
                },
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                autosize: true,
                legend: {
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "right",
                    x: 1
                }
            };

            const plotlyConfig = {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                displaylogo: false
            };

            Plotly.newPlot(combinedDiv, traces, combinedLayout, plotlyConfig);
        }

        // Dashboard & Table
        renderDashboard(selectedLabels);
        renderTable(selectedLabels, indicatorData);
    }

// Add window resize handler to ensure plots resize properly
window.addEventListener('resize', function() {
    // Find all plotly divs and trigger resize
    const plotDivs = document.querySelectorAll('[data-plotly-div]');
    plotDivs.forEach(div => {
        if (div._fullLayout) {
            Plotly.Plots.resize(div);
        }
    });
});

// Alternative function for responsive plot creation
function createResponsivePlot(container, data, layout, config) {
    return Plotly.newPlot(container, data, layout, config).then(function() {
        // Ensure the plot resizes when the window resizes
        window.addEventListener('resize', function() {
            Plotly.Plots.resize(container);
        });
    });
}


    // Render table
    function renderTable(selectedLabels, indicatorData) {
        const thead = document.getElementById('table-head');
        const tbody = document.getElementById('table-body');
        thead.innerHTML = "";
        tbody.innerHTML = "";

        if (!selectedLabels || selectedLabels.length === 0) return;

        let headerHtml = `<tr><th>Time</th>`;
        selectedLabels.forEach(label => {
            headerHtml += `<th>${label} Value</th><th>${label} Goal</th>`;
        });
        headerHtml += `</tr>`;
        thead.innerHTML = headerHtml;

        const maxLength = Math.max(...selectedLabels.map(l=>indicatorData[l].x.length));
        for (let t=0; t<maxLength; t++){
            let rowHtml = `<tr><td>${t}</td>`;
            selectedLabels.forEach(label=>{
                const val = indicatorData[label].y[t];
                const goal = indicatorData[label].goal[t];
                let color='';
                if(val!==undefined && goal!==undefined){
                    const ratio = val/goal;
                    if(ratio>=0.95) color='bg-green-200';
                    else if(ratio>=0.8) color='bg-yellow-200';
                    else color='bg-red-200';
                }
                rowHtml += `<td class="${color}">${val!==undefined?val.toFixed(2):'-'}</td>
                            <td>${goal!==undefined?goal.toFixed(2):'-'}</td>`;
            });
            rowHtml += "</tr>";
            tbody.innerHTML += rowHtml;
        }
    }

    // Initial render
    renderPlots(allIndicators);

    // Dropdown change
    selectEl.addEventListener('change', ()=>{
        if(selectEl.value==='all') renderPlots(allIndicators);
        else renderPlots([selectEl.value]);
    });

    // Compare modal
    document.getElementById('compare-button').addEventListener('click',()=>compareModal.classList.remove('hidden'));
    document.getElementById('compare-cancel').addEventListener('click',()=>compareModal.classList.add('hidden'));
    document.getElementById('compare-submit').addEventListener('click',()=>{
        const checked = Array.from(document.querySelectorAll('.compare-checkbox:checked')).map(c=>c.value);
        if(checked.length>0) renderPlots(checked);
        compareModal.classList.add('hidden');
    });

    // Simulation steps update (local only)
    updateStepsBtn.addEventListener('click',()=>{
        const newSteps = parseInt(numStepsInput.value);
        if(!isNaN(newSteps) && newSteps>0){
            console.log("Simulation steps updated to", newSteps);
            // Optional: trigger backend recalculation via POST
        }
    });
});