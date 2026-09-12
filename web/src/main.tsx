import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { ProductionPresentationProvider } from './services/GameDataProvider'
import { HttpBackendPresentationGateway } from './services/HttpBackendPresentationGateway'
import './styles.css'
import './overview.css'
import './interactiveEvent.css'

const provider = new ProductionPresentationProvider(new HttpBackendPresentationGateway())

createRoot(document.getElementById('root')!).render(
  <StrictMode><App provider={provider} /></StrictMode>,
)
