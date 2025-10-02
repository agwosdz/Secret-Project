<script>
	import { createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	export let title = '';
	export let description = '';
	export let loading = false;
	export let error = '';
	export let hasUnsavedChanges = false;
	export let canSave = true;
	export let canReset = true;
	export let showActions = true;
	export let collapsible = false;
	export let collapsed = false;
	export let icon = '';
	
	function handleSave() {
		dispatch('save');
	}
	
	function handleReset() {
		dispatch('reset');
	}
	
	function toggleCollapsed() {
		if (collapsible) {
			collapsed = !collapsed;
		}
	}
</script>

<div class="settings-section" class:loading class:has-error={error} class:collapsed>
	<div class="section-header" class:clickable={collapsible} on:click={toggleCollapsed}>
		<div class="header-content">
			{#if icon}
				<span class="section-icon">{icon}</span>
			{/if}
			<div class="header-text">
				<h3 class="section-title">{title}</h3>
				{#if description}
					<p class="section-description">{description}</p>
				{/if}
			</div>
		</div>
		
		<div class="header-actions">
			{#if hasUnsavedChanges}
				<div class="unsaved-indicator">
					<div class="unsaved-dot"></div>
					<span class="unsaved-text">Unsaved changes</span>
				</div>
			{/if}
			
			{#if collapsible}
				<button class="collapse-button" type="button">
					<svg class="collapse-icon" class:rotated={!collapsed} viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
					</svg>
				</button>
			{/if}
		</div>
	</div>
	
	{#if error}
		<div class="error-banner">
			<svg class="error-icon" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
			</svg>
			<span>{error}</span>
		</div>
	{/if}
	
	{#if !collapsed}
		<div class="section-content">
			{#if loading}
				<div class="loading-overlay">
					<div class="loading-spinner"></div>
					<span class="loading-text">Loading settings...</span>
				</div>
			{/if}
			
			<div class="content-wrapper" class:loading>
				<slot />
			</div>
			
			{#if showActions}
				<div class="section-actions">
					<button
						type="button"
						class="action-button secondary"
						disabled={!canReset || !hasUnsavedChanges || loading}
						on:click={handleReset}
					>
						Reset Changes
					</button>
					
					<button
						type="button"
						class="action-button primary"
						disabled={!canSave || !hasUnsavedChanges || loading}
						on:click={handleSave}
					>
						{#if loading}
							<div class="button-spinner"></div>
						{/if}
						Save Changes
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.settings-section {
		background: var(--color-surface, #ffffff);
		border: 1px solid var(--color-border, #e5e7eb);
		border-radius: 0.5rem;
		overflow: hidden;
		transition: all 0.2s ease;
	}
	
	.settings-section.loading {
		opacity: 0.8;
	}
	
	.settings-section.has-error {
		border-color: var(--color-error, #ef4444);
	}
	
	.section-header {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--color-border, #e5e7eb);
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--color-surface-secondary, #f9fafb);
	}
	
	.section-header.clickable {
		cursor: pointer;
		transition: background-color 0.2s ease;
	}
	
	.section-header.clickable:hover {
		background: var(--color-surface-hover, #f3f4f6);
	}
	
	.header-content {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex: 1;
	}
	
	.section-icon {
		font-size: 1.25rem;
	}
	
	.header-text {
		flex: 1;
	}
	
	.section-title {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--color-text-primary, #111827);
	}
	
	.section-description {
		margin: 0.25rem 0 0 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary, #6b7280);
	}
	
	.header-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.unsaved-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--color-warning, #f59e0b);
		font-size: 0.875rem;
	}
	
	.unsaved-dot {
		width: 0.5rem;
		height: 0.5rem;
		background: var(--color-warning, #f59e0b);
		border-radius: 50%;
		animation: pulse 2s infinite;
	}
	
	.collapse-button {
		background: none;
		border: none;
		padding: 0.25rem;
		cursor: pointer;
		color: var(--color-text-secondary, #6b7280);
		transition: color 0.2s ease;
	}
	
	.collapse-button:hover {
		color: var(--color-text-primary, #111827);
	}
	
	.collapse-icon {
		width: 1.25rem;
		height: 1.25rem;
		transition: transform 0.2s ease;
	}
	
	.collapse-icon.rotated {
		transform: rotate(180deg);
	}
	
	.error-banner {
		padding: 0.75rem 1.5rem;
		background: var(--color-error-light, #fef2f2);
		border-bottom: 1px solid var(--color-border, #e5e7eb);
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--color-error, #ef4444);
		font-size: 0.875rem;
	}
	
	.error-icon {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
	}
	
	.section-content {
		position: relative;
	}
	
	.loading-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(255, 255, 255, 0.8);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		z-index: 10;
	}
	
	.loading-spinner {
		width: 2rem;
		height: 2rem;
		border: 2px solid var(--color-border, #e5e7eb);
		border-top: 2px solid var(--color-primary, #3b82f6);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	.loading-text {
		font-size: 0.875rem;
		color: var(--color-text-secondary, #6b7280);
	}
	
	.content-wrapper {
		padding: 1.5rem;
		transition: opacity 0.2s ease;
	}
	
	.content-wrapper.loading {
		opacity: 0.5;
		pointer-events: none;
	}
	
	.section-actions {
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--color-border, #e5e7eb);
		background: var(--color-surface-secondary, #f9fafb);
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
	}
	
	.action-button {
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		border: 1px solid transparent;
	}
	
	.action-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.action-button.primary {
		background: var(--color-primary, #3b82f6);
		color: white;
	}
	
	.action-button.primary:hover:not(:disabled) {
		background: var(--color-primary-dark, #2563eb);
	}
	
	.action-button.secondary {
		background: var(--color-surface, #ffffff);
		color: var(--color-text-primary, #374151);
		border-color: var(--color-border, #d1d5db);
	}
	
	.action-button.secondary:hover:not(:disabled) {
		background: var(--color-surface-hover, #f9fafb);
	}
	
	.button-spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	.collapsed .section-content {
		display: none;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
</style>