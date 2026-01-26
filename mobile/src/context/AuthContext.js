import React, { createContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSignout, setIsSignout] = useState(false);

  // Verificar se há usuário autenticado ao iniciar
  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (e) {
        // Erro ao recuperar usuário
      } finally {
        setIsLoading(false);
      }
    };

    bootstrapAsync();
  }, []);

  const authContext = {
    signIn: async (username, password) => {
      setIsLoading(true);
      try {
        const response = await authService.login(username, password);
        setUser(response.user);
        setIsSignout(false);
        return response;
      } catch (error) {
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    signUp: async (credentials) => {
      setIsLoading(true);
      try {
        // Se seu app tiver registro, implemente aqui
        throw new Error('Registro desabilitado. Contate o administrador.');
      } finally {
        setIsLoading(false);
      }
    },
    signOut: async () => {
      setIsLoading(true);
      try {
        await authService.logout();
        setUser(null);
        setIsSignout(true);
      } finally {
        setIsLoading(false);
      }
    },
    signUp: async (credentials) => {
      setIsLoading(true);
      try {
        // Registro desabilitado
        throw new Error('Registro desabilitado.');
      } finally {
        setIsLoading(false);
      }
    },
    user,
    isLoading,
    isSignout,
  };

  return (
    <AuthContext.Provider value={authContext}>
      {children}
    </AuthContext.Provider>
  );
};
