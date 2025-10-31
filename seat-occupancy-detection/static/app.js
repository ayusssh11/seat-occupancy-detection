// Global variables
let isRecording = false;
let eventSource = null;
let lastUpdateTime = Date.now();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Seat Occupancy Detection System - Web Interface Initialized');
    initializeSSE();
    checkConnection();
});

// Initialize Server-Sent Events for real-time updates
function initializeSSE() {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource('/api/stream');

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            updateStatistics(data);
            lastUpdateTime = Date.now();
        } catch (error) {
            console.error('Error parsing SSE data:', error);
        }
    };

    eventSource.onerror = function(error) {
        console.error('SSE connection error:', error);
        showToast('Connection lost. Reconnecting...', 'warning');
        
        // Try to reconnect after 5 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect SSE...');
            initializeSSE();
        }, 5000);
    };

    eventSource.onopen = function() {
        console.log('SSE connection established');
        updateSystemStatus('Online', 'success');
    };
}

// Update statistics display
function updateStatistics(data) {
    // Update occupancy stats
    document.getElementById('occupiedSeats').textContent = data.occupied || 0;
    document.getElementById('totalSeats').textContent = data.total || 0;
    document.getElementById('occupancyRate').textContent = (data.rate || 0) + '%';
    document.getElementById('emptySeats').textContent = (data.total - data.occupied) || 0;

    // Update progress bar
    const progress = data.rate || 0;
    const progressBar = document.getElementById('occupancyProgress');
    progressBar.style.width = progress + '%';
    progressBar.textContent = progress + '%';
    progressBar.setAttribute('aria-valuenow', progress);

    // Change progress bar color based on occupancy
    progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    if (progress < 30) {
        progressBar.classList.add('bg-success');
    } else if (progress < 70) {
        progressBar.classList.add('bg-warning');
    } else {
        progressBar.classList.add('bg-danger');
    }

    // Update FPS
    document.getElementById('systemFps').textContent = (data.fps || 0).toFixed(1);
    document.getElementById('fpsBadge').textContent = (data.fps || 0).toFixed(1) + ' FPS';

    // Update recording status
    isRecording = data.recording || false;
    updateRecordingUI();

    // Update chair statistics if available
    if (data.chairs_detected !== undefined) {
        const chairStatsElement = document.getElementById('chairStats');
        if (chairStatsElement) {
            document.getElementById('chairsDetected').textContent = data.chairs_detected || 0;
            document.getElementById('chairsAligned').textContent = data.chairs_aligned || 0;
        }
    }

    // Update seat status details
    if (data.seats) {
        updateSeatStatusDisplay(data.seats);
    }

    // Update last update time
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
}

// Update seat status display
function updateSeatStatusDisplay(seats) {
    const container = document.getElementById('seatStatusContainer');
    
    if (Object.keys(seats).length === 0) {
        container.innerHTML = `
            <p class="text-muted text-center mb-0">
                <i class="bi bi-exclamation-circle"></i>
                No seat zones configured
            </p>
        `;
        return;
    }

    let html = '<div class="d-flex flex-wrap gap-2">';
    
    for (const [seatName, status] of Object.entries(seats)) {
        const icon = status === 'occupied' ? 'person-fill' : 'person-dash';
        html += `
            <div class="seat-badge ${status}">
                <i class="bi bi-${icon}"></i>
                <span>${seatName.toUpperCase()}</span>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Update recording UI
function updateRecordingUI() {
    const recordBtn = document.getElementById('recordBtn');
    const recordBtnText = document.getElementById('recordBtnText');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const recordingStatus = document.getElementById('recordingStatus');

    if (isRecording) {
        recordBtn.classList.remove('btn-danger');
        recordBtn.classList.add('btn-warning');
        recordBtnText.textContent = 'Stop Recording';
        recordBtn.querySelector('i').className = 'bi bi-stop-circle';
        recordingIndicator.style.display = 'flex';
        recordingStatus.textContent = 'Yes';
        recordingStatus.className = 'badge bg-danger';
    } else {
        recordBtn.classList.remove('btn-warning');
        recordBtn.classList.add('btn-danger');
        recordBtnText.textContent = 'Start Recording';
        recordBtn.querySelector('i').className = 'bi bi-record-circle';
        recordingIndicator.style.display = 'none';
        recordingStatus.textContent = 'No';
        recordingStatus.className = 'badge bg-secondary';
    }
}

// Update system status
function updateSystemStatus(status, type) {
    const badge = document.getElementById('systemStatus');
    badge.textContent = status;
    badge.className = 'badge';
    
    switch(type) {
        case 'success':
            badge.classList.add('bg-success');
            break;
        case 'warning':
            badge.classList.add('bg-warning');
            break;
        case 'danger':
            badge.classList.add('bg-danger');
            break;
        default:
            badge.classList.add('bg-secondary');
    }
}

// Toggle recording
async function toggleRecording() {
    const endpoint = isRecording ? '/api/recording/stop' : '/api/recording/start';
    
    try {
        const response = await fetch(endpoint, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error toggling recording:', error);
        showToast('Failed to toggle recording', 'danger');
    }
}

// Reload calibration
async function reloadCalibration() {
    showToast('Reloading seat zones...', 'info');
    
    try {
        const response = await fetch('/api/calibrate/reload', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'warning');
        }
    } catch (error) {
        console.error('Error reloading calibration:', error);
        showToast('Failed to reload calibration', 'danger');
    }
}

// Run auto calibration
async function runAutoCalibration() {
    showToast('Running auto-calibration... This may take 30 seconds.', 'info');
    
    try {
        const response = await fetch('/api/calibrate/auto', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'warning');
        }
    } catch (error) {
        console.error('Error running auto-calibration:', error);
        showToast('Failed to run auto-calibration', 'danger');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastElement = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    const toastHeader = toastElement.querySelector('.toast-header');
    
    // Update message
    toastMessage.textContent = message;
    
    // Update icon and color based on type
    const iconClass = {
        'success': 'check-circle',
        'danger': 'x-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    }[type] || 'info-circle';
    
    const icon = toastHeader.querySelector('i');
    icon.className = `bi bi-${iconClass} me-2`;
    
    // Update header background
    toastHeader.className = `toast-header bg-${type} text-white`;
    
    // Show toast
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// Check connection status periodically
function checkConnection() {
    setInterval(() => {
        const timeSinceUpdate = Date.now() - lastUpdateTime;
        
        if (timeSinceUpdate > 5000) {
            updateSystemStatus('Disconnected', 'danger');
            document.getElementById('statusBadge').innerHTML = '<i class="bi bi-circle-fill"></i> Offline';
            document.getElementById('statusBadge').className = 'badge bg-danger me-2';
        } else {
            updateSystemStatus('Online', 'success');
            document.getElementById('statusBadge').innerHTML = '<i class="bi bi-circle-fill"></i> Live';
            document.getElementById('statusBadge').className = 'badge bg-success me-2';
        }
    }, 2000);
}

// Fetch initial stats on load
async function fetchInitialStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        updateStatistics(data);
    } catch (error) {
        console.error('Error fetching initial stats:', error);
    }
}

// Call on load
fetchInitialStats();
