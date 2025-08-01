/**
 * Tablet UI Application - Customer Interface
 */
class TabletApp {
  constructor() {
    this.socket = null;
    this.currentState = 'idle';
    this.autoResetTimer = null;
    this.connectionRetryTimer = null;
    
    this.initializeApp();
    this.connectToBackend();
  }

  initializeApp() {
    // Set up form submission
    const form = document.getElementById('registrationForm');
    if (form) {
      form.addEventListener('submit', (e) => this.handleFormSubmission(e));
    }

    // Set up cancel button
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.resetToIdle());
    }

    // Set up touch/click handlers for screen interactions
    this.setupInteractionHandlers();
    
    // Start idle animation
    this.startIdleAnimation();
  }

  connectToBackend() {
    try {
      // Connect to backend WebSocket
      this.socket = io('/ws/tablet', {
        transports: ['websocket'],
        upgrade: false,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10
      });

      this.socket.on('connect', () => {
        console.log('Connected to backend');
        this.handleConnectionStatus(true);
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from backend');
        this.handleConnectionStatus(false);
      });

      this.socket.on('message', (data) => {
        this.handleBackendMessage(data);
      });

      // Handle connection errors
      this.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        this.handleConnectionStatus(false);
      });

    } catch (error) {
      console.error('Error connecting to backend:', error);
      this.scheduleReconnection();
    }
  }

  handleBackendMessage(data) {
    console.log('Received message:', data);
    
    switch (data.action) {
      case 'set_state':
        this.setState(data.state);
        break;
        
      case 'show_registration_form':
        this.showRegistrationForm(data);
        break;
        
      case 'show_customer_info':
        this.showCustomerInfo(data);
        break;
        
      case 'show_confirmation':
        this.showConfirmation(data);
        break;
        
      case 'show_purchase_complete':
        this.showPurchaseComplete(data);
        break;
        
      case 'show_error':
        this.showError(data);
        break;
        
      case 'heartbeat':
        this.socket.emit('message', { action: 'heartbeat_ack' });
        break;
        
      default:
        console.log('Unknown action:', data.action);
    }
  }

  handleFormSubmission(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const customerData = {
      name: formData.get('name'),
      email: formData.get('email'),
      phone: formData.get('phone')
    };

    // Validate required fields
    if (!customerData.name || customerData.name.trim().length < 2) {
      this.showValidationError('Please enter a valid name');
      return;
    }

    // Show loading
    this.showLoading(true);

    // Send to backend
    this.sendMessage({
      action: 'submit_customer_form',
      data: customerData
    });
  }

  sendMessage(message) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
    } else {
      console.error('Not connected to backend');
      this.showError({ message: 'Connection error. Please try again.' });
    }
  }

  setState(state) {
    this.currentState = state;
    this.showScreen(state === 'idle' ? 'idleScreen' : state);
    
    // Clear any auto-reset timer when changing states
    this.clearAutoReset();
  }

  showScreen(screenId) {
    // Hide all screens
    const screens = document.querySelectorAll('.screen');
    screens.forEach(screen => screen.classList.remove('active'));
    
    // Show target screen
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
      targetScreen.classList.add('active');
    }
    
    // Hide loading overlay
    this.showLoading(false);
  }

  showRegistrationForm(data) {
    this.showScreen('registrationScreen');
    
    // Clear form
    const form = document.getElementById('registrationForm');
    if (form) {
      form.reset();
    }
    
    // Focus first input
    const firstInput = document.getElementById('customerName');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100);
    }
    
    // Set auto-reset timer
    this.setAutoReset(data.timeout || 120);
  }

  showCustomerInfo(data) {
    this.showScreen('customerInfoScreen');
    
    const detailsContainer = document.getElementById('customerDetails');
    if (detailsContainer && data.customer) {
      detailsContainer.innerHTML = `
        <div class="detail-item">
          <label>Name:</label>
          <span>${data.customer.name}</span>
        </div>
        <div class="detail-item">
          <label>Member Since:</label>
          <span>${new Date(data.customer.joined_at).toLocaleDateString()}</span>
        </div>
      `;
    }
    
    // Set auto-reset timer
    this.setAutoReset(data.auto_reset || 10);
  }

  showConfirmation(data) {
    this.showScreen('confirmationScreen');
    
    const messageContainer = document.getElementById('confirmationMessage');
    if (messageContainer) {
      messageContainer.innerHTML = `
        <h2>${data.type === 'success' ? 'Success!' : 'Welcome!'}</h2>
        <p>${data.message}</p>
      `;
    }
    
    // Show barcode if provided
    if (data.barcode_image) {
      const barcodeDisplay = document.getElementById('barcodeDisplay');
      const barcodeImage = document.getElementById('barcodeImage');
      
      if (barcodeDisplay && barcodeImage) {
        barcodeImage.src = data.barcode_image;
        barcodeDisplay.style.display = 'block';
      }
    }
    
    // Set auto-reset timer
    this.setAutoReset(data.auto_reset || 5);
  }

  showPurchaseComplete(data) {
    this.showScreen('purchaseCompleteScreen');
    
    // Update purchase info
    const purchaseInfo = document.getElementById('purchaseInfo');
    if (purchaseInfo && data.receipt_data) {
      purchaseInfo.innerHTML = `
        <div class="purchase-detail">
          <label>Amount:</label>
          <span class="amount">$${data.receipt_data.amount}</span>
        </div>
        <div class="purchase-detail">
          <label>Receipt:</label>
          <span>#${data.receipt_data.receipt_id || 'N/A'}</span>
        </div>
      `;
    }
    
    // Update points
    const pointsElement = document.getElementById('pointsAwarded');
    if (pointsElement) {
      pointsElement.textContent = data.points_awarded || 0;
    }
    
    // Set auto-reset timer
    this.setAutoReset(data.auto_reset || 8);
  }

  showError(data) {
    this.showScreen('errorScreen');
    
    const messageContainer = document.getElementById('errorMessage');
    if (messageContainer) {
      messageContainer.innerHTML = `
        <h2>Oops!</h2>
        <p>${data.message || 'Something went wrong. Please try again.'}</p>
      `;
    }
    
    // Set auto-reset timer
    this.setAutoReset(data.auto_reset || 3);
  }

  showValidationError(message) {
    // Show inline validation error
    const existingError = document.querySelector('.validation-error');
    if (existingError) {
      existingError.remove();
    }
    
    const errorElement = document.createElement('div');
    errorElement.className = 'validation-error';
    errorElement.textContent = message;
    
    const form = document.getElementById('registrationForm');
    if (form) {
      form.insertBefore(errorElement, form.querySelector('.form-actions'));
    }
    
    // Remove error after 3 seconds
    setTimeout(() => {
      if (errorElement.parentNode) {
        errorElement.remove();
      }
    }, 3000);
  }

  showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
      overlay.style.display = show ? 'flex' : 'none';
    }
  }

  resetToIdle() {
    this.setState('idle');
    this.clearAutoReset();
    
    // Clear any validation errors
    const validationErrors = document.querySelectorAll('.validation-error');
    validationErrors.forEach(error => error.remove());
    
    // Notify backend
    this.sendMessage({ action: 'reset_to_idle' });
    
    // Restart idle animation
    this.startIdleAnimation();
  }

  setAutoReset(seconds) {
    this.clearAutoReset();
    
    if (seconds > 0) {
      this.autoResetTimer = setTimeout(() => {
        this.resetToIdle();
      }, seconds * 1000);
    }
  }

  clearAutoReset() {
    if (this.autoResetTimer) {
      clearTimeout(this.autoResetTimer);
      this.autoResetTimer = null;
    }
  }

  setupInteractionHandlers() {
    // Reset to idle on screen tap (except during registration)
    document.addEventListener('click', (event) => {
      if (this.currentState === 'idle') {
        // Do nothing on idle screen
        return;
      }
      
      // Don't reset if clicking on form elements
      if (event.target.closest('form') || event.target.closest('.btn')) {
        return;
      }
      
      // Reset to idle after a delay
      setTimeout(() => {
        if (this.currentState !== 'registration') {
          this.resetToIdle();
        }
      }, 5000);
    });
    
    // Handle keyboard input for accessibility
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.resetToIdle();
      }
    });
  }

  startIdleAnimation() {
    // Add CSS animation class to the smiley face
    const smileyFace = document.querySelector('.smiley-face');
    if (smileyFace) {
      smileyFace.classList.add('animated');
    }
  }

  handleConnectionStatus(connected) {
    if (connected) {
      // Connection restored
      if (this.connectionRetryTimer) {
        clearInterval(this.connectionRetryTimer);
        this.connectionRetryTimer = null;
      }
    } else {
      // Connection lost - schedule reconnection attempts
      this.scheduleReconnection();
    }
  }

  scheduleReconnection() {
    if (this.connectionRetryTimer) {
      return; // Already trying to reconnect
    }
    
    this.connectionRetryTimer = setInterval(() => {
      if (!this.socket || !this.socket.connected) {
        console.log('Attempting to reconnect...');
        this.connectToBackend();
      }
    }, 5000);
  }
}

// Initialize the tablet app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.tabletApp = new TabletApp();
});
