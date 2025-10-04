<script lang="ts">
	import type { ErrorContext, RecoveryAction } from '$lib/errorRecovery';
	import InteractiveButton from './InteractiveButton.svelte';
	import LoadingSpinner from './LoadingSpinner.svelte';
	import ContextualHelp from './ContextualHelp.svelte';
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	export let errorContext: ErrorContext;
	export let showTechnicalDetails = false;
	export let showPreventionTips = true;
	export let compact = false;

	const dispatch = createEventDispatcher<{
		action: { actionId: string; action: RecoveryAction };
		dismiss: void;
		toggleDetails: { expanded: boolean };
	}>();

	let isExpanded = false;
	let isExecutingAction = false;
	let executingActionId: string | null = null;
	let showDetails = false;
	let showTechnicalInfo = false;
	let showPreventionTipsExpanded = false;
	let showContextInfo = false;
	let showContextualHelp = false;

	$: shouldShowInlineHelp = errorContext.showInlineHelp && errorContext.helpContext;

	// Get severity-based styling
	$: severityClass = getSeverityClass(errorContext.severity);
	$: iconForSeverity = getIconForSeverity(errorContext.severity);

	function getSeverityClass(severity: ErrorContext['severity']): string {
		const classes = {
			low: 'border-yellow-200 bg-yellow-50 text-yellow-800',
			medium: 'border-orange-200 bg-orange-50 text-orange-800',
			high: 'border-red-200 bg-red-50 text-red-800',
			critical: 'border-red-300 bg-red-100 text-red-900'
		};
		return classes[severity] || classes.medium;
	}

	function getIconForSeverity(severity: ErrorContext['severity']): string {
		const icons = {
			low: '⚠️',
			medium: '❗',
			high: '🚨',
			critical: '💥'
		};
		return icons[severity] || icons.medium;
	}

	async function executeAction(action: RecoveryAction) {
		if (action.disabled || isExecutingAction) return;

		isExecutingAction = true;
		executingActionId = action.id;

		try {
			await action.action();
			dispatch('action', { actionId: action.id, action });
		} catch (error) {
			console.error(`Failed to execute recovery action ${action.id}:`, error);
			// Could show a nested error here
		} finally {
			isExecutingAction = false;
			executingActionId = null;
		}
	}

	function toggleDetails() {
		isExpanded = !isExpanded;
		dispatch('toggleDetails', { expanded: isExpanded });
	}

	function handleDismiss() {
		dispatch('dismiss');
	}

	// Progressive disclosure helpers
	function toggleMainDetails() {
		showDetails = !showDetails;
	}

	function toggleTechnicalInfo() {
		showTechnicalInfo = !showTechnicalInfo;
	}

	function togglePreventionTipsExpanded() {
		showPreventionTipsExpanded = !showPreventionTipsExpanded;
	}

	function toggleContextInfo() {
		showContextInfo = !showContextInfo;
	}

	// Get primary and secondary actions
	$: primaryActions = errorContext.recoveryActions.filter(a => a.variant === 'primary');
	$: secondaryActions = errorContext.recoveryActions.filter(a => a.variant !== 'primary');
</script>

<div class="error-recovery-panel {severityClass} {compact ? 'compact' : ''}" role="alert">
	<!-- Header -->
	<div class="error-header">
		<div class="error-icon">
			{iconForSeverity}
		</div>
		<div class="error-content">
			<h3 class="error-title">
				{errorContext.type.charAt(0).toUpperCase() + errorContext.type.slice(1)} Error
			</h3>
			<p class="error-message">
				{errorContext.userMessage}
			</p>
			
			<!-- Primary suggestion -->
			{#if errorContext.suggestions && errorContext.suggestions.length > 0}
				<p class="error-suggestion">
					💡 {errorContext.suggestions[0]}
				</p>
			{/if}
		</div>
		
		<!-- Dismiss button -->
		{#if !compact}
			<button 
				class="dismiss-button"
				on:click={handleDismiss}
				aria-label="Dismiss error"
			>
				✕
			</button>
		{/if}
	</div>

	<!-- Primary Actions -->
	{#if primaryActions.length > 0}
		<div class="primary-actions">
			{#each primaryActions as action}
				<InteractiveButton
					variant={action.variant}
					disabled={action.disabled || isExecutingAction}
					loading={executingActionId === action.id}
					on:click={() => executeAction(action)}
					class="recovery-action primary"
				>
					{#if action.icon && executingActionId !== action.id}
						<span class="action-icon">{action.icon}</span>
					{/if}
					{action.label}
				</InteractiveButton>
			{/each}
		</div>
	{/if}

	<!-- Secondary Actions -->
	{#if secondaryActions.length > 0 && !compact}
		<div class="secondary-actions">
			{#each secondaryActions as action}
				<InteractiveButton
					variant="ghost"
					size="sm"
					disabled={action.disabled || isExecutingAction}
					loading={executingActionId === action.id}
					on:click={() => executeAction(action)}
					class="recovery-action secondary"
				>
					{#if action.icon && executingActionId !== action.id}
						<span class="action-icon">{action.icon}</span>
					{/if}
					{action.label}
				</InteractiveButton>
			{/each}
		</div>
	{/if}

	<!-- Progressive Disclosure Sections -->
	{#if !compact}
		<div class="disclosure-sections">
			<!-- Quick Suggestions (always visible if available) -->
			{#if errorContext.suggestions && errorContext.suggestions.length > 0}
				<div class="suggestions-section">
					<h4>Quick Solutions:</h4>
					<ul class="suggestions-list">
						{#each errorContext.suggestions.slice(0, 2) as suggestion}
							<li>{suggestion}</li>
						{/each}
					</ul>
					
					{#if errorContext.suggestions.length > 2}
						<button 
							class="expand-toggle"
							on:click={toggleMainDetails}
							aria-expanded={showDetails}
							aria-controls="additional-suggestions"
						>
							<span class="toggle-icon" class:expanded={showDetails}>▶</span>
							Show {errorContext.suggestions.length - 2} More Solutions
						</button>
						
						{#if showDetails}
							<div 
								id="additional-suggestions" 
								class="expanded-content"
								transition:slide={{ duration: 300, easing: quintOut }}
							>
								<ul class="suggestions-list">
									{#each errorContext.suggestions.slice(2) as suggestion}
										<li>{suggestion}</li>
									{/each}
								</ul>
							</div>
						{/if}
					{/if}
				</div>
			{/if}

			<!-- Context Information -->
			{#if errorContext.context}
				<div class="expandable-section">
					<button 
						class="expand-toggle"
						on:click={toggleContextInfo}
						aria-expanded={showContextInfo}
						aria-controls="context-info"
					>
						<span class="toggle-icon" class:expanded={showContextInfo}>▶</span>
						Context Information
					</button>
					
					{#if showContextInfo}
						<div 
							id="context-info" 
							class="expanded-content"
							transition:slide={{ duration: 300, easing: quintOut }}
						>
							<div class="context-details">
								{#if errorContext.context.fileName}
									<div class="context-item">
										<span class="context-label">File:</span>
										<span class="context-value">{errorContext.context.fileName}</span>
									</div>
								{/if}
								{#if errorContext.context.fileSize}
									<div class="context-item">
										<span class="context-label">Size:</span>
										<span class="context-value">{(errorContext.context.fileSize / 1024).toFixed(1)} KB</span>
									</div>
								{/if}
								{#if errorContext.context.fileType}
									<div class="context-item">
										<span class="context-label">Type:</span>
										<span class="context-value">{errorContext.context.fileType}</span>
									</div>
								{/if}
								{#if errorContext.context.uploadProgress !== undefined}
									<div class="context-item">
										<span class="context-label">Progress:</span>
										<span class="context-value">{errorContext.context.uploadProgress}%</span>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Prevention Tips -->
			{#if showPreventionTips && errorContext.preventionTips?.length > 0}
				<div class="expandable-section">
					<button 
						class="expand-toggle"
						on:click={togglePreventionTipsExpanded}
						aria-expanded={showPreventionTipsExpanded}
						aria-controls="prevention-tips"
					>
						<span class="toggle-icon" class:expanded={showPreventionTipsExpanded}>▶</span>
						Prevention Tips
					</button>
					
					{#if showPreventionTipsExpanded}
						<div 
							id="prevention-tips" 
							class="expanded-content"
							transition:slide={{ duration: 300, easing: quintOut }}
						>
							<ul class="prevention-list">
								{#each errorContext.preventionTips as tip}
									<li>{tip}</li>
								{/each}
							</ul>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Technical Information (for developers/advanced users) -->
			{#if showTechnicalDetails && errorContext.technicalMessage}
				<div class="expandable-section technical">
					<button 
						class="expand-toggle technical"
						on:click={toggleTechnicalInfo}
						aria-expanded={showTechnicalInfo}
						aria-controls="technical-info"
					>
						<span class="toggle-icon" class:expanded={showTechnicalInfo}>▶</span>
						Technical Details
					</button>
					
					{#if showTechnicalInfo}
						<div 
							id="technical-info" 
							class="expanded-content technical"
							transition:slide={{ duration: 300, easing: quintOut }}
						>
							<div class="technical-details-enhanced">
								{#if errorContext.errorCode}
									<div class="tech-item">
										<span class="tech-label">Error Code:</span>
										<code class="tech-value">{errorContext.errorCode}</code>
									</div>
								{/if}
								{#if errorContext.timestamp}
									<div class="tech-item">
										<span class="tech-label">Timestamp:</span>
										<code class="tech-value">{new Date(errorContext.timestamp).toLocaleString()}</code>
									</div>
								{/if}
								<div class="tech-item">
									<span class="tech-label">Technical Message:</span>
									<pre class="tech-value stack-trace">{errorContext.technicalMessage}</pre>
								</div>
								{#if errorContext.requestId}
									<div class="tech-item">
										<span class="tech-label">Request ID:</span>
										<code class="tech-value">{errorContext.requestId}</code>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Contextual Help Integration -->
			{#if shouldShowInlineHelp}
				<div class="contextual-help-section">
					<ContextualHelp 
						context={errorContext.helpContext}
						errorType={errorContext.type}
						inline={true}
						on:toggle={(e) => console.log('Help toggled:', e.detail)}
						on:resource-opened={(e) => console.log('Resource opened:', e.detail)}
					/>
				</div>
			{/if}

			<!-- Additional Help Toggle -->
			{#if errorContext.helpContext && !shouldShowInlineHelp}
				<div class="expandable-section">
					<button 
						class="expand-toggle help"
						on:click={() => toggleSection('help')}
						aria-expanded={showContextualHelp}
						aria-controls="contextual-help"
					>
						<span class="toggle-icon" class:expanded={showContextualHelp}>▶</span>
						Get Help with {errorContext.userFriendlyType}
					</button>
					
					{#if showContextualHelp}
						<div 
							id="contextual-help" 
							class="expanded-content help"
							transition:slide={{ duration: 300, easing: quintOut }}
						>
							<ContextualHelp 
								context={errorContext.helpContext}
								errorType={errorContext.type}
								compact={true}
								on:toggle={(e) => console.log('Help toggled:', e.detail)}
								on:resource-opened={(e) => console.log('Resource opened:', e.detail)}
							/>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Help Links -->
			{#if errorContext.helpUrl}
				<div class="help-section">
					<h5>Need More Help?</h5>
					<div class="help-links">
						<a 
							href={errorContext.helpUrl} 
							class="help-link"
							target="_blank"
							rel="noopener noreferrer"
							aria-label="Open troubleshooting guide in new tab"
						>
							📚 View Troubleshooting Guide
							<span class="external-icon" aria-hidden="true">↗</span>
						</a>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.error-recovery-panel {
		border: 1px solid;
		border-radius: 8px;
		padding: 16px;
		margin: 8px 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.error-recovery-panel.compact {
		padding: 12px;
		margin: 4px 0;
	}

	.error-header {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		margin-bottom: 12px;
	}

	.error-icon {
		font-size: 20px;
		flex-shrink: 0;
		margin-top: 2px;
	}

	.error-content {
		flex: 1;
		min-width: 0;
	}

	.error-title {
		margin: 0 0 4px 0;
		font-size: 16px;
		font-weight: 600;
		line-height: 1.2;
	}

	.error-message {
		margin: 0 0 8px 0;
		font-size: 14px;
		line-height: 1.4;
	}

	.error-suggestion {
		margin: 0;
		font-size: 13px;
		font-style: italic;
		opacity: 0.9;
		line-height: 1.3;
	}

	.dismiss-button {
		background: none;
		border: none;
		font-size: 18px;
		cursor: pointer;
		padding: 4px;
		border-radius: 4px;
		opacity: 0.6;
		transition: opacity 0.2s ease;
		flex-shrink: 0;
	}

	.dismiss-button:hover {
		opacity: 1;
		background-color: rgba(0, 0, 0, 0.1);
	}

	.primary-actions {
		display: flex;
		gap: 8px;
		margin-bottom: 8px;
		flex-wrap: wrap;
	}

	.secondary-actions {
		display: flex;
		gap: 6px;
		margin-bottom: 8px;
		flex-wrap: wrap;
	}

	:global(.recovery-action) {
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	:global(.recovery-action .action-icon) {
		font-size: 14px;
	}

	/* Progressive Disclosure Sections */
	.disclosure-sections {
		margin-top: 12px;
	}

	.expandable-section {
		border-top: 1px solid rgba(0, 0, 0, 0.1);
		padding-top: 12px;
		margin-top: 8px;
	}

	.expandable-section.technical {
		border-top: 1px solid rgba(0, 0, 0, 0.15);
		background-color: rgba(0, 0, 0, 0.02);
		border-radius: 4px;
		padding: 12px;
		margin-top: 12px;
	}

	.expand-toggle {
		background: none;
		border: none;
		font-size: 13px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 0;
		color: inherit;
		opacity: 0.8;
		transition: opacity 0.2s ease;
		font-weight: 500;
	}

	.expand-toggle:hover {
		opacity: 1;
	}

	.expand-toggle.technical {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 12px;
		color: #666;
	}

	.toggle-icon {
		transition: transform 0.2s ease;
		font-size: 10px;
		color: #666;
	}

	.toggle-icon.expanded {
		transform: rotate(90deg);
	}

	.expanded-content {
		margin-top: 12px;
		padding-left: 20px;
	}

	.expanded-content.technical {
		background-color: rgba(0, 0, 0, 0.03);
		border-radius: 4px;
		padding: 12px;
		margin-left: 0;
	}

	.suggestions-section {
		margin-bottom: 12px;
	}

	.suggestions-section h4 {
		margin: 0 0 8px 0;
		font-size: 14px;
		font-weight: 600;
		color: #2d5a27;
	}

	.suggestions-list {
		margin: 0;
		padding-left: 18px;
		font-size: 13px;
		line-height: 1.5;
	}

	.suggestions-list li {
		margin-bottom: 6px;
		color: #444;
	}

	.prevention-list {
		margin: 0;
		padding-left: 18px;
		font-size: 12px;
		line-height: 1.4;
	}

	.prevention-list li {
		margin-bottom: 4px;
		color: #555;
	}

	/* Context Information */
	.context-details {
		display: grid;
		gap: 8px;
		font-size: 12px;
	}

	.context-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 6px 12px;
		background-color: rgba(0, 0, 0, 0.03);
		border-radius: 4px;
	}

	.context-label {
		font-weight: 600;
		color: #666;
	}

	.context-value {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		color: #333;
		background-color: rgba(0, 0, 0, 0.05);
		padding: 2px 6px;
		border-radius: 3px;
	}

	/* Technical Details */
	.technical-details-enhanced {
		display: grid;
		gap: 12px;
	}

	.tech-item {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.tech-label {
		font-size: 11px;
		font-weight: 600;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.tech-value {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 11px;
		background-color: rgba(0, 0, 0, 0.05);
		border: 1px solid rgba(0, 0, 0, 0.1);
		border-radius: 3px;
		padding: 6px 8px;
		color: #333;
	}

	.stack-trace {
		white-space: pre-wrap;
		word-break: break-word;
		max-height: 150px;
		overflow-y: auto;
		line-height: 1.3;
	}

	/* Help Section */
	.help-section {
		margin-top: 16px;
		padding: 12px;
		background-color: rgba(0, 102, 204, 0.05);
		border: 1px solid rgba(0, 102, 204, 0.2);
		border-radius: 6px;
	}

	.help-section h5 {
		margin: 0 0 8px 0;
		font-size: 13px;
		font-weight: 600;
		color: #666;
	}

	.help-links {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
	}

	.help-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		color: #0066cc;
		text-decoration: none;
		padding: 6px 12px;
		border: 1px solid #0066cc;
		border-radius: 6px;
		transition: all 0.2s ease;
		background-color: rgba(0, 102, 204, 0.05);
	}

	.help-link:hover {
		background-color: rgba(0, 102, 204, 0.1);
		transform: translateY(-1px);
		box-shadow: 0 2px 4px rgba(0, 102, 204, 0.2);
	}

	.external-icon {
		font-size: 10px;
		opacity: 0.7;
	}

	/* Severity-based styling */
	.severity-low {
		border-left: 4px solid #28a745;
		background-color: rgba(40, 167, 69, 0.05);
	}

	.severity-low .error-title {
		color: #1e7e34;
	}

	.severity-medium {
		border-left: 4px solid #ffc107;
		background-color: rgba(255, 193, 7, 0.05);
	}

	.severity-medium .error-title {
		color: #856404;
	}

	.severity-high {
		border-left: 4px solid #dc3545;
		background-color: rgba(220, 53, 69, 0.05);
	}

	.severity-high .error-title {
		color: #721c24;
	}

	/* Contextual help styles */
	.inline-help {
		margin: 12px 0;
		padding: 12px;
		background-color: rgba(0, 102, 204, 0.05);
		border: 1px solid rgba(0, 102, 204, 0.2);
		border-radius: 8px;
		font-size: 14px;
		line-height: 1.4;
	}

	.help-links {
		margin-top: 12px;
	}

	.help-links-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 8px;
		margin-top: 8px;
	}

	/* Responsive adjustments */
	@media (max-width: 480px) {
		.error-recovery-panel {
			padding: 12px;
		}

		.error-header {
			gap: 8px;
		}

		.primary-actions,
		.secondary-actions {
			flex-direction: column;
		}

		:global(.recovery-action) {
			width: 100%;
			justify-content: center;
		}

		.help-links-grid {
			grid-template-columns: 1fr;
		}

		.inline-help {
			padding: 8px;
			font-size: 13px;
		}
	}
</style>