import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { authAPI } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'viewer';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, role?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('user');
      
      if (token && savedUser) {
        try {
          const parsedUser = JSON.parse(savedUser);
          setUser(parsedUser);
          
          // Verify token is still valid
          try {
            await authAPI.getProfile();
          } catch (error) {
            // Token is invalid, clear storage
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            setUser(null);
          }
        } catch (error) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login({ email, password });
      const { user, token } = response;
      
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Login failed';
      throw new Error(errorMessage);
    }
  };

  const register = async (email: string, password: string, name: string, role: string = 'viewer') => {
    try {
      const response = await authAPI.register({ email, password, name, role: role as any });
      const { user, token } = response;
      
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Registration failed';
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setUser(null);
    authAPI.logout().catch(() => {}); // Silent fail for logout
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};