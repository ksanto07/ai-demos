const { app, BrowserWindow } = require('electron');
const path = require('path');

const viewport = { width: 960, height: 720 };

function resolvePageHtmlPath() {
  return path.join(__dirname, '..', 'page', 'index.html');
}

function createDemoWindow() {
  const win = new BrowserWindow({
    width: viewport.width,
    height: viewport.height,
    center: true,
    title: 'Ledger',
    backgroundColor: '#e7eef2',
    autoHideMenuBar: true,
    webPreferences: { sandbox: true },
  });
  win.loadFile(resolvePageHtmlPath());
  return win;
}

app.whenReady().then(() => {
  createDemoWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createDemoWindow();
  });
});

app.on('window-all-closed', () => {
  app.quit();
});
