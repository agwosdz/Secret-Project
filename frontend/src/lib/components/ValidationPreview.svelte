<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	export let files: File[] = [];
	export let maxFileSize: number = 10 * 1024 * 1024; // 10MB default
	export let allowedTypes: string[] = ['.mid', '.midi'];
	export let maxFiles: number = 10;
	export let showPreview: boolean = true;

	interface ValidationIssue {
		type: 'error' | 'warning' | 'info';
		message: string;
		file?: string;
		suggestion?: string;
		preventUpload?: boolean;
	}

	const dispatch = createEventDispatcher<{
		fix: { issue: ValidationIssue; files: File[] };
		proceed: { files: File[] };
		cancel: void;
	}>();

	let validationIssues: ValidationIssue[] = [];
	let hasBlockingIssues = false;

	$: if (files.length > 0) {
		validateFiles();
	}

	function validateFiles() {
		validationIssues = [];
		hasBlockingIssues = false;

		// Check file count
		if (files.length > maxFiles) {
			validationIssues.push({
				type: 'error',
				message: `Too many files selected (${files.length}/${maxFiles})`,
				suggestion: `Please select no more than ${maxFiles} files`,
				preventUpload: true
			});
			hasBlockingIssues = true;
		}

		// Check individual files
		files.forEach((file, index) => {
			// File size validation
			if (file.size > maxFileSize) {
				validationIssues.push({
					type: 'error',
					message: `File "${file.name}" is too large (${formatFileSize(file.size)})`,
					file: file.name,
					suggestion: `Maximum size allowed is ${formatFileSize(maxFileSize)}`,
					preventUpload: true
				});
				hasBlockingIssues = true;
			}

			// File type validation
			const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
			if (!allowedTypes.includes(fileExtension)) {
				validationIssues.push({
					type: 'error',
					message: `File "${file.name}" has unsupported format (${fileExtension})`,
					file: file.name,
					suggestion: `Supported formats: ${allowedTypes.join(', ')}`,
					preventUpload: true
				});
				hasBlockingIssues = true;
			}

			// File name validation
			if (file.name.length > 100) {
				validationIssues.push({
					type: 'warning',
					message: `File "${file.name}" has a very long name`,
					file: file.name,
					suggestion: 'Consider renaming to a shorter name for better compatibility'
				});
			}

			// Empty file check
			if (file.size === 0) {
				validationIssues.push({
					type: 'error',
					message: `File "${file.name}" is empty`,
					file: file.name,
					suggestion: 'Please select a valid MIDI file',
					preventUpload: true
				});
				hasBlockingIssues = true;
			}

			// Duplicate name check
			const duplicateIndex = files.findIndex((f, i) => i !== index && f.name === file.name);
			if (duplicateIndex !== -1) {
				validationIssues.push({
					type: 'warning',
					message: `Duplicate file name: "${file.name}"`,
					file: file.name,
					suggestion: 'Files with the same name may overwrite each other'
				});
			}
		});

		// Performance warnings
		if (files.length > 5) {
			validationIssues.push({
				type: 'info',
				message: `Uploading ${files.length} files simultaneously`,
				suggestion: 'Large batches may take longer to process'
			});
		}

		const totalSize = files.reduce((sum, file) => sum + file.size, 0);
		if (totalSize > 50 * 1024 * 1024) { // 50MB
			validationIssues.push({
				type: 'warning',
				message: `Large total upload size: ${formatFileSize(totalSize)}`,
				suggestion: 'Consider uploading in smaller batches for better performance'
			});
		}
	}

	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
	}

	function getIssueIcon(type: ValidationIssue['type']): string {
		switch (type) {
			case 'error': return '❌';
			case 'warning': return '⚠️';
			case 'info': return 'ℹ️';
			default: return '•';
		}
	}

	function getIssueClass(type: ValidationIssue['type']): string {
		switch (type) {
			case 'error': return 'issue-error';
			case 'warning': return 'issue-warning';
			case 'info': return 'issue-info';
			default: return '';
		}
	}

	function handleProceed() {
		dispatch('proceed', { files });
	}

	function handleCancel() {
		dispatch('cancel');
	}

	function handleFixIssue(issue: ValidationIssue) {
		dispatch('fix', { issue, files });
	}
</script>

{#if showPreview && files.length > 0}
	<div class="validation-preview" transition:slide={{ duration: 300, easing: quintOut }}>
		<div class="preview-header">
			<h3>Upload Preview</h3>
			<span class="file-count">{files.length} file{files.length !== 1 ? 's' : ''} selected</span>
		</div>

		<!-- File List -->
		<div class="file-list">
			{#each files as file, index}
				<div class="file-item">
					<div class="file-info">
						<span class="file-name">{file.name}</span>
						<span class="file-size">{formatFileSize(file.size)}</span>
					</div>
					<div class="file-status">
						{#if validationIssues.some(issue => issue.file === file.name && issue.type === 'error')}
							<span class="status-error">❌</span>
						{:else if validationIssues.some(issue => issue.file === file.name && issue.type === 'warning')}
							<span class="status-warning">⚠️</span>
						{:else}
							<span class="status-ok">✅</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		<!-- Validation Issues -->
		{#if validationIssues.length > 0}
			<div class="validation-issues">
				<h4>Validation Results</h4>
				{#each validationIssues as issue}
					<div class="validation-issue {getIssueClass(issue.type)}">
						<div class="issue-header">
							<span class="issue-icon">{getIssueIcon(issue.type)}</span>
							<span class="issue-message">{issue.message}</span>
						</div>
						{#if issue.suggestion}
							<div class="issue-suggestion">
								💡 {issue.suggestion}
							</div>
						{/if}
						{#if issue.preventUpload}
							<button 
								class="fix-button"
								on:click={() => handleFixIssue(issue)}
							>
								Fix Issue
							</button>
						{/if}
					</div>
				{/each}
			</div>
		{/if}

		<!-- Action Buttons -->
		<div class="preview-actions">
			<button class="cancel-button" on:click={handleCancel}>
				Cancel
			</button>
			<button 
				class="proceed-button" 
				class:disabled={hasBlockingIssues}
				disabled={hasBlockingIssues}
				on:click={handleProceed}
			>
				{hasBlockingIssues ? 'Fix Issues First' : 'Proceed with Upload'}
			</button>
		</div>
	</div>
{/if}

<style>
	.validation-preview {
		background: white;
		border: 1px solid #e1e5e9;
		border-radius: 12px;
		padding: 20px;
		margin: 16px 0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.preview-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
		padding-bottom: 12px;
		border-bottom: 1px solid #e1e5e9;
	}

	.preview-header h3 {
		margin: 0;
		color: #2c3e50;
		font-size: 18px;
		font-weight: 600;
	}

	.file-count {
		background: #f8f9fa;
		color: #6c757d;
		padding: 4px 12px;
		border-radius: 16px;
		font-size: 14px;
		font-weight: 500;
	}

	.file-list {
		margin-bottom: 16px;
	}

	.file-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: #f8f9fa;
		border-radius: 8px;
		margin-bottom: 8px;
	}

	.file-info {
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.file-name {
		font-weight: 500;
		color: #2c3e50;
		margin-bottom: 2px;
	}

	.file-size {
		font-size: 12px;
		color: #6c757d;
	}

	.file-status {
		margin-left: 12px;
	}

	.status-ok { color: #28a745; }
	.status-warning { color: #ffc107; }
	.status-error { color: #dc3545; }

	.validation-issues {
		margin-bottom: 20px;
	}

	.validation-issues h4 {
		margin: 0 0 12px 0;
		color: #2c3e50;
		font-size: 16px;
		font-weight: 600;
	}

	.validation-issue {
		padding: 12px;
		border-radius: 8px;
		margin-bottom: 8px;
		border-left: 4px solid;
	}

	.issue-error {
		background: rgba(220, 53, 69, 0.05);
		border-left-color: #dc3545;
	}

	.issue-warning {
		background: rgba(255, 193, 7, 0.05);
		border-left-color: #ffc107;
	}

	.issue-info {
		background: rgba(0, 123, 255, 0.05);
		border-left-color: #007bff;
	}

	.issue-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 4px;
	}

	.issue-icon {
		font-size: 14px;
	}

	.issue-message {
		font-weight: 500;
		color: #2c3e50;
	}

	.issue-suggestion {
		font-size: 14px;
		color: #6c757d;
		margin-left: 22px;
		margin-top: 4px;
	}

	.fix-button {
		background: #007bff;
		color: white;
		border: none;
		padding: 6px 12px;
		border-radius: 6px;
		font-size: 12px;
		cursor: pointer;
		margin-top: 8px;
		margin-left: 22px;
		transition: background-color 0.2s ease;
	}

	.fix-button:hover {
		background: #0056b3;
	}

	.preview-actions {
		display: flex;
		gap: 12px;
		justify-content: flex-end;
		padding-top: 16px;
		border-top: 1px solid #e1e5e9;
	}

	.cancel-button {
		background: #6c757d;
		color: white;
		border: none;
		padding: 10px 20px;
		border-radius: 8px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.cancel-button:hover {
		background: #545b62;
	}

	.proceed-button {
		background: #28a745;
		color: white;
		border: none;
		padding: 10px 20px;
		border-radius: 8px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.proceed-button:hover:not(.disabled) {
		background: #1e7e34;
	}

	.proceed-button.disabled {
		background: #6c757d;
		cursor: not-allowed;
		opacity: 0.6;
	}

	/* Responsive adjustments */
	@media (max-width: 480px) {
		.validation-preview {
			padding: 16px;
		}

		.preview-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
		}

		.file-item {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
		}

		.file-status {
			margin-left: 0;
		}

		.preview-actions {
			flex-direction: column;
		}

		.cancel-button,
		.proceed-button {
			width: 100%;
		}
	}
</style>