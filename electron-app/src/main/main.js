/**
 * Main Electron process for the Tienda Loyalty System
 */
const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const isDev = process.argv.includes('--dev');
const LoyaltyService = require('./loyalty-service');

// Keep a global reference of the window object
let mainWindow;
let loyaltyService;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, '../../assets/icon.png'),
    show: false
  });

  // Load the cashier interface
  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (loyaltyService) {
      loyaltyService.disconnect();
    }
  });

  // Initialize loyalty service
  loyaltyService = new LoyaltyService(mainWindow);
  loyaltyService.connect();
}

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();

  // Create application menu
  createMenu();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('start-customer-registration', async () => {
  if (loyaltyService) {
    return await loyaltyService.startCustomerRegistration();
  }
  return { success: false, error: 'Service not connected' };
});

ipcMain.handle('scan-customer-barcode', async (event, barcode) => {
  if (loyaltyService) {
    return await loyaltyService.scanCustomerBarcode(barcode);
  }
  return { success: false, error: 'Service not connected' };
});

ipcMain.handle('get-connection-status', () => {
  if (loyaltyService) {
    return loyaltyService.getConnectionStatus();
  }
  return { connected: false };
});

ipcMain.handle('get-recent-activity', async () => {
  if (loyaltyService) {
    return await loyaltyService.getRecentActivity();
  }
  return { purchases: [], customers: [] };
});

ipcMain.handle('search-customers', async (event, query) => {
  if (loyaltyService) {
    return await loyaltyService.searchCustomers(query);
  }
  return [];
});

ipcMain.handle('reset-tablet', async () => {
  if (loyaltyService) {
    return await loyaltyService.resetTablet();
  }
  return { success: false };
});

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Customer',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-action', 'new-customer');
          }
        },
        {
          label: 'Scan Barcode',
          accelerator: 'CmdOrCtrl+B',
          click: () => {
            mainWindow.webContents.send('menu-action', 'scan-barcode');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.reload();
          }
        },
        {
          label: 'Force Reload',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: () => {
            mainWindow.webContents.reloadIgnoringCache();
          }
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        }
      ]
    },
    {
      label: 'Tablet',
      submenu: [
        {
          label: 'Reset Tablet',
          click: async () => {
            if (loyaltyService) {
              await loyaltyService.resetTablet();
            }
          }
        },
        {
          label: 'Check Connection',
          click: () => {
            mainWindow.webContents.send('menu-action', 'check-connection');
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Tienda Loyalty System',
              message: 'Tienda Loyalty System v1.0.0',
              detail: 'A modern customer loyalty and point tracking system.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Handle protocol for deep linking (optional)
app.setAsDefaultProtocolClient('tienda-loyalty');

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, url) => {
    event.preventDefault();
  });
});
