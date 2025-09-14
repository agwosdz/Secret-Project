<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fly, fade, scale } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { statusManager, type StatusMessage, type ProgressStatus } from '$lib/statusCommunication';
	import InteractiveButton from './InteractiveButton.svelte';

	export let position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center' = 'top-right';
	export let maxWidth = '400px';
	export let showProgress = true;

	let messages: StatusMessage[] = [];
	let progressStatuses: ProgressStatus[] = [];
	let unsubscribeMessages: (() => void) | null = null;
	let unsubscribeProgress: (() => void) | null = null;

	onMount(() => {
		// Subscribe to status updates
		unsubscribeMessages = statusManager.onMessagesChange((newMessages) => {
			messages = newMessages;
		});

		unsubscribeProgress = statusManager.onProgressChange((newStatuses) => {
			progressStatuses = newStatuses;
		});

		// Get initial state
		messages = statusManager.getMessages();
		progressStatuses = statusManager.getProgressStatuses();
	});

	onDestroy(() => {
		if (unsubscribeMessages) unsubscribeMessages();
		if (unsubscribeProgress) unsubscribeProgress();
	});

	function dismissMessage(id: string) {
		statusManager.removeMessage(id);
	}

	function executeAction(action: any) {
		action.action();
	}

	function getTransitionParams(index: number) {
		const isTop = position.includes('top');
		const isLeft = position.includes('left');
		const isCenter = position.includes('center');

		let x = 0;
		let y = 0;

		if (isCenter) {
			y = isTop ? -100 : 100;
		} else {
			x = isLeft ? -100 : 100;
			y = isTop ? -50 : 50;
		}

		return {
			x,
			y,
			duration: 300,
			easing: quintOut,
			delay: index * 50
		};
	}

	function formatTime(ms: number): string {
		if (ms < 1000) return `${Math.round(ms)}ms`;
		if (ms < 60000) return `${Math.round(ms / 1000)}s`;
		return `${Math.round(ms / 60000)}m`;
	}

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
	}
</script>

<div class="status-display" class:position-{position} style="--max-width: {maxWidth}">
	<!-- Progress Indicators -->
	{#if showProgress && progressStatuses.length > 0}
		<div class="progress-container">
			{#each progressStatuses as progress, index (progress.id)}
				<div 
					class="progress-item"
					in:fly={getTransitionParams(index)}
					out:fly={{ ...getTransitionParams(index), duration: 200 }}
				>
					<div class="progress-header">
						<span class="progress-label">{progress.label}</span>
						<span class="progress-percentage">{Math.round(progress.progress)}%</span>
					</div>
					<div class="progress-bar">
						<div 
							class="progress-fill"
							style="width: {progress.progress}%"
						></div>
					</div>
					{#if progress.speed || progress.estimatedTime}
						<div class="progress-details">
							{#if progress.speed}
								<span class="progress-speed">{progress.speed}</span>
							{/if}
							{#if progress.estimatedTime}
								<span class="progress-eta">ETA: {formatTime(progress.estimatedTime)}</span>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	<!-- Status Messages -->
	{#if messages.length > 0}
		<div class="messages-container">
			{#each messages as message, index (message.id)}
				<div 
					class="status-message status-{message.type}"
					in:fly={getTransitionParams(index)}
					out:fly={{ ...getTransitionParams(index), duration: 200 }}
					role="alert"
					aria-live="polite"
				>
					<div class="message-header">
						<div class="message-icon-title">
							{#if message.icon}
								<span class="message-icon" class:spinning={message.type === 'loading'}>
									{message.icon}
								</span>
							{/if}
							<h3 class="message-title">{message.title}</h3>
						</div>
						{#if message.autoDismiss !== false}
							<InteractiveButton
								variant="ghost"
								size="small"
								class="dismiss-btn"
								on:click={() => dismissMessage(message.id)}
								aria-label="Dismiss message"
							>
								×
							</InteractiveButton>
						{/if}
					</div>
					<p class="message-content">{message.message}</p>
					
					{#if message.progress !== undefined}
						<div class="message-progress">
							<div class="progress-bar">
								<div 
									class="progress-fill"
									style="width: {message.progress}%"
								></div>
							</div>
							<span class="progress-text">{Math.round(message.progress)}%</span>
						</div>
					{/if}

					{#if message.actions && message.actions.length > 0}
						<div class="message-actions">
							{#each message.actions as action}
								<InteractiveButton
									variant={action.variant || 'secondary'}
									size="small"
									on:click={() => executeAction(action)}
								>
									{#if action.icon}
										<span class="action-icon">{action.icon}</span>
									{/if}
									{action.label}
								</InteractiveButton>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.status-display {
		position: fixed;
		z-index: 1000;
		pointer-events: none;
		max-width: var(--max-width);
		width: 100%;
		padding: 1rem;
		box-sizing: border-box;
	}

	/* Position variants */
	.position-top-right {
		top: 0;
		right: 0;
	}

	.position-top-left {
		top: 0;
		left: 0;
	}

	.position-bottom-right {
		bottom: 0;
		right: 0;
	}

	.position-bottom-left {
		bottom: 0;
		left: 0;
	}

	.position-top-center {
		top: 0;
		left: 50%;
		transform: translateX(-50%);
	}

	.position-bottom-center {
		bottom: 0;
		left: 50%;
		transform: translateX(-50%);
	}

	.progress-container,
	.messages-container {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.progress-item,
	.status-message {
		pointer-events: auto;
		background: white;
		border-radius: 12px;
		padding: 1rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1);
		border: 1px solid #e5e7eb;
		backdrop-filter: blur(8px);
		max-width: 100%;
		word-wrap: break-word;
	}

	/* Status message variants */
	.status-success {
		border-left: 4px solid #10b981;
		background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
	}

	.status-error {
		border-left: 4px solid #ef4444;
		background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
	}

	.status-warning {
		border-left: 4px solid #f59e0b;
		background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
	}

	.status-info {
		border-left: 4px solid #3b82f6;
		background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
	}

	.status-loading {
		border-left: 4px solid #6b7280;
		background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
	}

	.message-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.5rem;
	}

	.message-icon-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.message-icon {
		font-size: 1.25rem;
		line-height: 1;
		flex-shrink: 0;
	}

	.message-icon.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.message-title {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #111827;
		line-height: 1.25;
	}

	.message-content {
		margin: 0;
		font-size: 0.8125rem;
		color: #4b5563;
		line-height: 1.4;
	}

	.message-progress {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.75rem;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.progress-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #111827;
	}

	.progress-percentage {
		font-size: 0.75rem;
		font-weight: 600;
		color: #6b7280;
	}

	.progress-bar {
		flex: 1;
		height: 8px;
		background: #f3f4f6;
		border-radius: 4px;
		overflow: hidden;
		position: relative;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #1d4ed8);
		transition: width 0.3s ease;
		border-radius: 4px;
		position: relative;
		box-shadow: 0 1px 2px rgba(59, 130, 246, 0.3);
	}

	.progress-text {
		font-size: 0.75rem;
		font-weight: 600;
		color: #6b7280;
		flex-shrink: 0;
	}

	.progress-details {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 0.25rem;
		font-size: 0.6875rem;
		color: #6b7280;
	}

	.progress-speed,
	.progress-eta {
		font-weight: 500;
	}

	.message-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.75rem;
		flex-wrap: wrap;
	}

	.action-icon {
		margin-right: 0.25rem;
	}

	:global(.dismiss-btn) {
		padding: 0.25rem !important;
		min-width: auto !important;
		width: 1.5rem !important;
		height: 1.5rem !important;
		font-size: 1rem !important;
		line-height: 1 !important;
		color: #6b7280 !important;
		border-radius: 50% !important;
	}

	:global(.dismiss-btn:hover) {
		color: #374151 !important;
		background: #f3f4f6 !important;
	}

	/* Mobile responsive */
	@media (max-width: 768px) {
		.status-display {
			padding: 0.75rem;
			max-width: calc(100vw - 1.5rem);
		}

		.progress-item,
		.status-message {
			padding: 0.875rem;
			border-radius: 8px;
		}

		.message-title {
			font-size: 0.8125rem;
		}

		.message-content {
			font-size: 0.75rem;
		}

		.message-actions {
			flex-direction: column;
		}
	}

	/* Dark mode support - Use .dark class instead */
	:global(.dark) .progress-item,
	:global(.dark) .status-message {
		background: #1f2937;
		border-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .status-success {
		background: linear-gradient(135deg, #064e3b 0%, #1f2937 100%);
	}

	:global(.dark) .status-error {
		background: linear-gradient(135deg, #7f1d1d 0%, #1f2937 100%);
	}

	:global(.dark) .status-warning {
		background: linear-gradient(135deg, #78350f 0%, #1f2937 100%);
	}

	:global(.dark) .status-info {
		background: linear-gradient(135deg, #1e3a8a 0%, #1f2937 100%);
	}

	:global(.dark) .status-loading {
		background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
	}

	:global(.dark) .message-title {
		color: #f9fafb;
	}

	:global(.dark) .message-content {
		color: #d1d5db;
	}

	:global(.dark) .progress-bar {
		background: #374151;
	}

	:global(.dark) .progress-percentage,
	:global(.dark) .progress-text,
	:global(.dark) .progress-details {
		color: #9ca3af;
	}
</style>