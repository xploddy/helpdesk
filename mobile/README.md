# HelpDesk Mobile - React Native com Expo

Aplicativo mobile nativo para gerenciar tickets de HelpDesk no Android usando React Native e Expo.

## ✨ Features

- 🔐 **Login Seguro** - Autenticação com backend Flask
- 📋 **Dashboard** - Visão geral de tickets com estatísticas
- 🎟️ **Gerenciar Tickets** - Visualizar, criar e resolver tickets
- 👤 **Perfil de Usuário** - Informações pessoais e logout
- 📱 **Interface Mobile** - Design otimizado para telas pequenas
- ⚡ **Offline Ready** - Estrutura preparada para funcionalidades offline
- 🔄 **Sincronização** - Em tempo real com servidor Flask

## 📱 Tecnologias

- **React Native 0.73** - Framework para desenvolvimento mobile
- **Expo 50** - Plataforma para compilação e testes
- **React Navigation 6** - Sistema de navegação
- **Axios** - Cliente HTTP
- **Context API** - Gerenciamento de estado
- **expo-secure-store** - Armazenamento seguro

## 🚀 Quick Start

### 1. Instalação

```bash
cd mobile
npm install
```

### 2. Configurar IP do Backend

Abra `src/services/api.js` e altere:

```javascript
const API_BASE_URL = 'http://192.168.1.135:5050';
```

### 3. Iniciar Desenvolvimento

```bash
npm start
```

### 4. Testar no Android

- Abra **Expo Go** no seu telefone
- Escaneie o **QR code** que apareceu no terminal
- App carrega automaticamente

## 📚 Documentação

- [Guia Completo de Instalação e Uso](../GUIA_EXPO_ANDROID.md)
- [Detalhes Técnicos da Arquitetura](./TECNICO.md)

## 🎯 Estrutura do Projeto

```
src/
├── services/api.js          # Comunicação com backend
├── context/AuthContext.js   # Autenticação global
├── screens/                 # Telas do aplicativo
│   ├── LoginScreen.js
│   ├── DashboardScreen.js
│   ├── TicketDetailScreen.js
│   ├── CreateTicketScreen.js
│   └── ProfileScreen.js
└── navigation/RootNavigator.js  # Navegação
```

## 🧪 Credenciais de Teste

- **Username:** admin
- **Senha:** admin

## 🔌 Endpoints da API

O app se conecta aos seguintes endpoints do Flask:

- `POST /auth/login` - Login
- `GET /tickets` - Listar tickets
- `GET /tickets/{id}` - Detalhes do ticket
- `POST /tickets` - Criar novo ticket
- `PATCH /tickets/{id}` - Atualizar status
- `POST /tickets/{id}/comments` - Adicionar comentário

## ⚠️ Pré-requisitos

- ✅ Node.js 16+
- ✅ npm ou yarn
- ✅ Android com Expo Go instalado
- ✅ Backend Flask rodando

## 🛠️ Troubleshooting

### App não conecta ao servidor
1. Verifique se Flask está rodando: `python run.py`
2. Confirme seu IP local
3. Teste a conexão: http://seu-ip:5050

### QR code não aparece
```bash
npm start -- --clear
```

### Permissão negada ao instalar
```bash
npm install --force
```

## 📈 Próximas Melhorias

- [ ] Offline mode com sincronização
- [ ] Push notifications
- [ ] Upload de arquivos/anexos
- [ ] Dark mode
- [ ] Busca avançada de tickets
- [ ] Build APK standalone

## 📞 Suporte

Verifique o arquivo [GUIA_EXPO_ANDROID.md](../GUIA_EXPO_ANDROID.md) para mais informações e troubleshooting.

## 📄 Licença

Mesmo projeto que o backend HelpDesk.

---

**Desenvolvido com ❤️ usando React Native + Expo**
