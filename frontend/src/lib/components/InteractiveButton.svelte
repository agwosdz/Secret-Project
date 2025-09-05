<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' = 'primary';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let disabled: boolean = false;
	export let loading: boolean = false;
	export let ripple: boolean = true;
	export let href: string | undefined = undefined;
	export let type: 'button' | 'submit' | 'reset' = 'button';
	export let ariaLabel: string | undefined = undefined;
	export let className: string = '';

	const dispatch = createEventDispatcher();

	let buttonElement: HTMLButtonElement | HTMLAnchorElement;
	let rippleElement: HTMLDivElement;

	const sizeClasses = {
		sm: 'btn-sm',
		md: 'btn-md',
		lg: 'btn-lg'
	};

	const variantClasses = {
		primary: 'btn-primary',
		secondary: 'btn-secondary',
		outline: 'btn-outline',
		ghost: 'btn-ghost',
		danger: 'btn-danger'
	};

	function handleClick(event: MouseEvent) {
		if (disabled || loading) {
			event.preventDefault();
			return;
		}

		if (ripple && buttonElement) {
			createRipple(event);
		}

		dispatch('click', event);
	}

	function createRipple(event: MouseEvent) {
		const button = buttonElement;
		const rect = button.getBoundingClientRect();
		const size = Math.max(rect.width, rect.height);
		const x = event.clientX - rect.left - size / 2;
		const y = event.clientY - rect.top - size / 2;

		const ripple = document.createElement('div');
		ripple.className = 'ripple-effect';
		ripple.style.width = ripple.style.height = size + 'px';
		ripple.style.left = x + 'px';
		ripple.style.top = y + 'px';

		button.appendChild(ripple);

		setTimeout(() => {
			if (ripple.parentNode) {
				ripple.parentNode.removeChild(ripple);
			}
		}, 600);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleClick(event as any);
		}
	}
</script>

{#if href && !disabled}
	<a
		bind:this={buttonElement}
		{href}
		class="btn {variantClasses[variant]} {sizeClasses[size]} {className}"
		class:disabled
		class:loading
		class:btn-ripple={ripple}
		aria-label={ariaLabel}
		on:click={handleClick}
		on:keydown={handleKeydown}
		role="button"
		tabindex="0"
	>
		{#if loading}
			<div class="loading-spinner" aria-hidden="true"></div>
		{/if}
		<slot />
	</a>
{:else}
	<button
		bind:this={buttonElement}
		{type}
		{disabled}
		class="btn {variantClasses[variant]} {sizeClasses[size]} {className}"
		class:loading
		class:btn-ripple={ripple}
		aria-label={ariaLabel}
		on:click={handleClick}
	>
		{#if loading}
			<div class="loading-spinner" aria-hidden="true"></div>
		{/if}
		<slot />
	</button>
{/if}

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		border: none;
		border-radius: var(--radius-md);
		font-weight: var(--font-medium);
		line-height: 1;
		cursor: pointer;
		transition: all var(--duration-fast) var(--ease-material);
		text-decoration: none;
		user-select: none;
		position: relative;
		overflow: hidden;
		transform: translateY(0);
		white-space: nowrap;
	}

	/* Size variants */
	.btn-sm {
		padding: var(--space-2) var(--space-3);
		font-size: var(--text-xs);
		min-height: 32px;
	}

	.btn-md {
		padding: var(--space-3) var(--space-4);
		font-size: var(--text-sm);
		min-height: 40px;
	}

	.btn-lg {
		padding: var(--space-4) var(--space-6);
		font-size: var(--text-base);
		min-height: 48px;
	}

	/* Hover effect */
	.btn::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
		transform: scale(0);
		transition: transform var(--duration-fast) var(--ease-material);
		pointer-events: none;
		opacity: 0;
	}

	.btn:hover::before {
		transform: scale(1);
		opacity: 1;
	}

	.btn:active {
		transform: translateY(1px) scale(0.98);
		transition: transform 0.1s var(--ease-bounce);
	}

	/* Variant styles */
	.btn-primary {
		background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
		color: var(--color-text-inverse);
		box-shadow: 0 2px 8px rgba(var(--color-primary-rgb), 0.3);
	}

	.btn-primary:hover {
		background: linear-gradient(135deg, var(--color-primary-hover), var(--color-primary));
		box-shadow: 0 4px 16px rgba(var(--color-primary-rgb), 0.4);
		transform: translateY(-2px);
	}

	.btn-secondary {
		background: var(--color-surface);
		color: var(--color-text-primary);
		border: 1px solid var(--color-border);
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.btn-secondary:hover {
		background: var(--color-surface-hover);
		border-color: var(--color-primary);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transform: translateY(-1px);
	}

	.btn-outline {
		background: transparent;
		color: var(--color-primary);
		border: 2px solid var(--color-primary);
	}

	.btn-outline:hover {
		background: var(--color-primary);
		color: var(--color-text-inverse);
		transform: translateY(-1px);
	}

	.btn-ghost {
		background: transparent;
		color: var(--color-text-primary);
		border: none;
	}

	.btn-ghost:hover {
		background: var(--color-surface-hover);
	}

	.btn-danger {
		background: linear-gradient(135deg, var(--color-error), var(--color-error-dark));
		color: var(--color-text-inverse);
		box-shadow: 0 2px 8px rgba(var(--color-error-rgb), 0.3);
	}

	.btn-danger:hover {
		background: linear-gradient(135deg, var(--color-error-hover), var(--color-error));
		box-shadow: 0 4px 16px rgba(var(--color-error-rgb), 0.4);
		transform: translateY(-2px);
	}

	/* Disabled state */
	.btn:disabled,
	.btn.disabled {
		opacity: 0.5;
		cursor: not-allowed;
		pointer-events: none;
		transform: none;
		box-shadow: none;
	}

	.btn:disabled::before,
	.btn.disabled::before {
		display: none;
	}

	/* Loading state */
	.btn.loading {
		pointer-events: none;
		position: relative;
	}

	.loading-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	/* Ripple effect */
	:global(.ripple-effect) {
		position: absolute;
		border-radius: 50%;
		background: rgba(255, 255, 255, 0.6);
		transform: scale(0);
		animation: ripple 0.6s linear;
		pointer-events: none;
	}

	@keyframes ripple {
		to {
			transform: scale(4);
			opacity: 0;
		}
	}

	/* Focus styles */
	.btn:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}

	/* Reduced motion */
	@media (prefers-reduced-motion: reduce) {
		.btn {
			transition: none;
		}
		
		.btn::before {
			transition: none;
		}
		
		.loading-spinner {
			animation: none;
		}
		
		:global(.ripple-effect) {
			animation: none;
		}
	}
</style>