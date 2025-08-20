import React, {createContext, useContext, useReducer, useEffect} from 'react';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {STORAGE_KEYS, OFFLINE_CONFIG} from '@config/constants';
import {OfflineManager} from '@services/OfflineManager';

interface OfflineAction {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  endpoint: string;
  data?: any;
  timestamp: number;
  retryCount: number;
}

interface OfflineState {
  isOnline: boolean;
  isConnected: boolean;
  connectionType: string | null;
  pendingActions: OfflineAction[];
  isSyncing: boolean;
  lastSyncTime: number | null;
  syncError: string | null;
}

interface OfflineContextType {
  state: OfflineState;
  addOfflineAction: (action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>) => void;
  removeOfflineAction: (id: string) => void;
  syncOfflineActions: () => Promise<void>;
  clearOfflineActions: () => void;
  retryFailedActions: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

type OfflineActionType =
  | {type: 'SET_CONNECTION_STATUS'; payload: {isOnline: boolean; isConnected: boolean; connectionType: string | null}}
  | {type: 'ADD_OFFLINE_ACTION'; payload: OfflineAction}
  | {type: 'REMOVE_OFFLINE_ACTION'; payload: string}
  | {type: 'SET_PENDING_ACTIONS'; payload: OfflineAction[]}
  | {type: 'SET_SYNCING'; payload: boolean}
  | {type: 'SET_LAST_SYNC_TIME'; payload: number}
  | {type: 'SET_SYNC_ERROR'; payload: string | null}
  | {type: 'INCREMENT_RETRY_COUNT'; payload: string}
  | {type: 'CLEAR_OFFLINE_ACTIONS'};

const initialState: OfflineState = {
  isOnline: true,
  isConnected: true,
  connectionType: null,
  pendingActions: [],
  isSyncing: false,
  lastSyncTime: null,
  syncError: null,
};

const offlineReducer = (state: OfflineState, action: OfflineActionType): OfflineState => {
  switch (action.type) {
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        isOnline: action.payload.isOnline,
        isConnected: action.payload.isConnected,
        connectionType: action.payload.connectionType,
      };
    case 'ADD_OFFLINE_ACTION':
      return {
        ...state,
        pendingActions: [...state.pendingActions, action.payload],
      };
    case 'REMOVE_OFFLINE_ACTION':
      return {
        ...state,
        pendingActions: state.pendingActions.filter(a => a.id !== action.payload),
      };
    case 'SET_PENDING_ACTIONS':
      return {
        ...state,
        pendingActions: action.payload,
      };
    case 'SET_SYNCING':
      return {
        ...state,
        isSyncing: action.payload,
      };
    case 'SET_LAST_SYNC_TIME':
      return {
        ...state,
        lastSyncTime: action.payload,
      };
    case 'SET_SYNC_ERROR':
      return {
        ...state,
        syncError: action.payload,
      };
    case 'INCREMENT_RETRY_COUNT':
      return {
        ...state,
        pendingActions: state.pendingActions.map(action =>
          action.id === action.payload
            ? {...action, retryCount: action.retryCount + 1}
            : action
        ),
      };
    case 'CLEAR_OFFLINE_ACTIONS':
      return {
        ...state,
        pendingActions: [],
        syncError: null,
      };
    default:
      return state;
  }
};

export const OfflineProvider: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [state, dispatch] = useReducer(offlineReducer, initialState);

  useEffect(() => {
    // Load pending actions from storage
    loadPendingActions();

    // Load last sync time
    loadLastSyncTime();

    // Set up network listener
    const unsubscribe = NetInfo.addEventListener(networkState => {
      const wasOffline = !state.isConnected;
      const isNowOnline = networkState.isConnected && networkState.isInternetReachable;

      dispatch({
        type: 'SET_CONNECTION_STATUS',
        payload: {
          isOnline: isNowOnline || false,
          isConnected: networkState.isConnected || false,
          connectionType: networkState.type,
        },
      });

      // If we just came back online, sync pending actions
      if (wasOffline && isNowOnline && state.pendingActions.length > 0) {
        syncOfflineActions();
      }
    });

    // Set up periodic sync when online
    const syncInterval = setInterval(() => {
      if (state.isOnline && state.pendingActions.length > 0 && !state.isSyncing) {
        syncOfflineActions();
      }
    }, OFFLINE_CONFIG.SYNC_INTERVAL);

    return () => {
      unsubscribe();
      clearInterval(syncInterval);
    };
  }, []);

  const loadPendingActions = async () => {
    try {
      const storedActions = await AsyncStorage.getItem(STORAGE_KEYS.OFFLINE_DATA);
      if (storedActions) {
        const actions = JSON.parse(storedActions);
        dispatch({type: 'SET_PENDING_ACTIONS', payload: actions});
      }
    } catch (error) {
      console.error('Failed to load pending actions:', error);
    }
  };

  const loadLastSyncTime = async () => {
    try {
      const lastSync = await AsyncStorage.getItem(STORAGE_KEYS.LAST_SYNC);
      if (lastSync) {
        dispatch({type: 'SET_LAST_SYNC_TIME', payload: parseInt(lastSync, 10)});
      }
    } catch (error) {
      console.error('Failed to load last sync time:', error);
    }
  };

  const savePendingActions = async (actions: OfflineAction[]) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.OFFLINE_DATA, JSON.stringify(actions));
    } catch (error) {
      console.error('Failed to save pending actions:', error);
    }
  };

  const addOfflineAction = (actionData: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>) => {
    const action: OfflineAction = {
      ...actionData,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retryCount: 0,
    };

    dispatch({type: 'ADD_OFFLINE_ACTION', payload: action});
    
    // Save to storage
    const updatedActions = [...state.pendingActions, action];
    savePendingActions(updatedActions);
  };

  const removeOfflineAction = (id: string) => {
    dispatch({type: 'REMOVE_OFFLINE_ACTION', payload: id});
    
    // Save to storage
    const updatedActions = state.pendingActions.filter(a => a.id !== id);
    savePendingActions(updatedActions);
  };

  const syncOfflineActions = async () => {
    if (!state.isOnline || state.isSyncing || state.pendingActions.length === 0) {
      return;
    }

    dispatch({type: 'SET_SYNCING', payload: true});
    dispatch({type: 'SET_SYNC_ERROR', payload: null});

    try {
      const successfulActions: string[] = [];
      const failedActions: string[] = [];

      // Process actions in order
      for (const action of state.pendingActions) {
        try {
          await OfflineManager.executeOfflineAction(action);
          successfulActions.push(action.id);
        } catch (error) {
          console.error(`Failed to sync action ${action.id}:`, error);
          
          // Increment retry count
          dispatch({type: 'INCREMENT_RETRY_COUNT', payload: action.id});
          
          // Remove action if max retries exceeded
          if (action.retryCount >= OFFLINE_CONFIG.MAX_RETRY_ATTEMPTS) {
            failedActions.push(action.id);
          }
        }
      }

      // Remove successful and permanently failed actions
      const actionsToRemove = [...successfulActions, ...failedActions];
      actionsToRemove.forEach(id => removeOfflineAction(id));

      // Update last sync time
      const now = Date.now();
      dispatch({type: 'SET_LAST_SYNC_TIME', payload: now});
      await AsyncStorage.setItem(STORAGE_KEYS.LAST_SYNC, now.toString());

      if (failedActions.length > 0) {
        dispatch({
          type: 'SET_SYNC_ERROR',
          payload: `${failedActions.length} actions failed permanently and were removed`,
        });
      }
    } catch (error: any) {
      dispatch({type: 'SET_SYNC_ERROR', payload: error.message});
    } finally {
      dispatch({type: 'SET_SYNCING', payload: false});
    }
  };

  const clearOfflineActions = () => {
    dispatch({type: 'CLEAR_OFFLINE_ACTIONS'});
    AsyncStorage.removeItem(STORAGE_KEYS.OFFLINE_DATA);
  };

  const retryFailedActions = async () => {
    if (state.pendingActions.length > 0) {
      await syncOfflineActions();
    }
  };

  const value: OfflineContextType = {
    state,
    addOfflineAction,
    removeOfflineAction,
    syncOfflineActions,
    clearOfflineActions,
    retryFailedActions,
  };

  return (
    <OfflineContext.Provider value={value}>
      {children}
    </OfflineContext.Provider>
  );
};

export const useOffline = () => {
  const context = useContext(OfflineContext);
  if (context === undefined) {
    throw new Error('useOffline must be used within an OfflineProvider');
  }
  return context;
};