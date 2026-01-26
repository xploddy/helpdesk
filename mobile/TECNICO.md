# 🔧 Observações Técnicas - Projeto Mobile

## Arquitetura

### Stack Utilizado
- **React Native 0.73.2** - Framework cross-platform
- **Expo 50** - Toolchain para desenvolvimento rápido
- **React Navigation 6** - Navegação com Stack + Bottom Tabs
- **Axios** - Cliente HTTP para API
- **expo-secure-store** - Armazenamento seguro de tokens

---

## Estrutura de Pastas

```
mobile/
├── App.js                    # Root component
├── index.js                  # Entry point Expo
├── app.json                  # Configuração Expo (manifesto)
├── package.json              # Dependências Node
├── .babelrc                  # Configuração Babel
├── .gitignore                # Git ignore
├── src/
│   ├── services/
│   │   └── api.js           # Serviço Axios com interceptors
│   ├── context/
│   │   └── AuthContext.js   # Context API para autenticação
│   ├── screens/             # Componentes de tela
│   │   ├── LoginScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── TicketDetailScreen.js
│   │   ├── CreateTicketScreen.js
│   │   └── ProfileScreen.js
│   └── navigation/
│       └── RootNavigator.js # Navegação com React Navigation
└── assets/                  # Imagens e ícones
```

---

## Fluxo de Autenticação

```
[LoginScreen] 
    ↓ (credenciais)
[authService.login()] 
    ↓ POST /auth/login
[Flask Backend]
    ↓ (retorna user + token)
[SecureStore] (armazena token)
    ↓
[AuthContext.signIn()] 
    ↓ (atualiza state)
[RootNavigator] (muda para Home)
```

---

## Comunicação com Backend

### API Service (src/services/api.js)

#### Interceptor de Request
```javascript
- Adiciona header "Authorization: Bearer {token}"
- Usa token armazenado em SecureStore
```

#### Interceptor de Response
```javascript
- Trata erros HTTP
- Formata mensagens de erro
```

---

## Autenticação

### Token Storage
```javascript
// Salvo em SecureStore (encriptado no dispositivo)
await SecureStore.setItemAsync('auth_token', token);

// Recuperado antes de cada requisição
const token = await SecureStore.getItemAsync('auth_token');
```

### Logout
```javascript
// Remove token e dados de usuário
await authService.logout();
```

---

## Navegação

### Estrutura

```
RootNavigator
├── [Não autenticado]
│   └── LoginScreen
└── [Autenticado]
    └── BottomTabNavigator
        ├── Home (Stack)
        │   ├── DashboardScreen
        │   ├── TicketDetailScreen
        │   └── CreateTicketScreen
        └── Profile (Stack)
            └── ProfileScreen
```

---

## Padrões Utilizados

### 1. **Context API para Estado Global**
```javascript
// AuthContext fornece: user, isLoading, signIn, signOut
<AuthProvider>
  <RootNavigator />
</AuthProvider>
```

### 2. **Custom Hooks (opcional para expandir)**
```javascript
// Exemplo futuro:
const useAuth = () => useContext(AuthContext);
```

### 3. **Serviço de API Centralizado**
```javascript
// Todas as requisições passam por aqui
// Facilita mudanças de URL, headers, etc.
import { ticketService, authService } from '../services/api';
```

### 4. **Tratamento de Erros**
```javascript
try {
  await ticketService.getTickets();
} catch (error) {
  Alert.alert('Erro', error.message);
}
```

---

## Dependências Principais

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| expo | ^50.0.0 | Plataforma Expo |
| react-native | 0.73.2 | Framework UI |
| @react-navigation/native | ^6.1.9 | Navegação |
| axios | ^1.6.2 | Cliente HTTP |
| expo-secure-store | ~12.8.1 | Storage seguro |
| @react-native-async-storage | 1.21.0 | Storage local |

---

## IP Dinâmico

⚠️ **IMPORTANTE:** O IP `192.168.1.100` é exemplo. Ajuste para seu IP local:

```javascript
// src/services/api.js
const API_BASE_URL = 'http://SEU_IP_AQUI:5050';
```

**Obter seu IP:**
```powershell
ipconfig
# Procure por "IPv4 Address"
```

---

## Hot Reload

Mudanças no código recarregam automaticamente:
- Salve o arquivo
- App recarrega em 1-2 segundos
- Não perde estado (geralmente)

Para full reload, pressione `r` no terminal Expo.

---

## Build para Android Standalone (Futuro)

Para gerar APK sem precisar do Expo Go:

```bash
eas build --platform android
```

Requer conta Expo e CLI. Veja documentação Expo.

---

## Segurança

### Implementado ✅
- Token salvo em SecureStore (encriptado)
- Senha não salva localmente
- CORS habilitado no Flask (se necessário)

### Recomendações 🔒
- Use HTTPS em produção
- Implemente refresh token
- Adicione biometria (Face ID / Fingerprint)
- Validar tokens no servidor

---

## Performance

### Otimizações Usadas
- FlatList com keyExtractor para listas
- React.memo em componentes reutilizáveis
- Lazy loading de screens com React Navigation

### Possíveis Melhorias
- Cache local com SQLite
- Paginação em listas grandes
- Otimizar renderização com useMemo

---

## Testes

Para expandir o projeto com testes:

```bash
npm install --save-dev jest @testing-library/react-native
```

---

## Troubleshooting Técnico

| Erro | Causa | Solução |
|------|-------|---------|
| "Cannot find module" | Dependências não instaladas | `npm install` |
| "Connection refused" | Flask não rodando | `python run.py` |
| "Invalid IP" | IP incorreto | Alterar `api.js` |
| "Blank screen" | App não carregou | Pressionar `r` no terminal |
| "CORS error" | Flask sem CORS | Implementar Flask-CORS |

---

## Next Steps (Próximas Features)

1. **Pull to Refresh** - Atualizar tickets deslizando
2. **Search** - Buscar tickets por título
3. **Offline Mode** - Funcionar sem conexão
4. **Push Notifications** - Avisar sobre novos tickets
5. **File Upload** - Anexar imagens/docs
6. **Dark Mode** - Tema escuro
7. **Themes Customization** - Cores personalizáveis
8. **Analytics** - Rastrear uso do app

---

**Documentação atualizada em: 16/01/2026**
