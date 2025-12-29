# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

# HR Analytics Platform - Frontend

A modern React-based frontend for the AI-Powered HR Analytics Platform, built with cutting-edge web technologies.

## 🚀 Features

### ✅ **Completed Core Features**
- **Modern React 18** with TypeScript for type safety
- **Tailwind CSS** for responsive, utility-first styling
- **Zustand** for lightweight state management
- **React Router v6** for client-side routing
- **React Hook Form** with Zod validation
- **Axios** with automatic token refresh
- **Socket.IO Client** for real-time updates
- **React Hot Toast** for notifications

### 🎯 **Key Components Built**
- **Authentication System** - Login/Register with JWT
- **Dashboard** - Overview with stats and quick actions
- **Layout System** - Header, Sidebar, Protected Routes
- **UI Components** - Modern, accessible components
- **API Services** - Complete service layer for backend integration
- **State Management** - Auth and Resume stores with Zustand

## 🛠️ Technology Stack

### **Core Technologies**
- **React 18** - Latest React with concurrent features
- **TypeScript** - Full type safety and better DX
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework

### **State & Data Management**
- **Zustand** - Simple, scalable state management
- **React Hook Form** - Performant forms with easy validation
- **Zod** - TypeScript-first schema validation
- **Axios** - HTTP client with interceptors

### **Real-time & UX**
- **Socket.IO Client** - Real-time WebSocket communication
- **React Hot Toast** - Beautiful toast notifications
- **Lucide React** - Modern icon library
- **React Dropzone** - File upload with drag & drop

## 🚀 Getting Started

### **Prerequisites**
- Node.js 18+ and npm
- Backend API running (see API documentation)

### **Installation**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### **Environment Configuration**
Create `.env` file:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=http://localhost:8000
```

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Route components
├── store/              # Zustand state stores
├── services/           # API service layer
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

This frontend provides a solid foundation for the HR Analytics Platform with modern React practices, comprehensive type safety, and a scalable architecture ready for feature expansion.

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
