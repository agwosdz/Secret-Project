<script lang="ts">
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let color: 'primary' | 'secondary' | 'white' = 'primary';
	export let label: string = 'Loading...';

	const sizeClasses = {
		sm: 'w-4 h-4',
		md: 'w-6 h-6',
		lg: 'w-8 h-8'
	};

	const colorClasses = {
		primary: 'text-primary',
		secondary: 'text-secondary',
		white: 'text-white'
	};
</script>

<div 
	class="loading-spinner {sizeClasses[size]} {colorClasses[color]}" 
	role="status" 
	aria-label={label}
>
	<svg 
		class="animate-spin" 
		fill="none" 
		viewBox="0 0 24 24"
		aria-hidden="true"
	>
		<circle 
			class="opacity-25" 
			cx="12" 
			cy="12" 
			r="10" 
			stroke="currentColor" 
			stroke-width="4"
		></circle>
		<path 
			class="opacity-75" 
			fill="currentColor" 
			d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
		></path>
	</svg>
	<span class="sr-only">{label}</span>
</div>

<style>
	.loading-spinner {
		display: inline-block;
		color: var(--color-primary);
	}

	.loading-spinner svg {
		width: 100%;
		height: 100%;
	}

	.w-4 { width: 1rem; }
	.h-4 { height: 1rem; }
	.w-6 { width: 1.5rem; }
	.h-6 { height: 1.5rem; }
	.w-8 { width: 2rem; }
	.h-8 { height: 2rem; }

	.text-primary { color: var(--color-primary); }
	.text-secondary { color: var(--color-text-secondary); }
	.text-white { color: white; }

	.animate-spin {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.animate-spin {
			animation: none;
		}
	}
</style>