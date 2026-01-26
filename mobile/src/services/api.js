import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

// Configuração do servidor Flask
const API_BASE_URL = 'http://128.202.1.87:5050'; // Altere para seu IP local

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Erro ao recuperar token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Serviço de autenticação
export const authService = {
  async login(username, password) {
    try {
      const response = await api.post('/login', {
        username,
        password,
      });

      if (response.data && response.data.user) {
        // Armazena token (se enviado pelo servidor)
        if (response.data.token) {
          await SecureStore.setItemAsync('auth_token', response.data.token);
        }
        await SecureStore.setItemAsync('user', JSON.stringify(response.data.user));
        return response.data;
      }
      throw new Error('Credenciais inválidas');
    } catch (error) {
      throw this.handleError(error);
    }
  },

  async logout() {
    try {
      await SecureStore.deleteItemAsync('auth_token');
      await SecureStore.deleteItemAsync('user');
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  },

  async getCurrentUser() {
    try {
      const userJson = await SecureStore.getItemAsync('user');
      return userJson ? JSON.parse(userJson) : null;
    } catch (error) {
      console.error('Erro ao recuperar usuário:', error);
      return null;
    }
  },

  handleError(error) {
    if (error.response) {
      return new Error(error.response.data?.message || 'Erro na requisição');
    } else if (error.request) {
      return new Error('Erro de conexão. Verifique se o servidor está rodando.');
    } else {
      return error;
    }
  },
};

// Serviço de Tickets
export const ticketService = {
  async getTickets() {
    try {
      const response = await api.get('/tickets');
      return response.data.tickets || [];
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async getTicket(id) {
    try {
      const response = await api.get(`/tickets/${id}`);
      return response.data.ticket;
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async createTicket(ticketData) {
    try {
      const response = await api.post('/tickets', ticketData);
      return response.data.ticket;
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async updateTicket(id, ticketData) {
    try {
      const response = await api.put(`/tickets/${id}`, ticketData);
      return response.data.ticket;
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async resolveTicket(id, status = 'Resolvido') {
    try {
      const response = await api.patch(`/tickets/${id}`, {
        status,
      });
      return response.data.ticket;
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async addComment(ticketId, content) {
    try {
      const response = await api.post(`/tickets/${ticketId}/comments`, {
        content,
      });
      return response.data.comment;
    } catch (error) {
      throw authService.handleError(error);
    }
  },
};

// Serviço de Usuários
export const userService = {
  async getUsers() {
    try {
      const response = await api.get('/users');
      return response.data.users || [];
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async searchUsers(query) {
    try {
      const response = await api.get('/users', { params: { q: query } });
      return response.data.users || [];
    } catch (error) {
      throw authService.handleError(error);
    }
  },

  async getUser(id) {
    try {
      const response = await api.get(`/users/${id}`);
      return response.data.user;
    } catch (error) {
      throw authService.handleError(error);
    }
  },
};

// Serviço de Dashboard
export const dashboardService = {
  async getStats() {
    try {
      const response = await api.get('/');
      return response.data;
    } catch (error) {
      throw authService.handleError(error);
    }
  },
};

export default api;
