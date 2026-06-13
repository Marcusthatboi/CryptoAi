import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './hooks/useAuth.jsx'
import { WebSocketProvider } from './hooks/useWebSocket'
import { LanguageProvider } from './context/LanguageContext'
import { registerServiceWorker } from './swRegistration'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AuthProvider>
      <LanguageProvider>
        <WebSocketProvider>
          <App />
        </WebSocketProvider>
      </LanguageProvider>
    </AuthProvider>
  </BrowserRouter>
)

registerServiceWorker()
