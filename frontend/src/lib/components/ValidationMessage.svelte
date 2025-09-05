<script lang="ts">
	import type { ValidationResult } from '$lib/upload';

	export let validation: ValidationResult | null = null;
	export let showDetails = false;
	export let variant: 'inline' | 'card' | 'toast' = 'inline';
	export let size: 'small' | 'medium' | 'large' = 'medium';

	$: hasError = validation && !validation.valid;
	$: hasDetails = validation?.details || validation?.suggestion;
</script>

{#if hasError}
	<div class="validation-message {variant} {size}" role="alert" aria-live="polite">
		<div class="message-header">
			<svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
				<circle cx="12" cy="12" r="10"/>
				<line x1="15" y1="9" x2="9" y2="15"/>
				<line x1="9" y1="9" x2="15" y2="15"/>
			</svg>
			<span class="message-text">{validation.message}</span>
		</div>

		{#if validation.suggestion && (showDetails || variant === 'card')}
			<div class="suggestion">
				<svg class="suggestion-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<circle cx="12" cy="12" r="10"/>
					<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
					<line x1="12" y1="17" x2="12.01" y2="17"/>
				</svg>
				<span>{validation.suggestion}</span>
			</div>
		{/if}

		{#if validation.details && showDetails}
			<div class="details">
				{#if validation.details.actualExtension && validation.details.allowedExtensions}
					<div class="detail-item">
						<strong>Found:</strong> .{validation.details.actualExtension}
					</div>
					<div class="detail-item">
						<strong>Allowed:</strong> {validation.details.allowedExtensions.join(', ')}
					</div>
				{/if}
				{#if validation.details.actualSize && validation.details.maxSize}
					<div class="detail-item">
						<strong>File size:</strong> {validation.details.actualSize}
					</div>
					<div class="detail-item">
						<strong>Maximum:</strong> {validation.details.maxSize}
					</div>
				{/if}
				{#if validation.details.actualSize && !validation.details.maxSize}
					<div class="detail-item">
						<strong>File size:</strong> {validation.details.actualSize}
					</div>
				{/if}
			</div>
		{/if}

		{#if hasDetails && !showDetails && variant === 'inline'}
			<button 
				class="toggle-details" 
				on:click={() => showDetails = !showDetails}
				aria-label="Show more details"
			>
				Show details
				<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<polyline points="6,9 12,15 18,9"/>
				</svg>
			</button>
		{/if}
	</div>
{/if}

<style>
	.validation-message {
		border-radius: 8px;
		transition: all 0.2s ease;
		animation: slideIn 0.3s ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.inline {
		background: #fef2f2;
		border: 1px solid #fecaca;
		padding: 0.75rem;
		margin: 0.5rem 0;
	}

	.card {
		background: white;
		border: 1px solid #fecaca;
		padding: 1rem;
		margin: 1rem 0;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.toast {
		background: #fef2f2;
		border: 1px solid #fecaca;
		padding: 0.75rem;
		border-radius: 6px;
	}

	.small {
		font-size: 0.875rem;
		padding: 0.5rem;
	}

	.medium {
		font-size: 0.9375rem;
	}

	.large {
		font-size: 1rem;
		padding: 1.25rem;
	}

	.message-header {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
	}

	.error-icon {
		width: 1.25rem;
		height: 1.25rem;
		color: #dc2626;
		flex-shrink: 0;
		stroke-width: 2;
		margin-top: 0.125rem;
	}

	.message-text {
		color: #991b1b;
		font-weight: 500;
		line-height: 1.5;
	}

	.suggestion {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		margin-top: 0.75rem;
		padding: 0.75rem;
		background: #f0f9ff;
		border: 1px solid #bae6fd;
		border-radius: 6px;
	}

	.suggestion-icon {
		width: 1rem;
		height: 1rem;
		color: #0369a1;
		flex-shrink: 0;
		stroke-width: 2;
		margin-top: 0.125rem;
	}

	.suggestion span {
		color: #0c4a6e;
		font-size: 0.875rem;
		line-height: 1.4;
	}

	.details {
		margin-top: 0.75rem;
		padding: 0.75rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
	}

	.detail-item {
		margin: 0.25rem 0;
		color: #374151;
	}

	.detail-item strong {
		color: #111827;
		font-weight: 600;
	}

	.toggle-details {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		margin-top: 0.5rem;
		padding: 0.25rem 0;
		background: none;
		border: none;
		color: #6b7280;
		font-size: 0.875rem;
		cursor: pointer;
		transition: color 0.2s ease;
	}

	.toggle-details:hover {
		color: #374151;
	}

	.toggle-details:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
		border-radius: 4px;
	}

	.chevron {
		width: 1rem;
		height: 1rem;
		stroke-width: 2;
		transition: transform 0.2s ease;
	}

	.toggle-details:hover .chevron {
		transform: translateY(1px);
	}
</style>