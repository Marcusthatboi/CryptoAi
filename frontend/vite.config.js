import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const tunnelDomain = (env.VITE_TUNNEL_DOMAIN || 'dacryptobeast.com').trim()
  const useTunnelHmr = env.VITE_TUNNEL_HMR === 'true'
  const buildStamp = new Date().toISOString()

  return {
    plugins: [react()],
    define: {
      __BUILD_STAMP__: JSON.stringify(buildStamp)
    },
    server: {
      host: '127.0.0.1',
      port: 5175,
      strictPort: false,
      middlewareMode: false,
      allowedHosts: ['dacryptobeast.com', 'www.dacryptobeast.com', 'localhost', '127.0.0.1', '192.168.1.147'],
      hmr: useTunnelHmr
        ? {
            protocol: 'wss',
            host: tunnelDomain,
            clientPort: 443
          }
        : undefined,
      proxy: {
        '/health': {
          target: 'http://127.0.0.1:8002',
          changeOrigin: true
        },
        '/api': {
          target: 'http://127.0.0.1:8002',
          changeOrigin: true
        }
      }
    }
  }
})
