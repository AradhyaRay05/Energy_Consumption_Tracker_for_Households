class ToastNotification {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    /**
     * Show a toast notification
     * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
     * @param {string} title - Toast title
     * @param {string} message - Toast message (optional)
     * @param {number} duration - Duration in milliseconds (default: 5000)
     */
    show(type = 'info', title = '', message = '', duration = 5000) {
        const toast = this.createToast(type, title, message);
        this.container.appendChild(toast);

        // Auto-remove after duration
        const timeout = setTimeout(() => {
            this.hide(toast);
        }, duration);

        // Store timeout ID for manual close
        toast.dataset.timeoutId = timeout;

        return toast;
    }

    createToast(type, title, message) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        // Icon based on type
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <p class="toast-title">${title}</p>
                ${message ? `<p class="toast-message">${message}</p>` : ''}
            </div>
            <button class="toast-close" aria-label="Close">×</button>
            <div class="toast-progress" style="color: ${this.getColor(type)}"></div>
        `;

        // Close button functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            clearTimeout(toast.dataset.timeoutId);
            this.hide(toast);
        });

        return toast;
    }

    hide(toast) {
        toast.classList.add('toast-hiding');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }

    getColor(type) {
        const colors = {
            success: '#06A77D',
            error: '#D62828',
            warning: '#F77F00',
            info: '#2E86AB'
        };
        return colors[type] || colors.info;
    }

    // Convenience methods
    success(title, message = '', duration = 5000) {
        return this.show('success', title, message, duration);
    }

    error(title, message = '', duration = 5000) {
        return this.show('error', title, message, duration);
    }

    warning(title, message = '', duration = 5000) {
        return this.show('warning', title, message, duration);
    }

    info(title, message = '', duration = 5000) {
        return this.show('info', title, message, duration);
    }
}

// Create global instance
const toast = new ToastNotification();

// Make it available globally
window.toast = toast;
