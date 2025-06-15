// Enhanced Dashboard JavaScript Functionality
// This file provides advanced interactivity and functionality for the municipal dashboard

class DashboardManager {
    constructor() {
        this.charts = {};
        this.filters = {
            period: '7',
            status: 'all',
            category: 'all',
            priority: 'all'
        };
        this.realTimeEnabled = false;
        this.notifications = [];
        this.shortcuts = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.setupKeyboardShortcuts();
        this.initializeRealTime();
        this.setupAdvancedFilters();
        this.initializeNotifications();
    }

    setupEventListeners() {
        // Advanced search functionality
        const searchInput = document.getElementById('dashboard-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Filter change handlers
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-filter]')) {
                this.handleFilterChange(e.target);
            }
        });

        // Chart interaction handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-chart-action]')) {
                this.handleChartAction(e.target);
            }
        });

        // Export handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-export]')) {
                this.handleExport(e.target.dataset.export);
            }
        });

        // Real-time toggle
        const realTimeToggle = document.getElementById('realtime-toggle');
        if (realTimeToggle) {
            realTimeToggle.addEventListener('change', this.toggleRealTime.bind(this));
        }
    }

    setupKeyboardShortcuts() {
        this.shortcuts = {
            'ctrl+r': () => this.refreshDashboard(),
            'ctrl+e': () => this.exportDashboard(),
            'ctrl+f': () => this.focusSearch(),
            'ctrl+1': () => this.switchView('overview'),
            'ctrl+2': () => this.switchView('problems'),
            'ctrl+3': () => this.switchView('complaints'),
            'ctrl+4': () => this.switchView('analytics'),
            'esc': () => this.closeModals(),
            'ctrl+shift+d': () => this.toggleDarkMode(),
            'ctrl+shift+n': () => this.createNewItem(),
            'ctrl+shift+s': () => this.openSettings()
        };

        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            if (this.shortcuts[key]) {
                e.preventDefault();
                this.shortcuts[key]();
            }
        });
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');
        if (e.metaKey) parts.push('meta');
        
        if (e.key !== 'Control' && e.key !== 'Shift' && e.key !== 'Alt' && e.key !== 'Meta') {
            parts.push(e.key.toLowerCase());
        }
        
        return parts.join('+');
    }

    initializeCharts() {
        this.initAdvancedTimeSeriesChart();
        this.initInteractiveStatusChart();
        this.initAnimatedCategoriesChart();
        this.initHeatmapChart();
        this.initGaugeCharts();
        this.initTrendAnalysisChart();
    }

    initAdvancedTimeSeriesChart() {
        const options = {
            series: [
                {
                    name: 'Problèmes',
                    type: 'area',
                    data: this.getTimeSeriesData('problems')
                },
                {
                    name: 'Réclamations',
                    type: 'line',
                    data: this.getTimeSeriesData('complaints')
                },
                {
                    name: 'Résolutions',
                    type: 'column',
                    data: this.getTimeSeriesData('resolutions')
                }
            ],
            chart: {
                height: 400,
                type: 'line',
                stacked: false,
                toolbar: {
                    show: true,
                    tools: {
                        download: true,
                        selection: true,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    }
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.handleDataPointClick(config);
                    },
                    legendClick: (chartContext, seriesIndex, config) => {
                        this.handleLegendClick(seriesIndex);
                    }
                }
            },
            colors: ['#ef4444', '#3b82f6', '#22c55e'],
            stroke: {
                width: [0, 3, 0],
                curve: 'smooth'
            },
            fill: {
                type: ['gradient', 'solid', 'solid'],
                gradient: {
                    shadeIntensity: 1,
                    type: 'vertical',
                    opacityFrom: 0.7,
                    opacityTo: 0.1,
                    stops: [0, 100]
                }
            },
            markers: {
                size: [0, 6, 0],
                hover: {
                    size: 8
                }
            },
            xaxis: {
                type: 'datetime',
                categories: this.getDateCategories(),
                labels: {
                    style: {
                        colors: '#64748b'
                    },
                    datetimeFormatter: {
                        year: 'yyyy',
                        month: 'MMM \'yy',
                        day: 'dd MMM',
                        hour: 'HH:mm'
                    }
                }
            },
            yaxis: [
                {
                    title: {
                        text: 'Signalements',
                        style: {
                            color: '#64748b'
                        }
                    },
                    labels: {
                        style: {
                            colors: '#64748b'
                        }
                    }
                },
                {
                    opposite: true,
                    title: {
                        text: 'Résolutions',
                        style: {
                            color: '#64748b'
                        }
                    },
                    labels: {
                        style: {
                            colors: '#64748b'
                        }
                    }
                }
            ],
            tooltip: {
                shared: true,
                intersect: false,
                theme: 'dark',
                custom: function({ series, seriesIndex, dataPointIndex, w }) {
                    return `
                        <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border">
                            <div class="font-semibold mb-2">${w.globals.categoryLabels[dataPointIndex]}</div>
                            ${series.map((s, i) => `
                                <div class="flex items-center space-x-2 mb-1">
                                    <div class="w-3 h-3 rounded-full" style="background-color: ${w.globals.colors[i]}"></div>
                                    <span class="text-sm">${w.globals.seriesNames[i]}: ${s[dataPointIndex]}</span>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            },
            legend: {
                position: 'top',
                horizontalAlign: 'left',
                offsetX: 40,
                labels: {
                    colors: '#64748b'
                },
                markers: {
                    width: 12,
                    height: 12,
                    radius: 6
                }
            },
            grid: {
                borderColor: '#e2e8f0',
                strokeDashArray: 5,
                xaxis: {
                    lines: {
                        show: true
                    }
                },
                yaxis: {
                    lines: {
                        show: true
                    }
                }
            }
        };

        this.charts.timeSeries = new ApexCharts(document.querySelector("#time-series-chart"), options);
        this.charts.timeSeries.render();
    }

    initInteractiveStatusChart() {
        const statusData = this.getStatusData();
        const options = {
            series: statusData.values,
            labels: statusData.labels,
            chart: {
                type: 'donut',
                height: 350,
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.filterByStatus(statusData.labels[config.dataPointIndex]);
                    }
                }
            },
            colors: ['#f59e0b', '#3b82f6', '#22c55e', '#ef4444', '#64748b', '#8b5cf6'],
            plotOptions: {
                pie: {
                    donut: {
                        size: '70%',
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: '16px',
                                fontWeight: 600,
                                color: '#374151'
                            },
                            value: {
                                show: true,
                                fontSize: '24px',
                                fontWeight: 700,
                                color: '#111827',
                                formatter: function (val) {
                                    return parseInt(val)
                                }
                            },
                            total: {
                                show: true,
                                showAlways: false,
                                label: 'Total',
                                fontSize: '16px',
                                fontWeight: 600,
                                color: '#374151',
                                formatter: function (w) {
                                    return w.globals.seriesTotals.reduce((a, b) => {
                                        return a + b
                                    }, 0)
                                }
                            }
                        }
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function (val, opts) {
                    return opts.w.config.series[opts.seriesIndex]
                },
                style: {
                    fontSize: '12px',
                    fontWeight: 600
                },
                dropShadow: {
                    enabled: false
                }
            },
            legend: {
                position: 'bottom',
                offsetY: 10,
                labels: {
                    colors: '#64748b'
                },
                markers: {
                    width: 12,
                    height: 12,
                    radius: 6
                }
            },
            tooltip: {
                theme: 'dark',
                y: {
                    formatter: function(val, opts) {
                        const total = opts.series.reduce((a, b) => a + b, 0);
                        const percentage = ((val / total) * 100).toFixed(1);
                        return `${val} (${percentage}%)`;
                    }
                }
            },
            responsive: [{
                breakpoint: 480,
                options: {
                    chart: {
                        height: 300
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }]
        };

        this.charts.status = new ApexCharts(document.querySelector("#status-chart"), options);
        this.charts.status.render();
    }

    initAnimatedCategoriesChart() {
        const categoriesData = this.getCategoriesData();
        const options = {
            series: [{
                name: 'Signalements',
                data: categoriesData.values
            }],
            chart: {
                type: 'bar',
                height: 350,
                toolbar: {
                    show: true
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    }
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.filterByCategory(categoriesData.labels[config.dataPointIndex]);
                    }
                }
            },
            colors: ['#3b82f6'],
            plotOptions: {
                bar: {
                    borderRadius: 8,
                    horizontal: true,
                    distributed: true,
                    dataLabels: {
                        position: 'top'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                offsetX: 10,
                style: {
                    fontSize: '12px',
                    colors: ['#fff']
                }
            },
            xaxis: {
                categories: categoriesData.labels,
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            yaxis: {
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            grid: {
                borderColor: '#e2e8f0',
                strokeDashArray: 5
            },
            tooltip: {
                theme: 'dark',
                y: {
                    formatter: function(val) {
                        return val + ' signalements';
                    }
                }
            }
        };

        this.charts.categories = new ApexCharts(document.querySelector("#categories-chart"), options);
        this.charts.categories.render();
    }

    initHeatmapChart() {
        const heatmapData = this.generateHeatmapData();
        const options = {
            series: heatmapData,
            chart: {
                height: 350,
                type: 'heatmap',
                toolbar: {
                    show: true
                }
            },
            colors: ['#3b82f6'],
            dataLabels: {
                enabled: false
            },
            xaxis: {
                type: 'category',
                categories: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            yaxis: {
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            title: {
                text: 'Activité par jour et heure',
                style: {
                    color: '#374151'
                }
            },
            tooltip: {
                theme: 'dark'
            }
        };

        if (document.querySelector("#heatmap-chart")) {
            this.charts.heatmap = new ApexCharts(document.querySelector("#heatmap-chart"), options);
            this.charts.heatmap.render();
        }
    }

    initGaugeCharts() {
        // Performance gauge
        const performanceOptions = {
            series: [75],
            chart: {
                height: 250,
                type: 'radialBar',
                toolbar: {
                    show: false
                }
            },
            plotOptions: {
                radialBar: {
                    startAngle: -135,
                    endAngle: 225,
                    hollow: {
                        margin: 0,
                        size: '70%',
                        background: 'transparent',
                        image: undefined,
                        position: 'front',
                        dropShadow: {
                            enabled: true,
                            top: 3,
                            left: 0,
                            blur: 4,
                            opacity: 0.24
                        }
                    },
                    track: {
                        background: '#e2e8f0',
                        strokeWidth: '67%',
                        margin: 0,
                        dropShadow: {
                            enabled: true,
                            top: -3,
                            left: 0,
                            blur: 4,
                            opacity: 0.35
                        }
                    },
                    dataLabels: {
                        show: true,
                        name: {
                            offsetY: -10,
                            show: true,
                            color: '#374151',
                            fontSize: '17px'
                        },
                        value: {
                            formatter: function(val) {
                                return parseInt(val) + '%';
                            },
                            color: '#111827',
                            fontSize: '36px',
                            show: true,
                        }
                    }
                }
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shade: 'dark',
                    type: 'horizontal',
                    shadeIntensity: 0.5,
                    gradientToColors: ['#22c55e'],
                    inverseColors: true,
                    opacityFrom: 1,
                    opacityTo: 1,
                    stops: [0, 100]
                }
            },
            stroke: {
                lineCap: 'round'
            },
            labels: ['Performance']
        };

        if (document.querySelector("#performance-gauge")) {
            this.charts.performance = new ApexCharts(document.querySelector("#performance-gauge"), performanceOptions);
            this.charts.performance.render();
        }
    }

    initTrendAnalysisChart() {
        const trendData = this.generateTrendData();
        const options = {
            series: [{
                name: 'Tendance',
                data: trendData
            }],
            chart: {
                type: 'line',
                height: 200,
                sparkline: {
                    enabled: true
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                }
            },
            stroke: {
                curve: 'smooth',
                width: 3
            },
            colors: ['#3b82f6'],
            tooltip: {
                theme: 'dark',
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        if (document.querySelector("#trend-chart")) {
            this.charts.trend = new ApexCharts(document.querySelector("#trend-chart"), options);
            this.charts.trend.render();
        }
    }

    setupAdvancedFilters() {
        // Date range picker
        this.initDateRangePicker();
        
        // Multi-select filters
        this.initMultiSelectFilters();
        
        // Advanced search with autocomplete
        this.initAdvancedSearch();
        
        // Saved filters
        this.initSavedFilters();
    }

    initDateRangePicker() {
        const dateRangeInput = document.getElementById('date-range-picker');
        if (dateRangeInput) {
            // Initialize date range picker (would use a library like Flatpickr in real implementation)
            dateRangeInput.addEventListener('change', (e) => {
                this.handleDateRangeChange(e.target.value);
            });
        }
    }

    initMultiSelectFilters() {
        const multiSelects = document.querySelectorAll('[data-multi-select]');
        multiSelects.forEach(select => {
            this.enhanceMultiSelect(select);
        });
    }

    enhanceMultiSelect(selectElement) {
        // Create custom multi-select dropdown
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        
        const button = document.createElement('button');
        button.className = 'form-input flex items-center justify-between w-full';
        button.innerHTML = `
            <span>Sélectionner...</span>
            <i class="fas fa-chevron-down"></i>
        `;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'absolute top-full left-0 right-0 bg-white dark:bg-secondary-800 border border-secondary-200 dark:border-secondary-700 rounded-lg shadow-lg z-50 hidden';
        
        // Add options
        const options = Array.from(selectElement.options);
        options.forEach(option => {
            const item = document.createElement('label');
            item.className = 'flex items-center space-x-2 p-3 hover:bg-secondary-50 dark:hover:bg-secondary-700 cursor-pointer';
            item.innerHTML = `
                <input type="checkbox" value="${option.value}" class="rounded">
                <span>${option.text}</span>
            `;
            dropdown.appendChild(item);
        });
        
        wrapper.appendChild(button);
        wrapper.appendChild(dropdown);
        
        selectElement.parentNode.replaceChild(wrapper, selectElement);
        
        // Handle interactions
        button.addEventListener('click', () => {
            dropdown.classList.toggle('hidden');
        });
        
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
    }

    initAdvancedSearch() {
        const searchInput = document.getElementById('advanced-search');
        if (searchInput) {
            // Add search suggestions
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'absolute top-full left-0 right-0 bg-white dark:bg-secondary-800 border border-secondary-200 dark:border-secondary-700 rounded-lg shadow-lg z-50 hidden';
            
            searchInput.parentNode.appendChild(suggestionsContainer);
            
            searchInput.addEventListener('input', this.debounce((e) => {
                this.showSearchSuggestions(e.target.value, suggestionsContainer);
            }, 300));
        }
    }

    showSearchSuggestions(query, container) {
        if (query.length < 2) {
            container.classList.add('hidden');
            return;
        }
        
        // Mock suggestions (would come from API in real implementation)
        const suggestions = [
            'Problème de voirie',
            'Éclairage public',
            'Collecte des déchets',
            'Réclamation administrative',
            'Problème d\'eau'
        ].filter(item => item.toLowerCase().includes(query.toLowerCase()));
        
        if (suggestions.length === 0) {
            container.classList.add('hidden');
            return;
        }
        
        container.innerHTML = suggestions.map(suggestion => `
            <div class="p-3 hover:bg-secondary-50 dark:hover:bg-secondary-700 cursor-pointer border-b border-secondary-100 dark:border-secondary-600 last:border-b-0">
                ${suggestion}
            </div>
        `).join('');
        
        container.classList.remove('hidden');
        
        // Handle suggestion clicks
        container.addEventListener('click', (e) => {
            if (e.target.matches('div')) {
                document.getElementById('advanced-search').value = e.target.textContent;
                container.classList.add('hidden');
                this.performSearch(e.target.textContent);
            }
        });
    }

    initSavedFilters() {
        const savedFilters = this.getSavedFilters();
        const container = document.getElementById('saved-filters');
        
        if (container && savedFilters.length > 0) {
            container.innerHTML = savedFilters.map(filter => `
                <button class="btn-secondary text-sm" data-filter-id="${filter.id}">
                    <i class="fas fa-filter mr-1"></i>
                    ${filter.name}
                </button>
            `).join('');
            
            container.addEventListener('click', (e) => {
                if (e.target.matches('[data-filter-id]')) {
                    this.applySavedFilter(e.target.dataset.filterId);
                }
            });
        }
    }

    initializeRealTime() {
        // WebSocket connection for real-time updates
        if (window.WebSocket) {
            this.setupWebSocket();
        }
        
        // Fallback polling
        this.setupPolling();
    }

    setupWebSocket() {
        try {
            this.ws = new WebSocket(`ws://${window.location.host}/ws/dashboard/`);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.realTimeEnabled = true;
                this.showNotification('Connexion temps réel établie', 'success');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.realTimeEnabled = false;
                this.showNotification('Connexion temps réel perdue', 'warning');
                
                // Attempt to reconnect
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showNotification('Erreur de connexion temps réel', 'error');
            };
        } catch (error) {
            console.error('WebSocket not supported:', error);
            this.setupPolling();
        }
    }

    setupPolling() {
        // Fallback polling every 30 seconds
        setInterval(() => {
            if (!this.realTimeEnabled) {
                this.fetchUpdates();
            }
        }, 30000);
    }

    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'new_problem':
                this.handleNewProblem(data.payload);
                break;
            case 'new_complaint':
                this.handleNewComplaint(data.payload);
                break;
            case 'status_update':
                this.handleStatusUpdate(data.payload);
                break;
            case 'metrics_update':
                this.handleMetricsUpdate(data.payload);
                break;
            default:
                console.log('Unknown update type:', data.type);
        }
    }

    handleNewProblem(problem) {
        // Update metrics
        this.updateMetricCard('total-problems', '+1');
        
        // Add to recent activities
        this.addRecentActivity({
            type: 'problem',
            text: `Nouveau problème: ${problem.description.substring(0, 50)}...`,
            timestamp: new Date(),
            status: problem.status
        });
        
        // Update charts
        this.updateChartData('problems', problem);
        
        // Show notification
        this.showNotification('Nouveau problème signalé', 'info');
        
        // Add to map if coordinates available
        if (problem.latitude && problem.longitude) {
            this.addMapMarker(problem);
        }
    }

    handleNewComplaint(complaint) {
        // Similar to handleNewProblem but for complaints
        this.updateMetricCard('total-complaints', '+1');
        this.addRecentActivity({
            type: 'complaint',
            text: `Nouvelle réclamation: ${complaint.subject}`,
            timestamp: new Date(),
            status: complaint.status
        });
        this.updateChartData('complaints', complaint);
        this.showNotification('Nouvelle réclamation reçue', 'info');
    }

    handleStatusUpdate(update) {
        // Update status charts
        this.updateStatusChart(update);
        
        // Update recent activities
        this.updateActivityStatus(update.id, update.new_status);
        
        // Show notification
        this.showNotification(`Statut mis à jour: ${update.new_status}`, 'success');
    }

    handleMetricsUpdate(metrics) {
        // Update all metric cards
        Object.keys(metrics).forEach(key => {
            this.updateMetricCard(key, metrics[key]);
        });
    }

    initializeNotifications() {
        // Create notification permission request
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Setup notification center
        this.setupNotificationCenter();
    }

    setupNotificationCenter() {
        const notificationButton = document.getElementById('notification-button');
        const notificationPanel = document.getElementById('notification-panel');
        
        if (notificationButton && notificationPanel) {
            notificationButton.addEventListener('click', () => {
                notificationPanel.classList.toggle('hidden');
                this.loadNotifications();
            });
            
            // Close panel when clicking outside
            document.addEventListener('click', (e) => {
                if (!notificationButton.contains(e.target) && !notificationPanel.contains(e.target)) {
                    notificationPanel.classList.add('hidden');
                }
            });
        }
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    showNotification(message, type = 'info', duration = 5000) {
        // Show in-app notification
        if (window.toastManager) {
            window.toastManager.show(message, type, duration);
        }
        
        // Show browser notification if permission granted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Belediyti Dashboard', {
                body: message,
                icon: '/static/img/favicon.ico',
                tag: 'dashboard-notification'
            });
        }
    }

    updateMetricCard(cardId, value) {
        const card = document.getElementById(cardId);
        if (card) {
            const valueElement = card.querySelector('.metric-value');
            if (valueElement) {
                if (typeof value === 'string' && value.startsWith('+')) {
                    const currentValue = parseInt(valueElement.textContent);
                    const increment = parseInt(value.substring(1));
                    valueElement.textContent = currentValue + increment;
                    
                    // Add animation
                    valueElement.classList.add('micro-bounce');
                    setTimeout(() => valueElement.classList.remove('micro-bounce'), 600);
                } else {
                    valueElement.textContent = value;
                }
            }
        }
    }

    addRecentActivity(activity) {
        const container = document.getElementById('recent-activities');
        if (container) {
            const activityElement = this.createActivityElement(activity);
            container.insertBefore(activityElement, container.firstChild);
            
            // Remove oldest if more than 10
            const activities = container.children;
            if (activities.length > 10) {
                container.removeChild(activities[activities.length - 1]);
            }
        }
    }

    createActivityElement(activity) {
        const element = document.createElement('div');
        element.className = 'activity-item p-4 rounded-xl border border-secondary-200 dark:border-secondary-700 animate-fade-in-down';
        
        const iconClass = activity.type === 'problem' ? 'fa-triangle-exclamation text-danger-600' : 'fa-file-signature text-info-600';
        const bgClass = activity.type === 'problem' ? 'bg-danger-100 dark:bg-danger-900/30' : 'bg-info-100 dark:bg-info-900/30';
        
        element.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 ${bgClass} rounded-full flex items-center justify-center">
                        <i class="fas ${iconClass} text-sm"></i>
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm text-secondary-900 dark:text-white font-medium">${activity.text}</p>
                    <div class="flex items-center space-x-2 mt-1">
                        <span class="status-badge status-${activity.status}">${activity.status}</span>
                        <span class="text-xs text-secondary-500">${this.formatTimeAgo(activity.timestamp)}</span>
                    </div>
                </div>
            </div>
        `;
        
        return element;
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'À l\'instant';
        if (minutes < 60) return `Il y a ${minutes} min`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `Il y a ${hours}h`;
        
        const days = Math.floor(hours / 24);
        return `Il y a ${days}j`;
    }

    // Data generation methods (would come from API in real implementation)
    getTimeSeriesData(type) {
        // Mock data generation
        const data = [];
        const now = new Date();
        
        for (let i = 29; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            
            let value;
            switch (type) {
                case 'problems':
                    value = Math.floor(Math.random() * 20) + 5;
                    break;
                case 'complaints':
                    value = Math.floor(Math.random() * 15) + 3;
                    break;
                case 'resolutions':
                    value = Math.floor(Math.random() * 18) + 4;
                    break;
                default:
                    value = Math.floor(Math.random() * 10) + 1;
            }
            
            data.push([date.getTime(), value]);
        }
        
        return data;
    }

    getDateCategories() {
        const categories = [];
        const now = new Date();
        
        for (let i = 29; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            categories.push(date.getTime());
        }
        
        return categories;
    }

    getStatusData() {
        return {
            labels: ['En attente', 'En cours', 'Résolu', 'Rejeté', 'Délégué', 'En examen'],
            values: [25, 18, 45, 8, 12, 15]
        };
    }

    getCategoriesData() {
        return {
            labels: ['Voirie', 'Éclairage', 'Déchets', 'Eau', 'Sécurité', 'Administratif'],
            values: [35, 28, 22, 18, 15, 12]
        };
    }

    generateHeatmapData() {
        const data = [];
        const hours = ['00h', '04h', '08h', '12h', '16h', '20h'];
        
        hours.forEach(hour => {
            const hourData = {
                name: hour,
                data: []
            };
            
            for (let day = 0; day < 7; day++) {
                hourData.data.push({
                    x: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'][day],
                    y: Math.floor(Math.random() * 20) + 1
                });
            }
            
            data.push(hourData);
        });
        
        return data;
    }

    generateTrendData() {
        const data = [];
        for (let i = 0; i < 30; i++) {
            data.push(Math.floor(Math.random() * 100) + 50);
        }
        return data;
    }

    getSavedFilters() {
        // Mock saved filters (would come from localStorage or API)
        return [
            { id: 1, name: 'Problèmes urgents' },
            { id: 2, name: 'Cette semaine' },
            { id: 3, name: 'Non résolus' }
        ];
    }

    // Event handlers
    handleSearch(query) {
        console.log('Searching for:', query);
        // Implement search logic
    }

    handleFilterChange(filterElement) {
        const filterType = filterElement.dataset.filter;
        const value = filterElement.value;
        
        this.filters[filterType] = value;
        this.applyFilters();
    }

    handleChartAction(actionElement) {
        const action = actionElement.dataset.chartAction;
        const chartId = actionElement.dataset.chartId;
        
        switch (action) {
            case 'export':
                this.exportChart(chartId);
                break;
            case 'fullscreen':
                this.toggleChartFullscreen(chartId);
                break;
            case 'refresh':
                this.refreshChart(chartId);
                break;
        }
    }

    handleExport(exportType) {
        switch (exportType) {
            case 'pdf':
                this.exportToPDF();
                break;
            case 'excel':
                this.exportToExcel();
                break;
            case 'csv':
                this.exportToCSV();
                break;
            case 'image':
                this.exportToImage();
                break;
        }
    }

    handleDataPointClick(config) {
        console.log('Data point clicked:', config);
        // Implement drill-down functionality
    }

    handleLegendClick(seriesIndex) {
        console.log('Legend clicked:', seriesIndex);
        // Implement series toggle functionality
    }

    // Action methods
    refreshDashboard() {
        if (window.loadingManager) {
            window.loadingManager.show('Actualisation du tableau de bord...');
        }
        
        // Simulate refresh
        setTimeout(() => {
            if (window.loadingManager) {
                window.loadingManager.hide();
            }
            this.showNotification('Tableau de bord actualisé', 'success');
        }, 2000);
    }

    exportDashboard() {
        this.showNotification('Export en cours...', 'info');
        // Implement export logic
    }

    focusSearch() {
        const searchInput = document.getElementById('dashboard-search') || document.getElementById('advanced-search');
        if (searchInput) {
            searchInput.focus();
        }
    }

    switchView(view) {
        console.log('Switching to view:', view);
        // Implement view switching logic
    }

    closeModals() {
        // Close all open modals and dropdowns
        document.querySelectorAll('.modal, .dropdown-menu').forEach(element => {
            element.classList.add('hidden');
        });
    }

    toggleDarkMode() {
        if (window.Alpine && window.Alpine.store('theme')) {
            window.Alpine.store('theme').toggle();
        }
    }

    createNewItem() {
        this.showNotification('Ouverture du formulaire de création...', 'info');
        // Implement new item creation
    }

    openSettings() {
        this.showNotification('Ouverture des paramètres...', 'info');
        // Implement settings modal
    }

    applyFilters() {
        console.log('Applying filters:', this.filters);
        // Implement filter application logic
    }

    applySavedFilter(filterId) {
        console.log('Applying saved filter:', filterId);
        // Implement saved filter application
    }

    filterByStatus(status) {
        this.filters.status = status;
        this.applyFilters();
        this.showNotification(`Filtré par statut: ${status}`, 'info');
    }

    filterByCategory(category) {
        this.filters.category = category;
        this.applyFilters();
        this.showNotification(`Filtré par catégorie: ${category}`, 'info');
    }

    exportChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].dataURI().then((uri) => {
                const link = document.createElement('a');
                link.href = uri.imgURI;
                link.download = `chart-${chartId}.png`;
                link.click();
            });
        }
    }

    toggleChartFullscreen(chartId) {
        const chartContainer = document.getElementById(`${chartId}-chart`);
        if (chartContainer) {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                chartContainer.requestFullscreen();
            }
        }
    }

    refreshChart(chartId) {
        if (this.charts[chartId]) {
            // Regenerate data and update chart
            this.charts[chartId].updateSeries([{
                data: this.getTimeSeriesData(chartId)
            }]);
        }
    }

    exportToPDF() {
        this.showNotification('Génération du PDF...', 'info');
        // Implement PDF export
    }

    exportToExcel() {
        this.showNotification('Génération du fichier Excel...', 'info');
        // Implement Excel export
    }

    exportToCSV() {
        this.showNotification('Génération du fichier CSV...', 'info');
        // Implement CSV export
    }

    exportToImage() {
        this.showNotification('Génération de l\'image...', 'info');
        // Implement image export
    }

    fetchUpdates() {
        // Fetch updates from API
        fetch('/api/dashboard/updates/')
            .then(response => response.json())
            .then(data => {
                this.handleRealTimeUpdate(data);
            })
            .catch(error => {
                console.error('Error fetching updates:', error);
            });
    }

    updateChartData(type, newData) {
        // Update chart with new data point
        if (this.charts.timeSeries) {
            // Add new data point to time series
            const series = this.charts.timeSeries.w.config.series;
            const newPoint = [new Date().getTime(), 1];
            
            if (type === 'problems') {
                series[0].data.push(newPoint);
                series[0].data.shift(); // Remove oldest point
            } else if (type === 'complaints') {
                series[1].data.push(newPoint);
                series[1].data.shift(); // Remove oldest point
            }
            
            this.charts.timeSeries.updateSeries(series);
        }
    }

    updateStatusChart(update) {
        if (this.charts.status) {
            // Update status chart data
            // This would involve recalculating the status distribution
            const newData = this.getStatusData();
            this.charts.status.updateSeries(newData.values);
        }
    }

    addMapMarker(problem) {
        // Add marker to map (if map is initialized)
        if (window.dashboardMap) {
            const marker = L.marker([problem.latitude, problem.longitude])
                .addTo(window.dashboardMap)
                .bindPopup(`
                    <div class="p-2">
                        <h4 class="font-bold text-sm">${problem.description.substring(0, 50)}...</h4>
                        <p class="text-xs text-gray-600 mt-1">Statut: ${problem.status}</p>
                    </div>
                `);
        }
    }

    updateActivityStatus(activityId, newStatus) {
        const activityElement = document.querySelector(`[data-activity-id="${activityId}"]`);
        if (activityElement) {
            const statusBadge = activityElement.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = `status-badge status-${newStatus}`;
                statusBadge.textContent = newStatus;
            }
        }
    }

    loadNotifications() {
        // Load notifications from API or localStorage
        const notifications = this.getNotifications();
        const container = document.getElementById('notification-list');
        
        if (container) {
            container.innerHTML = notifications.map(notification => `
                <div class="p-4 border-b border-secondary-200 dark:border-secondary-700 hover:bg-secondary-50 dark:hover:bg-secondary-700 transition-colors">
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                            <i class="fas ${notification.icon} text-${notification.type}-600"></i>
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium text-secondary-900 dark:text-white">${notification.title}</p>
                            <p class="text-xs text-secondary-600 dark:text-secondary-400 mt-1">${notification.message}</p>
                            <p class="text-xs text-secondary-500 mt-1">${this.formatTimeAgo(new Date(notification.timestamp))}</p>
                        </div>
                        ${!notification.read ? '<div class="w-2 h-2 bg-primary-600 rounded-full"></div>' : ''}
                    </div>
                </div>
            `).join('');
        }
    }

    getNotifications() {
        // Mock notifications (would come from API)
        return [
            {
                id: 1,
                title: 'Nouveau problème signalé',
                message: 'Un problème de voirie a été signalé rue de la République',
                type: 'info',
                icon: 'fa-info-circle',
                timestamp: new Date(Date.now() - 300000), // 5 minutes ago
                read: false
            },
            {
                id: 2,
                title: 'Réclamation résolue',
                message: 'La réclamation #1234 a été marquée comme résolue',
                type: 'success',
                icon: 'fa-check-circle',
                timestamp: new Date(Date.now() - 900000), // 15 minutes ago
                read: true
            }
        ];
    }

    toggleRealTime(enabled) {
        this.realTimeEnabled = enabled;
        if (enabled) {
            this.setupWebSocket();
            this.showNotification('Mode temps réel activé', 'success');
        } else {
            if (this.ws) {
                this.ws.close();
            }
            this.showNotification('Mode temps réel désactivé', 'info');
        }
    }

    handleDateRangeChange(dateRange) {
        console.log('Date range changed:', dateRange);
        // Implement date range filtering
        this.applyFilters();
    }

    performSearch(query) {
        console.log('Performing search:', query);
        // Implement search functionality
        this.showNotification(`Recherche: ${query}`, 'info');
    }
}

// Initialize dashboard manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}

