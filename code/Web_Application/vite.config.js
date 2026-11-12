// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: dev server, /api proxy, file watching
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: ran start_project.sh in WSL + Docker, checked localhost:3000, :8080/docs and /api/health/database

import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // Load only proxy settings. Database credentials belong exclusively to Python.
  const env = loadEnv(mode, process.cwd(), 'API_PROXY_');
  return {
    server: {
      watch: {
        usePolling: process.env.DEV_USE_POLLING === 'true',
        interval: 300,
      },
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
