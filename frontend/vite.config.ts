import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:5000',
				changeOrigin: true
			},
			'/health': {
				target: 'http://localhost:5000',
				changeOrigin: true
			},
			'/socket.io': {
				target: 'http://localhost:5000',
				changeOrigin: true,
				ws: true
			}
		}
	}
});
