<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import { writable } from 'svelte/store';

	const dispatch = createEventDispatcher();

	export let steps = [];
	export let isActive = false;
	export let showSkip = true;
	export let showProgress = true;
	export let theme = 'dark';

	let currentStep = 0;
	let highlightElement = null;
	let tourOverlay = null;
	let stepElement = null;

	// Default steps for upload page
	const defaultSteps = [
		{
			id: 'drop-zone',
			title: 'Upload Your MIDI File',
			content: 'Drag and drop a MIDI file here, or click to browse. We support .mid and .midi formats.',
			position: 'bottom'
		},
		{
			id: 'file-info-title',
			title: 'File Information',
			content: 'Once uploaded, you\'ll see detailed information about your MIDI file including tracks and duration.',
			position: 'right'
		},
		{
			id: 'upload-actions-title',
			title: 'Upload Actions',
			content: 'Use these buttons to upload your file or reset the form. You can also use Ctrl+Z to undo actions.',
			position: 'top'
		}
	];

	$: currentSteps = steps.length > 0 ? steps : defaultSteps;
	$: currentStepData = currentSteps[currentStep];

	function nextStep() {
		if (currentStep < currentSteps.length - 1) {
			currentStep++;
			updateHighlight();
		} else {
			finishTour();
		}
	}

	function prevStep() {
		if (currentStep > 0) {
			currentStep--;
			updateHighlight();
		}
	}

	function skipTour() {
		dispatch('skip');
		isActive = false;
		cleanupHighlight();
	}

	function finishTour() {
		dispatch('complete');
		isActive = false;
		cleanupHighlight();
	}

	function updateHighlight() {
		if (!currentStepData || !isActive) return;

		const element = document.getElementById(currentStepData.id);
		if (element) {
			highlightElement = element;
			
			// Add highlight class
			element.classList.add('tour-highlight');
			
			// Scroll element into view
			element.scrollIntoView({ 
				behavior: 'smooth', 
				block: 'center' 
			});
			
			// Position the step tooltip
			positionStepTooltip(element);
		}
	}

	function positionStepTooltip(element) {
		if (!stepElement) return;

		const rect = element.getBoundingClientRect();
		const position = currentStepData.position || 'bottom';
		const offset = 20;

		let top, left;

		switch (position) {
			case 'top':
				top = rect.top - stepElement.offsetHeight - offset;
				left = rect.left + (rect.width / 2) - (stepElement.offsetWidth / 2);
				break;
			case 'bottom':
				top = rect.bottom + offset;
				left = rect.left + (rect.width / 2) - (stepElement.offsetWidth / 2);
				break;
			case 'left':
				top = rect.top + (rect.height / 2) - (stepElement.offsetHeight / 2);
				left = rect.left - stepElement.offsetWidth - offset;
				break;
			case 'right':
				top = rect.top + (rect.height / 2) - (stepElement.offsetHeight / 2);
				left = rect.right + offset;
				break;
		}

		// Ensure tooltip stays within viewport
		top = Math.max(10, Math.min(top, window.innerHeight - stepElement.offsetHeight - 10));
		left = Math.max(10, Math.min(left, window.innerWidth - stepElement.offsetWidth - 10));

		stepElement.style.top = `${top}px`;
		stepElement.style.left = `${left}px`;
	}

	function cleanupHighlight() {
		if (highlightElement) {
			highlightElement.classList.remove('tour-highlight');
			highlightElement = null;
		}
	}

	function handleKeydown(event) {
		if (!isActive) return;

		switch (event.key) {
			case 'Escape':
				skipTour();
				break;
			case 'ArrowRight':
			case 'Enter':
				nextStep();
				break;
			case 'ArrowLeft':
				prevStep();
				break;
		}
	}

	onMount(() => {
		if (isActive) {
			updateHighlight();
		}

		return () => {
			cleanupHighlight();
		};
	});

	$: if (isActive && currentStepData) {
		updateHighlight();
	}

	$: if (!isActive) {
		cleanupHighlight();
	}
</script>

<svelte:window on:keydown={handleKeydown} on:resize={() => isActive && updateHighlight()} />

{#if isActive}
	<!-- Overlay -->
	<div class="tour-overlay" bind:this={tourOverlay} role="dialog" aria-modal="true" aria-labelledby="tour-title">
		<!-- Step tooltip -->
		{#if currentStepData}
			<div 
				class="tour-step tour-step-{theme}"
				bind:this={stepElement}
				role="tooltip"
				aria-live="polite"
			>
				<div class="tour-step-header">
					<h3 id="tour-title" class="tour-step-title">{currentStepData.title}</h3>
					{#if showProgress}
						<div class="tour-progress">
							<span class="tour-step-counter">{currentStep + 1} of {currentSteps.length}</span>
							<div class="tour-progress-bar">
								<div 
									class="tour-progress-fill" 
									style="width: {((currentStep + 1) / currentSteps.length) * 100}%"
								></div>
							</div>
						</div>
					{/if}
				</div>
				
				<div class="tour-step-content">
					<p>{currentStepData.content}</p>
				</div>
				
				<div class="tour-step-actions">
					{#if showSkip}
						<button 
							class="tour-btn tour-btn-ghost" 
							on:click={skipTour}
							aria-label="Skip tour"
						>
							Skip
						</button>
					{/if}
					
					<div class="tour-navigation">
						{#if currentStep > 0}
							<button 
								class="tour-btn tour-btn-secondary" 
								on:click={prevStep}
								aria-label="Previous step"
							>
								Back
							</button>
						{/if}
						
						<button 
							class="tour-btn tour-btn-primary" 
							on:click={nextStep}
							aria-label={currentStep < currentSteps.length - 1 ? 'Next step' : 'Finish tour'}
						>
							{currentStep < currentSteps.length - 1 ? 'Next' : 'Finish'}
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	:global(.tour-highlight) {
		position: relative;
		z-index: 1001;
		box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 8px rgba(59, 130, 246, 0.2);
		border-radius: 8px;
		animation: tourPulse 2s infinite;
	}

	@keyframes tourPulse {
		0%, 100% {
			box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 8px rgba(59, 130, 246, 0.2);
		}
		50% {
			box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.7), 0 0 0 12px rgba(59, 130, 246, 0.3);
		}
	}

	.tour-overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.5);
		z-index: 1000;
		pointer-events: none;
	}

	.tour-step {
		position: fixed;
		max-width: 320px;
		min-width: 280px;
		border-radius: 12px;
		padding: 20px;
		pointer-events: auto;
		animation: tourStepFadeIn 0.3s ease-out;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
		z-index: 1002;
	}

	.tour-step-dark {
		background: #1f2937;
		color: white;
		border: 1px solid #374151;
	}

	.tour-step-light {
		background: white;
		color: #1f2937;
		border: 1px solid #e5e7eb;
	}

	.tour-step-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 12px;
	}

	.tour-step-title {
		margin: 0;
		font-size: 18px;
		font-weight: 600;
		line-height: 1.3;
	}

	.tour-progress {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 4px;
	}

	.tour-step-counter {
		font-size: 12px;
		opacity: 0.7;
		font-weight: 500;
	}

	.tour-progress-bar {
		width: 60px;
		height: 4px;
		background: rgba(255, 255, 255, 0.2);
		border-radius: 2px;
		overflow: hidden;
	}

	.tour-step-dark .tour-progress-bar {
		background: rgba(255, 255, 255, 0.2);
	}

	.tour-step-light .tour-progress-bar {
		background: rgba(0, 0, 0, 0.1);
	}

	.tour-progress-fill {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s ease;
	}

	.tour-step-content {
		margin-bottom: 20px;
	}

	.tour-step-content p {
		margin: 0;
		line-height: 1.5;
		font-size: 14px;
		opacity: 0.9;
	}

	.tour-step-actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
	}

	.tour-navigation {
		display: flex;
		gap: 8px;
	}

	.tour-btn {
		padding: 8px 16px;
		border-radius: 6px;
		border: none;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.tour-btn-primary {
		background: #3b82f6;
		color: white;
	}

	.tour-btn-primary:hover {
		background: #2563eb;
		transform: translateY(-1px);
	}

	.tour-btn-secondary {
		background: rgba(255, 255, 255, 0.1);
		color: inherit;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.tour-step-light .tour-btn-secondary {
		background: rgba(0, 0, 0, 0.05);
		border: 1px solid rgba(0, 0, 0, 0.1);
	}

	.tour-btn-secondary:hover {
		background: rgba(255, 255, 255, 0.2);
		transform: translateY(-1px);
	}

	.tour-step-light .tour-btn-secondary:hover {
		background: rgba(0, 0, 0, 0.1);
	}

	.tour-btn-ghost {
		background: transparent;
		color: inherit;
		opacity: 0.7;
	}

	.tour-btn-ghost:hover {
		opacity: 1;
		transform: translateY(-1px);
	}

	@keyframes tourStepFadeIn {
		from {
			opacity: 0;
			transform: scale(0.95) translateY(-10px);
		}
		to {
			opacity: 1;
			transform: scale(1) translateY(0);
		}
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.tour-step {
			max-width: calc(100vw - 40px);
			min-width: auto;
			padding: 16px;
			left: 20px !important;
			right: 20px;
			width: auto;
		}

		.tour-step-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
		}

		.tour-progress {
			align-items: flex-start;
		}

		.tour-step-actions {
			flex-direction: column;
			align-items: stretch;
		}

		.tour-navigation {
			justify-content: space-between;
		}

		.tour-btn {
			flex: 1;
		}
	}
</style>