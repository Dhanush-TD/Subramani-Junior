import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    // Keep Vite on the port expected by Tauri
    port: 5176,
    strictPort: true,

    // Prevent Vite from watching files that can cause EBUSY/locking errors
    watch: {
      ignored: [
        '**/src-tauri/**',
        '**/*.zip',
      ],
    },
  },
})