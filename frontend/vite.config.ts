import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Get backend port from environment variable, default to 5001
const BACKEND_PORT = process.env.VITE_BACKEND_PORT || process.env.FLASK_PORT || '5001';
const BACKEND_HOST = process.env.VITE_BACKEND_HOST || 'localhost';
const backendTarget = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: backendTarget,
				changeOrigin: true
			},
			'/health': {
				target: backendTarget,
				changeOrigin: true
			},
			'/socket.io': {
				target: backendTarget,
				changeOrigin: true,
				ws: true
			}
		}
	}
});
