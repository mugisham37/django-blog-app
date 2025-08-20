#!/usr/bin/env node
/**
 * Hot Reloading Configuration for Development Services
 * 
 * This script configures and manages hot reloading for all development services
 * including Django API, Next.js web app, and shared packages.
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const chokidar = require('chokidar');

class HotReloadManager {
  constructor() {
    this.processes = new Map();
    this.watchers = new Map();
    this.config = this.loadConfig();
  }

  loadConfig() {
    const configPath = path.join(process.cwd(), 'tools', 'hot-reload.config.json');
    
    const defaultConfig = {
      services: {
        django: {
          command: 'python manage.py runserver 0.0.0.0:8000',
          cwd: 'apps/api',
          env: { DJANGO_SETTINGS_MODULE: 'config.settings.development' },
          watchPaths: ['apps/api/**/*.py', 'packages/**/*.py'],
          ignorePaths: ['**/__pycache__/**', '**/*.pyc', '**/migrations/**'],
          restartDelay: 1000,
          enabled: true
        },
        nextjs: {
          command: 'npm run dev',
          cwd: 'apps/web',
          env: { NODE_ENV: 'development' },
          watchPaths: ['apps/web/**/*.{js,jsx,ts,tsx}', 'packages/api-client/**/*.ts', 'packages/types/**/*.ts'],
          ignorePaths: ['**/node_modules/**', '**/.next/**', '**/dist/**'],
          restartDelay: 500,
          enabled: true
        },
        typeGeneration: {
          command: 'python tools/type-generator.py --watch',
          cwd: '.',
          env: {},
          watchPaths: ['apps/api/**/models.py'],
          ignorePaths: ['**/__pycache__/**'],
          restartDelay: 2000,
          enabled: true
        },
        apiClientGeneration: {
          command: 'python tools/api-client-generator.py --watch',
          cwd: '.',
          env: {},
          watchPaths: ['apps/api/**/views.py', 'apps/api/**/serializers.py', 'apps/api/**/urls.py'],
          ignorePaths: ['**/__pycache__/**'],
          restartDelay: 2000,
          enabled: true
        }
      },
      global: {
        clearConsole: true,
        showTimestamps: true,
        colorOutput: true,
        debounceDelay: 300
      }
    };

    if (fs.existsSync(configPath)) {
      try {
        const userConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        return this.mergeConfig(defaultConfig, userConfig);
      } catch (error) {
        console.warn('Failed to load hot-reload config, using defaults:', error.message);
      }
    }

    // Create default config file
    fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
    console.log(`Created default hot-reload config at ${configPath}`);
    
    return defaultConfig;
  }

  mergeConfig(defaultConfig, userConfig) {
    return {
      ...defaultConfig,
      services: { ...defaultConfig.services, ...userConfig.services },
      global: { ...defaultConfig.global, ...userConfig.global }
    };
  }

  async startService(serviceName, serviceConfig) {
    if (!serviceConfig.enabled) {
      console.log(`Service ${serviceName} is disabled`);
      return;
    }

    const { command, cwd, env } = serviceConfig;
    const workingDir = path.resolve(cwd);

    console.log(`Starting ${serviceName}...`);
    console.log(`Command: ${command}`);
    console.log(`Working directory: ${workingDir}`);

    const [cmd, ...args] = command.split(' ');
    const process = spawn(cmd, args, {
      cwd: workingDir,
      env: { ...process.env, ...env },
      stdio: 'pipe'
    });

    process.stdout.on('data', (data) => {
      this.logOutput(serviceName, data.toString(), 'stdout');
    });

    process.stderr.on('data', (data) => {
      this.logOutput(serviceName, data.toString(), 'stderr');
    });

    process.on('close', (code) => {
      console.log(`${serviceName} exited with code ${code}`);
      this.processes.delete(serviceName);
    });

    process.on('error', (error) => {
      console.error(`Failed to start ${serviceName}:`, error);
    });

    this.processes.set(serviceName, process);
    
    // Setup file watching for this service
    this.setupWatcher(serviceName, serviceConfig);
  }

  setupWatcher(serviceName, serviceConfig) {
    const { watchPaths, ignorePaths, restartDelay } = serviceConfig;
    
    if (!watchPaths || watchPaths.length === 0) {
      return;
    }

    console.log(`Setting up file watcher for ${serviceName}...`);
    console.log(`Watching: ${watchPaths.join(', ')}`);
    console.log(`Ignoring: ${ignorePaths.join(', ')}`);

    const watcher = chokidar.watch(watchPaths, {
      ignored: ignorePaths,
      ignoreInitial: true,
      persistent: true
    });

    let restartTimeout;

    const handleChange = (eventType, filePath) => {
      console.log(`File ${eventType}: ${filePath}`);
      
      // Clear existing timeout
      if (restartTimeout) {
        clearTimeout(restartTimeout);
      }

      // Debounce restart
      restartTimeout = setTimeout(() => {
        this.restartService(serviceName, serviceConfig);
      }, restartDelay);
    };

    watcher
      .on('change', (filePath) => handleChange('changed', filePath))
      .on('add', (filePath) => handleChange('added', filePath))
      .on('unlink', (filePath) => handleChange('removed', filePath));

    this.watchers.set(serviceName, watcher);
  }

  async restartService(serviceName, serviceConfig) {
    console.log(`Restarting ${serviceName}...`);
    
    // Stop existing process
    const existingProcess = this.processes.get(serviceName);
    if (existingProcess) {
      existingProcess.kill('SIGTERM');
      
      // Wait for process to exit
      await new Promise((resolve) => {
        existingProcess.on('close', resolve);
        setTimeout(resolve, 5000); // Force resolve after 5 seconds
      });
    }

    // Start new process
    await this.startService(serviceName, serviceConfig);
  }

  logOutput(serviceName, data, type) {
    const timestamp = this.config.global.showTimestamps 
      ? `[${new Date().toLocaleTimeString()}] ` 
      : '';
    
    const prefix = this.config.global.colorOutput 
      ? this.getColoredPrefix(serviceName, type)
      : `[${serviceName}] `;

    const lines = data.trim().split('\n');
    lines.forEach(line => {
      if (line.trim()) {
        console.log(`${timestamp}${prefix}${line}`);
      }
    });
  }

  getColoredPrefix(serviceName, type) {
    const colors = {
      django: '\x1b[32m', // Green
      nextjs: '\x1b[34m', // Blue
      typeGeneration: '\x1b[35m', // Magenta
      apiClientGeneration: '\x1b[36m', // Cyan
    };
    
    const typeColors = {
      stdout: '',
      stderr: '\x1b[31m' // Red for errors
    };

    const reset = '\x1b[0m';
    const serviceColor = colors[serviceName] || '\x1b[37m'; // Default white
    const typeColor = typeColors[type] || '';

    return `${serviceColor}[${serviceName}]${reset}${typeColor} `;
  }

  async startAll() {
    console.log('Starting all development services...');
    
    if (this.config.global.clearConsole) {
      console.clear();
    }

    const services = Object.entries(this.config.services);
    
    for (const [serviceName, serviceConfig] of services) {
      await this.startService(serviceName, serviceConfig);
      // Small delay between service starts
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('\nAll services started. Press Ctrl+C to stop all services.');
    
    // Handle graceful shutdown
    process.on('SIGINT', () => this.stopAll());
    process.on('SIGTERM', () => this.stopAll());
  }

  async stopAll() {
    console.log('\nStopping all services...');
    
    // Stop all watchers
    for (const [serviceName, watcher] of this.watchers) {
      console.log(`Stopping watcher for ${serviceName}...`);
      await watcher.close();
    }
    this.watchers.clear();

    // Stop all processes
    for (const [serviceName, process] of this.processes) {
      console.log(`Stopping ${serviceName}...`);
      process.kill('SIGTERM');
    }

    // Wait for all processes to exit
    const exitPromises = Array.from(this.processes.values()).map(process => 
      new Promise(resolve => {
        process.on('close', resolve);
        setTimeout(resolve, 3000); // Force resolve after 3 seconds
      })
    );

    await Promise.all(exitPromises);
    console.log('All services stopped.');
    process.exit(0);
  }

  async restartAll() {
    console.log('Restarting all services...');
    
    for (const [serviceName, serviceConfig] of Object.entries(this.config.services)) {
      if (serviceConfig.enabled) {
        await this.restartService(serviceName, serviceConfig);
      }
    }
  }

  listServices() {
    console.log('Available services:');
    for (const [serviceName, serviceConfig] of Object.entries(this.config.services)) {
      const status = serviceConfig.enabled ? 'enabled' : 'disabled';
      const running = this.processes.has(serviceName) ? 'running' : 'stopped';
      console.log(`  ${serviceName}: ${status}, ${running}`);
    }
  }

  async startService(serviceName) {
    const serviceConfig = this.config.services[serviceName];
    if (!serviceConfig) {
      console.error(`Service ${serviceName} not found`);
      return;
    }

    await this.startService(serviceName, serviceConfig);
  }

  async stopService(serviceName) {
    const process = this.processes.get(serviceName);
    if (!process) {
      console.log(`Service ${serviceName} is not running`);
      return;
    }

    console.log(`Stopping ${serviceName}...`);
    process.kill('SIGTERM');
    
    const watcher = this.watchers.get(serviceName);
    if (watcher) {
      await watcher.close();
      this.watchers.delete(serviceName);
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'start';
  
  const manager = new HotReloadManager();

  switch (command) {
    case 'start':
      if (args[1]) {
        await manager.startService(args[1]);
      } else {
        await manager.startAll();
      }
      break;
    
    case 'stop':
      if (args[1]) {
        await manager.stopService(args[1]);
      } else {
        await manager.stopAll();
      }
      break;
    
    case 'restart':
      if (args[1]) {
        const serviceConfig = manager.config.services[args[1]];
        if (serviceConfig) {
          await manager.restartService(args[1], serviceConfig);
        } else {
          console.error(`Service ${args[1]} not found`);
        }
      } else {
        await manager.restartAll();
      }
      break;
    
    case 'list':
      manager.listServices();
      break;
    
    case 'help':
    default:
      console.log(`
Hot Reload Manager

Usage:
  node tools/hot-reload-config.js [command] [service]

Commands:
  start [service]   Start all services or specific service
  stop [service]    Stop all services or specific service  
  restart [service] Restart all services or specific service
  list             List all available services
  help             Show this help message

Services:
  django           Django API server
  nextjs           Next.js web application
  typeGeneration   TypeScript type generation
  apiClientGeneration API client generation

Examples:
  node tools/hot-reload-config.js start
  node tools/hot-reload-config.js start django
  node tools/hot-reload-config.js restart nextjs
  node tools/hot-reload-config.js list
      `);
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { HotReloadManager };