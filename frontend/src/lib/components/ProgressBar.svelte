<script lang="ts">
	export let progress: number = 0; // 0-100
	export let label: string = '';
	export let showPercentage: boolean = true;
	export let showTimeEstimate: boolean = false;
	export let estimatedTimeRemaining: number = 0; // in seconds
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
	export let animated: boolean = true;

	// Clamp progress between 0 and 100
	$: clampedProgress = Math.max(0, Math.min(100, progress));

	// Format time estimate
	$: formattedTime = formatTime(estimatedTimeRemaining);

	function formatTime(seconds: number): string {
		if (seconds < 60) {
			return `${Math.round(seconds)}s`;
		} else if (seconds < 3600) {
			const minutes = Math.floor(seconds / 60);
			const remainingSeconds = Math.round(seconds % 60);
			return `${minutes}m ${remainingSeconds}s`;
		} else {
			const hours = Math.floor(seconds / 3600);
			const minutes = Math.floor((seconds % 3600) / 60);
			return `${hours}h ${minutes}m`;
		}
	}

	const sizeClasses = {
		sm: 'h-2',
		md: 'h-3',
		lg: 'h-4'
	};

	const variantClasses = {
		default: 'bg-primary',
		success: 'bg-success',
		warning: 'bg-warning',
		error: 'bg-error'
	};
</script>

<div class="progress-container" role="progressbar" aria-valuenow={clampedProgress} aria-valuemin="0" aria-valuemax="100" aria-label={label || 'Progress'}>
	{#if label || showPercentage || showTimeEstimate}
		<div class="progress-header">
			{#if label}
				<span class="progress-label text-sm font-medium text-secondary">{label}</span>
			{/if}
			<div class="progress-info">
				{#if showPercentage}
					<span class="progress-percentage text-sm font-medium text-primary">{Math.round(clampedProgress)}%</span>
				{/if}
				{#if showTimeEstimate && estimatedTimeRemaining > 0}
					<span class="progress-time text-xs text-tertiary">~{formattedTime} remaining</span>
				{/if}
			</div>
		</div>
	{/if}
	
	<div class="progress-track {sizeClasses[size]}">
		<div 
			class="progress-fill {variantClasses[variant]} {sizeClasses[size]} {animated ? 'animated' : ''}" 
			style="width: {clampedProgress}%"
		></div>
	</div>
</div>

<style>
	.progress-container {
		width: 100%;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-2);
	}

	.progress-info {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.progress-track {
		width: 100%;
		background-color: var(--color-gray-200);
		border-radius: var(--radius-full);
		overflow: hidden;
		position: relative;
	}

	.progress-fill {
		height: 100%;
		border-radius: var(--radius-full);
		transition: width var(--duration-normal) var(--ease-material);
		position: relative;
		overflow: hidden;
	}

	.progress-fill.animated::after {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		bottom: 0;
		right: 0;
		background-image: linear-gradient(
			-45deg,
			transparent 33%,
			rgba(255, 255, 255, 0.1) 33%,
			rgba(255, 255, 255, 0.1) 66%,
			transparent 66%
		);
		background-size: 30px 30px;
		animation: progress-stripes 1s linear infinite;
	}

	@keyframes progress-stripes {
		0% {
			background-position: 0 0;
		}
		100% {
			background-position: 30px 0;
		}
	}

	/* Size Classes */
	.h-2 { height: 0.5rem; }
	.h-3 { height: 0.75rem; }
	.h-4 { height: 1rem; }

	/* Color Classes */
	.bg-primary { background-color: var(--color-primary); }
	.bg-success { background-color: var(--color-success); }
	.bg-warning { background-color: var(--color-warning); }
	.bg-error { background-color: var(--color-error); }

	/* Typography Classes */
	.text-sm { font-size: var(--text-sm); }
	.text-xs { font-size: var(--text-xs); }
	.font-medium { font-weight: var(--font-medium); }
	.text-secondary { color: var(--color-text-secondary); }
	.text-primary { color: var(--color-primary); }
	.text-tertiary { color: var(--color-text-tertiary); }

	@media (prefers-reduced-motion: reduce) {
		.progress-fill {
			transition: none;
		}
		
		.progress-fill.animated::after {
			animation: none;
		}
	}
</style>