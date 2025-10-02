<script>
	export let type = 'info'; // 'success', 'error', 'warning', 'info', 'validating'
	export let message = '';
	export let details = [];
	export let dismissible = false;
	export let compact = false;
	export let showIcon = true;
	
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	
	function dismiss() {
		dispatch('dismiss');
	}
	
	$: iconName = getIconForType(type);
	$: colorClass = `validation-${type}`;
	
	function getIconForType(type) {
		switch (type) {
			case 'success':
				return 'check-circle';
			case 'error':
				return 'x-circle';
			case 'warning':
				return 'exclamation-triangle';
			case 'validating':
				return 'loading';
			case 'info':
			default:
				return 'information-circle';
		}
	}
</script>

{#if message || details.length > 0}
	<div class="validation-message {colorClass}" class:compact class:dismissible>
		<div class="message-content">
			{#if showIcon}
				<div class="message-icon">
					{#if type === 'validating'}
						<div class="spinner"></div>
					{:else if iconName === 'check-circle'}
						<svg viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
						</svg>
					{:else if iconName === 'x-circle'}
						<svg viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
						</svg>
					{:else if iconName === 'exclamation-triangle'}
						<svg viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
						</svg>
					{:else}
						<svg viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
						</svg>
					{/if}
				</div>
			{/if}
			
			<div class="message-text">
				{#if message}
					<div class="primary-message">{message}</div>
				{/if}
				
				{#if details.length > 0}
					<ul class="message-details">
						{#each details as detail}
							<li>{detail}</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>
		
		{#if dismissible}
			<button class="dismiss-button" on:click={dismiss} type="button" aria-label="Dismiss message">
				<svg viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>
		{/if}
	</div>
{/if}

<style>
	.validation-message {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		padding: 0.75rem;
		border-radius: 0.375rem;
		border: 1px solid;
		font-size: 0.875rem;
		line-height: 1.4;
		transition: all 0.2s ease;
	}
	
	.validation-message.compact {
		padding: 0.5rem;
		font-size: 0.8125rem;
	}
	
	.message-content {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		flex: 1;
	}
	
	.message-icon {
		flex-shrink: 0;
		width: 1.25rem;
		height: 1.25rem;
		margin-top: 0.125rem;
	}
	
	.compact .message-icon {
		width: 1rem;
		height: 1rem;
	}
	
	.message-icon svg {
		width: 100%;
		height: 100%;
	}
	
	.spinner {
		width: 100%;
		height: 100%;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	.message-text {
		flex: 1;
		min-width: 0;
	}
	
	.primary-message {
		font-weight: 500;
		margin-bottom: 0.25rem;
	}
	
	.message-details {
		margin: 0;
		padding-left: 1rem;
		list-style-type: disc;
	}
	
	.message-details li {
		margin-bottom: 0.125rem;
	}
	
	.message-details li:last-child {
		margin-bottom: 0;
	}
	
	.dismiss-button {
		flex-shrink: 0;
		background: none;
		border: none;
		padding: 0.125rem;
		cursor: pointer;
		border-radius: 0.25rem;
		transition: background-color 0.2s ease;
		width: 1.25rem;
		height: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.dismiss-button:hover {
		background: rgba(0, 0, 0, 0.1);
	}
	
	.dismiss-button svg {
		width: 1rem;
		height: 1rem;
	}
	
	/* Type-specific styles */
	.validation-success {
		background: var(--color-success-light, #f0fdf4);
		border-color: var(--color-success, #22c55e);
		color: var(--color-success-dark, #15803d);
	}
	
	.validation-error {
		background: var(--color-error-light, #fef2f2);
		border-color: var(--color-error, #ef4444);
		color: var(--color-error-dark, #dc2626);
	}
	
	.validation-warning {
		background: var(--color-warning-light, #fffbeb);
		border-color: var(--color-warning, #f59e0b);
		color: var(--color-warning-dark, #d97706);
	}
	
	.validation-info {
		background: var(--color-info-light, #eff6ff);
		border-color: var(--color-info, #3b82f6);
		color: var(--color-info-dark, #1d4ed8);
	}
	
	.validation-validating {
		background: var(--color-surface-secondary, #f9fafb);
		border-color: var(--color-border, #d1d5db);
		color: var(--color-text-secondary, #6b7280);
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
</style>