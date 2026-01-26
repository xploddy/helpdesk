# 📱 Guia de Teste no Android com Expo Go

## 🎯 O que foi criado

Um **aplicativo mobile nativo em React Native** que se conecta ao seu backend Flask HelpDesk. O app permite:

- ✅ Login no sistema
- ✅ Visualizar dashboard com estatísticas
- ✅ Listar todos os tickets
- ✅ Visualizar detalhes de cada ticket
- ✅ Criar novos tickets
- ✅ Marcar tickets como resolvidos
- ✅ Visualizar perfil do usuário
- ✅ Fazer logout

---

## 📦 Pré-requisitos

1. **Node.js** (v16+) - [Download aqui](https://nodejs.org/)
2. **npm ou yarn** (vem com Node.js)
3. **Expo CLI** - será instalado via npm
4. **Expo Go App** - Instale no seu Android:
   - Google Play Store: https://play.google.com/store/apps/details?id=host.exp.exponent
5. **Python rodando** (Flask backend em http://192.168.1.100:5050)

---

## 🚀 Passo a Passo de Instalação

### 1️⃣ Navegar para a pasta do projeto mobile

```powershell
cd d:\App\HelpDeskApp\mobile
```

### 2️⃣ Instalar dependências

```powershell
npm install
```

Ou com yarn:
```powershell
yarn install
```

⏱️ **Tempo esperado:** 3-5 minutos (primeira vez é mais lenta)

---

### 3️⃣ Configurar o endereço do servidor Flask

Abra o arquivo `src/services/api.js` e altere a linha com seu IP local:

```javascript
const API_BASE_URL = 'http://192.168.1.100:5050'; // ALTERE AQUI PARA SEU IP
```

**Como descobrir seu IP no Windows:**

Abra o PowerShell e execute:
```powershell
ipconfig
```

Procure por **"IPv4 Address"** na seção do seu adaptador de rede (ex: 192.168.1.100 ou 10.0.0.5)

---

### 4️⃣ Iniciar o servidor Expo

No PowerShell (na pasta `mobile`), execute:

```powershell
npm start
```

Você verá um output assim:
```
Starting Expo Go...
✓ Expo ready at http://localhost:19000
```

---

## 📱 Testando no Android

### Opção A: Com dispositivo físico (Recomendado)

1. **Abra a aplicação Expo Go** no seu Android
2. **Aponte a câmera** para o QR code que apareceu no terminal PowerShell
3. **Aguarde o carregamento** (leva 10-30 segundos)

### Opção B: Com emulador Android

1. **Abra o Android Studio** com um emulador ligado
2. No terminal PowerShell, pressione `a` para Android
3. Ou escanei o QR code que aparece

---

## ⚙️ Estrutura do Projeto Mobile

```
mobile/
├── App.js                          # Arquivo principal
├── index.js                        # Entry point
├── app.json                        # Configuração Expo
├── package.json                    # Dependências
├── src/
│   ├── services/
│   │   └── api.js                 # Serviço de API (comunicação com Flask)
│   ├── context/
│   │   └── AuthContext.js         # Contexto de autenticação
│   ├── screens/
│   │   ├── LoginScreen.js         # Tela de login
│   │   ├── DashboardScreen.js     # Dashboard com tickets
│   │   ├── TicketDetailScreen.js  # Detalhes do ticket
│   │   ├── CreateTicketScreen.js  # Criar novo ticket
│   │   └── ProfileScreen.js       # Perfil do usuário
│   └── navigation/
│       └── RootNavigator.js       # Navegação (Stack + Tabs)
└── assets/
```

---

## 🔧 Troubleshooting

### ❌ "Erro de conexão com servidor"
- Verifique se o Flask está rodando: `python run.py`
- Confirme o IP em `src/services/api.js`
- Teste o IP no navegador: http://seu-ip:5050
- **Dica:** Use `localhost` se testar no emulador da mesma máquina

### ❌ "QR code não aparece"
- Limpe cache: Delete pasta `.expo` e reinstale dependências
```powershell
npm start -- --clear
```

### ❌ "Permissão negada ao instalar npm"
- Use administrador no PowerShell, ou:
```powershell
npm install --force
```

### ❌ "Arquivo não encontrado"
- Certifique-se de estar na pasta correta: `d:\App\HelpDeskApp\mobile`

---

## 🧪 Testando as Funcionalidades

### ✅ Login
- **Username:** admin
- **Senha:** admin
- Clique em "Entrar"

### ✅ Dashboard
- Veja estatísticas de tickets
- Veja lista de tickets recentes
- Clique no botão "+" para criar novo

### ✅ Novo Ticket
- Preencha título e descrição
- Escolha categoria (TI, Financeiro, RH, Infraestrutura)
- Escolha prioridade (Baixa, Média, Alta, Crítica)
- Clique em "Criar Ticket"

### ✅ Detalhes do Ticket
- Clique em qualquer ticket para ver detalhes
- Veja informações completas
- Se não resolvido, clique "Marcar como Resolvido"

### ✅ Perfil
- Clique na aba "Perfil"
- Veja informações do seu usuário
- Clique "Sair" para fazer logout

---

## 🔌 Conexão Backend

O app se conecta ao Flask automaticamente. Os endpoints usados são:

| Funcionalidade | Método | Endpoint |
|---|---|---|
| Login | POST | `/auth/login` |
| Listar Tickets | GET | `/tickets` |
| Detalhes Ticket | GET | `/tickets/{id}` |
| Criar Ticket | POST | `/tickets` |
| Resolver Ticket | PATCH | `/tickets/{id}` |
| Adicionar Comentário | POST | `/tickets/{id}/comments` |
| Listar Usuários | GET | `/users` |

---

## 📋 Notas Importantes

1. **IP Local:** Se mudar de rede, altere o IP em `src/services/api.js`
2. **Sessão:** O token é salvo localmente usando `expo-secure-store`
3. **Hot Reload:** Mudanças no código recarregam automaticamente no app
4. **Certificados:** Se usar HTTPS, configure em `api.js`

---

## 🎓 Próximos Passos

Para evoluir o app:

1. **Adicionar offline mode** - cache local de tickets
2. **Notificações push** - avisos de novo ticket atribuído
3. **Upload de arquivos** - anexar imagens ao ticket
4. **Temas** - dark mode, light mode
5. **Build para APK** - gerar versão standalone sem Expo

---

## 📞 Suporte

Se tiver problemas:

1. Verifique se Flask está rodando
2. Confirme o IP/porta em `src/services/api.js`
3. Limpe cache: `npm start -- --clear`
4. Reinstale dependências: `npm install`
5. Reinicie o Expo Go no Android

---

## ✨ Resumo dos Comandos

```powershell
# Entrar na pasta
cd mobile

# Instalar dependências (primeira vez)
npm install

# Iniciar servidor Expo
npm start

# Apenas Android
npm start -- --android

# Limpar cache e reiniciar
npm start -- --clear

# Para o servidor
Ctrl + C
```

---

**Desenvolvido com ❤️ usando React Native + Expo**
