// Django Personal Blog - Main JavaScript with optimization features

// WebP support detection
function detectWebPSupport() {
    return new Promise((resolve) => {
        const webP = new Image();
        webP.onload = webP.onerror = function () {
            resolve(webP.height === 2);
        };
        webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
    });
}

// Apply WebP support class to document
detectWebPSupport().then(hasWebP => {
    document.documentElement.classList.add(hasWebP ? 'webp' : 'no-webp');
});

// Utility functions
const BlogUtils = {
    // Debounce function for performance
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    // Throttle function for scroll events
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Get cookie value
    getCookie: function(name) {
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
    },

    // CSRF token for AJAX requests
    getCSRFToken: function() {
        return this.getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize common functionality
    initializeMessages();
    initializeNavigation();
    enhanceForms();
    initReadingProgress();
    initBackToTop();
    
    // Handle image errors globally
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            handleImageError(e.target);
        }
    }, true);
    
    // Add loading states to external links
    const externalLinks = document.querySelectorAll('a[href^="http"]:not([href*="' + window.location.hostname + '"])');
    externalLinks.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
});

// Auto-hide messages after 5 seconds
function initializeMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
}

// Mobile navigation toggle
function initializeNavigation() {
    console.log('Navigation initialized');
}

// Progressive enhancement for forms
function enhanceForms() {
    const forms = document.querySelectorAll('form[data-enhance]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Processing...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }, 5000);
            }
        });
    });
}

// Reading progress indicator
function initReadingProgress() {
    const progressBar = document.querySelector('.reading-progress');
    const article = document.querySelector('article');
    
    if (progressBar && article) {
        const updateProgress = BlogUtils.throttle(() => {
            const articleTop = article.offsetTop;
            const articleHeight = article.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrollTop = window.pageYOffset;
            
            const progress = Math.min(
                Math.max((scrollTop - articleTop + windowHeight) / articleHeight, 0),
                1
            );
            
            progressBar.style.width = `${progress * 100}%`;
        }, 16); // ~60fps
        
        window.addEventListener('scroll', updateProgress);
        updateProgress(); // Initial call
    }
}

// Back to top button
function initBackToTop() {
    const backToTopBtn = document.querySelector('.back-to-top');
    
    if (backToTopBtn) {
        const toggleVisibility = BlogUtils.throttle(() => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }, 100);
        
        window.addEventListener('scroll', toggleVisibility);
        
        backToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// Image error handling
function handleImageError(img) {
    img.style.display = 'none';
    
    // Try to show a placeholder
    const placeholder = img.nextElementSibling;
    if (placeholder && placeholder.classList.contains('image-placeholder')) {
        placeholder.style.display = 'block';
    }
}

// CSRF token helper for AJAX requests (legacy support)
function getCSRFToken() {
    return BlogUtils.getCSRFToken();
}

// Utility function for making AJAX requests
function makeAjaxRequest(url, method, data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback(null, JSON.parse(xhr.responseText));
            } else {
                callback(new Error('Request failed'), null);
            }
        }
    };
    
    xhr.send(JSON.stringify(data));
}

// Export utilities for use in other scripts
window.BlogUtils = BlogUtils;