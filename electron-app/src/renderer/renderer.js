/**
 * Renderer process for the Tienda Loyalty System
 * Handles UI interactions and communication with main process
 */

const { ipcRenderer } = require('electron');

class CashierInterface {
  constructor() {
    this.currentCustomer = null;
    this.connectionStatus = false;
    this.barcodeModal = null;
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.updateClock();
    this.loadRecentActivity();
    this.checkConnectionStatus();
    
    // Update clock every second
    setInterval(() => this.updateClock(), 1000);
    
    // Check connection every 30 seconds
    setInterval(() => this.checkConnectionStatus(), 30000);
  }

  setupEventListeners() {
    // Button event listeners
    document.getElementById('newCustomerBtn').addEventListener('click', () => {
      this.startCustomerRegistration();
    });

    document.getElementById('scanBarcodeBtn').addEventListener('click', () => {
      this.showBarcodeScanner();
    });

    document.getElementById('resetTabletBtn').addEventListener('click', () => {
      this.resetTablet();
    });

    // Modal event listeners
    document.getElementById('closeBarcodeModal').addEventListener('click', () => {
      this.hideBarcodeScanner();
    });

    document.getElementById('processBarcodeBtn').addEventListener('click', () => {
      this.processBarcodeInput();
    });

    // Barcode input listener
    document.getElementById('barcodeInput').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.processBarcodeInput();
      }
    });

    // IPC event listeners
    ipcRenderer.on('connection-status', (event, data) => {
      this.updateConnectionStatus(data.connected);
    });

    ipcRenderer.on('customer-scanned', (event, data) => {
      this.handleCustomerScanned(data);
    });

    ipcRenderer.on('customer-registered', (event, data) => {
      this.handleCustomerRegistered(data);
    });

    ipcRenderer.on('purchase-processed', (event, data) => {
      this.handlePurchaseProcessed(data);
    });

    ipcRenderer.on('registration-started', () => {
      this.showStatusMessage('Customer registration started on tablet', 'success');
    });

    ipcRenderer.on('tablet-reset', () => {
      this.showStatusMessage('Tablet reset to idle state', 'info');
    });

    ipcRenderer.on('menu-action', (event, action) => {
      this.handleMenuAction(action);
    });

    // Close modal when clicking outside
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        this.hideBarcodeScanner();
      }
    });
  }

  updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    document.getElementById('currentTime').textContent = timeString;
  }

  async checkConnectionStatus() {
    try {
      const status = await ipcRenderer.invoke('get-connection-status');
      this.updateConnectionStatus(status.connected);
    } catch (error) {
      console.error('Error checking connection status:', error);
      this.updateConnectionStatus(false);
    }
  }

  updateConnectionStatus(connected) {
    this.connectionStatus = connected;
    const statusElement = document.getElementById('connectionStatus');
    const indicator = statusElement.querySelector('.status-indicator');
    const text = statusElement.querySelector('span');

    if (connected) {
      indicator.classList.add('connected');
      text.textContent = 'Connected';
    } else {
      indicator.classList.remove('connected');
      text.textContent = 'Disconnected';
    }

    // Enable/disable buttons based on connection
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(btn => {
      btn.disabled = !connected;
      if (!connected) {
        btn.style.opacity = '0.5';
        btn.style.pointerEvents = 'none';
      } else {
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
      }
    });
  }

  async startCustomerRegistration() {
    try {
      const result = await ipcRenderer.invoke('start-customer-registration');
      if (result.success) {
        this.showStatusMessage('Customer registration started on tablet', 'success');
      } else {
        this.showStatusMessage(`Error: ${result.error}`, 'error');
      }
    } catch (error) {
      console.error('Error starting customer registration:', error);
      this.showStatusMessage('Failed to start customer registration', 'error');
    }
  }

  showBarcodeScanner() {
    this.barcodeModal = document.getElementById('barcodeModal');
    this.barcodeModal.classList.add('show');
    
    // Clear previous input and focus
    const input = document.getElementById('barcodeInput');
    input.value = '';
    input.focus();
    
    // Clear previous status
    const status = document.getElementById('barcodeStatus');
    status.style.display = 'none';
    status.className = 'barcode-status';
  }

  hideBarcodeScanner() {
    if (this.barcodeModal) {
      this.barcodeModal.classList.remove('show');
    }
  }

  async processBarcodeInput() {
    const input = document.getElementById('barcodeInput');
    const barcode = input.value.trim();
    
    if (!barcode) {
      this.showBarcodeStatus('Please enter a barcode', 'error');
      return;
    }

    try {
      this.showBarcodeStatus('Processing barcode...', 'info');
      
      const result = await ipcRenderer.invoke('scan-customer-barcode', barcode);
      
      if (result.success) {
        if (result.customer) {
          this.showBarcodeStatus(`Customer found: ${result.customer.name}`, 'success');
          setTimeout(() => this.hideBarcodeScanner(), 2000);
        } else {
          this.showBarcodeStatus('Customer not found - they can still make a purchase', 'warning');
        }
      } else {
        this.showBarcodeStatus(`Error: ${result.error}`, 'error');
      }
    } catch (error) {
      console.error('Error processing barcode:', error);
      this.showBarcodeStatus('Failed to process barcode', 'error');
    }
  }

  showBarcodeStatus(message, type) {
    const status = document.getElementById('barcodeStatus');
    status.textContent = message;
    status.className = `barcode-status ${type}`;
    status.style.display = 'block';
  }

  async resetTablet() {
    try {
      const result = await ipcRenderer.invoke('reset-tablet');
      if (result.success) {
        this.showStatusMessage('Tablet reset successfully', 'success');
        this.clearCurrentCustomer();
      } else {
        this.showStatusMessage(`Error resetting tablet: ${result.error}`, 'error');
      }
    } catch (error) {
      console.error('Error resetting tablet:', error);
      this.showStatusMessage('Failed to reset tablet', 'error');
    }
  }

  handleCustomerScanned(data) {
    this.currentCustomer = data.customer;
    
    if (data.customer) {
      this.showCurrentCustomer(data.customer);
      this.showStatusMessage(`Customer scanned: ${data.customer.name}`, 'success');
    } else {
      this.showStatusMessage(`Barcode scanned: ${data.barcode} (unregistered customer)`, 'info');
    }
  }

  handleCustomerRegistered(data) {
    if (data.success && data.customer) {
      this.showStatusMessage(`New customer registered: ${data.customer.name}`, 'success');
      this.loadRecentActivity(); // Refresh the customer list
    } else {
      this.showStatusMessage('Customer registration failed', 'error');
    }
  }

  handlePurchaseProcessed(data) {
    if (data.success) {
      const customer = data.customer;
      const purchase = data.purchase;
      const points = data.points_awarded;
      
      this.showStatusMessage(
        `Purchase processed: $${purchase.amount} - ${points} points awarded to ${customer.name}`,
        'success'
      );
      
      this.loadRecentActivity(); // Refresh activity
      this.clearCurrentCustomer();
    } else {
      this.showStatusMessage('Purchase processing failed', 'error');
    }
  }

  showCurrentCustomer(customer) {
    const panel = document.getElementById('currentCustomerPanel');
    const info = document.getElementById('customerInfo');
    
    info.innerHTML = `
      <div class="customer-detail">
        <div class="label">Name</div>
        <div class="value">${customer.name}</div>
      </div>
      <div class="customer-detail">
        <div class="label">Email</div>
        <div class="value">${customer.email || 'Not provided'}</div>
      </div>
      <div class="customer-detail">
        <div class="label">Phone</div>
        <div class="value">${customer.phone || 'Not provided'}</div>
      </div>
      <div class="customer-detail">
        <div class="label">Barcode</div>
        <div class="value">${customer.barcode_data}</div>
      </div>
      <div class="customer-detail">
        <div class="label">Member Since</div>
        <div class="value">${new Date(customer.joined_at).toLocaleDateString()}</div>
      </div>
    `;
    
    panel.style.display = 'block';
  }

  clearCurrentCustomer() {
    this.currentCustomer = null;
    document.getElementById('currentCustomerPanel').style.display = 'none';
  }

  async loadRecentActivity() {
    try {
      const activity = await ipcRenderer.invoke('get-recent-activity');
      this.updateRecentPurchases(activity.recent_purchases || []);
      this.updateRecentCustomers(activity.recent_customers || []);
    } catch (error) {
      console.error('Error loading recent activity:', error);
    }
  }

  updateRecentPurchases(purchases) {
    const container = document.getElementById('recentPurchases');
    
    if (purchases.length === 0) {
      container.innerHTML = '<div class="loading">No recent purchases</div>';
      return;
    }

    container.innerHTML = purchases.map(purchase => `
      <div class="activity-item">
        <div class="activity-item-info">
          <div class="activity-item-title">Purchase #${purchase.receipt_id || purchase.id.slice(-8)}</div>
          <div class="activity-item-subtitle">${new Date(purchase.timestamp).toLocaleString()}</div>
        </div>
        <div class="activity-item-value success">$${purchase.amount}</div>
      </div>
    `).join('');
  }

  updateRecentCustomers(customers) {
    const container = document.getElementById('recentCustomers');
    
    if (customers.length === 0) {
      container.innerHTML = '<div class="loading">No recent customers</div>';
      return;
    }

    container.innerHTML = customers.map(customer => `
      <div class="activity-item">
        <div class="activity-item-info">
          <div class="activity-item-title">${customer.name}</div>
          <div class="activity-item-subtitle">${customer.email || customer.phone || 'No contact info'}</div>
        </div>
        <div class="activity-item-value info">${customer.barcode_data}</div>
      </div>
    `).join('');
  }

  handleMenuAction(action) {
    switch (action) {
      case 'new-customer':
        this.startCustomerRegistration();
        break;
      case 'scan-barcode':
        this.showBarcodeScanner();
        break;
      case 'check-connection':
        this.checkConnectionStatus();
        break;
    }
  }

  showStatusMessage(message, type = 'info') {
    const container = document.getElementById('statusMessages');
    
    const messageElement = document.createElement('div');
    messageElement.className = `status-message ${type}`;
    messageElement.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <i class="fas fa-${this.getStatusIcon(type)}"></i>
        <span>${message}</span>
      </div>
    `;
    
    container.appendChild(messageElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
      }
    }, 5000);
  }

  getStatusIcon(type) {
    switch (type) {
      case 'success': return 'check-circle';
      case 'error': return 'exclamation-circle';
      case 'warning': return 'exclamation-triangle';
      default: return 'info-circle';
    }
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.cashierInterface = new CashierInterface();
});
