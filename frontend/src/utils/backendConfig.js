const DEFAULT_LOCAL_API_BASE = 'http://localhost:8002'
const DEFAULT_PROD_API_BASE = 'https://api.dacryptobeast.com'

const isLocalHostname = (hostname = '') => {
  const normalized = String(hostname || '').toLowerCase()
  return normalized === 'localhost' || normalized === '127.0.0.1'
}

const isLocalAddressUrl = (value = '') => {
  try {
    const parsed = new URL(value)
    return isLocalHostname(parsed.hostname)
  } catch {
    return false
  }
}

const shouldUseDefaultProdApi = (hostname = '') => {
  const normalized = String(hostname || '').toLowerCase()
  return normalized === 'dacryptobeast.com' || normalized === 'www.dacryptobeast.com'
}

const upgradeHttpToHttpsIfNeeded = (url = '', currentHostname = '') => {
  if (!url || isLocalAddressUrl(url) || isLocalHostname(currentHostname)) {
    return url
  }

  try {
    const parsed = new URL(url)
    if (parsed.protocol === 'http:') {
      parsed.protocol = 'https:'
      return parsed.toString().replace(/\/$/, '')
    }
  } catch {
    return url
  }

  return url
}

export const getApiBaseUrl = () => {
  const configured = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '')
  const hasWindow = typeof window !== 'undefined'
  const hostname = hasWindow ? window.location.hostname : 'localhost'
  const protocol = hasWindow ? window.location.protocol : 'http:'

  if (configured) {
    // Guardrail: never use localhost API for non-local browser origins.
    if (!isLocalHostname(hostname) && isLocalAddressUrl(configured)) {
      if (shouldUseDefaultProdApi(hostname)) {
        return DEFAULT_PROD_API_BASE
      }

      return `${protocol}//${hostname}:8002`
    }

    return upgradeHttpToHttpsIfNeeded(configured, hostname)
  }

  if (isLocalHostname(hostname)) {
    return DEFAULT_LOCAL_API_BASE
  }

  if (shouldUseDefaultProdApi(hostname)) {
    return DEFAULT_PROD_API_BASE
  }

  return `${protocol}//${hostname}:8002`
}

export const getWsBaseUrl = () => {
  const configuredWs = (import.meta.env.VITE_WS_URL || '').trim().replace(/\/$/, '')
  const hasWindow = typeof window !== 'undefined'
  const hostname = hasWindow ? window.location.hostname : 'localhost'
  const protocol = hasWindow ? window.location.protocol : 'http:'

  if (configuredWs) {
    // Guardrail: never use localhost WS endpoint for non-local browser origins.
    if (!isLocalHostname(hostname) && isLocalAddressUrl(configuredWs)) {
      if (shouldUseDefaultProdApi(hostname)) {
        return DEFAULT_PROD_API_BASE.replace(/^http/i, 'ws')
      }

      const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:'
      return `${wsProtocol}//${hostname}:8002`
    }

    if (!isLocalHostname(hostname)) {
      return configuredWs.replace(/^ws:/i, 'wss:')
    }

    return configuredWs
  }

  const apiBase = getApiBaseUrl()
  return apiBase.replace(/^http/i, 'ws')
}

export const API_BASE = getApiBaseUrl()
export const WS_BASE = getWsBaseUrl()
export const BACKEND_HEALTH_URL = `${API_BASE}/health`