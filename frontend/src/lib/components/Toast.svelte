<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';

	export let type: 'success' | 'error' | 'warning' | 'info' = 'info';
	export let title: string = '';
	export let message: string = '';
	export let duration: number = 5000; // Auto-dismiss after 5 seconds
	export let dismissible: boolean = true;
	export let persistent: boolean = false; // Don't auto-dismiss
	export let position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center' = 'top-right';

	const dispatch = createEventDispatcher();
	let visible = false;
	let timeoutId: number;

	const typeConfig = {
		success: {
			icon: '✓',
			color: 'success',
			ariaLabel: 'Success notification'
		},
		error: {
			icon: '✕',
			color: 'error',
			ariaLabel: 'Error notification'
		},
		warning: {
			icon: '⚠',
			color: 'warning',
			ariaLabel: 'Warning notification'
		},
		info: {
			icon: 'ℹ',
			color: 'info',
			ariaLabel: 'Information notification'
		}
	};

	const positionClasses = {
		'top-right': 'toast-top-right',
		'top-left': 'toast-top-left',
		'bottom-right': 'toast-bottom-right',
		'bottom-left': 'toast-bottom-left',
		'top-center': 'toast-top-center',
		'bottom-center': 'toast-bottom-center'
	};

	onMount(() => {
		visible = true;
		
		if (!persistent && duration > 0) {
			timeoutId = setTimeout(() => {
				dismiss();
			}, duration);
		}
		
		return () => {
			if (timeoutId) {
				clearTimeout(timeoutId);
			}
		};
	});

	function dismiss() {
		visible = false;
		setTimeout(() => {
			dispatch('dismiss');
		}, 300); // Wait for exit animation
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && dismissible) {
			dismiss();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if visible}
	<div 
		class="toast toast-{type} {positionClasses[position]} {visible ? 'toast-enter' : 'toast-exit'}"
		role="alert"
		aria-live="polite"
		aria-label={typeConfig[type].ariaLabel}
	>
		<div class="toast-content">
			<div class="toast-icon" aria-hidden="true">
				{typeConfig[type].icon}
			</div>
			
			<div class="toast-text">
				{#if title}
					<div class="toast-title">{title}</div>
				{/if}
				{#if message}
					<div class="toast-message">{message}</div>
				{/if}
			</div>
			
			{#if dismissible}
				<button 
					class="toast-dismiss"
					on:click={dismiss}
					aria-label="Dismiss notification"
					type="button"
				>
					×
				</button>
			{/if}
		</div>
		
		{#if !persistent && duration > 0}
			<div class="toast-progress" style="animation-duration: {duration}ms;"></div>
		{/if}
	</div>
{/if}

<style>
	.toast {
		position: fixed;
		z-index: var(--z-toast, 1000);
		max-width: 400px;
		min-width: 300px;
		background: var(--color-surface);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		border: 1px solid var(--color-border);
		overflow: hidden;
		pointer-events: auto;
	}

	.toast-content {
		display: flex;
		align-items: flex-start;
		padding: var(--space-4);
		gap: var(--space-3);
	}

	.toast-icon {
		flex-shrink: 0;
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 16px;
		font-weight: bold;
	}

	.toast-text {
		flex: 1;
		min-width: 0;
	}

	.toast-title {
		font-weight: var(--font-semibold);
		font-size: var(--text-sm);
		color: var(--color-text-primary);
		margin-bottom: var(--space-1);
	}

	.toast-message {
		font-size: var(--text-sm);
		color: var(--color-text-secondary);
		line-height: var(--leading-relaxed);
	}

	.toast-dismiss {
		flex-shrink: 0;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		cursor: pointer;
		color: var(--color-text-tertiary);
		font-size: 18px;
		line-height: 1;
		border-radius: var(--radius-sm);
		transition: all var(--duration-fast) var(--ease-material);
	}

	.toast-dismiss:hover {
		background-color: var(--color-gray-100);
		color: var(--color-text-secondary);
	}

	.toast-dismiss:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}

	.toast-progress {
		height: 3px;
		background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-primary) 100%);
		animation: toast-progress linear;
		transform-origin: left;
	}

	@keyframes toast-progress {
		from {
			transform: scaleX(1);
		}
		to {
			transform: scaleX(0);
		}
	}

	/* Type-specific styles */
	.toast-success {
		border-left: 4px solid var(--color-success);
	}

	.toast-success .toast-icon {
		color: var(--color-success);
	}

	.toast-error {
		border-left: 4px solid var(--color-error);
	}

	.toast-error .toast-icon {
		color: var(--color-error);
	}

	.toast-warning {
		border-left: 4px solid var(--color-warning);
	}

	.toast-warning .toast-icon {
		color: var(--color-warning);
	}

	.toast-info {
		border-left: 4px solid var(--color-info);
	}

	.toast-info .toast-icon {
		color: var(--color-info);
	}

	/* Position classes */
	.toast-top-right {
		top: var(--space-4);
		right: var(--space-4);
	}

	.toast-top-left {
		top: var(--space-4);
		left: var(--space-4);
	}

	.toast-bottom-right {
		bottom: var(--space-4);
		right: var(--space-4);
	}

	.toast-bottom-left {
		bottom: var(--space-4);
		left: var(--space-4);
	}

	.toast-top-center {
		top: var(--space-4);
		left: 50%;
		transform: translateX(-50%);
	}

	.toast-bottom-center {
		bottom: var(--space-4);
		left: 50%;
		transform: translateX(-50%);
	}

	/* Animation classes */
	.toast-enter {
		animation: toast-slide-in var(--duration-normal) var(--ease-material);
	}

	.toast-exit {
		animation: toast-slide-out var(--duration-normal) var(--ease-material);
	}

	@keyframes toast-slide-in {
		from {
			transform: translateX(100%);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	@keyframes toast-slide-out {
		from {
			transform: translateX(0);
			opacity: 1;
		}
		to {
			transform: translateX(100%);
			opacity: 0;
		}
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.toast {
			max-width: calc(100vw - 2rem);
			min-width: auto;
			left: var(--space-4) !important;
			right: var(--space-4) !important;
			transform: none !important;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.toast-enter,
		.toast-exit {
			animation: none;
		}
		
		.toast-progress {
			animation: none;
		}
	}
</style>