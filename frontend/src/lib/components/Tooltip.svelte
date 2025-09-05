<script>
	export let text = '';
	export let position = 'top'; // top, bottom, left, right
	export let delay = 500; // milliseconds
	export let maxWidth = '200px';
	export let theme = 'dark'; // dark, light
	export let arrow = true;
	export let disabled = false;
	export let trigger = 'hover'; // hover, click, focus

	let showTooltip = false;
	let tooltipElement;
	let triggerElement;
	let timeoutId;

	function handleMouseEnter() {
		if (disabled || trigger !== 'hover') return;
		clearTimeout(timeoutId);
		timeoutId = setTimeout(() => {
			showTooltip = true;
		}, delay);
	}

	function handleMouseLeave() {
		if (disabled || trigger !== 'hover') return;
		clearTimeout(timeoutId);
		showTooltip = false;
	}

	function handleClick() {
		if (disabled || trigger !== 'click') return;
		showTooltip = !showTooltip;
	}

	function handleFocus() {
		if (disabled || trigger !== 'focus') return;
		showTooltip = true;
	}

	function handleBlur() {
		if (disabled || trigger !== 'focus') return;
		showTooltip = false;
	}

	function handleKeydown(event) {
		if (event.key === 'Escape') {
			showTooltip = false;
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div 
	class="tooltip-container"
	bind:this={triggerElement}
	on:mouseenter={handleMouseEnter}
	on:mouseleave={handleMouseLeave}
	on:click={handleClick}
	on:focus={handleFocus}
	on:blur={handleBlur}
	role="button"
	tabindex="0"
	aria-describedby={showTooltip ? 'tooltip-content' : undefined}
>
	<slot />
	
	{#if showTooltip && text}
		<div 
			id="tooltip-content"
			class="tooltip tooltip-{position} tooltip-{theme} {arrow ? 'tooltip-arrow' : ''}"
			bind:this={tooltipElement}
			style="max-width: {maxWidth}"
			role="tooltip"
			aria-hidden="false"
		>
			{text}
		</div>
	{/if}
</div>

<style>
	.tooltip-container {
		position: relative;
		display: inline-block;
	}

	.tooltip {
		position: absolute;
		z-index: 1000;
		padding: 8px 12px;
		border-radius: 6px;
		font-size: 14px;
		line-height: 1.4;
		white-space: nowrap;
		pointer-events: none;
		animation: tooltipFadeIn 0.2s ease-out;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.tooltip-dark {
		background: rgba(0, 0, 0, 0.9);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.tooltip-light {
		background: white;
		color: var(--color-text);
		border: 1px solid var(--color-border);
	}

	/* Position variants */
	.tooltip-top {
		bottom: calc(100% + 8px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip-bottom {
		top: calc(100% + 8px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip-left {
		right: calc(100% + 8px);
		top: 50%;
		transform: translateY(-50%);
	}

	.tooltip-right {
		left: calc(100% + 8px);
		top: 50%;
		transform: translateY(-50%);
	}

	/* Arrow styles */
	.tooltip-arrow::before {
		content: '';
		position: absolute;
		width: 0;
		height: 0;
		border: 6px solid transparent;
	}

	.tooltip-top.tooltip-arrow::before {
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		border-top-color: rgba(0, 0, 0, 0.9);
	}

	.tooltip-bottom.tooltip-arrow::before {
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		border-bottom-color: rgba(0, 0, 0, 0.9);
	}

	.tooltip-left.tooltip-arrow::before {
		left: 100%;
		top: 50%;
		transform: translateY(-50%);
		border-left-color: rgba(0, 0, 0, 0.9);
	}

	.tooltip-right.tooltip-arrow::before {
		right: 100%;
		top: 50%;
		transform: translateY(-50%);
		border-right-color: rgba(0, 0, 0, 0.9);
	}

	/* Light theme arrow colors */
	.tooltip-light.tooltip-arrow::before {
		border-top-color: white;
		border-bottom-color: white;
		border-left-color: white;
		border-right-color: white;
	}

	.tooltip-light.tooltip-top.tooltip-arrow::before {
		border-top-color: white;
	}

	.tooltip-light.tooltip-bottom.tooltip-arrow::before {
		border-bottom-color: white;
	}

	.tooltip-light.tooltip-left.tooltip-arrow::before {
		border-left-color: white;
	}

	.tooltip-light.tooltip-right.tooltip-arrow::before {
		border-right-color: white;
	}

	@keyframes tooltipFadeIn {
		from {
			opacity: 0;
			transform: translateX(-50%) translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateX(-50%) translateY(0);
		}
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.tooltip {
			font-size: 12px;
			padding: 6px 10px;
			max-width: 150px !important;
			white-space: normal;
		}
	}
</style>