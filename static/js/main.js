// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Function to automatically calculate percentage for household stats
    const calculateHouseholdPercentage = function() {
        const totalHouseholdsInput = document.getElementById('total_rural_households');
        const currentHouseholdsInput = document.getElementById('households_with_tap_water_current');
        const percentageInput = document.getElementById('households_with_tap_water_current_pct');
        
        if (totalHouseholdsInput && currentHouseholdsInput && percentageInput) {
            const calculateFn = function() {
                const total = parseInt(totalHouseholdsInput.value) || 0;
                const current = parseInt(currentHouseholdsInput.value) || 0;
                
                if (total > 0) {
                    const percentage = (current / total) * 100;
                    percentageInput.value = percentage.toFixed(2);
                }
            };
            
            // Calculate on input change
            totalHouseholdsInput.addEventListener('input', calculateFn);
            currentHouseholdsInput.addEventListener('input', calculateFn);
        }
    };
    
    // Function to handle historical progress percentage calculation
    const calculateHistoricalPercentage = function() {
        const stateIdSelect = document.getElementById('state_id');
        const householdsInput = document.getElementById('households_with_tap_water');
        const percentageInput = document.getElementById('households_with_tap_water_pct');
        
        if (stateIdSelect && householdsInput && percentageInput) {
            // This is complex as we need total households for the selected state
            // We'll rely on the server-side calculation for now
        }
    };
    
    // Initialize form calculations
    calculateHouseholdPercentage();
    calculateHistoricalPercentage();
    
    // Handle alert dismissal
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'close-btn';
        closeBtn.onclick = function() {
            alert.style.display = 'none';
        };
        alert.appendChild(closeBtn);
        
        // Auto hide after 5 seconds
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // Confirmation for delete actions
    const deleteForms = document.querySelectorAll('form.delete-form');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Responsive charts resizing
    window.addEventListener('resize', function() {
        // Check if Plotly is loaded
        if (typeof Plotly !== 'undefined') {
            // Get all chart divs
            const chartDivs = document.querySelectorAll('[id$="-chart"]');
            chartDivs.forEach(function(div) {
                Plotly.relayout(div.id, {
                    'xaxis.autorange': true,
                    'yaxis.autorange': true
                });
            });
        }
    });
});