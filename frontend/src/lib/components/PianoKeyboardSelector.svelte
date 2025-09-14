<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let selectedSize = '88-key';
	export let disabled = false;

	const pianoSizes = [
		{ value: '25-key', label: '25-Key Mini', keys: 25, octaves: 2, description: 'Compact MIDI controller' },
		{ value: '37-key', label: '37-Key Compact', keys: 37, octaves: 3, description: 'Small synthesizer' },
		{ value: '49-key', label: '49-Key Standard', keys: 49, octaves: 4, description: 'Home keyboard' },
		{ value: '61-key', label: '61-Key Full', keys: 61, octaves: 5, description: 'Standard keyboard' },
		{ value: '76-key', label: '76-Key Extended', keys: 76, octaves: 6.25, description: 'Stage piano' },
		{ value: '88-key', label: '88-Key Grand', keys: 88, octaves: 7.25, description: 'Full acoustic piano' },
		{ value: 'custom', label: 'Custom Size', keys: 0, octaves: 0, description: 'Define your own layout' }
	];

	function handleSizeChange(size) {
		selectedSize = size;
		dispatch('change', { size });
	}

	function renderKeyboard(size) {
		const sizeData = pianoSizes.find(p => p.value === size);
		if (!sizeData || sizeData.keys === 0) return [];

		const keys = [];
		const whiteKeyWidth = Math.max(8, 200 / Math.ceil(sizeData.keys * 0.7)); // Approximate white key count
		const blackKeyWidth = whiteKeyWidth * 0.6;

		// Generate a simplified keyboard layout
		for (let i = 0; i < sizeData.keys; i++) {
			const keyNumber = i % 12;
			const isBlackKey = [1, 3, 6, 8, 10].includes(keyNumber);
			
			keys.push({
				id: i,
				isBlack: isBlackKey,
				width: isBlackKey ? blackKeyWidth : whiteKeyWidth,
				left: i * (whiteKeyWidth * 0.85) // Slight overlap for realistic look
			});
		}

		return keys;
	}

	$: keyboardKeys = renderKeyboard(selectedSize);
	$: selectedSizeData = pianoSizes.find(p => p.value === selectedSize);
</script>

<div class="piano-selector">
	<div class="size-options">
		<h3>Piano Size Selection</h3>
		<div class="size-grid">
			{#each pianoSizes as size}
				<button
					class="size-option"
					class:selected={selectedSize === size.value}
					class:disabled
					on:click={() => handleSizeChange(size.value)}
					{disabled}
				>
					<div class="size-label">{size.label}</div>
					<div class="size-details">
						{#if size.keys > 0}
							<span class="key-count">{size.keys} keys</span>
							<span class="octave-count">{size.octaves} octaves</span>
						{:else}
							<span class="custom-label">Custom</span>
						{/if}
					</div>
					<div class="size-description">{size.description}</div>
				</button>
			{/each}
		</div>
	</div>

	{#if selectedSizeData && selectedSizeData.keys > 0}
		<div class="keyboard-preview">
			<h4>Keyboard Layout Preview</h4>
			<div class="keyboard-container">
				<div class="keyboard" style="width: {Math.min(400, selectedSizeData.keys * 4)}px;">
					{#each keyboardKeys as key}
						<div
							class="key"
							class:black={key.isBlack}
							class:white={!key.isBlack}
							style="width: {key.width}px; left: {key.left}px;"
						></div>
					{/each}
				</div>
				<div class="keyboard-info">
					<div class="info-item">
						<span class="info-label">Total Keys:</span>
						<span class="info-value">{selectedSizeData.keys}</span>
					</div>
					<div class="info-item">
						<span class="info-label">Octaves:</span>
						<span class="info-value">{selectedSizeData.octaves}</span>
					</div>
					<div class="info-item">
						<span class="info-label">Type:</span>
						<span class="info-value">{selectedSizeData.description}</span>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.piano-selector {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		padding: 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		background: #fafafa;
	}

	.size-options h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.2rem;
		font-weight: 600;
	}

	.size-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 0.75rem;
	}

	.size-option {
		display: flex;
		flex-direction: column;
		padding: 0.75rem;
		border: 2px solid #ddd;
		border-radius: 6px;
		background: white;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: left;
	}

	.size-option:hover:not(.disabled) {
		border-color: #007acc;
		box-shadow: 0 2px 4px rgba(0, 122, 204, 0.1);
	}

	.size-option.selected {
		border-color: #007acc;
		background: #f0f8ff;
		box-shadow: 0 2px 8px rgba(0, 122, 204, 0.2);
	}

	.size-option.disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.size-label {
		font-weight: 600;
		color: #333;
		margin-bottom: 0.25rem;
	}

	.size-details {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
		font-size: 0.85rem;
	}

	.key-count, .octave-count {
		padding: 0.1rem 0.4rem;
		background: #e8f4f8;
		border-radius: 3px;
		color: #0066cc;
		font-weight: 500;
	}

	.custom-label {
		padding: 0.1rem 0.4rem;
		background: #fff3cd;
		border-radius: 3px;
		color: #856404;
		font-weight: 500;
	}

	.size-description {
		font-size: 0.8rem;
		color: #666;
		font-style: italic;
	}

	.keyboard-preview {
		padding: 1rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}

	.keyboard-preview h4 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1rem;
		font-weight: 600;
	}

	.keyboard-container {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		align-items: center;
	}

	.keyboard {
		position: relative;
		height: 60px;
		border: 1px solid #ccc;
		border-radius: 4px;
		background: #f8f8f8;
		overflow: hidden;
	}

	.key {
		position: absolute;
		top: 0;
		border-right: 1px solid #ddd;
	}

	.key.white {
		height: 100%;
		background: white;
		z-index: 1;
	}

	.key.black {
		height: 60%;
		background: #333;
		z-index: 2;
		border-radius: 0 0 3px 3px;
	}

	.keyboard-info {
		display: flex;
		gap: 1.5rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.info-label {
		font-size: 0.8rem;
		color: #666;
		font-weight: 500;
	}

	.info-value {
		font-size: 0.9rem;
		color: #333;
		font-weight: 600;
	}

	@media (max-width: 768px) {
		.size-grid {
			grid-template-columns: 1fr;
		}
		
		.keyboard-info {
			flex-direction: column;
			gap: 0.75rem;
		}
	}
</style>