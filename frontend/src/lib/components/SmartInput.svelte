<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import ValidationMessage from './ValidationMessage.svelte';
	import type { ValidationResult } from '$lib/upload';
	import type { ValidationOptions } from '$lib/validation';
	import { ErrorPreventionManager, type PreventiveTip, type ErrorPreventionConfig } from '$lib/errorPrevention';

	const dispatch = createEventDispatcher();

	// Props
	export let label: string;
	export let type: 'text' | 'email' | 'password' | 'number' | 'file' | 'textarea' = 'text';
	export let value: string | number | File | null = '';
	export let placeholder = '';
	export let required = false;
	export let disabled = false;
	export let readonly = false;
	export let validationOptions: ValidationOptions | null = null;
	export let preventiveTips: PreventiveTip[] = [];
	export let errorPreventionConfig: Partial<ErrorPreventionConfig> = {};
	export let showSmartTips = true;
	export let validateOnInput = false;
	export let validateOnBlur = true;
	export let helpText = '';
	export let id = '';

	// File-specific props
	export let accept: string | undefined = undefined;
	export let multiple = false;

	// Textarea-specific props
	export let rows = 4;

	// State
	let inputElement: HTMLInputElement | HTMLTextAreaElement;
	let focused = false;
	let touched = false;
	let validationResult: ValidationResult | null = null;
	let activeTips: PreventiveTip[] = [];
	let showTips = false;
	let isValidating = false;

	// Error prevention manager
	let errorPrevention: ErrorPreventionManager;

	$: fieldId = id || `smart-input-${Math.random().toString(36).substr(2, 9)}`;
	$: hasError = validationResult && !validationResult.valid;
	$: showValidation = hasError && (touched || validateOnInput);

	onMount(() => {
		// Initialize error prevention
		errorPrevention = new ErrorPreventionManager({
			enabled: showSmartTips,
			...errorPreventionConfig
		});

		// Listen to error prevention events
		errorPrevention.on('tipsChanged', (tips: PreventiveTip[]) => {
			activeTips = tips;
			showTips = tips.length > 0;
		});

		errorPrevention.on('validationResult', (result: ValidationResult | null) => {
			validationResult = result;
			dispatch('validation', result);
		});

		errorPrevention.on('validationStateChanged', (state) => {
			isValidating = state.isValidating;
		});
	});

	onDestroy(() => {
		if (errorPrevention) {
			errorPrevention.clear();
		}
	});

	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement | HTMLTextAreaElement;
		
		if (type === 'file') {
			const fileInput = target as HTMLInputElement;
			value = fileInput.files?.[0] || null;
		} else if (type === 'number') {
			value = target.valueAsNumber || 0;
		} else {
			value = target.value;
		}

		// Trigger error prevention
		if (errorPrevention && validationOptions) {
			errorPrevention.onInput(value, validationOptions, preventiveTips);
		}

		dispatch('input', { value, event });
	}

	function handleFocus(event: FocusEvent) {
		focused = true;

		// Trigger error prevention
		if (errorPrevention) {
			errorPrevention.onFocus(type, value, preventiveTips);
		}

		dispatch('focus', { value, event });
	}

	function handleBlur(event: FocusEvent) {
		focused = false;
		touched = true;

		// Trigger error prevention
		if (errorPrevention && validationOptions) {
			errorPrevention.onBlur(value, validationOptions, preventiveTips);
		}

		dispatch('blur', { value, event });
	}

	function handleChange(event: Event) {
		dispatch('change', { value, event });
	}

	// Public methods
	export function focus() {
		inputElement?.focus();
	}

	export function blur() {
		inputElement?.blur();
	}

	export function select() {
		if (inputElement && 'select' in inputElement) {
			inputElement.select();
		}
	}

	export function clearValidation() {
		validationResult = null;
		touched = false;
		if (errorPrevention) {
			errorPrevention.clear();
		}
	}
</script>

<div class="smart-input" class:has-error={showValidation} class:focused class:disabled class:validating={isValidating}>
	<label for={fieldId} class="input-label">
		{label}
		{#if required}
			<span class="required-indicator" aria-label="required">*</span>
		{/if}
		{#if isValidating}
			<span class="validating-indicator" aria-label="validating">
				<svg class="spinner" viewBox="0 0 24 24">
					<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="31.416" stroke-dashoffset="31.416">
						<animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
						<animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
					</svg>
			</span>
		{/if}
	</label>

	{#if helpText}
		<div class="help-text" id="{fieldId}-help">
			{helpText}
		</div>
	{/if}

	<!-- Preventive Tips -->
	{#if showTips && activeTips.length > 0}
		<div class="preventive-tips" role="status" aria-live="polite">
			{#each activeTips as tip}
				<div class="tip {tip.type}" id="{fieldId}-tip-{tip.id}">
					<div class="tip-header">
						<svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
							{#if tip.type === 'info'}
								<circle cx="12" cy="12" r="10"/>
								<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
								<line x1="12" y1="17" x2="12.01" y2="17"/>
							{:else if tip.type === 'warning'}
								<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
								<line x1="12" y1="9" x2="12" y2="13"/>
								<line x1="12" y1="17" x2="12.01" y2="17"/>
							{:else}
								<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
								<polyline points="22,4 12,14.01 9,11.01"/>
							{/if}
						</svg>
						<span class="tip-title">{tip.title}</span>
					</div>
					<p class="tip-message">{tip.message}</p>
				</div>
			{/each}
		</div>
	{/if}

	<div class="input-wrapper">
		{#if type === 'textarea'}
			<textarea
				bind:this={inputElement}
				id={fieldId}
				bind:value
				{placeholder}
				{required}
				{disabled}
				{readonly}
				{rows}
				class="input-field"
				aria-describedby="{helpText ? `${fieldId}-help` : ''} {showValidation ? `${fieldId}-error` : ''} {showTips ? activeTips.map(tip => `${fieldId}-tip-${tip.id}`).join(' ') : ''}"
				aria-invalid={showValidation}
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				on:change={handleChange}
			></textarea>
		{:else}
			<input
				bind:this={inputElement}
				id={fieldId}
				{type}
				bind:value
				{placeholder}
				{required}
				{disabled}
				{readonly}
				{accept}
				{multiple}
				class="input-field"
				aria-describedby="{helpText ? `${fieldId}-help` : ''} {showValidation ? `${fieldId}-error` : ''} {showTips ? activeTips.map(tip => `${fieldId}-tip-${tip.id}`).join(' ') : ''}"
				aria-invalid={showValidation}
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				on:change={handleChange}
			/>
		{/if}

		{#if showValidation && hasError}
			<div class="validation-icon" aria-hidden="true">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<circle cx="12" cy="12" r="10"/>
					<line x1="15" y1="9" x2="9" y2="15"/>
					<line x1="9" y1="9" x2="15" y2="15"/>
				</svg>
			</div>
		{/if}
	</div>

	{#if showValidation}
		<div id="{fieldId}-error">
			<ValidationMessage 
				validation={validationResult} 
				variant="inline" 
				size="small"
				showDetails={true}
			/>
		</div>
	{/if}
</div>

<style>
	.smart-input {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
		position: relative;
	}

	.input-label {
		font-weight: 500;
		color: #374151;
		font-size: 0.875rem;
		line-height: 1.25rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.required-indicator {
		color: #dc2626;
		font-weight: 600;
	}

	.validating-indicator {
		display: flex;
		align-items: center;
		margin-left: auto;
	}

	.spinner {
		width: 1rem;
		height: 1rem;
		color: #3b82f6;
	}

	.help-text {
		font-size: 0.8125rem;
		color: #6b7280;
		line-height: 1.4;
		margin-top: -0.25rem;
	}

	.preventive-tips {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin: 0.25rem 0;
	}

	.tip {
		padding: 0.75rem;
		border-radius: 6px;
		border: 1px solid;
		animation: slideIn 0.2s ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-5px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.tip.info {
		background: #f0f9ff;
		border-color: #bae6fd;
		color: #0c4a6e;
	}

	.tip.warning {
		background: #fffbeb;
		border-color: #fde68a;
		color: #92400e;
	}

	.tip.success {
		background: #f0fdf4;
		border-color: #bbf7d0;
		color: #166534;
	}

	.tip-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.tip-icon {
		width: 1rem;
		height: 1rem;
		stroke-width: 2;
		flex-shrink: 0;
	}

	.tip-title {
		font-weight: 600;
		font-size: 0.875rem;
	}

	.tip-message {
		font-size: 0.8125rem;
		line-height: 1.4;
		margin: 0;
		opacity: 0.9;
	}

	.input-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}

	.input-field {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.9375rem;
		line-height: 1.5;
		color: #111827;
		background-color: white;
		transition: all 0.2s ease;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
	}

	.input-field:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.input-field:disabled {
		background-color: #f9fafb;
		color: #6b7280;
		cursor: not-allowed;
	}

	.input-field:readonly {
		background-color: #f9fafb;
		cursor: default;
	}

	.input-field::placeholder {
		color: #9ca3af;
	}

	.has-error .input-field {
		border-color: #dc2626;
		box-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
	}

	.has-error .input-field:focus {
		border-color: #dc2626;
		box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
	}

	.focused .input-label {
		color: #3b82f6;
	}

	.has-error .input-label {
		color: #dc2626;
	}

	.disabled {
		opacity: 0.6;
	}

	.validating .input-field {
		border-color: #3b82f6;
	}

	.validation-icon {
		position: absolute;
		right: 0.75rem;
		top: 50%;
		transform: translateY(-50%);
		width: 1.25rem;
		height: 1.25rem;
		color: #dc2626;
		pointer-events: none;
	}

	.validation-icon svg {
		width: 100%;
		height: 100%;
		stroke-width: 2;
	}

	textarea.input-field {
		resize: vertical;
		min-height: 2.5rem;
		line-height: 1.5;
	}

	input[type="file"].input-field {
		padding: 0.5rem;
		border: 2px dashed #d1d5db;
		background-color: #f9fafb;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	input[type="file"].input-field:hover {
		border-color: #9ca3af;
		background-color: #f3f4f6;
	}

	input[type="file"].input-field:focus {
		border-color: #3b82f6;
		background-color: white;
	}

	.has-error input[type="file"].input-field {
		border-color: #dc2626;
	}
</style>