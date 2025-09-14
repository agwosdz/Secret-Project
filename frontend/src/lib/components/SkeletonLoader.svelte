<script lang="ts">
	export let width: string = '100%';
	export let height: string = '1rem';
	export let variant: 'text' | 'rectangular' | 'circular' | 'rounded' = 'text';
	export let lines: number = 1;
	export let animated: boolean = true;
	export let className: string = '';

	const variantClasses = {
		text: 'rounded-sm',
		rectangular: 'rounded-none',
		circular: 'rounded-full',
		rounded: 'rounded-md'
	};
</script>

{#if lines === 1}
	<div 
		class="skeleton {variantClasses[variant]} {animated ? 'animated' : ''} {className}"
		style="width: {width}; height: {height};"
		aria-hidden="true"
	></div>
{:else}
	<div class="skeleton-group" aria-hidden="true">
		{#each Array(lines) as _, i}
			<div 
				class="skeleton {variantClasses[variant]} {animated ? 'animated' : ''} {className}"
				style="width: {i === lines - 1 ? '75%' : width}; height: {height}; margin-bottom: {i === lines - 1 ? '0' : '0.5rem'};"
			></div>
		{/each}
	</div>
{/if}

<style>
	.skeleton {
		background: linear-gradient(
			90deg,
			var(--color-gray-200) 25%,
			var(--color-gray-100) 50%,
			var(--color-gray-200) 75%
		);
		background-size: 200% 100%;
		display: block;
	}

	.skeleton.animated {
		animation: skeleton-loading 1.5s ease-in-out infinite;
	}

	.skeleton-group {
		display: flex;
		flex-direction: column;
	}

	@keyframes skeleton-loading {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}

	/* Border Radius Classes */
	.rounded-none { border-radius: 0; }
	.rounded-sm { border-radius: var(--radius-sm); }
	.rounded-md { border-radius: var(--radius-md); }
	.rounded-full { border-radius: var(--radius-full); }

	/* Dark Mode Support - Use .dark class instead */
	:global(.dark) .skeleton {
		background: linear-gradient(
			90deg,
			var(--color-gray-700) 25%,
			var(--color-gray-600) 50%,
			var(--color-gray-700) 75%
		);
	}

	@media (prefers-reduced-motion: reduce) {
		.skeleton.animated {
			animation: none;
		}
	}
</style>