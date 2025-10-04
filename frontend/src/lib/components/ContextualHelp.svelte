<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	export let context: 'file-upload' | 'validation' | 'network' | 'general' = 'general';
	export let errorType: string | null = null;
	export let compact: boolean = false;
	export let inline: boolean = false;

	const dispatch = createEventDispatcher();

	let isExpanded = false;
	let showAdvanced = false;

	// Context-specific help content
	const helpContent = {
		'file-upload': {
			title: 'File Upload Help',
			icon: '📁',
			quickTips: [
				'Supported formats: MIDI (.mid, .midi)',
				'Maximum file size: 10MB',
				'Ensure stable internet connection'
			],
			commonIssues: [
				{
					issue: 'File too large',
					solution: 'Compress your MIDI file or split it into smaller sections',
					prevention: 'Check file size before selecting (keep under 10MB)'
				},
				{
					issue: 'Unsupported format',
					solution: 'Convert your file to MIDI format (.mid or .midi)',
					prevention: 'Only select MIDI files from your music software'
				},
				{
					issue: 'Upload fails',
					solution: 'Check your internet connection and try again',
					prevention: 'Use a stable connection and avoid peak hours'
				}
			],
			resources: [
				{ label: 'MIDI Format Guide', url: '/help/midi-format' },
				{ label: 'File Size Optimization', url: '/help/file-optimization' },
				{ label: 'Troubleshooting Uploads', url: '/help/upload-troubleshooting' }
			]
		},
		'validation': {
			title: 'Input Validation Help',
			icon: '✅',
			quickTips: [
				'All required fields must be filled',
				'Check format requirements carefully',
				'Use the preview feature when available'
			],
			commonIssues: [
				{
					issue: 'Required field missing',
					solution: 'Fill in all fields marked with an asterisk (*)',
					prevention: 'Review the form before submitting'
				},
				{
					issue: 'Invalid format',
					solution: 'Check the expected format shown in field hints',
					prevention: 'Use the format examples provided'
				},
				{
					issue: 'Value out of range',
					solution: 'Ensure values are within the specified limits',
					prevention: 'Check minimum and maximum values before entering'
				}
			],
			resources: [
				{ label: 'Input Format Guide', url: '/help/input-formats' },
				{ label: 'Validation Rules', url: '/help/validation-rules' }
			]
		},
		'network': {
			title: 'Connection Help',
			icon: '🌐',
			quickTips: [
				'Check your internet connection',
				'Try refreshing the page',
				'Wait a moment if server is busy'
			],
			commonIssues: [
				{
					issue: 'Connection timeout',
					solution: 'Wait a moment and try again - server may be busy',
					prevention: 'Avoid peak usage hours when possible'
				},
				{
					issue: 'Network error',
					solution: 'Check your internet connection and firewall settings',
					prevention: 'Ensure stable internet before starting uploads'
				},
				{
					issue: 'Server unavailable',
					solution: 'Try again later - the server may be under maintenance',
					prevention: 'Check service status page for planned maintenance'
				}
			],
			resources: [
				{ label: 'Connection Troubleshooting', url: '/help/connection-issues' },
				{ label: 'Service Status', url: '/status' }
			]
		},
		'general': {
			title: 'General Help',
			icon: '❓',
			quickTips: [
				'Save your work frequently',
				'Keep your browser updated',
				'Clear cache if experiencing issues'
			],
			commonIssues: [
				{
					issue: 'Page not responding',
					solution: 'Refresh the page or restart your browser',
					prevention: 'Keep browser updated and close unused tabs'
				},
				{
					issue: 'Features not working',
					solution: 'Clear browser cache and cookies',
					prevention: 'Use supported browsers (Chrome, Firefox, Safari, Edge)'
				}
			],
			resources: [
				{ label: 'User Guide', url: '/help/user-guide' },
				{ label: 'FAQ', url: '/help/faq' },
				{ label: 'Contact Support', url: '/support' }
			]
		}
	};

	$: currentHelp = helpContent[context] || helpContent.general;
	$: relevantIssue = errorType ? currentHelp.commonIssues.find(issue => 
		issue.issue.toLowerCase().includes(errorType.toLowerCase()) ||
		errorType.toLowerCase().includes(issue.issue.toLowerCase())
	) : null;

	function toggleExpanded() {
		isExpanded = !isExpanded;
		dispatch('toggle', { expanded: isExpanded });
	}

	function toggleAdvanced() {
		showAdvanced = !showAdvanced;
	}

	function openResource(url: string) {
		window.open(url, '_blank', 'noopener,noreferrer');
		dispatch('resource-opened', { url });
	}
</script>

<div class="contextual-help" class:compact class:inline>
	{#if !inline}
		<div class="help-header">
			<div class="help-icon" aria-hidden="true">{currentHelp.icon}</div>
			<h4 class="help-title">{currentHelp.title}</h4>
			{#if !compact}
				<button 
					class="expand-toggle"
					on:click={toggleExpanded}
					aria-expanded={isExpanded}
					aria-controls="help-content"
					title={isExpanded ? 'Hide help' : 'Show help'}
				>
					<span class="toggle-icon" class:expanded={isExpanded}>▼</span>
				</button>
			{/if}
		</div>
	{/if}

	{#if inline || isExpanded || compact}
		<div 
			id="help-content" 
			class="help-content"
			transition:slide={{ duration: 300, easing: quintOut }}
		>
			<!-- Error-specific help (if applicable) -->
			{#if relevantIssue}
				<div class="relevant-issue">
					<h5>🎯 Specific to your issue:</h5>
					<div class="issue-card">
						<div class="issue-title">{relevantIssue.issue}</div>
						<div class="issue-solution">
							<strong>Solution:</strong> {relevantIssue.solution}
						</div>
						<div class="issue-prevention">
							<strong>Prevention:</strong> {relevantIssue.prevention}
						</div>
					</div>
				</div>
			{/if}

			<!-- Quick Tips -->
			<div class="quick-tips">
				<h5>💡 Quick Tips:</h5>
				<ul class="tips-list">
					{#each currentHelp.quickTips as tip}
						<li>{tip}</li>
					{/each}
				</ul>
			</div>

			<!-- Common Issues (expandable) -->
			{#if !compact && currentHelp.commonIssues.length > 0}
				<div class="common-issues">
					<button 
						class="section-toggle"
						on:click={toggleAdvanced}
						aria-expanded={showAdvanced}
						aria-controls="advanced-help"
					>
						<span class="toggle-icon" class:expanded={showAdvanced}>▶</span>
						Common Issues & Solutions
					</button>
					
					{#if showAdvanced}
						<div 
							id="advanced-help" 
							class="advanced-content"
							transition:slide={{ duration: 300, easing: quintOut }}
						>
							{#each currentHelp.commonIssues as issue}
								{#if !relevantIssue || issue !== relevantIssue}
									<div class="issue-item">
										<div class="issue-header">
											<span class="issue-icon">🔧</span>
											<span class="issue-name">{issue.issue}</span>
										</div>
										<div class="issue-details">
											<div class="solution">
												<strong>Solution:</strong> {issue.solution}
											</div>
											<div class="prevention">
												<strong>Prevention:</strong> {issue.prevention}
											</div>
										</div>
									</div>
								{/if}
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Help Resources -->
			{#if currentHelp.resources.length > 0}
				<div class="help-resources">
					<h5>📚 More Help:</h5>
					<div class="resource-links">
						{#each currentHelp.resources as resource}
							<button 
								class="resource-link"
								on:click={() => openResource(resource.url)}
								title="Open {resource.label} in new tab"
							>
								{resource.label}
								<span class="external-icon" aria-hidden="true">↗</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.contextual-help {
		background-color: rgba(59, 130, 246, 0.05);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 8px;
		padding: 16px;
		margin: 12px 0;
		font-size: 14px;
		line-height: 1.5;
	}

	.contextual-help.compact {
		padding: 12px;
		font-size: 13px;
	}

	.contextual-help.inline {
		background-color: rgba(59, 130, 246, 0.03);
		border: none;
		border-left: 3px solid rgba(59, 130, 246, 0.3);
		border-radius: 0 4px 4px 0;
		padding: 12px 16px;
		margin: 8px 0;
	}

	.help-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 12px;
	}

	.help-icon {
		font-size: 18px;
	}

	.help-title {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
		color: #1e40af;
		flex: 1;
	}

	.expand-toggle {
		background: none;
		border: none;
		cursor: pointer;
		padding: 4px;
		border-radius: 4px;
		transition: background-color 0.2s ease;
		color: #6b7280;
	}

	.expand-toggle:hover {
		background-color: rgba(59, 130, 246, 0.1);
	}

	.toggle-icon {
		display: inline-block;
		transition: transform 0.2s ease;
		font-size: 12px;
	}

	.toggle-icon.expanded {
		transform: rotate(180deg);
	}

	.help-content {
		display: grid;
		gap: 16px;
	}

	/* Relevant Issue Styling */
	.relevant-issue {
		background-color: rgba(16, 185, 129, 0.05);
		border: 1px solid rgba(16, 185, 129, 0.2);
		border-radius: 6px;
		padding: 12px;
	}

	.relevant-issue h5 {
		margin: 0 0 8px 0;
		font-size: 14px;
		font-weight: 600;
		color: #059669;
	}

	.issue-card {
		background-color: white;
		border-radius: 4px;
		padding: 12px;
		border-left: 3px solid #10b981;
	}

	.issue-title {
		font-weight: 600;
		color: #374151;
		margin-bottom: 8px;
	}

	.issue-solution,
	.issue-prevention {
		margin-bottom: 6px;
		font-size: 13px;
		line-height: 1.4;
	}

	.issue-solution strong,
	.issue-prevention strong {
		color: #059669;
	}

	/* Quick Tips */
	.quick-tips h5 {
		margin: 0 0 8px 0;
		font-size: 14px;
		font-weight: 600;
		color: #1e40af;
	}

	.tips-list {
		margin: 0;
		padding-left: 18px;
		list-style-type: none;
	}

	.tips-list li {
		position: relative;
		margin-bottom: 6px;
		padding-left: 8px;
		color: #374151;
	}

	.tips-list li::before {
		content: '•';
		color: #3b82f6;
		font-weight: bold;
		position: absolute;
		left: -8px;
	}

	/* Common Issues */
	.section-toggle {
		background: none;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 0;
		font-size: 14px;
		font-weight: 600;
		color: #374151;
		transition: color 0.2s ease;
	}

	.section-toggle:hover {
		color: #1e40af;
	}

	.section-toggle .toggle-icon {
		font-size: 10px;
		color: #6b7280;
	}

	.section-toggle .toggle-icon.expanded {
		transform: rotate(90deg);
	}

	.advanced-content {
		padding-left: 16px;
		margin-top: 8px;
	}

	.issue-item {
		margin-bottom: 16px;
		padding: 12px;
		background-color: rgba(0, 0, 0, 0.02);
		border-radius: 6px;
		border-left: 3px solid #e5e7eb;
	}

	.issue-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 8px;
	}

	.issue-icon {
		font-size: 14px;
	}

	.issue-name {
		font-weight: 600;
		color: #374151;
	}

	.issue-details {
		display: grid;
		gap: 6px;
		font-size: 13px;
		line-height: 1.4;
	}

	.solution strong,
	.prevention strong {
		color: #6b7280;
	}

	/* Help Resources */
	.help-resources h5 {
		margin: 0 0 8px 0;
		font-size: 14px;
		font-weight: 600;
		color: #1e40af;
	}

	.resource-links {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.resource-link {
		background: none;
		border: 1px solid #3b82f6;
		border-radius: 6px;
		padding: 6px 12px;
		font-size: 13px;
		color: #3b82f6;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 4px;
		text-decoration: none;
	}

	.resource-link:hover {
		background-color: #3b82f6;
		color: white;
		transform: translateY(-1px);
		box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
	}

	.external-icon {
		font-size: 10px;
		opacity: 0.7;
	}

	/* Responsive adjustments */
	@media (max-width: 480px) {
		.contextual-help {
			padding: 12px;
			font-size: 13px;
		}

		.help-title {
			font-size: 15px;
		}

		.resource-links {
			flex-direction: column;
		}

		.resource-link {
			justify-content: center;
		}
	}
</style>