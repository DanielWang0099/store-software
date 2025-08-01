/**
 * Development startup script - starts all services
 */
const { spawn } = require('child_process');
const path = require('path');

const isWindows = process.platform === 'win32';

function startService(name, command, args, cwd) {
  console.log(`🚀 Starting ${name}...`);
  
  const child = spawn(command, args, {
    cwd: cwd,
    stdio: 'inherit',
    shell: isWindows
  });

  child.on('error', (error) => {
    console.error(`❌ Error starting ${name}:`, error.message);
  });

  child.on('exit', (code) => {
    if (code !== 0) {
      console.error(`❌ ${name} exited with code ${code}`);
    }
  });

  return child;
}

async function main() {
  console.log('🏪 Starting Tienda Loyalty System Development Environment');
  console.log('=' * 60);

  const services = [];

  try {
    // Start Python backend
    const backendProcess = startService(
      'Python Backend',
      isWindows ? 'python' : 'python3',
      ['-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
      path.join(__dirname, '..', 'backend')
    );
    services.push(backendProcess);

    // Wait a moment for backend to start
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Start Electron app
    const electronProcess = startService(
      'Electron App',
      'npm',
      ['run', 'dev'],
      path.join(__dirname, '..', 'electron-app')
    );
    services.push(electronProcess);

    console.log('\n✅ All services started successfully!');
    console.log('\n📋 Access Information:');
    console.log('- Backend API: http://localhost:8000');
    console.log('- API Documentation: http://localhost:8000/docs');
    console.log('- Tablet Interface: http://localhost:8000/tablet');
    console.log('- Cashier Interface: Electron app window');
    
    console.log('\n⚠️  Press Ctrl+C to stop all services');

    // Handle shutdown
    process.on('SIGINT', () => {
      console.log('\n🛑 Shutting down services...');
      services.forEach(service => {
        if (service && !service.killed) {
          service.kill();
        }
      });
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.log('\n🛑 Shutting down services...');
      services.forEach(service => {
        if (service && !service.killed) {
          service.kill();
        }
      });
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ Error starting services:', error.message);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('❌ Startup failed:', error.message);
  process.exit(1);
});
