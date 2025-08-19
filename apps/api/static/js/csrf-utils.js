/**
 * CSRF Token Utilities for Django Personal Blog System
 * Provides AJAX-compatible CSRF token management
 */

class CSRFManager {
    constructor() {
        this.token = null;
        this.tokenExpiry = null;
        this.refreshPromise = null;
        this.init();
    }

    /**
     * Initialize CSRF manager
     */
    init() {
        this.loadTokenFromCookie();
        this.setupAjaxDefaults();
        this.setupEventListeners();
    }

    /**
     * Load CSRF token from cookie
     */
    loadTokenFromCookie() {
        const cookieValue = this.getCookie('csrftoken');
        if (cookieValue) {
            this.token = cookieValue;
        }
    }

    /**
     * Get cookie value by name
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Setup jQuery AJAX defaults for CSRF
     */
    setupAjaxDefaults() {
        if (typeof $ !== 'undefined') {
            const self = this;
            
            // Setup CSRF token for all AJAX requests
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!self.csrfSafeMethod(settings.type) && !this.crossDomain) {
                        const token = self.getToken();
                        if (token) {
                            xhr.setRequestHeader("X-CSRFToken", token);
                        }
                    }
                }
            });

            // Handle CSRF failures
            $(document).ajaxError(function(event, xhr, settings) {
                if (xhr.status === 403 && xhr.responseJSON && xhr.responseJSON.code === 'CSRF_FAILED') {
                    self.handleCSRFFailure(xhr.responseJSON);
                }
            });
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for form submissions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (form.method.toLowerCase() === 'post') {
                this.ensureFormHasCSRFToken(form);
            }
        });

        // Listen for page visibility changes to refresh token
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkTokenExpiry();
            }
        });
    }

    /**
     * Check if HTTP method is CSRF safe
     */
    csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    /**
     * Get current CSRF token
     */
    getToken() {
        if (!this.token) {
            this.loadTokenFromCookie();
        }
        return this.token;
    }

    /**
     * Refresh CSRF token from server
     */
    async refreshToken() {
        if (this.refreshPromise) {
            return this.refreshPromise;
        }

        this.refreshPromise = fetch('/core/security/csrf-token/', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.csrf_token) {
                this.token = data.csrf_token;
                this.tokenExpiry = data.expires_in ? Date.now() + (data.expires_in * 1000) : null;
                this.updateFormTokens();
                console.log('CSRF token refreshed successfully');
            }
            return data;
        })
        .catch(error => {
            console.error('Failed to refresh CSRF token:', error);
            throw error;
        })
        .finally(() => {
            this.refreshPromise = null;
        });

        return this.refreshPromise;
    }

    /**
     * Handle CSRF failure
     */
    async handleCSRFFailure(errorData) {
        console.warn('CSRF validation failed, refreshing token...');
        
        try {
            await this.refreshToken();
            
            // Show user-friendly message
            this.showCSRFMessage('Security token refreshed. Please try your action again.');
            
        } catch (error) {
            console.error('Failed to handle CSRF failure:', error);
            this.showCSRFMessage('Security error. Please refresh the page and try again.', 'error');
        }
    }

    /**
     * Check if token needs refreshing
     */
    checkTokenExpiry() {
        if (this.tokenExpiry && Date.now() > this.tokenExpiry - 300000) { // 5 minutes before expiry
            this.refreshToken();
        }
    }

    /**
     * Ensure form has CSRF token
     */
    ensureFormHasCSRFToken(form) {
        let csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        
        if (!csrfInput) {
            csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            form.appendChild(csrfInput);
        }
        
        const token = this.getToken();
        if (token) {
            csrfInput.value = token;
        }
    }

    /**
     * Update all form tokens on the page
     */
    updateFormTokens() {
        const token = this.getToken();
        if (!token) return;

        document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(input => {
            input.value = token;
        });
    }

    /**
     * Show CSRF-related message to user
     */
    showCSRFMessage(message, type = 'info') {
        // Try to use existing notification system
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }

        // Fallback to simple alert or console
        if (type === 'error') {
            console.error(message);
            alert(message);
        } else {
            console.info(message);
        }
    }

    /**
     * Make CSRF-protected AJAX request
     */
    async ajaxRequest(url, options = {}) {
        const token = this.getToken();
        
        const defaultOptions = {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        };

        // Add CSRF token for non-safe methods
        if (!this.csrfSafeMethod(options.method || 'GET')) {
            defaultOptions.headers['X-CSRFToken'] = token;
        }

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, finalOptions);
            
            // Handle CSRF failures
            if (response.status === 403) {
                const errorData = await response.json();
                if (errorData.code === 'CSRF_FAILED') {
                    await this.handleCSRFFailure(errorData);
                    // Retry the request with new token
                    finalOptions.headers['X-CSRFToken'] = this.getToken();
                    return fetch(url, finalOptions);
                }
            }
            
            return response;
        } catch (error) {
            console.error('AJAX request failed:', error);
            throw error;
        }
    }

    /**
     * Get security status from server
     */
    async getSecurityStatus() {
        try {
            const response = await this.ajaxRequest('/core/security/status/', {
                method: 'GET'
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to get security status:', error);
            return null;
        }
    }

    /**
     * Report security incident to server
     */
    async reportIncident(type, details = {}) {
        try {
            const response = await this.ajaxRequest('/core/security/report-incident/', {
                method: 'POST',
                body: JSON.stringify({
                    type: type,
                    details: details,
                    timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    url: window.location.href
                })
            });
            
            if (response.ok) {
                console.log('Security incident reported successfully');
            }
        } catch (error) {
            console.error('Failed to report security incident:', error);
        }
    }
}

// Rate limiting utilities
class RateLimitManager {
    constructor() {
        this.limits = new Map();
        this.setupEventListeners();
    }

    /**
     * Setup event listeners for rate limit handling
     */
    setupEventListeners() {
        if (typeof $ !== 'undefined') {
            $(document).ajaxError((event, xhr, settings) => {
                if (xhr.status === 429) {
                    this.handleRateLimit(xhr);
                }
            });
        }
    }

    /**
     * Handle rate limit response
     */
    handleRateLimit(xhr) {
        const retryAfter = xhr.getResponseHeader('Retry-After');
        const rateLimitInfo = {
            limit: xhr.getResponseHeader('X-RateLimit-Limit'),
            remaining: xhr.getResponseHeader('X-RateLimit-Remaining'),
            reset: xhr.getResponseHeader('X-RateLimit-Reset'),
            retryAfter: retryAfter
        };

        console.warn('Rate limit exceeded:', rateLimitInfo);
        
        // Show user message
        const message = `Too many requests. Please wait ${retryAfter} seconds before trying again.`;
        this.showRateLimitMessage(message, rateLimitInfo);
        
        // Store rate limit info
        this.limits.set(xhr.responseURL || 'global', rateLimitInfo);
    }

    /**
     * Show rate limit message
     */
    showRateLimitMessage(message, rateLimitInfo) {
        if (typeof showNotification === 'function') {
            showNotification(message, 'warning');
        } else {
            console.warn(message);
            alert(message);
        }
    }

    /**
     * Check if URL is rate limited
     */
    isRateLimited(url) {
        const limitInfo = this.limits.get(url) || this.limits.get('global');
        if (!limitInfo) return false;
        
        const now = Math.floor(Date.now() / 1000);
        return now < parseInt(limitInfo.reset);
    }

    /**
     * Get rate limit info for URL
     */
    getRateLimitInfo(url) {
        return this.limits.get(url) || this.limits.get('global');
    }
}

// Initialize managers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.csrfManager = new CSRFManager();
    window.rateLimitManager = new RateLimitManager();
    
    console.log('CSRF and Rate Limit managers initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CSRFManager, RateLimitManager };
}