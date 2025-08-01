// Healthcare Dashboard JavaScript
// Comprehensive pre-authorization management system

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// Global state
let currentFile = null;
let currentView = 'overview';
let processingResults = null;
let mockData = generateMockData();

// API Configuration
const API_BASE = 'http://localhost:8000/api';

// Initialize dashboard
function initializeDashboard() {
    initializeNavigation();
    initializeFileUpload();
    initializeSampleButtons();
    initializeQuickActions();
    initializeModals();
    initializeHistoryFilters();
    initializeMemberSearch();

    // Load initial data
    loadDashboardData();

    console.log('Healthcare Dashboard initialized');
}

// Navigation between views
function initializeNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');

    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewName = link.getAttribute('data-view');
            switchView(viewName);
        });
    });
}

function switchView(viewName) {
    // Update sidebar active state
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
    });

    const targetSidebarLink = document.querySelector(`[data-view="${viewName}"]`);
    if (targetSidebarLink) {
        targetSidebarLink.classList.add('active');
    }

    // Update view content
    document.querySelectorAll('.dashboard-view').forEach(view => {
        view.classList.remove('active');
    });

    const targetView = document.getElementById(`${viewName}View`);
    if (targetView) {
        targetView.classList.add('active');
    }

    currentView = viewName;

    // Load view-specific data
    loadViewData(viewName);
}

// Load dashboard data
function loadDashboardData() {
    loadRecentRequests();
    loadHistoryTable();
    animateMetrics();
}

function loadViewData(viewName) {
    switch(viewName) {
        case 'overview':
            loadRecentRequests();
            break;
        case 'history':
            loadHistoryTable();
            break;
        default:
            break;
    }
}

// Load recent requests
function loadRecentRequests() {
    const recentRequestsContainer = document.getElementById('recentRequests');

    const recentRequests = mockData.requests.slice(0, 5);

    recentRequestsContainer.innerHTML = recentRequests.map(request => `
        <div class="request-item">
            <div class="request-info">
                <div class="request-id">#${request.id}</div>
                <div class="request-member">${request.memberName} • ${request.provider}</div>
            </div>
            <div class="request-status ${request.status.toLowerCase()}">${request.status}</div>
        </div>
    `).join('');
}

// Load history table
function loadHistoryTable() {
    const historyTableBody = document.getElementById('historyTableBody');

    if (!historyTableBody) return;

    historyTableBody.innerHTML = mockData.requests.map(request => `
        <tr>
            <td>#${request.id}</td>
            <td>${request.memberName}</td>
            <td>${request.provider}</td>
            <td>${request.service}</td>
            <td>${request.amount}</td>
            <td><span class="request-status ${request.status.toLowerCase()}">${request.status}</span></td>
            <td>${request.date}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewRequestDetails('${request.id}')">
                    View
                </button>
            </td>
        </tr>
    `).join('');
}

// Animate metrics on load
function animateMetrics() {
    const metricValues = document.querySelectorAll('.metric-value');

    metricValues.forEach(metric => {
        const finalValue = metric.textContent;
        metric.textContent = '0';

        // Animate number counting
        animateCounter(metric, finalValue);
    });
}

function animateCounter(element, finalValue) {
    const isNumber = /^\d+/.test(finalValue);
    if (!isNumber) {
        element.textContent = finalValue;
        return;
    }

    const number = parseInt(finalValue);
    const duration = 2000;
    const increment = number / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
        current += increment;
        if (current >= number) {
            element.textContent = finalValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current) + finalValue.replace(/^\d+/, '');
        }
    }, 16);
}

// File Upload Functionality
function initializeFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadActions = document.getElementById('uploadActions');

    if (!uploadArea || !fileInput) return;

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover');
        }, false);
    });

    uploadArea.addEventListener('drop', handleFileDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    // Format buttons
    const formatButtons = document.querySelectorAll('.format-btn');
    formatButtons.forEach(button => {
        button.addEventListener('click', () => {
            const format = button.getAttribute('data-format');
            processFile(format);
        });
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleFileDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
}

function handleFileSelection(file) {
    // Validate file
    if (!isValidFile(file)) {
        return;
    }

    currentFile = file;
    displayFileInfo(file);
    showUploadActions();

    // Auto switch to submit view if not already there
    if (currentView !== 'submit') {
        switchView('submit');
    }
}

function isValidFile(file) {
    const allowedTypes = ['.xml', '.csv', '.pdf', '.json'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExtension)) {
        showToast('Invalid file type. Please select XML, CSV, PDF, or JSON files.', 'error');
        return false;
    }

    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showToast('File too large. Maximum size is 10MB.', 'error');
        return false;
    }

    return true;
}

function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    if (!fileInfo) return;

    const sizeInKB = (file.size / 1024).toFixed(1);
    const fileType = file.name.split('.').pop().toUpperCase();

    fileInfo.innerHTML = `
        <h4>📄 ${file.name}</h4>
        <p>File size: ${sizeInKB} KB • Type: ${fileType}</p>
    `;

    // Update format buttons based on file type
    updateFormatButtons(fileType);
}

function showUploadActions() {
    const uploadActions = document.getElementById('uploadActions');
    if (uploadActions) {
        uploadActions.style.display = 'block';
        uploadActions.classList.add('fade-in-up');
    }
}

// Sample Files
function initializeSampleButtons() {
    const sampleButtons = document.querySelectorAll('.sample-btn');

    sampleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const format = button.getAttribute('data-format');
            processSampleFile(format);
        });
    });
}

async function processSampleFile(format) {
    const endpoint = format === 'eclaim' ? 'process/sample/eclaim' : 'process/sample/shafafiya';
    const formatName = format === 'eclaim' ? 'eClaimLink' : 'Shafafiya';

    showProcessingModal(`Processing ${formatName} sample...`);

    try {
        const response = await fetch(`${API_BASE}/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            processingResults = result;
            hideProcessingModal();
            showResultsModal(result, formatName);
        } else {
            throw new Error(result.error || 'Processing failed');
        }
    } catch (error) {
        hideProcessingModal();
        showToast(`Processing failed: ${error.message}`, 'error');
    }
}

// File Processing
async function processFile(format) {
    if (!currentFile) {
        showToast('Please select a file first.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', currentFile);

    // Determine endpoint and format name based on file type and format
    const fileExtension = currentFile.name.split('.').pop().toLowerCase();
    let endpoint, formatName;

    if (fileExtension === 'csv') {
        endpoint = 'process/csv';
        formatName = 'CSV';
    } else if (format === 'eclaim') {
        endpoint = 'process/eclaim';
        formatName = 'eClaimLink';
    } else if (format === 'shafafiya') {
        endpoint = 'process/shafafiya';
        formatName = 'Shafafiya';
    } else {
        showToast('Please select a valid format for processing.', 'error');
        return;
    }

    showProcessingModal(`Processing ${currentFile.name} as ${formatName}...`);

    try {
        const response = await fetch(`${API_BASE}/${endpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            processingResults = result;
            hideProcessingModal();
            showResultsModal(result, formatName);

            // Add to mock data for history
            addToHistory(result, formatName);
        } else {
            throw new Error(result.error || 'Processing failed');
        }
    } catch (error) {
        hideProcessingModal();
        showToast(`Processing failed: ${error.message}`, 'error');
    }
}

// Quick Actions
function initializeQuickActions() {
    const actionButtons = document.querySelectorAll('.action-btn');

    actionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const action = button.getAttribute('data-action');
            handleQuickAction(action);
        });
    });
}

function handleQuickAction(action) {
    switch(action) {
        case 'submit':
            switchView('submit');
            break;
        case 'search':
            switchView('members');
            document.getElementById('memberSearchInput')?.focus();
            break;
        case 'samples':
            switchView('submit');
            document.querySelector('.samples-section')?.scrollIntoView({
                behavior: 'smooth'
            });
            break;
        default:
            break;
    }
}

// Modals
function initializeModals() {
    // Processing modal is controlled by show/hide functions

    // Results modal
    const closeResults = document.getElementById('closeResults');
    const resultsModal = document.getElementById('resultsModal');

    if (closeResults) {
        closeResults.addEventListener('click', hideResultsModal);
    }

    if (resultsModal) {
        resultsModal.addEventListener('click', (e) => {
            if (e.target === resultsModal) {
                hideResultsModal();
            }
        });
    }

    // Tab navigation in results modal
    const tabButtons = document.querySelectorAll('.results-tabs .tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchResultsTab(tabName);
        });
    });

    // Download and approve buttons
    const downloadBtn = document.getElementById('downloadResults');
    const approveBtn = document.getElementById('approveRequest');

    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadResults);
    }

    if (approveBtn) {
        approveBtn.addEventListener('click', approveRequest);
    }
}

function showProcessingModal(message) {
    const modal = document.getElementById('processingModal');
    const text = document.getElementById('processingText');

    if (modal && text) {
        text.textContent = message;
        modal.style.display = 'flex';
    }
}

function hideProcessingModal() {
    const modal = document.getElementById('processingModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showResultsModal(result, formatType) {
    const modal = document.getElementById('resultsModal');
    if (!modal) return;

    // Populate modal content
    populateResultsModal(result, formatType);

    // Show modal
    modal.style.display = 'flex';

    // Set focus to first tab
    switchResultsTab('summary');
}

function hideResultsModal() {
    const modal = document.getElementById('resultsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function populateResultsModal(result, formatType) {
    const data = result.data;
    const metadata = result.metadata;

    // Summary Tab (renamed from Clinical Summary for CSV compatibility)
    const summaryContent = document.getElementById('summaryContent');
    if (summaryContent) {
        summaryContent.innerHTML = generateSummaryContent(data, formatType, metadata);
    }

    // Details Tab (renamed from Financial Details for CSV compatibility)
    const detailsContent = document.getElementById('detailsContent');
    if (detailsContent) {
        detailsContent.innerHTML = generateDetailsContent(data, formatType, metadata);
    }

    // Raw Data Tab
    const rawDataContent = document.getElementById('rawDataContent');
    if (rawDataContent) {
        rawDataContent.innerHTML = generateRawDataContent(data, formatType);
    }
}

function generateClinicalSummary(data, formatType) {
    let html = `
        <div class="clinical-overview">
            <div class="clinical-header">
                <h4>🏥 Clinical Assessment</h4>
                <div class="clinical-score">
                    <span class="score-label">AI Confidence</span>
                    <span class="score-value">94%</span>
                </div>
            </div>

            <div class="clinical-info">
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Authorization ID:</strong> ${data.authorization_id || 'N/A'}
                    </div>
                    <div class="info-item">
                        <strong>Member ID:</strong> ${data.member_id || 'N/A'}
                    </div>
                    <div class="info-item">
                        <strong>Provider:</strong> ${data.provider || 'N/A'}
                    </div>
                    <div class="info-item">
                        <strong>Format:</strong> ${formatType}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add format-specific clinical details
    if (formatType === 'eClaimLink' && data.services) {
        html += `
            <div class="clinical-services">
                <h5>🔬 Services Requested</h5>
                ${data.services.slice(0, 3).map((service, index) => `
                    <div class="service-card">
                        <div class="service-header">
                            <strong>Service ${index + 1}</strong>
                            <span class="service-amount">${service.requested_amount_value || 'N/A'} ${service.requested_amount_currency || 'AED'}</span>
                        </div>
                        <div class="service-details">
                            <p><strong>Activity:</strong> ${service.activity_code || 'N/A'}</p>
                            <p><strong>Diagnosis:</strong> ${service.diagnosis_code || 'N/A'}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (formatType === 'Shafafiya' && data.activities) {
        html += `
            <div class="clinical-activities">
                <h5>🔬 Activities Requested</h5>
                ${data.activities.slice(0, 3).map((activity, index) => `
                    <div class="activity-card">
                        <div class="activity-header">
                            <strong>Activity ${index + 1}</strong>
                            <span class="activity-amount">${activity.amount || 'N/A'}</span>
                        </div>
                        <div class="activity-details">
                            <p><strong>Type:</strong> ${activity.type || 'N/A'}</p>
                            <p><strong>Code:</strong> ${activity.code || 'N/A'}</p>
                            <p><strong>Description:</strong> ${activity.description || 'N/A'}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Clinical recommendation
    html += `
        <div class="clinical-recommendation">
            <h5>💡 AI Recommendation</h5>
            <div class="recommendation-card approved">
                <div class="recommendation-icon">✅</div>
                <div class="recommendation-content">
                    <strong>APPROVE</strong>
                    <p>All requested services meet clinical guidelines and coverage criteria. No additional documentation required.</p>
                </div>
            </div>
        </div>
    `;

    return html;
}

function generateFinancialDetails(data, formatType) {
    let totalAmount = 0;
    let currency = 'AED';

    // Calculate total amount
    if (formatType === 'eClaimLink' && data.services) {
        data.services.forEach(service => {
            if (service.requested_amount_value) {
                totalAmount += parseFloat(service.requested_amount_value) || 0;
                currency = service.requested_amount_currency || currency;
            }
        });
    } else if (formatType === 'Shafafiya' && data.activities) {
        data.activities.forEach(activity => {
            if (activity.amount) {
                totalAmount += parseFloat(activity.amount.replace(/[^\d.]/g, '')) || 0;
            }
        });
    }

    return `
        <div class="financial-overview">
            <div class="financial-summary">
                <div class="amount-card">
                    <div class="amount-label">Total Requested Amount</div>
                    <div class="amount-value">${totalAmount.toLocaleString()} ${currency}</div>
                </div>

                <div class="coverage-info">
                    <div class="coverage-item">
                        <span class="coverage-label">Coverage Level:</span>
                        <span class="coverage-value">100%</span>
                    </div>
                    <div class="coverage-item">
                        <span class="coverage-label">Member Copay:</span>
                        <span class="coverage-value">0 ${currency}</span>
                    </div>
                    <div class="coverage-item">
                        <span class="coverage-label">Approved Amount:</span>
                        <span class="coverage-value">${totalAmount.toLocaleString()} ${currency}</span>
                    </div>
                </div>
            </div>

            <div class="cost-breakdown">
                <h5>💰 Cost Breakdown</h5>
                <div class="breakdown-table">
                    <div class="breakdown-row header">
                        <span>Service/Activity</span>
                        <span>Amount</span>
                        <span>Status</span>
                    </div>
    `;

    // Add service/activity rows
    if (formatType === 'eClaimLink' && data.services) {
        data.services.forEach((service, index) => {
            return `
                    <div class="breakdown-row">
                        <span>Service ${index + 1}</span>
                        <span>${service.requested_amount_value || 'N/A'} ${service.requested_amount_currency || currency}</span>
                        <span class="status approved">Approved</span>
                    </div>
            `;
        });
    }

    return html + `
                </div>
            </div>
        </div>
    `;
}

function switchResultsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.results-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const targetTabBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (targetTabBtn) {
        targetTabBtn.classList.add('active');
    }

    // Update tab panels
    document.querySelectorAll('.results-tabs .tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    const targetTabPanel = document.getElementById(`${tabName}Tab`);
    if (targetTabPanel) {
        targetTabPanel.classList.add('active');
    }
}

function downloadResults() {
    if (!processingResults) return;

    const dataStr = JSON.stringify(processingResults.data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });

    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `nazmito-analysis-${Date.now()}.json`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast('Analysis report downloaded successfully!', 'success');
}

function approveRequest() {
    // Simulate approval process
    showToast('Pre-authorization request approved successfully!', 'success');
    hideResultsModal();

    // Update metrics (in real app, this would come from backend)
    updateDashboardMetrics();
}

// History and Search
function initializeHistoryFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const formatFilter = document.getElementById('formatFilter');
    const searchFilter = document.getElementById('searchFilter');

    if (statusFilter) {
        statusFilter.addEventListener('change', applyHistoryFilters);
    }

    if (formatFilter) {
        formatFilter.addEventListener('change', applyHistoryFilters);
    }

    if (searchFilter) {
        searchFilter.addEventListener('input', debounce(applyHistoryFilters, 300));
    }
}

function applyHistoryFilters() {
    const statusValue = document.getElementById('statusFilter')?.value || '';
    const formatValue = document.getElementById('formatFilter')?.value || '';
    const searchValue = document.getElementById('searchFilter')?.value.toLowerCase() || '';

    let filteredRequests = mockData.requests;

    if (statusValue) {
        filteredRequests = filteredRequests.filter(req =>
            req.status.toLowerCase() === statusValue.toLowerCase()
        );
    }

    if (formatValue) {
        filteredRequests = filteredRequests.filter(req =>
            req.format === formatValue
        );
    }

    if (searchValue) {
        filteredRequests = filteredRequests.filter(req =>
            req.id.toLowerCase().includes(searchValue) ||
            req.memberName.toLowerCase().includes(searchValue) ||
            req.memberId.toLowerCase().includes(searchValue)
        );
    }

    updateHistoryTable(filteredRequests);
}

function updateHistoryTable(requests) {
    const historyTableBody = document.getElementById('historyTableBody');
    if (!historyTableBody) return;

    historyTableBody.innerHTML = requests.map(request => `
        <tr>
            <td>#${request.id}</td>
            <td>${request.memberName}</td>
            <td>${request.provider}</td>
            <td>${request.service}</td>
            <td>${request.amount}</td>
            <td><span class="request-status ${request.status.toLowerCase()}">${request.status}</span></td>
            <td>${request.date}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewRequestDetails('${request.id}')">
                    View
                </button>
            </td>
        </tr>
    `).join('');
}

function initializeMemberSearch() {
    const searchBtn = document.getElementById('memberSearchBtn');
    const searchInput = document.getElementById('memberSearchInput');

    if (searchBtn) {
        searchBtn.addEventListener('click', performMemberSearch);
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performMemberSearch();
            }
        });
    }
}

function performMemberSearch() {
    const searchValue = document.getElementById('memberSearchInput')?.value.trim();
    const resultsContainer = document.getElementById('memberResults');

    if (!searchValue || !resultsContainer) return;

    // Simulate search results
    const mockMember = {
        id: 'M789012',
        name: 'Ahmed Al-Mansouri',
        emiratesId: '784-1234-5678901-2',
        dateOfBirth: '1985-03-15',
        phone: '+971 50 123 4567',
        email: 'ahmed.almansouri@email.com',
        insuranceProvider: 'Emirates Health Insurance',
        policyNumber: 'EHI-789012-2024',
        recentRequests: mockData.requests.slice(0, 3)
    };

    resultsContainer.innerHTML = `
        <div class="member-profile">
            <div class="member-header">
                <div class="member-avatar">👤</div>
                <div class="member-info">
                    <h3>${mockMember.name}</h3>
                    <p>Member ID: ${mockMember.id} • Emirates ID: ${mockMember.emiratesId}</p>
                </div>
            </div>

            <div class="member-details">
                <div class="detail-section">
                    <h4>Contact Information</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Phone:</strong> ${mockMember.phone}
                        </div>
                        <div class="detail-item">
                            <strong>Email:</strong> ${mockMember.email}
                        </div>
                        <div class="detail-item">
                            <strong>Date of Birth:</strong> ${mockMember.dateOfBirth}
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Insurance Details</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Provider:</strong> ${mockMember.insuranceProvider}
                        </div>
                        <div class="detail-item">
                            <strong>Policy Number:</strong> ${mockMember.policyNumber}
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Recent Pre-Authorization Requests</h4>
                    <div class="request-history">
                        ${mockMember.recentRequests.map(request => `
                            <div class="request-item">
                                <div class="request-info">
                                    <div class="request-id">#${request.id}</div>
                                    <div class="request-member">${request.service} • ${request.date}</div>
                                </div>
                                <div class="request-status ${request.status.toLowerCase()}">${request.status}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;

    resultsContainer.style.display = 'block';
}

// Utility Functions
function addToHistory(result, formatType) {
    const newRequest = {
        id: `REQ${Date.now().toString().slice(-6)}`,
        memberName: 'John Doe',
        memberId: 'M123456',
        provider: 'City Hospital',
        service: formatType === 'eClaimLink' ? 'Medical Consultation' : 'Diagnostic Test',
        amount: '1,250 AED',
        status: 'Approved',
        date: new Date().toLocaleDateString(),
        format: formatType
    };

    mockData.requests.unshift(newRequest);

    // Refresh displays
    if (currentView === 'overview') {
        loadRecentRequests();
    } else if (currentView === 'history') {
        loadHistoryTable();
    }
}

function updateDashboardMetrics() {
    // Simulate metrics update after approval
    const approvedCount = document.querySelector('.status-card.approved .status-count');
    if (approvedCount) {
        const current = parseInt(approvedCount.textContent);
        approvedCount.textContent = current + 1;
    }
}

function viewRequestDetails(requestId) {
    // Find request and show details
    const request = mockData.requests.find(r => r.id === requestId);
    if (request) {
        showToast(`Viewing details for request #${requestId}`, 'info');
        // In real app, this would open a detailed view modal
    }
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${getToastIcon(type)}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    // Add to document
    document.body.appendChild(toast);

    // Show with animation
    setTimeout(() => toast.classList.add('show'), 100);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return '✅';
        case 'error': return '❌';
        case 'warning': return '⚠️';
        default: return 'ℹ️';
    }
}

function debounce(func, wait) {
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

// Mock Data Generator
function generateMockData() {
    const statuses = ['Approved', 'Pending', 'Denied'];
    const providers = ['City Hospital', 'Al Noor Hospital', 'Emirates Hospital', 'Mediclinic', 'Aster Hospital'];
    const services = ['Medical Consultation', 'Diagnostic Test', 'Surgery', 'Physical Therapy', 'Prescription Medication'];
    const formats = ['eClaimLink', 'Shafafiya'];

    const requests = [];

    for (let i = 0; i < 50; i++) {
        requests.push({
            id: `REQ${String(i + 1).padStart(6, '0')}`,
            memberName: `Member ${i + 1}`,
            memberId: `M${String(i + 1).padStart(6, '0')}`,
            provider: providers[Math.floor(Math.random() * providers.length)],
            service: services[Math.floor(Math.random() * services.length)],
            amount: `${(Math.random() * 5000 + 500).toFixed(0).toLocaleString()} AED`,
            status: statuses[Math.floor(Math.random() * statuses.length)],
            date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleDateString(),
            format: formats[Math.floor(Math.random() * formats.length)]
        });
    }

    return { requests };
}

// Add toast styles dynamically
const toastStyles = `
    .toast {
        position: fixed;
        top: 100px;
        right: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 16px;
        z-index: 10001;
        transform: translateX(100%);
        transition: transform 0.3s ease-out;
        max-width: 400px;
    }

    .toast.show {
        transform: translateX(0);
    }

    .toast-success {
        border-left-color: #059669;
    }

    .toast-error {
        border-left-color: #dc2626;
    }

    .toast-warning {
        border-left-color: #d97706;
    }

    .toast-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .toast-icon {
        font-size: 1.25rem;
    }

    .toast-message {
        color: #374151;
        font-weight: 500;
    }
`;

// Add styles to document head
const toastStyleSheet = document.createElement('style');
toastStyleSheet.textContent = toastStyles;
document.head.appendChild(toastStyleSheet);

// CSV Processing Functions
async function processCSVFile(file, formatType) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const csvContent = e.target.result;
            const mockResult = analyzeCSVContent(csvContent, formatType);
            resolve(mockResult);
        };
        reader.readAsText(file);
    });
}

function analyzeCSVContent(csvContent, formatType) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    const headers = lines[0] ? lines[0].split(',').map(h => h.trim().replace(/"/g, '')) : [];
    const dataRows = lines.slice(1);

    // Basic CSV analysis
    const analysis = {
        totalRows: dataRows.length,
        totalColumns: headers.length,
        headers: headers,
        sampleData: dataRows.slice(0, 5).map(row =>
            row.split(',').map(cell => cell.trim().replace(/"/g, ''))
        ),
        qualityScore: calculateCSVQuality(headers, dataRows),
        dataTypes: detectDataTypes(headers, dataRows)
    };

    // Generate FHIR mapping simulation
    const fhirMapping = generateFHIRMapping(headers, formatType);

    return {
        success: true,
        data: {
            resourceType: 'Bundle',
            csv_analysis: analysis,
            fhir_mapping: fhirMapping,
            format_type: formatType,
            processing_timestamp: new Date().toISOString(),
            raw_data: csvContent.substring(0, 1000) + (csvContent.length > 1000 ? '...' : '')
        },
        metadata: {
            filename: 'uploaded-file.csv',
            file_size_bytes: csvContent.length,
            processing_time_seconds: (Math.random() * 2 + 1).toFixed(3),
            format: formatType,
            api_version: '1.0.0',
            processor_version: 'CSVProcessor'
        }
    };
}

function calculateCSVQuality(headers, dataRows) {
    if (!headers.length || !dataRows.length) return 0;

    let score = 0;
    const checks = {
        hasHeaders: headers.length > 0 ? 25 : 0,
        consistentColumns: checkColumnConsistency(dataRows, headers.length) ? 25 : 0,
        noEmptyHeaders: headers.every(h => h.length > 0) ? 25 : 0,
        dataCompleteness: calculateCompleteness(dataRows) * 25
    };

    return Object.values(checks).reduce((sum, val) => sum + val, 0);
}

function checkColumnConsistency(dataRows, expectedColumns) {
    return dataRows.every(row => row.split(',').length === expectedColumns);
}

function calculateCompleteness(dataRows) {
    if (!dataRows.length) return 0;

    const totalCells = dataRows.reduce((sum, row) => sum + row.split(',').length, 0);
    const emptyCells = dataRows.reduce((sum, row) => {
        return sum + row.split(',').filter(cell => !cell.trim()).length;
    }, 0);

    return Math.max(0, (totalCells - emptyCells) / totalCells);
}

function detectDataTypes(headers, dataRows) {
    if (!dataRows.length) return {};

    const types = {};
    const sampleRow = dataRows[0] ? dataRows[0].split(',') : [];

    headers.forEach((header, index) => {
        const sampleValue = sampleRow[index] ? sampleRow[index].trim() : '';
        types[header] = detectFieldType(sampleValue);
    });

    return types;
}

function detectFieldType(value) {
    if (!value) return 'empty';
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) return 'date';
    if (/^[+-]?\d*\.?\d+$/.test(value)) return 'number';
    if (/^[A-Z]\d{2}(\.\d+)?$/.test(value)) return 'icd_code';
    if (/^\d{5}$/.test(value)) return 'cpt_code';
    if (value.includes('@')) return 'email';
    if (/^\+?[\d\s()-]+$/.test(value)) return 'phone';
    return 'text';
}

function generateFHIRMapping(headers, formatType) {
    const mapping = {
        Patient: [],
        Claim: [],
        ServiceRequest: [],
        Observation: []
    };

    headers.forEach(header => {
        const lowerHeader = header.toLowerCase();

        // Patient mapping
        if (lowerHeader.includes('patient') || lowerHeader.includes('member')) {
            mapping.Patient.push({
                csv_field: header,
                fhir_field: 'identifier',
                confidence: 0.9
            });
        }

        // Claim mapping
        if (lowerHeader.includes('claim') || lowerHeader.includes('amount') || lowerHeader.includes('cost')) {
            mapping.Claim.push({
                csv_field: header,
                fhir_field: lowerHeader.includes('amount') ? 'total' : 'identifier',
                confidence: 0.85
            });
        }

        // ServiceRequest mapping
        if (lowerHeader.includes('service') || lowerHeader.includes('procedure') || lowerHeader.includes('cpt')) {
            mapping.ServiceRequest.push({
                csv_field: header,
                fhir_field: 'code',
                confidence: 0.8
            });
        }

        // Observation mapping
        if (lowerHeader.includes('diagnosis') || lowerHeader.includes('icd') || lowerHeader.includes('result')) {
            mapping.Observation.push({
                csv_field: header,
                fhir_field: 'code',
                confidence: 0.75
            });
        }
    });

    return mapping;
}

function generateMockCSVResult(formatName) {
    const isClaims = formatName.includes('Claims');

    return {
        success: true,
        data: {
            resourceType: 'Bundle',
            csv_analysis: {
                totalRows: isClaims ? 1250 : 850,
                totalColumns: isClaims ? 12 : 15,
                headers: isClaims ?
                    ['claim_id', 'member_id', 'provider_id', 'service_date', 'amount', 'status'] :
                    ['patient_id', 'encounter_id', 'diagnosis_code', 'procedure_code', 'provider_id', 'date'],
                qualityScore: Math.random() * 20 + 80, // 80-100
                dataTypes: {
                    'claim_id': 'text',
                    'member_id': 'text',
                    'amount': 'number',
                    'service_date': 'date',
                    'diagnosis_code': 'icd_code'
                }
            },
            fhir_mapping: {
                Patient: [{ csv_field: 'member_id', fhir_field: 'identifier', confidence: 0.9 }],
                Claim: [{ csv_field: 'claim_id', fhir_field: 'identifier', confidence: 0.9 }],
                ServiceRequest: [{ csv_field: 'procedure_code', fhir_field: 'code', confidence: 0.8 }]
            },
            format_type: formatName,
            processing_timestamp: new Date().toISOString()
        },
        metadata: {
            filename: `sample-${formatName.toLowerCase().replace(' ', '-')}.csv`,
            file_size_bytes: isClaims ? 156789 : 98432,
            processing_time_seconds: (Math.random() * 3 + 2).toFixed(3),
            format: formatName,
            api_version: '1.0.0',
            processor_version: 'CSVProcessor'
        }
    };
}

function updateFormatButtons(fileType) {
    const xmlFormats = document.querySelector('.xml-formats');
    const csvFormats = document.querySelector('.csv-formats');

    if (!xmlFormats || !csvFormats) return;

    if (fileType === 'CSV') {
        xmlFormats.style.display = 'none';
        csvFormats.style.display = 'block';
    } else if (fileType === 'XML') {
        xmlFormats.style.display = 'block';
        csvFormats.style.display = 'none';
    } else {
        // For other file types, show both
        xmlFormats.style.display = 'block';
        csvFormats.style.display = 'block';
    }
}

// Updated result generation functions
function generateSummaryContent(data, formatType, metadata) {
    // Handle CSV format
    if (formatType.includes('CSV')) {
        const quality = ((metadata?.data_quality_score || 0) * 100);
        const totalRecords = metadata?.total_records || 0;
        const detectedColumns = metadata?.detected_columns || 0;
        const processingTime = metadata?.processing_time_seconds || 0;
        const resourceTypes = metadata?.resource_types || [];

        return `
            <div class="csv-overview">
                <div class="csv-header">
                    <h4>📊 ${formatType} Analysis</h4>
                    <div class="quality-score">
                        <span class="score-label">Data Quality</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${quality}%"></div>
                        </div>
                        <span class="score-value">${Math.round(quality)}%</span>
                    </div>
                </div>

                <div class="csv-metrics">
                    <div class="metric-row">
                        <div class="metric-item">
                            <strong>📋 Total Records:</strong> ${totalRecords.toLocaleString()}
                        </div>
                        <div class="metric-item">
                            <strong>📄 Columns:</strong> ${detectedColumns}
                        </div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-item">
                            <strong>🔍 Format:</strong> ${formatType}
                        </div>
                        <div class="metric-item">
                            <strong>⏱️ Processing Time:</strong> ${processingTime.toFixed(3)}s
                        </div>
                    </div>
                </div>

                <div class="fhir-mapping-summary">
                    <h5>🔗 FHIR Resource Mapping</h5>
                    <div class="mapping-grid">
                        ${resourceTypes.map(resourceType => `
                            <div class="mapping-card">
                                <strong>${resourceType}</strong>
                                <span class="mapping-count">detected</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    // Original XML format logic - call the existing clinical summary function
    return generateClinicalSummary(data, formatType);
}

function generateDetailsContent(data, formatType, metadata) {
    // Handle CSV format
    if (formatType.includes('CSV')) {
        const rawData = data.raw_data || {};
        const columnMappings = rawData.column_mappings || [];
        const resourceDetections = rawData.resource_detections || [];
        const originalData = rawData.original_data || [];
        const headers = originalData.length > 0 ? Object.keys(originalData[0]) : [];

        return `
            <div class="csv-details">
                <div class="data-schema">
                    <h5>🗺️ Data Schema</h5>
                    <div class="schema-table">
                        <div class="schema-header">
                            <span>Column Name</span>
                            <span>Data Type</span>
                            <span>FHIR Mapping</span>
                        </div>
                        ${columnMappings.map(mapping => `
                            <div class="schema-row">
                                <span class="column-name">${mapping.original_column}</span>
                                <span class="data-type type-string">string</span>
                                <span class="fhir-mapping">${mapping.fhir_field || 'Unmapped'}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="data-preview">
                    <h5>🔍 Data Preview</h5>
                    <div class="preview-table">
                        <div class="preview-header">
                            ${headers.slice(0, 6).map(header =>
                                `<span>${header}</span>`
                            ).join('')}
                        </div>
                        ${originalData.slice(0, 3).map(row => `
                            <div class="preview-row">
                                ${headers.slice(0, 6).map(header =>
                                    `<span>${row[header] || '-'}</span>`
                                ).join('')}
                            </div>
                        `).join('')}
                    </div>
                    ${originalData.length > 3 ? `<p class="preview-note">Showing 3 of ${originalData.length.toLocaleString()} records</p>` : ''}
                </div>
            </div>
        `;
    }

    // Original XML format details
    return generateFinancialDetails(data, formatType);
}

function findFHIRMapping(columnName, mapping) {
    for (const [resource, mappings] of Object.entries(mapping)) {
        const found = mappings.find(m => m.csv_field === columnName);
        if (found) {
            return `${resource}.${found.fhir_field}`;
        }
    }
    return null;
}

function generateRawDataContent(data, formatType) {
    if (formatType.includes('CSV')) {
        const rawDataObj = data.raw_data || {};
        const rawDataText = typeof rawDataObj === 'string' ? rawDataObj : JSON.stringify(rawDataObj, null, 2);
        const escapedRawData = rawDataText.replace(/'/g, "\\'").replace(/\n/g, '\\n');

        return `
            <div class="csv-raw-data">
                <div class="raw-data-header">
                    <h5>📄 Raw CSV Data</h5>
                    <button class="btn btn-secondary btn-sm" onclick="copyToClipboard('${escapedRawData}')">Copy</button>
                </div>
                <div class="csv-viewer">
                    <pre><code>${rawDataText}</code></pre>
                </div>

                <div class="processing-metadata">
                    <h5>⚙️ Processing Metadata</h5>
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <strong>File Size:</strong> ${formatBytes(data.file_size_bytes || 0)}
                        </div>
                        <div class="metadata-item">
                            <strong>Processing Time:</strong> ${data.processing_time_seconds || 'N/A'}s
                        </div>
                        <div class="metadata-item">
                            <strong>Quality Score:</strong> ${Math.round(data.csv_analysis?.qualityScore || 0)}%
                        </div>
                        <div class="metadata-item">
                            <strong>Format:</strong> ${formatType}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Original XML raw data display
    const displayData = { ...data };
    delete displayData.raw_data; // Remove for cleaner display
    return `<div class="json-viewer"><pre>${JSON.stringify(displayData, null, 2)}</pre></div>`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Data copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy data', 'error');
    });
}

// Export for global access
window.NazmitoDashboard = {
    switchView,
    processFile,
    processSampleFile,
    showToast,
    viewRequestDetails
};
