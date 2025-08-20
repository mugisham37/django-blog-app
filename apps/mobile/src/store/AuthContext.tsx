import React, {createContext, useContext, useReducer, useEffect} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {STORAGE_KEYS} from '@config/constants';
import {AuthService} from '@services/AuthService';
import {BiometricService} from '@services/BiometricService';
import {User, AuthState, LoginCredentials, RegisterData} from '@types/auth';

interface AuthContextType {
  state: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithBiometric: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  enableBiometric: () => Promise<void>;
  disableBiometric: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | {type: 'SET_LOADING'; payload: boolean}
  | {type: 'SET_USER'; payload: User | null}
  | {type: 'SET_TOKENS'; payload: {accessToken: string; refreshToken: string}}
  | {type: 'SET_BIOMETRIC_ENABLED'; payload: boolean}
  | {type: 'SET_ERROR'; payload: string | null}
  | {type: 'CLEAR_AUTH'};

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  isBiometricEnabled: false,
  error: null,
};

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {...state, isLoading: action.payload};
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        error: null,
      };
    case 'SET_TOKENS':
      return {
        ...state,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        error: null,
      };
    case 'SET_BIOMETRIC_ENABLED':
      return {...state, isBiometricEnabled: action.payload};
    case 'SET_ERROR':
      return {...state, error: action.payload, isLoading: false};
    case 'CLEAR_AUTH':
      return {
        ...initialState,
        isLoading: false,
      };
    default:
      return state;
  }
};

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});

      const [accessToken, refreshToken, userData, biometricEnabled] =
        await Promise.all([
          AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN),
          AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN),
          AsyncStorage.getItem(STORAGE_KEYS.USER_DATA),
          AsyncStorage.getItem(STORAGE_KEYS.BIOMETRIC_ENABLED),
        ]);

      if (accessToken && refreshToken && userData) {
        const user = JSON.parse(userData);
        dispatch({type: 'SET_TOKENS', payload: {accessToken, refreshToken}});
        dispatch({type: 'SET_USER', payload: user});
        dispatch({
          type: 'SET_BIOMETRIC_ENABLED',
          payload: biometricEnabled === 'true',
        });

        // Verify token validity
        try {
          await AuthService.verifyToken(accessToken);
        } catch (error) {
          // Token invalid, try to refresh
          await refreshToken();
        }
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      dispatch({type: 'CLEAR_AUTH'});
    } finally {
      dispatch({type: 'SET_LOADING', payload: false});
    }
  };

  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});
      dispatch({type: 'SET_ERROR', payload: null});

      const response = await AuthService.login(credentials);
      
      await Promise.all([
        AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken),
        AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken),
        AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(response.user)),
      ]);

      dispatch({
        type: 'SET_TOKENS',
        payload: {
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
        },
      });
      dispatch({type: 'SET_USER', payload: response.user});
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    } finally {
      dispatch({type: 'SET_LOADING', payload: false});
    }
  };

  const loginWithBiometric = async () => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});
      dispatch({type: 'SET_ERROR', payload: null});

      const isAvailable = await BiometricService.isAvailable();
      if (!isAvailable) {
        throw new Error('Biometric authentication is not available');
      }

      const isAuthenticated = await BiometricService.authenticate();
      if (!isAuthenticated) {
        throw new Error('Biometric authentication failed');
      }

      // Retrieve stored credentials
      const [accessToken, refreshToken, userData] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN),
        AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN),
        AsyncStorage.getItem(STORAGE_KEYS.USER_DATA),
      ]);

      if (accessToken && refreshToken && userData) {
        const user = JSON.parse(userData);
        dispatch({type: 'SET_TOKENS', payload: {accessToken, refreshToken}});
        dispatch({type: 'SET_USER', payload: user});
      } else {
        throw new Error('No stored credentials found');
      }
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    } finally {
      dispatch({type: 'SET_LOADING', payload: false});
    }
  };

  const register = async (data: RegisterData) => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});
      dispatch({type: 'SET_ERROR', payload: null});

      const response = await AuthService.register(data);
      
      await Promise.all([
        AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken),
        AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken),
        AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(response.user)),
      ]);

      dispatch({
        type: 'SET_TOKENS',
        payload: {
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
        },
      });
      dispatch({type: 'SET_USER', payload: response.user});
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    } finally {
      dispatch({type: 'SET_LOADING', payload: false});
    }
  };

  const logout = async () => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});

      if (state.accessToken) {
        await AuthService.logout(state.accessToken);
      }

      await Promise.all([
        AsyncStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN),
        AsyncStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
        AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA),
        AsyncStorage.removeItem(STORAGE_KEYS.BIOMETRIC_ENABLED),
      ]);

      dispatch({type: 'CLEAR_AUTH'});
    } catch (error) {
      console.error('Logout failed:', error);
      // Clear local state even if server logout fails
      dispatch({type: 'CLEAR_AUTH'});
    }
  };

  const refreshToken = async () => {
    try {
      if (!state.refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await AuthService.refreshToken(state.refreshToken);
      
      await Promise.all([
        AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken),
        AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken),
      ]);

      dispatch({
        type: 'SET_TOKENS',
        payload: {
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
        },
      });
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      throw error;
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    try {
      dispatch({type: 'SET_LOADING', payload: true});
      dispatch({type: 'SET_ERROR', payload: null});

      if (!state.accessToken) {
        throw new Error('No access token available');
      }

      const updatedUser = await AuthService.updateProfile(state.accessToken, data);
      
      await AsyncStorage.setItem(
        STORAGE_KEYS.USER_DATA,
        JSON.stringify(updatedUser)
      );

      dispatch({type: 'SET_USER', payload: updatedUser});
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    } finally {
      dispatch({type: 'SET_LOADING', payload: false});
    }
  };

  const enableBiometric = async () => {
    try {
      const isAvailable = await BiometricService.isAvailable();
      if (!isAvailable) {
        throw new Error('Biometric authentication is not available');
      }

      const isAuthenticated = await BiometricService.authenticate();
      if (!isAuthenticated) {
        throw new Error('Biometric authentication failed');
      }

      await AsyncStorage.setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
      dispatch({type: 'SET_BIOMETRIC_ENABLED', payload: true});
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    }
  };

  const disableBiometric = async () => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, 'false');
      dispatch({type: 'SET_BIOMETRIC_ENABLED', payload: false});
    } catch (error: any) {
      dispatch({type: 'SET_ERROR', payload: error.message});
      throw error;
    }
  };

  const value: AuthContextType = {
    state,
    login,
    loginWithBiometric,
    register,
    logout,
    refreshToken,
    updateProfile,
    enableBiometric,
    disableBiometric,
    checkAuthStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};