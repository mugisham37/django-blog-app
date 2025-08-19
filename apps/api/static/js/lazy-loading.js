/**
 * Lazy loading and infinite scroll functionality
 * for Django Personal Blog System
 */

class LazyImageLoader {
    constructor() {
        this.imageObserver = null;
        this.init();
    }

    init() {
        // Use Intersection Observer for modern browsers
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver(
                this.handleImageIntersection.bind(this),
                {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                }
            );
            this.observeImages();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }
    }

    observeImages() {
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(img => {
            this.imageObserver.observe(img);
        });
    }

    handleImageIntersection(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                this.loadImage(img);
                observer.unobserve(img);
            }
        });
    }

    loadImage(img) {
        const container = img.closest('.lazy-image-container');
        const placeholder = container?.querySelector('.lazy-image-placeholder');
        
        // Show loading state
        if (placeholder) {
            placeholder.classList.add('loading');
        }

        // Create new image to preload
        const imageLoader = new Image();
        
        imageLoader.onload = () => {
            // Set the actual src
            img.src = img.dataset.src;
            
            // Set srcset if available
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
            }
            
            // Remove data attributes
            delete img.dataset.src;
            delete img.dataset.srcset;
            
            // Add loaded class for animations
            img.classList.add('loaded');
            
            // Hide placeholder
            if (placeholder) {
                placeholder.style.opacity = '0';
                setTimeout(() => {
                    placeholder.style.display = 'none';
                }, 300);
            }
        };
        
        imageLoader.onerror = () => {
            // Handle error - show error placeholder or hide image
            img.classList.add('error');
            if (placeholder) {
                placeholder.innerHTML = '<div class="image-error">Failed to load image</div>';
                placeholder.classList.remove('loading');
            }
        };
        
        // Start loading
        imageLoader.src = img.dataset.src;
    }

    loadAllImages() {
        // Fallback for browsers without Intersection Observer
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(img => {
            this.loadImage(img);
        });
    }

    // Method to handle dynamically added images
    observeNewImages() {
        if (this.imageObserver) {
            const newImages = document.querySelectorAll('.lazy-image[data-src]:not(.observed)');
            newImages.forEach(img => {
                img.classList.add('observed');
                this.imageObserver.observe(img);
            });
        }
    }
}

class InfiniteScroll {
    constructor(options = {}) {
        this.container = options.container || '.post-list';
        this.loadMoreUrl = options.loadMoreUrl || null;
        this.loadingClass = options.loadingClass || 'loading';
        this.endClass = options.endClass || 'end-reached';
        this.threshold = options.threshold || 200;
        
        this.isLoading = false;
        this.hasMore = true;
        this.page = 1;
        
        this.init();
    }

    init() {
        this.containerElement = document.querySelector(this.container);
        if (!this.containerElement) return;

        // Create loading indicator
        this.createLoadingIndicator();
        
        // Set up scroll listener
        if ('IntersectionObserver' in window) {
            this.setupIntersectionObserver();
        } else {
            this.setupScrollListener();
        }
    }

    createLoadingIndicator() {
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'infinite-scroll-loading';
        this.loadingIndicator.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <span>Loading more posts...</span>
            </div>
        `;
        this.loadingIndicator.style.display = 'none';
        
        // Insert after container
        this.containerElement.parentNode.insertBefore(
            this.loadingIndicator, 
            this.containerElement.nextSibling
        );
    }

    setupIntersectionObserver() {
        this.scrollObserver = new IntersectionObserver(
            this.handleScrollIntersection.bind(this),
            {
                rootMargin: `${this.threshold}px`,
                threshold: 0.01
            }
        );
        
        this.scrollObserver.observe(this.loadingIndicator);
    }

    setupScrollListener() {
        window.addEventListener('scroll', this.handleScroll.bind(this));
    }

    handleScrollIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                this.loadMore();
            }
        });
    }

    handleScroll() {
        if (this.isLoading || !this.hasMore) return;

        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        if (scrollTop + windowHeight >= documentHeight - this.threshold) {
            this.loadMore();
        }
    }

    async loadMore() {
        if (this.isLoading || !this.hasMore) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const url = this.buildLoadMoreUrl();
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/html'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.html && data.html.trim()) {
                this.appendContent(data.html);
                this.page++;
                
                // Check if there are more pages
                this.hasMore = data.has_next || false;
                
                // Observe new lazy images
                if (window.lazyImageLoader) {
                    window.lazyImageLoader.observeNewImages();
                }
                
                // Trigger custom event
                this.containerElement.dispatchEvent(new CustomEvent('infiniteScrollLoaded', {
                    detail: { page: this.page, hasMore: this.hasMore }
                }));
            } else {
                this.hasMore = false;
            }

        } catch (error) {
            console.error('Error loading more content:', error);
            this.showError();
        } finally {
            this.isLoading = false;
            this.hideLoading();
            
            if (!this.hasMore) {
                this.showEndMessage();
            }
        }
    }

    buildLoadMoreUrl() {
        if (this.loadMoreUrl) {
            const url = new URL(this.loadMoreUrl, window.location.origin);
            url.searchParams.set('page', this.page + 1);
            return url.toString();
        }
        
        // Build URL from current page
        const url = new URL(window.location);
        url.searchParams.set('page', this.page + 1);
        return url.toString();
    }

    appendContent(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Append each child to the container
        while (tempDiv.firstChild) {
            this.containerElement.appendChild(tempDiv.firstChild);
        }
    }

    showLoading() {
        this.loadingIndicator.style.display = 'block';
        this.containerElement.classList.add(this.loadingClass);
    }

    hideLoading() {
        this.loadingIndicator.style.display = 'none';
        this.containerElement.classList.remove(this.loadingClass);
    }

    showError() {
        this.loadingIndicator.innerHTML = `
            <div class="loading-error">
                <span>Failed to load more posts</span>
                <button onclick="window.infiniteScroll.loadMore()" class="retry-btn">Retry</button>
            </div>
        `;
        this.loadingIndicator.style.display = 'block';
    }

    showEndMessage() {
        this.loadingIndicator.innerHTML = `
            <div class="loading-end">
                <span>No more posts to load</span>
            </div>
        `;
        this.loadingIndicator.style.display = 'block';
        this.containerElement.classList.add(this.endClass);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize lazy image loading
    window.lazyImageLoader = new LazyImageLoader();
    
    // Initialize infinite scroll if post list exists
    const postList = document.querySelector('.post-list');
    if (postList) {
        window.infiniteScroll = new InfiniteScroll({
            container: '.post-list',
            threshold: 300
        });
    }
});

// Handle dynamic content loading
document.addEventListener('htmx:afterSwap', function() {
    if (window.lazyImageLoader) {
        window.lazyImageLoader.observeNewImages();
    }
});

// Export for use in other scripts
window.LazyImageLoader = LazyImageLoader;
window.InfiniteScroll = InfiniteScroll;