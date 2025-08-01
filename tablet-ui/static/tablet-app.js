/**
 * Tablet interface application for Tienda Loyalty System
 * Handles customer-facing interactions and WebSocket communication
 */

class TabletInterface {
  constructor() {
    this.socket = null;
    this.currentState = 'idle';
    this.isConnected = false;
    this.idleTimeout = null;
    this.countdownInterval = null;
    
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.connectWebSocket();
    this.showState('idle');
    
    // Auto-reset to idle after inactivity
    this.setupIdleTimer();
  }

  setupEventListeners() {
    // Registration form
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
      registrationForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitRegistration();
      });
    }

    // Retry button
    const retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.showState('idle');
      });
    }

    // Reset idle timer on any interaction
    document.addEventListener('click', () => this.resetIdleTimer());
    document.addEventListener('keypress', () => this.resetIdleTimer());
    document.addEventListener('touchstart', () => this.resetIdleTimer());

    // Prevent context menu and text selection
    document.addEventListener('contextmenu', (e) => e.preventDefault());
    document.addEventListener('selectstart', (e) => e.preventDefault());
  }

  connectWebSocket() {
    try {
      // Connect to backend WebSocket
      this.socket = io('/ws/tablet', {
        transports: ['websocket'],
        upgrade: false,
        timeout: 20000,
        forceNew: true
      });

      this.socket.on('connect', () => {
        console.log('Connected to backend');
        this.isConnected = true;
        this.updateConnectionIndicator(true);
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from backend');
        this.isConnected = false;
        this.updateConnectionIndicator(false);
      });

      this.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        this.isConnected = false;
        this.updateConnectionIndicator(false);
      });

      // Handle backend messages
      this.socket.on('message', (data) => {
        this.handleBackendMessage(data);
      });

      // Heartbeat
      setInterval(() => {
        if (this.isConnected) {
          this.socket.emit('heartbeat');
        }
      }, 30000);

    } catch (error) {
      console.error('Error setting up WebSocket:', error);
      this.updateConnectionIndicator(false);
    }
  }

  handleBackendMessage(data) {
    console.log('Received message:', data);
    
    switch (data.action) {
      case 'show_registration_form':
        this.showRegistrationForm(data);
        break;
      case 'show_confirmation':
        this.showConfirmation(data);
        break;
      case 'show_error':
        this.showError(data);
        break;
      case 'show_customer_info':
        this.showCustomerInfo(data);
        break;
      case 'show_purchase_complete':
        this.showPurchaseComplete(data);
        break;
      case 'set_state':
        this.showState(data.state);
        break;
      case 'heartbeat_ack':
        // Heartbeat acknowledged
        break;
      default:
        console.warn('Unknown action:', data.action);
    }
  }

  showState(state) {
    console.log('Showing state:', state);
    
    // Hide all states
    const allStates = document.querySelectorAll('.state-container');
    allStates.forEach(container => {
      container.classList.remove('active');
    });

    // Show target state
    const targetState = document.getElementById(`${state}State`);
    if (targetState) {
      targetState.classList.add('active');
      this.currentState = state;
    }

    // Reset idle timer for non-idle states
    if (state !== 'idle') {
      this.resetIdleTimer();
    }
  }

  showRegistrationForm(data) {
    this.showState('registration');
    
    // Focus on first input
    setTimeout(() => {
      const firstInput = document.getElementById('customerName');
      if (firstInput) {
        firstInput.focus();
      }
    }, 300);

    // Set form timeout if specified
    if (data.timeout) {
      setTimeout(() => {
        if (this.currentState === 'registration') {
          this.showState('idle');
        }
      }, data.timeout * 1000);
    }
  }

  submitRegistration() {
    const form = document.getElementById('registrationForm');
    const formData = new FormData(form);
    
    const customerData = {
      name: formData.get('name')?.trim(),
      email: formData.get('email')?.trim() || null,
      phone: formData.get('phone')?.trim() || null
    };

    // Validate required fields
    if (!customerData.name) {
      this.showFormError('Please enter your name');
      return;
    }

    // Send to backend
    if (this.isConnected) {
      this.socket.emit('submit_customer_form', {
        action: 'submit_customer_form',
        data: customerData
      });
      
      console.log('Registration submitted:', customerData);
    } else {
      this.showError({ message: 'Connection lost. Please try again.' });
    }
  }

  showFormError(message) {
    // Create or update error message in form
    let errorElement = document.querySelector('.form-error');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'form-error';
      errorElement.style.cssText = `
        background: #fef2f2;
        color: #dc2626;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #fecaca;
      `;
      
      const form = document.getElementById('registrationForm');
      form.insertBefore(errorElement, form.firstChild);
    }
    
    errorElement.textContent = message;
    
    // Remove error after 5 seconds
    setTimeout(() => {
      if (errorElement.parentNode) {
        errorElement.parentNode.removeChild(errorElement);
      }
    }, 5000);
  }

  showConfirmation(data) {
    this.showState('confirmation');
    
    // Update confirmation message
    const title = document.getElementById('confirmationTitle');
    const message = document.getElementById('confirmationMessage');
    
    if (data.title) title.textContent = data.title;
    if (data.message) message.textContent = data.message;

    // Show customer card if customer data is available
    if (data.customer) {
      this.displayCustomerCard(data.customer);
    }

    // Auto-reset timer
    const autoReset = data.auto_reset || 5;
    this.startCountdown(autoReset);
  }

  displayCustomerCard(customer) {
    const customerCard = document.getElementById('customerCard');
    const customerName = document.getElementById('newCustomerName');
    const barcodeContainer = document.getElementById('barcodeContainer');
    const barcodeNumber = document.getElementById('barcodeNumber');
    
    if (customer.name) {
      customerName.textContent = customer.name;
    }
    
    if (customer.barcode_data) {
      barcodeNumber.textContent = customer.barcode_data;
    }
    
    // Show barcode image if available
    if (customer.barcode_image) {
      barcodeContainer.innerHTML = `<img src="${customer.barcode_image}" alt="Customer Barcode" style="max-width: 100%; height: auto;">`;
    }
    
    customerCard.style.display = 'block';
  }

  showCustomerInfo(data) {
    this.showState('customerInfo');
    
    const customerDisplay = document.getElementById('customerDisplay');
    
    if (data.customer) {
      customerDisplay.innerHTML = `
        <div style="text-align: center;">
          <h3 style="font-size: 1.5rem; margin-bottom: 1rem;">${data.customer.name}</h3>
          <p style="font-size: 1rem; color: #6b7280;">Member since ${new Date(data.customer.joined_at).toLocaleDateString()}</p>
        </div>
      `;
    } else {
      customerDisplay.innerHTML = `
        <div style="text-align: center;">
          <h3 style="font-size: 1.5rem; margin-bottom: 1rem;">Customer: ${data.barcode}</h3>
          <p style="font-size: 1rem; color: #6b7280;">Processing purchase...</p>
        </div>
      `;
    }

    // Auto-reset after 10 seconds if no purchase processed
    setTimeout(() => {
      if (this.currentState === 'customerInfo') {
        this.showState('idle');
      }
    }, 10000);
  }

  showPurchaseComplete(data) {
    this.showState('purchaseComplete');
    
    const purchaseSummary = document.getElementById('purchaseSummary');
    const pointsAwarded = document.getElementById('pointsAwarded');
    
    if (data.receipt_data) {
      purchaseSummary.innerHTML = `
        <div style="text-align: center;">
          <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem;">Purchase Amount</h3>
          <p style="font-size: 2rem; font-weight: 600; color: #059669;">$${data.receipt_data.amount || '0.00'}</p>
        </div>
      `;
    }
    
    if (data.points_awarded) {
      pointsAwarded.innerHTML = `
        <div style="text-align: center;">
          <i class="fas fa-star" style="font-size: 2rem; margin-bottom: 1rem;"></i>
          <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem;">Points Earned</h3>
          <p style="font-size: 2.5rem; font-weight: 700;">${data.points_awarded}</p>
        </div>
      `;
    }

    // Auto-reset after 8 seconds
    const autoReset = data.auto_reset || 8;
    setTimeout(() => {
      this.showState('idle');
    }, autoReset * 1000);
  }

  showError(data) {
    this.showState('error');
    
    const errorMessage = document.getElementById('errorMessage');
    if (data.message) {
      errorMessage.textContent = data.message;
    }

    // Auto-reset after 3 seconds if specified
    if (data.auto_reset) {
      setTimeout(() => {
        this.showState('idle');
      }, data.auto_reset * 1000);
    }
  }

  startCountdown(seconds) {
    const countdownElement = document.getElementById('countdown');
    if (!countdownElement) return;

    let remaining = seconds;
    countdownElement.textContent = remaining;

    this.countdownInterval = setInterval(() => {
      remaining--;
      countdownElement.textContent = remaining;
      
      if (remaining <= 0) {
        clearInterval(this.countdownInterval);
        this.showState('idle');
      }
    }, 1000);
  }

  setupIdleTimer() {
    this.resetIdleTimer();
  }

  resetIdleTimer() {
    // Clear existing timer
    if (this.idleTimeout) {
      clearTimeout(this.idleTimeout);
    }

    // Don't set timer if in idle state
    if (this.currentState === 'idle') {
      return;
    }

    // Set new timer for 30 seconds
    this.idleTimeout = setTimeout(() => {
      if (this.currentState !== 'idle') {
        console.log('Auto-reset to idle due to inactivity');
        this.showState('idle');
      }
    }, 30000);
  }

  updateConnectionIndicator(connected) {
    const indicator = document.getElementById('connectionIndicator');
    if (indicator) {
      if (connected) {
        indicator.classList.remove('disconnected');
        indicator.innerHTML = '<i class="fas fa-wifi"></i>';
      } else {
        indicator.classList.add('disconnected');
        indicator.innerHTML = '<i class="fas fa-wifi-slash"></i>';
      }
    }
  }

  // Public methods for debugging
  simulateRegistration() {
    this.showRegistrationForm({ timeout: 120 });
  }

  simulateConfirmation() {
    this.showConfirmation({
      message: 'Welcome, Test Customer!',
      customer: {
        name: 'Test Customer',
        barcode_data: 'TEST123456789',
        barcode_image: null
      },
      auto_reset: 5
    });
  }

  simulatePurchase() {
    this.showPurchaseComplete({
      receipt_data: { amount: 45.99 },
      points_awarded: 46,
      auto_reset: 8
    });
  }
}

// Initialize the tablet interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.tabletInterface = new TabletInterface();
  
  // Expose methods for debugging in development
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.debug = {
      showRegistration: () => window.tabletInterface.simulateRegistration(),
      showConfirmation: () => window.tabletInterface.simulateConfirmation(),
      showPurchase: () => window.tabletInterface.simulatePurchase(),
      showIdle: () => window.tabletInterface.showState('idle'),
      showError: () => window.tabletInterface.showError({ message: 'Test error message' })
    };
    
    console.log('Debug methods available: window.debug');
  }
});
