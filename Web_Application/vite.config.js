import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // Load only proxy settings. Database credentials belong exclusively to Python.
  const env = loadEnv(mode, process.cwd(), 'API_PROXY_');
  return {
    server: {
      proxy: {
        '^/api(?:/|$)': {
          target: process.env.API_PROXY_TARGET || env.API_PROXY_TARGET || 'http://127.0.0.1:8080',
          changeOrigin: true,
          proxyTimeout: 12000,
          timeout: 12000,
        },
      },
    },
  };
});
