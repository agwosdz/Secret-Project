import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	// Load environment variables from .env files
	const env = loadEnv(mode, process.cwd(), '');
	
	// Get backend port from environment variable, default to 5001 for RPI
	const BACKEND_PORT = env.VITE_BACKEND_PORT || env.FLASK_PORT || '5001';
	const BACKEND_HOST = env.VITE_BACKEND_HOST || 'localhost';
	const backendTarget = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

	console.log('Vite proxy configuration:');
	console.log('BACKEND_HOST:', BACKEND_HOST);
	console.log('BACKEND_PORT:', BACKEND_PORT);
	console.log('backendTarget:', backendTarget);

	return {
		plugins: [sveltekit()],
		server: {
			proxy: {
				'/api': {
					target: backendTarget,
					changeOrigin: true,
					secure: false,
					configure: (proxy, _options) => {
						proxy.on('error', (err, _req, _res) => {
							console.log('proxy error', err);
						});
						proxy.on('proxyReq', (proxyReq, req, _res) => {
							console.log('Sending Request to the Target:', req.method, req.url);
						});
						proxy.on('proxyRes', (proxyRes, req, _res) => {
							console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
						});
					}
				},
				'/health': {
					target: backendTarget,
					changeOrigin: true,
					secure: false
				},
				'/socket.io': {
					target: backendTarget,
					changeOrigin: true,
					ws: true,
					secure: false,
					configure: (proxy, _options) => {
						proxy.on('error', (err, _req, _res) => {
							console.log('socket.io proxy error', err);
						});
					}
				}
			}
		}
	};
});
