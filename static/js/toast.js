/**
 * Toast Notification System
 * Provides success, error, warning, and info toasts
 */

export function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Set styles based on type
    const colors = {
        success: '#22C55E',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    };
    
    toast.style.cssText = `
        background: white;
        border-left: 4px solid ${colors[type]};
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        min-width: 300px;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 12px;
    `;

    // Add icon based on type
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <span style="font-size: 20px; color: ${colors[type]}; font-weight: bold;">${icons[type]}</span>
        <span style="flex: 1; color: #1F2937; font-size: 14px;">${message}</span>
        <button style="background: none; border: none; color: #6B7280; cursor: pointer; font-size: 18px; padding: 0;">&times;</button>
    `;

    // Add close button functionality
    const closeBtn = toast.querySelector('button');
    closeBtn.onclick = () => removeToast(toast);

    // Add to container
    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => removeToast(toast), duration);

    return toast;
}

function removeToast(toast) {
    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Add CSS animations if not already present
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
