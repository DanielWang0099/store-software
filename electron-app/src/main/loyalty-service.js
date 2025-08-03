/**
 * Loyalty service for handling backend communication
 */
const io = require('socket.io-client');
const axios = require('axios');
const Store = require('electron-store');

class LoyaltyService {
  constructor(mainWindow) {
    this.mainWindow = mainWindow;
    this.socket = null;
    this.store = new Store();
    this.apiBaseUrl = 'http://localhost:8000';
    this.isConnected = false;
    this.currentCustomerScan = null;
    
    // Load settings
    this.loadSettings();
  }

  loadSettings() {
    this.apiBaseUrl = this.store.get('apiBaseUrl', 'http://127.0.0.1:8000');
  }

  async connect() {
    const maxRetries = 5;
    const retryDelay = 2000; // 2 seconds
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Test API connection first
        const response = await axios.get(`${this.apiBaseUrl}/health`, {
          timeout: 5000
        });
        console.log(`Backend API connected (attempt ${attempt}):`, response.data);

        // Connect WebSocket
        this.socket = io(this.apiBaseUrl, {
          transports: ['websocket'],
          upgrade: false,
          timeout: 10000,
          reconnection: true,
          reconnectionAttempts: 3,
          reconnectionDelay: 2000
        });

        this.socket.on('connect', () => {
          console.log('WebSocket connected to backend');
          this.isConnected = true;
          this.notifyRenderer('connection-status', { connected: true });
          
          // Identify as electron client
          this.socket.emit('identify_client', { type: 'electron' });
        });

        this.socket.on('disconnect', () => {
          console.log('WebSocket disconnected from backend');
          this.isConnected = false;
          this.notifyRenderer('connection-status', { connected: false });
        });

        // Handle backend messages
        this.socket.on('message', (data) => {
          this.handleBackendMessage(data);
        });
        
        this.socket.on('electron_message', (data) => {
          this.handleBackendMessage(data);
        });

        this.socket.on('process_customer_registration', (data) => {
          this.handleCustomerRegistration(data);
        });

        this.socket.on('process_purchase', (data) => {
          this.handlePurchaseProcessing(data);
        });

        // Connection successful, break out of retry loop
        break;

      } catch (error) {
        console.error(`Connection attempt ${attempt} failed:`, error.message);
        
        if (attempt === maxRetries) {
          console.error('All connection attempts failed');
          this.notifyRenderer('connection-error', { 
            error: `Failed to connect after ${maxRetries} attempts: ${error.message}` 
          });
        } else {
          console.log(`Retrying in ${retryDelay / 1000} seconds...`);
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnected = false;
  }

  async startCustomerRegistration() {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to backend' };
    }

    try {
      this.socket.emit('message', {
        action: 'start_registration',
        timestamp: new Date().toISOString()
      });

      this.notifyRenderer('registration-started', {});
      
      return { success: true };
    } catch (error) {
      console.error('Error starting customer registration:', error);
      return { success: false, error: error.message };
    }
  }

  async scanCustomerBarcode(barcode) {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to backend' };
    }

    try {
      // Store current scan
      this.currentCustomerScan = {
        barcode: barcode,
        scannedAt: new Date().toISOString()
      };

      // Send to backend
      this.socket.emit('message', {
        action: 'customer_scanned',
        barcode: barcode,
        timestamp: new Date().toISOString()
      });

      // Try to find customer info
      const customer = await this.getCustomerByBarcode(barcode);
      
      this.notifyRenderer('customer-scanned', {
        barcode: barcode,
        customer: customer,
        timestamp: new Date().toISOString()
      });

      return { success: true, customer: customer };
    } catch (error) {
      console.error('Error scanning customer barcode:', error);
      return { success: false, error: error.message };
    }
  }

  async getCustomerByBarcode(barcode) {
    try {
      const response = await axios.get(`${this.apiBaseUrl}/api/customers/barcode/${barcode}`);
      return response.data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return null; // Customer not found
      }
      throw error;
    }
  }

  async getRecentActivity() {
    try {
      const response = await axios.get(`${this.apiBaseUrl}/api/admin/recent-activity`);
      return response.data;
    } catch (error) {
      console.error('Error getting recent activity:', error);
      return { recent_purchases: [], recent_customers: [] };
    }
  }

  async searchCustomers(query) {
    try {
      const response = await axios.get(`${this.apiBaseUrl}/api/customers`, {
        params: { search: query }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching customers:', error);
      return [];
    }
  }

  async resetTablet() {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to backend' };
    }

    try {
      this.socket.emit('message', {
        action: 'reset_tablet',
        timestamp: new Date().toISOString()
      });

      return { success: true };
    } catch (error) {
      console.error('Error resetting tablet:', error);
      return { success: false, error: error.message };
    }
  }

  handleBackendMessage(data) {
    console.log('Received from backend:', data);
    
    switch (data.action) {
      case 'tablet_reset':
        this.notifyRenderer('tablet-reset', data);
        break;
      case 'registration_started':
        this.notifyRenderer('registration-started', data);
        break;
      case 'system_status':
        this.notifyRenderer('system-status', data);
        break;
      default:
        this.notifyRenderer('backend-message', data);
    }
  }

  async handleCustomerRegistration(data) {
    try {
      const customerData = data.customer_data;
      
      // Create customer via API
      const response = await axios.post(`${this.apiBaseUrl}/api/customers`, customerData);
      const newCustomer = response.data;

      console.log('Customer registered:', newCustomer);
      
      this.notifyRenderer('customer-registered', {
        customer: newCustomer,
        success: true
      });

    } catch (error) {
      console.error('Error processing customer registration:', error);
      this.notifyRenderer('customer-registration-error', {
        error: error.message,
        success: false
      });
    }
  }

  async handlePurchaseProcessing(data) {
    try {
      const purchaseData = data.purchase_data;
      
      // Process purchase via API
      const response = await axios.post(`${this.apiBaseUrl}/api/purchases/process-barcode-purchase`, {
        barcode: purchaseData.barcode,
        receipt_data: purchaseData.receipt_data
      });
      
      const result = response.data;
      
      console.log('Purchase processed:', result);
      
      // Notify backend that receipt was processed
      this.socket.emit('message', {
        action: 'receipt_processed',
        receipt_data: {
          ...result.purchase,
          points_awarded: result.points_awarded
        }
      });

      this.notifyRenderer('purchase-processed', {
        purchase: result.purchase,
        customer: result.customer,
        points_awarded: result.points_awarded,
        success: true
      });

      // Clear current customer scan
      this.currentCustomerScan = null;

    } catch (error) {
      console.error('Error processing purchase:', error);
      this.notifyRenderer('purchase-processing-error', {
        error: error.message,
        success: false
      });
    }
  }

  notifyRenderer(event, data) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send(event, data);
    }
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      apiBaseUrl: this.apiBaseUrl,
      currentCustomerScan: this.currentCustomerScan
    };
  }
}

module.exports = LoyaltyService;
