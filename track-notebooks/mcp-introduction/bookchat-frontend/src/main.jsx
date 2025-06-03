import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css' // Global styles
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
