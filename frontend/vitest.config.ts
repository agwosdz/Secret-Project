import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [
		svelte({
			compilerOptions: {
				dev: true,
				generate: 'dom'
			},
			onwarn: (warning, handler) => {
				// Suppress warnings during testing
				if (warning.code === 'css-unused-selector') return;
				handler(warning);
			}
		})
	],
	test: {
		environment: 'happy-dom',
		globals: true,
		setupFiles: ['./src/test-setup.ts'],
		include: ['src/**/*.{test,spec}.{js,ts}'],
		exclude: ['node_modules', '.svelte-kit']
	}
});