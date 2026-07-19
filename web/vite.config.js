import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: { alias: { '@': path.resolve(__dirname, './src') } },
    server: { port: 5173, host: true },
    build: {
        chunkSizeWarningLimit: 900,
        rollupOptions: {
            output: {
                manualChunks: {
                    'react-vendor': ['react', 'react-dom', 'react-router-dom'],
                    'query-vendor': ['@tanstack/react-query'],
                    'firebase-vendor': ['firebase/app', 'firebase/auth'],
                    'charts-vendor': ['recharts'],
                    'motion-vendor': ['framer-motion'],
                    'icons-vendor': ['lucide-react']
                }
            }
        }
    }
});
