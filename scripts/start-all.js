#!/usr/bin/env node
/**
 * Start all services for development
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Tienda Loyalty System...\n');

// Start backend server
console.log('📡 Starting Python backend...');
const backend = spawn('python', ['-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'], {
  cwd: path.join(__dirname, '../backend'),
  stdio: 'inherit',
  shell: true
});

// Start Electron app after a delay
setTimeout(() => {
  console.log('🖥️  Starting Electron app...');
  const electron = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, '../electron-app'),
    stdio: 'inherit',
    shell: true
  });

  electron.on('close', (code) => {
    console.log(`Electron app exited with code ${code}`);
    process.exit(code);
  });
}, 5000);

backend.on('close', (code) => {
  console.log(`Backend exited with code ${code}`);
  process.exit(code);
});

// Handle Ctrl+C
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down services...');
  backend.kill();
  process.exit(0);
});
