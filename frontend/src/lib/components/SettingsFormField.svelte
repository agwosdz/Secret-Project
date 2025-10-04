<script>
	import { createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	export let type = 'text';
	export let label = '';
	export let value = '';
	export let placeholder = '';
	export let required = false;
	export let disabled = false;
	export let error = '';
	export let helpText = '';
	export let min = undefined;
	export let max = undefined;
	export let step = undefined;
	export let options = []; // For select fields
	export let loading = false;
	export let validationState = 'none'; // 'none', 'validating', 'valid', 'invalid'
	export let id = '';
	
	// Generate unique ID if not provided
	if (!id) {
		id = `field-${Math.random().toString(36).substr(2, 9)}`;
	}
	
	function handleInput(event) {
		let newValue = event.target.value;
		
		// Convert to appropriate type for number inputs
		if (type === 'number' || type === 'range') {
			newValue = parseFloat(newValue);
			// Handle NaN case
			if (isNaN(newValue)) {
				newValue = 0;
			}
		}
		
		value = newValue;
		dispatch('input', { value: newValue, id });
	}
	
	function handleChange(event) {
		let newValue = event.target.value;
		
		// Convert to appropriate type for number inputs
		if (type === 'number' || type === 'range') {
			newValue = parseFloat(newValue);
			// Handle NaN case
			if (isNaN(newValue)) {
				newValue = 0;
			}
		}
		
		value = newValue;
		dispatch('change', { value: newValue, id });
	}
	
	$: hasError = error && error.length > 0;
	$: isValid = validationState === 'valid';
	$: isValidating = validationState === 'validating';
</script>

<div class="form-field" class:has-error={hasError} class:is-valid={isValid}>
	{#if label}
		<label for={id} class="field-label">
			{label}
			{#if required}
				<span class="required-indicator">*</span>
			{/if}
		</label>
	{/if}
	
	<div class="field-wrapper">
		{#if type === 'select'}
			<select
				{id}
				bind:value
				{disabled}
				{required}
				on:change={handleChange}
				class="field-input select-input"
				class:loading
			>
				{#if placeholder}
					<option value="" disabled>{placeholder}</option>
				{/if}
				{#each options as option}
					<option value={option.value}>{option.label}</option>
				{/each}
			</select>
		{:else if type === 'textarea'}
			<textarea
				{id}
				bind:value
				{placeholder}
				{disabled}
				{required}
				on:input={handleInput}
				on:change={handleChange}
				class="field-input textarea-input"
				class:loading
			></textarea>
		{:else if type === 'checkbox'}
			<label class="checkbox-wrapper">
				<input
					{id}
					type="checkbox"
					bind:checked={value}
					{disabled}
					{required}
					on:change={handleChange}
					class="checkbox-input"
				/>
				<span class="checkbox-label">{label}</span>
			</label>
		{:else}
			<input
				{id}
				{type}
				bind:value
				{placeholder}
				{disabled}
				{required}
				{min}
				{max}
				{step}
				on:input={handleInput}
				on:change={handleChange}
				class="field-input text-input"
				class:loading
			/>
		{/if}
		
		<!-- Validation indicator -->
		<div class="validation-indicator">
			{#if isValidating}
				<div class="spinner"></div>
			{:else if isValid}
				<svg class="check-icon" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
				</svg>
			{:else if hasError}
				<svg class="error-icon" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
			{/if}
		</div>
	</div>
	
	{#if hasError}
		<div class="error-message">
			{error}
		</div>
	{:else if helpText}
		<div class="help-text">
			{helpText}
		</div>
	{/if}
</div>

<style>
	.form-field {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.field-label {
		font-weight: 500;
		color: var(--color-text-primary, #374151);
		font-size: 0.875rem;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	
	.required-indicator {
		color: var(--color-error, #ef4444);
		font-weight: bold;
	}
	
	.field-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}
	
	.field-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--color-border, #d1d5db);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		transition: all 0.2s ease;
		background: var(--color-surface, #ffffff);
		color: var(--color-text-primary, #374151);
	}
	
	.field-input:focus {
		outline: none;
		border-color: var(--color-primary, #3b82f6);
		box-shadow: 0 0 0 3px var(--color-primary-alpha, rgba(59, 130, 246, 0.1));
	}
	
	.field-input:disabled {
		background: var(--color-surface-disabled, #f9fafb);
		color: var(--color-text-disabled, #9ca3af);
		cursor: not-allowed;
	}
	
	.field-input.loading {
		background-image: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
		background-size: 200% 100%;
		animation: loading-shimmer 1.5s infinite;
	}
	
	.has-error .field-input {
		border-color: var(--color-error, #ef4444);
		box-shadow: 0 0 0 3px var(--color-error-alpha, rgba(239, 68, 68, 0.1));
	}
	
	.is-valid .field-input {
		border-color: var(--color-success, #10b981);
		box-shadow: 0 0 0 3px var(--color-success-alpha, rgba(16, 185, 129, 0.1));
	}
	
	.textarea-input {
		min-height: 4rem;
		resize: vertical;
	}
	
	.select-input {
		cursor: pointer;
		background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
		background-position: right 0.5rem center;
		background-repeat: no-repeat;
		background-size: 1.5em 1.5em;
		padding-right: 2.5rem;
	}
	
	.checkbox-wrapper {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.checkbox-input {
		width: 1rem;
		height: 1rem;
		accent-color: var(--color-primary, #3b82f6);
	}
	
	.checkbox-label {
		font-size: 0.875rem;
		color: var(--color-text-primary, #374151);
	}
	
	.validation-indicator {
		position: absolute;
		right: 0.75rem;
		display: flex;
		align-items: center;
		pointer-events: none;
	}
	
	.spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid var(--color-border, #d1d5db);
		border-top: 2px solid var(--color-primary, #3b82f6);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	.check-icon {
		width: 1rem;
		height: 1rem;
		color: var(--color-success, #10b981);
	}
	
	.error-icon {
		width: 1rem;
		height: 1rem;
		color: var(--color-error, #ef4444);
	}
	
	.error-message {
		color: var(--color-error, #ef4444);
		font-size: 0.75rem;
		margin-top: 0.25rem;
	}
	
	.help-text {
		color: var(--color-text-secondary, #6b7280);
		font-size: 0.75rem;
		margin-top: 0.25rem;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	@keyframes loading-shimmer {
		0% { background-position: -200% 0; }
		100% { background-position: 200% 0; }
	}
</style>