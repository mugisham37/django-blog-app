import AsyncStorage from '@react-native-async-storage/async-storage';
import {MMKV} from 'react-native-mmkv';
import {ApiClient} from '@services/ApiClient';
import {STORAGE_KEYS, CACHE_CONFIG} from '@config/constants';

interface OfflineAction {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  endpoint: string;
  data?: any;
  timestamp: number;
  retryCount: number;
}

interface CachedData {
  data: any;
  timestamp: number;
  ttl: number;
}

class OfflineManagerClass {
  private storage: MMKV;

  constructor() {
    this.storage = new MMKV({
      id: 'offline-cache',
      encryptionKey: 'offline-encryption-key',
    });
  }

  /**
   * Store offline request for later execution
   */
  async storeOfflineRequest(config: any): Promise<void> {
    try {
      const action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'> = {
        type: this.getActionType(config.method),
        endpoint: config.url,
        data: config.data,
      };

      // Get existing offline actions
      const existingActions = await this.getOfflineActions();
      
      const newAction: OfflineAction = {
        ...action,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        retryCount: 0,
      };

      const updatedActions = [...existingActions, newAction];
      await AsyncStorage.setItem(STORAGE_KEYS.OFFLINE_DATA, JSON.stringify(updatedActions));
    } catch (error) {
      console.error('Failed to store offline request:', error);
    }
  }

  /**
   * Execute offline action when back online
   */
  async executeOfflineAction(action: OfflineAction): Promise<void> {
    try {
      switch (action.type) {
        case 'CREATE':
          await ApiClient.post(action.endpoint, action.data);
          break;
        case 'UPDATE':
          await ApiClient.put(action.endpoint, action.data);
          break;
        case 'DELETE':
          await ApiClient.delete(action.endpoint);
          break;
        default:
          throw new Error(`Unknown action type: ${action.type}`);
      }
    } catch (error) {
      console.error(`Failed to execute offline action ${action.id}:`, error);
      throw error;
    }
  }

  /**
   * Get all stored offline actions
   */
  async getOfflineActions(): Promise<OfflineAction[]> {
    try {
      const storedActions = await AsyncStorage.getItem(STORAGE_KEYS.OFFLINE_DATA);
      return storedActions ? JSON.parse(storedActions) : [];
    } catch (error) {
      console.error('Failed to get offline actions:', error);
      return [];
    }
  }

  /**
   * Cache data for offline access
   */
  cacheData(key: string, data: any, ttl: number = CACHE_CONFIG.TTL): void {
    try {
      const cachedData: CachedData = {
        data,
        timestamp: Date.now(),
        ttl,
      };
      this.storage.set(key, JSON.stringify(cachedData));
    } catch (error) {
      console.error('Failed to cache data:', error);
    }
  }

  /**
   * Get cached data
   */
  getCachedData(key: string): any | null {
    try {
      const cachedDataString = this.storage.getString(key);
      if (!cachedDataString) {
        return null;
      }

      const cachedData: CachedData = JSON.parse(cachedDataString);
      const now = Date.now();

      // Check if data has expired
      if (now - cachedData.timestamp > cachedData.ttl) {
        this.storage.delete(key);
        return null;
      }

      return cachedData.data;
    } catch (error) {
      console.error('Failed to get cached data:', error);
      return null;
    }
  }

  /**
   * Remove cached data
   */
  removeCachedData(key: string): void {
    try {
      this.storage.delete(key);
    } catch (error) {
      console.error('Failed to remove cached data:', error);
    }
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    try {
      this.storage.clearAll();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  /**
   * Get cache size
   */
  getCacheSize(): number {
    try {
      const keys = this.storage.getAllKeys();
      let totalSize = 0;

      keys.forEach(key => {
        const value = this.storage.getString(key);
        if (value) {
          totalSize += new Blob([value]).size;
        }
      });

      return totalSize;
    } catch (error) {
      console.error('Failed to get cache size:', error);
      return 0;
    }
  }

  /**
   * Cleanup expired cache entries
   */
  cleanupExpiredCache(): void {
    try {
      const keys = this.storage.getAllKeys();
      const now = Date.now();

      keys.forEach(key => {
        const cachedDataString = this.storage.getString(key);
        if (cachedDataString) {
          try {
            const cachedData: CachedData = JSON.parse(cachedDataString);
            if (now - cachedData.timestamp > cachedData.ttl) {
              this.storage.delete(key);
            }
          } catch (error) {
            // Invalid cached data, remove it
            this.storage.delete(key);
          }
        }
      });
    } catch (error) {
      console.error('Failed to cleanup expired cache:', error);
    }
  }

  /**
   * Manage cache size by removing oldest entries
   */
  manageCacheSize(): void {
    try {
      const currentSize = this.getCacheSize();
      
      if (currentSize > CACHE_CONFIG.MAX_SIZE) {
        const keys = this.storage.getAllKeys();
        const entries: Array<{key: string; timestamp: number}> = [];

        keys.forEach(key => {
          const cachedDataString = this.storage.getString(key);
          if (cachedDataString) {
            try {
              const cachedData: CachedData = JSON.parse(cachedDataString);
              entries.push({key, timestamp: cachedData.timestamp});
            } catch (error) {
              // Invalid cached data, remove it
              this.storage.delete(key);
            }
          }
        });

        // Sort by timestamp (oldest first)
        entries.sort((a, b) => a.timestamp - b.timestamp);

        // Remove oldest entries until under size limit
        let removedSize = 0;
        for (const entry of entries) {
          const value = this.storage.getString(entry.key);
          if (value) {
            removedSize += new Blob([value]).size;
            this.storage.delete(entry.key);
            
            if (currentSize - removedSize <= CACHE_CONFIG.MAX_SIZE * 0.8) {
              break;
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to manage cache size:', error);
    }
  }

  /**
   * Sync cached data with server
   */
  async syncCachedData(): Promise<void> {
    try {
      const keys = this.storage.getAllKeys();
      const syncPromises: Promise<void>[] = [];

      keys.forEach(key => {
        if (key.startsWith('sync_')) {
          const cachedData = this.getCachedData(key);
          if (cachedData && cachedData.needsSync) {
            syncPromises.push(this.syncSingleItem(key, cachedData));
          }
        }
      });

      await Promise.allSettled(syncPromises);
    } catch (error) {
      console.error('Failed to sync cached data:', error);
    }
  }

  /**
   * Sync single cached item with server
   */
  private async syncSingleItem(key: string, data: any): Promise<void> {
    try {
      // Extract endpoint from key
      const endpoint = key.replace('sync_', '');
      
      // Sync with server
      await ApiClient.post(`/sync/${endpoint}`, data);
      
      // Mark as synced
      const updatedData = {...data, needsSync: false, lastSynced: Date.now()};
      this.cacheData(key, updatedData);
    } catch (error) {
      console.error(`Failed to sync item ${key}:`, error);
      throw error;
    }
  }

  /**
   * Get action type from HTTP method
   */
  private getActionType(method: string): 'CREATE' | 'UPDATE' | 'DELETE' {
    switch (method?.toLowerCase()) {
      case 'post':
        return 'CREATE';
      case 'put':
      case 'patch':
        return 'UPDATE';
      case 'delete':
        return 'DELETE';
      default:
        return 'CREATE';
    }
  }

  /**
   * Initialize offline manager
   */
  async initialize(): Promise<void> {
    try {
      // Cleanup expired cache on startup
      this.cleanupExpiredCache();
      
      // Manage cache size
      this.manageCacheSize();
      
      // Set up periodic cleanup
      setInterval(() => {
        this.cleanupExpiredCache();
        this.manageCacheSize();
      }, CACHE_CONFIG.CLEANUP_INTERVAL);
    } catch (error) {
      console.error('Failed to initialize offline manager:', error);
    }
  }
}

export const OfflineManager = new OfflineManagerClass();