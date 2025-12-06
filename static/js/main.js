document.addEventListener('DOMContentLoaded', () => {
    // Flash Messages
    const alerts = document.querySelectorAll('.flash-message');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 3000);
    }

    // CHART LOGIC
    const chartCanvas = document.getElementById('searchChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        const isDark = document.documentElement.classList.contains('dark');
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? '#334155' : '#f1f5f9';

        // Check if we have the complex data object (Line Chart)
        if (chartCanvas.dataset.chart) {
            const chartData = JSON.parse(chartCanvas.dataset.chart);
            
            new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: { 
                        legend: { 
                            position: 'top',
                            labels: { color: textColor }
                        } 
                    },
                    scales: {
                        y: { 
                            beginAtZero: false,
                            grid: { color: gridColor },
                            ticks: { color: textColor }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: textColor }
                        }
                    }
                }
            });
        } 
        // Fallback for simple bar charts (if used elsewhere)
        else if (chartCanvas.dataset.labels) {
            const labels = JSON.parse(chartCanvas.dataset.labels);
            const prices = JSON.parse(chartCanvas.dataset.prices);
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Price',
                        data: prices,
                        backgroundColor: ['#ef4444', '#f97316', '#3b82f6'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: false } }
                }
            });
        }
    }
});