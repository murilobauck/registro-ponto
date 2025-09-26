# 📋 Registro de Ponto

Um aplicativo web moderno para registro e controle de ponto eletrônico, desenvolvido com React e Vite.

## 🔗 Demo

Acesse a aplicação em funcionamento: [https://registro-ponto-seven.vercel.app](https://registro-ponto-seven.vercel.app)

## 📖 Sobre o Projeto

O **Registro de Ponto** é uma aplicação web que permite aos usuários registrar seus horários de trabalho de forma digital e eficiente. O sistema oferece uma interface intuitiva para controle de entrada e saída, facilitando o acompanhamento da jornada de trabalho.

## 🚀 Tecnologias Utilizadas

### Frontend
- **React 19.1.1** - Biblioteca JavaScript para construção de interfaces
- **React Router DOM 7.9.2** - Navegação entre páginas
- **Vite 7.1.7** - Ferramenta de build rápida e moderna

### Cloud & Autenticação
- **AWS Amplify 5.3.27** - Plataforma de desenvolvimento full-stack
- **AWS Amplify UI React 5.3.3** - Componentes UI pré-construídos

### Estilo & Ícones
- **Boxicons 2.1.4** - Biblioteca de ícones
- **CSS** - Estilização customizada

### Ferramentas de Desenvolvimento
- **ESLint** - Linting e qualidade de código
- **TypeScript Types** - Tipagem estática

## 📁 Estrutura do Projeto

```
registro-ponto/
├── src/                    # Código fonte da aplicação
├── index.html             # Página HTML principal
├── package.json           # Dependências e scripts
├── vite.config.js         # Configuração do Vite
├── eslint.config.js       # Configuração do ESLint
├── vercel.json           # Configuração para deploy na Vercel
└── .gitignore            # Arquivos ignorados pelo Git
```

## 🛠️ Funcionalidades

- ✅ **Registro de Entrada e Saída** - Controle preciso de horários
- 🔐 **Autenticação Segura** - Integração com AWS Amplify
- 📱 **Interface Responsiva** - Funciona em desktop e mobile
- 🎯 **Verificação Biométrica** - Usando AWS Liveness Detection
- 📊 **Controle de Jornada** - Acompanhamento de horas trabalhadas
- 🌐 **Deploy Automático** - Hospedado na Vercel

## 🚀 Como Executar

### Pré-requisitos
- Node.js (versão 16 ou superior)
- npm ou yarn

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/murilobauck/registro-ponto.git
cd registro-ponto
```

2. Instale as dependências:
```bash
npm install
```

3. Configure as variáveis de ambiente do AWS Amplify (crie um arquivo `.env`):
```bash
# Adicione suas credenciais do AWS Amplify
VITE_AWS_REGION=sua-regiao
VITE_AWS_USER_POOL_ID=seu-user-pool-id
VITE_AWS_USER_POOL_WEB_CLIENT_ID=seu-client-id
```

4. Execute o projeto em modo de desenvolvimento:
```bash
npm run dev
```

5. Acesse `http://localhost:5173` no seu navegador

### Scripts Disponíveis

- `npm run dev` - Inicia o servidor de desenvolvimento
- `npm run build` - Cria a build de produção
- `npm run preview` - Visualiza a build de produção
- `npm run lint` - Executa o linting do código

## 🏗️ Arquitetura

O projeto utiliza uma arquitetura moderna baseada em:

- **React** para a interface do usuário
- **AWS Amplify** para backend-as-a-service
- **Vite** para bundling e desenvolvimento rápido
- **Vercel** para hospedagem e CI/CD

## 📱 Responsividade

A aplicação é totalmente responsiva, adaptando-se a diferentes tamanhos de tela:
- 📱 Mobile (smartphones)
- 📱 Tablet (tablets)
- 💻 Desktop (computadores)

## 🔒 Segurança

- Autenticação via AWS Cognito
- Verificação biométrica com Liveness Detection
- Comunicação segura via HTTPS
- Validação de dados no frontend e backend

## 🚀 Deploy

O projeto está configurado para deploy automático na Vercel. Qualquer push para a branch `master` dispara um novo deploy.

## 👨‍💻 Autor

- **Murilo Bauck** - [@murilobauck](https://github.com/murilobauck)

⭐ Se você achou este projeto útil, considere dar uma estrela no repositório!
