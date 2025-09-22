// Global variables
let systemInitialized = false;
let availableCompanies = [];

// DOM ready
$(document).ready(function() {
    loadSampleQueries();
    setupEventListeners();
});

function setupEventListeners() {
    // Initialize system button
    $('#initializeBtn').click(initializeSystem);
    
    // Query form submission
    $('#queryForm').submit(function(e) {
        e.preventDefault();
        processQuery();
    });
    
    // Sample query buttons
    $(document).on('click', '.btn-sample-query', function() {
        const query = $(this).data('query');
        $('#queryInput').val(query);
        processQuery();
    });
}

function initializeSystem() {
    const $btn = $('#initializeBtn');
    const $loadingStatus = $('#loadingStatus');
    const $systemStatus = $('#systemStatus');
    
    // Update UI
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Initializing...');
    $loadingStatus.html('<i class="fas fa-spinner fa-spin me-2"></i>Initializing RAG System...');
    
    $.ajax({
        url: '/api/initialize',
        method: 'POST',
        success: function(response) {
            if (response.success) {
                systemInitialized = true;
                availableCompanies = response.companies || [];
                
                // Update UI
                $loadingStatus.addClass('d-none');
                $systemStatus.removeClass('d-none').addClass('fade-in');
                $('#companyCount').text(availableCompanies.length);
                
                $btn.removeClass('btn-light').addClass('btn-success')
                   .html('<i class="fas fa-check-circle me-2"></i>System Ready!');
                
                showNotification('System initialized successfully!', 'success');
            } else {
                showNotification('Failed to initialize system: ' + response.message, 'danger');
                $btn.prop('disabled', false).html('<i class="fas fa-play-circle me-2"></i>Initialize System');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error initializing system: ' + error, 'danger');
            $btn.prop('disabled', false).html('<i class="fas fa-play-circle me-2"></i>Initialize System');
        }
    });
}

function processQuery() {
    if (!systemInitialized) {
        showNotification('Please initialize the system first', 'warning');
        return;
    }
    
    const query = $('#queryInput').val().trim();
    const numResults = parseInt($('#numResults').val());
    
    if (!query) {
        showNotification('Please enter a question', 'warning');
        return;
    }
    
    // Update UI
    const $searchBtn = $('#searchBtn');
    $searchBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Searching...');
    
    // Hide previous results
    $('#resultsSection').addClass('d-none');
    
    $.ajax({
        url: '/api/query',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            query: query,
            num_results: numResults
        }),
        success: function(response) {
            if (response.success) {
                displayResults(response.result);
            } else {
                showNotification('Query failed: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error processing query: ' + error, 'danger');
        },
        complete: function() {
            $searchBtn.prop('disabled', false).html('<i class="fas fa-search me-2"></i>Search & Analyze');
        }
    });
}

function displayResults(result) {
    const $resultsSection = $('#resultsSection');
    const $resultsContent = $('#resultsContent');
    const $searchTime = $('#searchTime');
    
    // Update search time
    $searchTime.text(`Search completed in ${result.search_time.toFixed(3)} seconds`);
    
    // Build results HTML
    let resultsHTML = `
        <div class="row mb-4">
            <div class="col-12">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-question-circle me-2"></i>
                    Query: "${result.query}"
                </h6>
                <div class="d-flex flex-wrap gap-2 mb-3">
                    <span class="badge bg-primary">
                        <i class="fas fa-building me-1"></i>
                        Company: ${result.company_detected}
                    </span>
                    <span class="badge bg-success">
                        <i class="fas fa-file-alt me-1"></i>
                        ${result.search_results.length} Sources
                    </span>
                    <span class="badge bg-info">
                        <i class="fas fa-clock me-1"></i>
                        ${result.search_time.toFixed(3)}s
                    </span>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-12">
                <div class="ai-response">
                    <h6 class="text-primary mb-3">
                        <i class="fas fa-robot me-2"></i>AI Analysis
                    </h6>
                    <div class="ai-answer">
                        ${formatAIAnswer(result.ai_answer)}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-book me-2"></i>Source Documents
                </h6>
                <div class="source-documents">
                    ${formatSourceDocuments(result.search_results)}
                </div>
            </div>
        </div>
    `;
    
    $resultsContent.html(resultsHTML);
    $resultsSection.removeClass('d-none').addClass('fade-in');
    
    // Scroll to results
    $('html, body').animate({
        scrollTop: $resultsSection.offset().top - 100
    }, 800);
}

function formatAIAnswer(answer) {
    // Format the AI answer with better typography
    return answer.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function formatSourceDocuments(sources) {
    return sources.map((source, index) => `
        <div class="source-document">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0">
                    <span class="badge bg-secondary me-2">${index + 1}</span>
                    ${source.company} (Page ${source.page})
                </h6>
                <span class="badge bg-${source.relevance_score === 'High' ? 'success' : 'warning'}">
                    ${source.relevance_score} Relevance
                </span>
            </div>
            <p class="text-muted mb-0">${source.content_preview}</p>
        </div>
    `).join('');
}

function loadSampleQueries() {
    $.get('/api/sample_queries', function(response) {
        if (response.success) {
            const $container = $('#sampleQueries');
            let html = '';
            
            response.sample_queries.forEach(category => {
                html += `
                    <div class="col-md-6 col-lg-3 mb-3">
                        <h6 class="text-primary mb-3">
                            <i class="fas fa-tag me-2"></i>${category.category}
                        </h6>
                        ${category.queries.map(query => `
                            <button class="btn btn-sample-query w-100 mb-2" data-query="${query}">
                                <i class="fas fa-play-circle me-2"></i>
                                ${query}
                            </button>
                        `).join('')}
                    </div>
                `;
            });
            
            $container.html(html);
        }
    });
}

function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const iconClass = {
        'success': 'fas fa-check-circle',
        'danger': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    const notification = $(`
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 80px; right: 20px; z-index: 1050; min-width: 300px;">
            <i class="${iconClass} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(notification);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        notification.alert('close');
    }, 5000);
}
