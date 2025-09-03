// Improved dashboard.js with better layout and error handling

function renderDashboard(label, dataObj) {
    const dashboard = document.getElementById("indicator-dashboard");
    const container = document.getElementById("dashboard-content");
    
    if (!container) {
        console.error("Dashboard content container not found");
        return;
    }

    container.innerHTML = "";

    if (!label || !dataObj) {
        dashboard.classList.add("hidden");
        return;
    }

    dashboard.classList.remove("hidden");

    // Safe calculations with error handling
    const first = dataObj.y[0];
    const last = dataObj.y[dataObj.y.length - 1];
    const growth = first !== 0 ? (((last - first) / first) * 100).toFixed(2) : 'N/A';
    const maxValue = Math.max(...dataObj.y).toFixed(2);
    const minValue = Math.min(...dataObj.y).toFixed(2);

    const cards = [
        { title: "Indicator", value: label, icon: "📊" },
        { title: "Initial Value", value: first.toFixed(2), icon: "🎯" },
        { title: "Final Value", value: last.toFixed(2), icon: "📈" },
        { title: "Growth Rate", value: `${growth}%`, icon: "📊" },
        { title: "Max Value", value: maxValue, icon: "⬆️" },
        { title: "Min Value", value: minValue, icon: "⬇️" }
    ];

    // Create a responsive grid layout
    container.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4";

    cards.forEach(c => {
        const div = document.createElement("div");
        div.className = "p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow";
        div.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">${c.title}</p>
                    <p class="text-2xl font-bold text-gray-900 mt-1">${c.value}</p>
                </div>
                <div class="text-2xl opacity-50">${c.icon}</div>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderTable(selectedIndicators, indicatorData) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    
    if (!thead || !tbody) {
        console.error("Table elements not found");
        return;
    }

    thead.innerHTML = '';
    tbody.innerHTML = '';

    if (!selectedIndicators || selectedIndicators.length === 0) return;

    if (selectedIndicators.length === 1) {
        const label = selectedIndicators[0];
        const dataObj = indicatorData[label];
        
        thead.innerHTML = `
            <tr class="bg-gray-50">
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Color</th>
            </tr>
        `;

        dataObj.x.forEach((t, idx) => {
            const value = dataObj.y[idx];
            const goal = dataObj.goal[idx];
            const progress = goal > 0 ? ((value / goal) * 100).toFixed(1) : 'N/A';
            const progressClass = progress !== 'N/A' ? 
                (parseFloat(progress) >= 100 ? 'text-green-600' : 
                 parseFloat(progress) >= 80 ? 'text-yellow-600' : 'text-red-600') : 'text-gray-500';

            tbody.innerHTML += `
                <tr class="bg-white border-b border-gray-200 hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${t}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" style="color:${dataObj.row.color}">${value.toFixed(2)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${goal.toFixed(2)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${progressClass}">${progress}%</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="w-4 h-4 rounded-full shadow-inner" style="background:${dataObj.row.color}"></div>
                    </td>
                </tr>
            `;
        });

        renderDashboard(label, dataObj);
    } else {
        // Multiple indicators: show first indicator in dashboard
        renderDashboard(selectedIndicators[0], indicatorData[selectedIndicators[0]]);
        
        thead.innerHTML = `
            <tr class="bg-gray-50">
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Indicator</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Color</th>
            </tr>
        `;

        selectedIndicators.forEach(label => {
            const dataObj = indicatorData[label];
            dataObj.x.forEach((t, idx) => {
                const value = dataObj.y[idx];
                const goal = dataObj.goal[idx];
                const progress = goal > 0 ? ((value / goal) * 100).toFixed(1) : 'N/A';
                const progressClass = progress !== 'N/A' ? 
                    (parseFloat(progress) >= 100 ? 'text-green-600' : 
                     parseFloat(progress) >= 80 ? 'text-yellow-600' : 'text-red-600') : 'text-gray-500';

                tbody.innerHTML += `
                    <tr class="bg-white border-b border-gray-200 hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${t}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${label}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" style="color:${dataObj.row.color}">${value.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${goal.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${progressClass}">${progress}%</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="w-4 h-4 rounded-full shadow-inner" style="background:${dataObj.row.color}"></div>
                        </td>
                    </tr>
                `;
            });
        });
    }
}

// Additional utility function for better data visualization
function getPerformanceColor(value, goal) {
    if (!goal || goal === 0) return '#6b7280'; // gray for no goal
    const ratio = value / goal;
    if (ratio >= 1) return '#10b981'; // green for achieved
    if (ratio >= 0.8) return '#f59e0b'; // amber for close
    return '#ef4444'; // red for far from goal
}

// Export functions if using modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderDashboard, renderTable, getPerformanceColor };
}