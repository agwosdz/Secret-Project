<script lang="ts">
	import ValidationMessage from './ValidationMessage.svelte';
	import type { ValidationResult } from '$lib/upload';

	export let label: string;
	export let type: 'text' | 'email' | 'password' | 'number' | 'file' | 'textarea' = 'text';
	export let value: string | number = '';
	export let placeholder = '';
	export let required = false;
	export let disabled = false;
	export let readonly = false;
	export let maxlength: number | undefined = undefined;
	export let minlength: number | undefined = undefined;
	export let min: number | undefined = undefined;
	export let max: number | undefined = undefined;
	export let step: number | undefined = undefined;
	export let accept: string | undefined = undefined;
	export let multiple = false;
	export let rows = 4;
	export let validation: ValidationResult | null = null;
	export let validateOnBlur = true;
	export let validateOnInput = false;
	export let showValidationDetails = false;
	export let helpText = '';
	export let id = '';

	let inputElement: HTMLInputElement | HTMLTextAreaElement;
	let focused = false;
	let touched = false;

	$: hasError = validation && !validation.valid;
	$: showValidation = hasError && (touched || validateOnInput);
	$: fieldId = id || `field-${Math.random().toString(36).substr(2, 9)}`;

	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement | HTMLTextAreaElement;
		if (type === 'number') {
			value = target.valueAsNumber || 0;
		} else {
			value = target.value;
		}
		
		if (validateOnInput) {
			touched = true;
		}
	}

	function handleBlur() {
		focused = false;
		if (validateOnBlur) {
			touched = true;
		}
	}

	function handleFocus() {
		focused = true;
	}

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
</script>

<div class="form-field" class:has-error={showValidation} class:focused class:disabled>
	<label for={fieldId} class="field-label">
		{label}
		{#if required}
			<span class="required-indicator" aria-label="required">*</span>
		{/if}
	</label>

	{#if helpText}
		<div class="help-text" id="{fieldId}-help">
			{helpText}
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
				{maxlength}
				{minlength}
				{rows}
				class="field-input"
				aria-describedby="{helpText ? `${fieldId}-help` : ''} {showValidation ? `${fieldId}-error` : ''}"
				aria-invalid={showValidation}
				on:input={handleInput}
				on:blur={handleBlur}
				on:focus={handleFocus}
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
				{maxlength}
				{minlength}
				{min}
				{max}
				{step}
				{accept}
				{multiple}
				class="field-input"
				aria-describedby="{helpText ? `${fieldId}-help` : ''} {showValidation ? `${fieldId}-error` : ''}"
				aria-invalid={showValidation}
				on:input={handleInput}
				on:blur={handleBlur}
				on:focus={handleFocus}
				on:change
			/>
		{/if}

		{#if showValidation}
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
				{validation} 
				variant="inline" 
				size="small"
				showDetails={showValidationDetails}
			/>
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
		color: #374151;
		font-size: 0.875rem;
		line-height: 1.25rem;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.required-indicator {
		color: #dc2626;
		font-weight: 600;
	}

	.help-text {
		font-size: 0.8125rem;
		color: #6b7280;
		line-height: 1.4;
		margin-top: -0.25rem;
	}

	.input-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}

	.field-input {
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

	.field-input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.field-input:disabled {
		background-color: #f9fafb;
		color: #6b7280;
		cursor: not-allowed;
	}

	.field-input:readonly {
		background-color: #f9fafb;
		cursor: default;
	}

	.field-input::placeholder {
		color: #9ca3af;
	}

	.has-error .field-input {
		border-color: #dc2626;
		box-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
	}

	.has-error .field-input:focus {
		border-color: #dc2626;
		box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
	}

	.focused .field-label {
		color: #3b82f6;
	}

	.has-error .field-label {
		color: #dc2626;
	}

	.disabled {
		opacity: 0.6;
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

	textarea.field-input {
		resize: vertical;
		min-height: 2.5rem;
		line-height: 1.5;
	}

	input[type="file"].field-input {
		padding: 0.5rem;
		border: 2px dashed #d1d5db;
		background-color: #f9fafb;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	input[type="file"].field-input:hover {
		border-color: #9ca3af;
		background-color: #f3f4f6;
	}

	input[type="file"].field-input:focus {
		border-color: #3b82f6;
		background-color: white;
	}

	.has-error input[type="file"].field-input {
		border-color: #dc2626;
	}
</style>