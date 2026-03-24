const { contextBridge, ipcRenderer } = require('electron');

// Expose bridge communication to the React app
// React code can call: window.electronBridge.printReceipt(data)
contextBridge.exposeInMainWorld('electronBridge', {
  // Check if running in Electron
  isElectron: true,

  // Bridge health check
  checkBridge: () => ipcRenderer.invoke('bridge:health'),

  // Fiscal operations - direct to local bridge (no cloud needed!)
  printReceipt: (data) => ipcRenderer.invoke('bridge:print-receipt', data),
  printReceiptCUI: (data) => ipcRenderer.invoke('bridge:print-receipt-cui', data),
  cashIn: (data) => ipcRenderer.invoke('bridge:cash-in', data),
  cashOut: (data) => ipcRenderer.invoke('bridge:cash-out', data),
  reportX: () => ipcRenderer.invoke('bridge:report-x'),
  reportZ: () => ipcRenderer.invoke('bridge:report-z'),
  cancelReceipt: () => ipcRenderer.invoke('bridge:cancel'),
  openDrawer: () => ipcRenderer.invoke('bridge:open-drawer'),

  // Auto-start bridge
  startBridge: () => ipcRenderer.invoke('bridge:start')
});
