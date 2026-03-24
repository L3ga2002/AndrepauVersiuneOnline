const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

// Configuration
const BRIDGE_URL = 'http://localhost:5555';
const isDev = process.env.ELECTRON_DEV === 'true';
let mainWindow;
let bridgeProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'ANDREPAU POS',
    icon: path.join(__dirname, '../public/favicon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    autoHideMenuBar: true
  });

  // In dev, load from React dev server; in prod, load built files
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    const appPath = app.getAppPath();
    const indexPath = path.join(appPath, 'build', 'index.html');
    console.log('Loading from:', indexPath);
    mainWindow.loadFile(indexPath);
    // Temporary: open DevTools to debug black screen
    mainWindow.webContents.openDevTools();
  }

  // Show errors in production for debugging
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorCode, errorDescription);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ===== Bridge Communication (bypasses browser PNA restrictions) =====

// Direct HTTP call to local bridge - no browser restrictions in Electron!
function callBridge(endpoint, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint, BRIDGE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: method,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ success: true, data: JSON.parse(data), status: res.statusCode });
        } catch {
          resolve({ success: true, data: data, status: res.statusCode });
        }
      });
    });

    req.on('error', (err) => {
      resolve({ success: false, error: err.message });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ success: false, error: 'Timeout' });
    });

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// IPC handlers - React app calls these via preload bridge
ipcMain.handle('bridge:health', async () => {
  return await callBridge('/health');
});

ipcMain.handle('bridge:print-receipt', async (event, receiptData) => {
  return await callBridge('/fiscal/receipt', 'POST', receiptData);
});

ipcMain.handle('bridge:print-receipt-cui', async (event, receiptData) => {
  return await callBridge('/fiscal/receipt_cui', 'POST', receiptData);
});

ipcMain.handle('bridge:cash-in', async (event, data) => {
  return await callBridge('/fiscal/cash_in', 'POST', data);
});

ipcMain.handle('bridge:cash-out', async (event, data) => {
  return await callBridge('/fiscal/cash_out', 'POST', data);
});

ipcMain.handle('bridge:report-x', async () => {
  return await callBridge('/fiscal/report/x', 'POST');
});

ipcMain.handle('bridge:report-z', async () => {
  return await callBridge('/fiscal/report/z', 'POST');
});

ipcMain.handle('bridge:cancel', async () => {
  return await callBridge('/fiscal/cancel', 'POST');
});

ipcMain.handle('bridge:open-drawer', async () => {
  return await callBridge('/fiscal/drawer', 'POST');
});

// Auto-start bridge service
ipcMain.handle('bridge:start', async () => {
  if (bridgeProcess) return { success: true, message: 'Bridge already running' };
  
  try {
    const bridgePath = path.join(process.env.USERPROFILE || '', 'SuccesDrv', 'fiscal_bridge.py');
    bridgeProcess = spawn('python', [bridgePath], {
      cwd: path.join(process.env.USERPROFILE || '', 'SuccesDrv'),
      detached: false
    });
    
    bridgeProcess.on('exit', () => { bridgeProcess = null; });
    
    // Wait a moment for bridge to start
    await new Promise(r => setTimeout(r, 2000));
    const health = await callBridge('/health');
    return health;
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (bridgeProcess) {
    bridgeProcess.kill();
    bridgeProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
