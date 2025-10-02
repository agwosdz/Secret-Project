<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Define proper types for settings
	interface PianoSettings {
		size?: string;
		keyMapping?: string;
	}

	interface LEDSettings {
		ledCount?: number;
		ledOrientation?: string;
	}

	interface Settings {
		piano?: PianoSettings;
		led?: LEDSettings;
	}

	export let settings: Settings = {};
	export let disabled: boolean = false;

	// Define types for piano size data
	interface PianoSize {
		value: string;
		label: string;
		keys: number;
		octaves: number;
		description: string;
		startNote: string;
		endNote: string;
	}

	interface KeyMappingOption {
		value: string;
		label: string;
		description: string;
	}

	// Extract current values from settings with proper type safety
	$: selectedSize = settings.piano?.size || '88-key';
	$: ledCount = settings.led?.ledCount || 246;
	$: ledOrientation = settings.led?.ledOrientation || 'normal';
	$: keyMapping = settings.piano?.keyMapping || 'chromatic';

	const pianoSizes: PianoSize[] = [
		{ value: '25-key', label: '25-Key Mini', keys: 25, octaves: 2, description: 'Compact MIDI controller', startNote: 'C3', endNote: 'C5' },
		{ value: '37-key', label: '37-Key Compact', keys: 37, octaves: 3, description: 'Small synthesizer', startNote: 'C2', endNote: 'C5' },
		{ value: '49-key', label: '49-Key Standard', keys: 49, octaves: 4, description: 'Home keyboard', startNote: 'C2', endNote: 'C6' },
		{ value: '61-key', label: '61-Key Full', keys: 61, octaves: 5, description: 'Standard keyboard', startNote: 'C1', endNote: 'C6' },
		{ value: '76-key', label: '76-Key Extended', keys: 76, octaves: 6.25, description: 'Stage piano', startNote: 'E0', endNote: 'G6' },
		{ value: '88-key', label: '88-Key Grand', keys: 88, octaves: 7.25, description: 'Full acoustic piano', startNote: 'A0', endNote: 'C8' },
		{ value: 'custom', label: 'Custom Size', keys: 0, octaves: 0, description: 'Define your own layout', startNote: '', endNote: '' }
	];

	const keyMappingOptions: KeyMappingOption[] = [
		{ value: 'chromatic', label: 'Chromatic (All Keys)', description: 'Map LEDs to all piano keys including black keys' },
		{ value: 'white-keys-only', label: 'White Keys Only', description: 'Map LEDs only to white keys (C, D, E, F, G, A, B)' },
		{ value: 'custom', label: 'Custom Mapping', description: 'Define custom key-to-LED mapping' }
	];

	function handleSizeChange(size: string) {
		const sizeData = pianoSizes.find(p => p.value === size);
		if (!sizeData) return;
		
		const updatedSettings = {
			...settings,
			piano: {
				...settings.piano,
				enabled: settings.piano?.enabled ?? true,
				octave: settings.piano?.octave ?? 4,
				size: size,
				keys: sizeData.keys,
				octaves: sizeData.octaves,
				startNote: sizeData.startNote,
				endNote: sizeData.endNote
			}
		};
		
		// Auto-adjust LED count based on piano size and mapping
		if (size !== 'custom') {
			const estimatedLEDs = calculateLEDCount(sizeData.keys, keyMapping);
			updatedSettings.led = {
				...settings.led,
				enabled: settings.led?.enabled ?? true,
				count: settings.led?.count ?? estimatedLEDs,
				brightness: settings.led?.brightness ?? 50,
				ledCount: estimatedLEDs
			};
		}
		
		dispatch('change', updatedSettings);
	}

	function handleKeyMappingChange(mapping: string) {
		const sizeData = pianoSizes.find(p => p.value === selectedSize);
		const estimatedLEDs = calculateLEDCount(sizeData?.keys || 88, mapping);
		
		const updatedSettings = {
			...settings,
			piano: {
				...settings.piano,
				enabled: settings.piano?.enabled ?? true,
				octave: settings.piano?.octave ?? 4,
				keyMapping: mapping
			},
			led: {
				...settings.led,
				enabled: settings.led?.enabled ?? true,
				count: settings.led?.count ?? estimatedLEDs,
				brightness: settings.led?.brightness ?? 50,
				ledCount: estimatedLEDs
			}
		};
		
		dispatch('change', updatedSettings);
	}

	function calculateLEDCount(keys: number, mapping: string): number {
		switch (mapping) {
			case 'white-keys-only':
				// Approximate 7 white keys per octave
				return Math.ceil(keys * 0.58); // ~58% of keys are white
			case 'chromatic':
			default:
				return keys; // 1:1 mapping
		}
	}

	function renderKeyboard(size: string) {
		const sizeData = pianoSizes.find(p => p.value === size);
		if (!sizeData || sizeData.keys === 0) return [];

		const keys = [];
		// Calculate container width dynamically to fill available space
		// Use the keyboard container's actual width or fallback to max-width
		let containerWidth = 1200; // Default fallback
		
		// Try to get actual container width if element exists
		if (typeof window !== 'undefined') {
			const keyboardElement = document.querySelector('.keyboard');
			if (keyboardElement) {
				containerWidth = keyboardElement.offsetWidth || 1200;
			}
		}
		
		const whiteKeyCount = Math.ceil(sizeData.keys * 0.58); // Approximate white key count
		const whiteKeyWidth = containerWidth / whiteKeyCount; // Fill entire width
		const blackKeyWidth = whiteKeyWidth * 0.65; // Slightly wider black keys
		const blackKeyHeight = 80; // Taller black keys
		const whiteKeyHeight = 120; // Taller white keys

		let whiteKeyIndex = 0;
		let ledIndex = 0;

		// Generate keyboard layout with proper key positioning
		for (let i = 0; i < sizeData.keys; i++) {
			const keyNumber = i % 12;
			const isBlackKey = [1, 3, 6, 8, 10].includes(keyNumber);
			
			let left, width, height, zIndex;
			let hasLED = false;
			let ledNumber = null;

			if (isBlackKey) {
				// Position black keys between white keys
				left = (whiteKeyIndex - 0.3) * whiteKeyWidth;
				width = blackKeyWidth;
				height = blackKeyHeight;
				zIndex = 2;
			} else {
				left = whiteKeyIndex * whiteKeyWidth;
				width = whiteKeyWidth;
				height = whiteKeyHeight;
				zIndex = 1;
				whiteKeyIndex++;
			}

			// Determine LED mapping
			if (keyMapping === 'white-keys-only' && !isBlackKey) {
				hasLED = true;
				ledNumber = ledOrientation === 'normal' ? ledIndex : (ledCount - 1 - ledIndex);
				ledIndex++;
			} else if (keyMapping === 'chromatic') {
				hasLED = true;
				ledNumber = ledOrientation === 'normal' ? ledIndex : (ledCount - 1 - ledIndex);
				ledIndex++;
			}
			
			keys.push({
				id: i,
				isBlack: isBlackKey,
				width,
				height,
				left: Math.max(0, left),
				zIndex,
				hasLED,
				ledNumber,
				note: getNoteForKey(i, sizeData.startNote)
			});
		}

		return keys;
	}

	function getNoteForKey(keyIndex, startNote) {
		const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
		const noteIndex = keyIndex % 12;
		const octave = Math.floor(keyIndex / 12) + (startNote ? parseInt(startNote.slice(-1)) : 4);
		return `${notes[noteIndex]}${octave}`;
	}

	$: keyboardKeys = renderKeyboard(selectedSize);
	$: selectedSizeData = pianoSizes.find(p => p.value === selectedSize);
	$: selectedMappingData = keyMappingOptions.find(m => m.value === keyMapping);
</script>

<div class="piano-selector">
	<div class="section">
		<h3 class="section-title">Piano Size Configuration</h3>
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
							<span class="note-range">{size.startNote} - {size.endNote}</span>
						{:else}
							<span class="custom-label">Custom</span>
						{/if}
					</div>
					<div class="size-description">{size.description}</div>
				</button>
			{/each}
		</div>
	</div>

	<div class="section">
		<h3 class="section-title">Key-to-LED Mapping</h3>
		<div class="mapping-options">
			{#each keyMappingOptions as mapping}
				<label class="mapping-option">
					<input
						type="radio"
						name="keyMapping"
						value={mapping.value}
						checked={keyMapping === mapping.value}
						on:change={() => handleKeyMappingChange(mapping.value)}
						{disabled}
					/>
					<div class="mapping-content">
						<div class="mapping-label">{mapping.label}</div>
						<div class="mapping-description">{mapping.description}</div>
					</div>
				</label>
			{/each}
		</div>
	</div>

	{#if selectedSizeData && selectedSizeData.keys > 0}
		<div class="section">
			<h3 class="section-title">Visual Key-to-LED Mapping Preview</h3>
			<div class="keyboard-container">
				<div class="keyboard-wrapper">
					<div class="keyboard" style="height: 140px; position: relative;">
						{#each keyboardKeys as key}
							<div
								class="key"
								class:black={key.isBlack}
								class:white={!key.isBlack}
								class:has-led={key.hasLED}
								style="width: {key.width}px; height: {key.height}px; left: {key.left}px; z-index: {key.zIndex}; position: absolute;"
								title="{key.note}{key.hasLED ? ` → LED ${key.ledNumber}` : ' (no LED)'}"
							>
								{#if key.hasLED}
									<div class="led-indicator">{key.ledNumber}</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
				
				<div class="mapping-info">
					<div class="info-grid">
						<div class="info-item">
							<span class="info-label">Piano Keys:</span>
							<span class="info-value">{selectedSizeData.keys}</span>
						</div>
						<div class="info-item">
							<span class="info-label">LED Count:</span>
							<span class="info-value">{ledCount}</span>
						</div>
						<div class="info-item">
							<span class="info-label">Mapping:</span>
							<span class="info-value">{selectedMappingData?.label}</span>
						</div>
						<div class="info-item">
							<span class="info-label">Orientation:</span>
							<span class="info-value">{ledOrientation === 'normal' ? 'Low to High' : 'High to Low'}</span>
						</div>
						<div class="info-item">
							<span class="info-label">Note Range:</span>
							<span class="info-value">{selectedSizeData.startNote} - {selectedSizeData.endNote}</span>
						</div>
						<div class="info-item">
							<span class="info-label">Efficiency:</span>
							<span class="info-value">{Math.round((ledCount / selectedSizeData.keys) * 100)}% LED usage</span>
						</div>
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

	.section {
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
		padding: 1rem;
	}

	.section-title {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.2rem;
		font-weight: 600;
	}

	.size-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
		flex-wrap: wrap;
	}

	.key-count, .octave-count, .note-range {
		padding: 0.1rem 0.4rem;
		background: #e8f4f8;
		border-radius: 3px;
		color: #0066cc;
		font-weight: 500;
		font-size: 0.75rem;
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

	.mapping-options {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.mapping-option {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		padding: 0.75rem;
		border: 1px solid #ddd;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.mapping-option:hover {
		border-color: #007acc;
		background: #f8fbff;
	}

	.mapping-option input[type="radio"] {
		margin-top: 0.25rem;
	}

	.mapping-content {
		flex: 1;
	}

	.mapping-label {
		font-weight: 600;
		color: #333;
		margin-bottom: 0.25rem;
	}

	.mapping-description {
		font-size: 0.85rem;
		color: #666;
	}

	.keyboard-container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		align-items: center;
	}

	.keyboard-wrapper {
		display: flex;
		justify-content: center;
		width: 100%;
	}

	.keyboard {
		border: 2px solid #ccc;
		border-radius: 8px;
		background: #f8f8f8;
		overflow: hidden; /* Changed from visible to hidden to contain keys */
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
		width: 100%;
		min-width: 800px; /* Increased minimum width */
		max-width: 1200px; /* Increased maximum width */
		height: 140px; /* Increased height to accommodate taller keys */
		position: relative; /* Ensure proper positioning context */
	}

	.key {
		border: 2px solid #ddd; /* Thicker border for better visibility */
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		padding-bottom: 6px; /* Increased padding */
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Added subtle shadow */
	}

	.key.white {
		background: white;
		border-radius: 0 0 4px 4px;
	}

	.key.white:hover {
		background: #f0f0f0;
	}

	.key.black {
		background: #333;
		border-radius: 0 0 4px 4px;
		border-color: #222;
	}

	.key.black:hover {
		background: #555;
	}

	.key.has-led {
		box-shadow: inset 0 0 0 2px #00ff00;
	}

	.key.has-led.white {
		background: #f0fff0;
	}

	.key.has-led.black {
		background: #2a4a2a;
	}

	.led-indicator {
		font-size: 0.8rem; /* Slightly larger font */
		font-weight: bold;
		color: #00aa00;
		background: rgba(255, 255, 255, 0.95); /* More opaque background */
		border-radius: 3px; /* Slightly larger border radius */
		padding: 2px 4px; /* Increased padding */
		min-width: 20px; /* Wider minimum width */
		text-align: center;
		border: 1px solid rgba(0, 170, 0, 0.3); /* Subtle border */
	}

	.key.black .led-indicator {
		color: #00ff00;
		background: rgba(0, 0, 0, 0.8);
	}

	.mapping-info {
		width: 100%;
		max-width: 500px;
	}

	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 1rem;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.5rem;
		background: #f8f9fa;
		border-radius: 4px;
		border: 1px solid #e9ecef;
	}

	.info-label {
		font-size: 0.8rem;
		color: #666;
		font-weight: 500;
		text-align: center;
	}

	.info-value {
		font-size: 0.9rem;
		color: #333;
		font-weight: 600;
		text-align: center;
	}

	@media (max-width: 768px) {
		.size-grid {
			grid-template-columns: 1fr;
		}
		
		.info-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.keyboard {
			min-width: 600px; /* Reduce minimum width for smaller screens */
			max-width: 100%; /* Allow full width on smaller screens */
		}
		
		.mapping-option {
			flex-direction: column;
			gap: 0.5rem;
		}
	}

	@media (max-width: 480px) {
		.info-grid {
			grid-template-columns: 1fr;
		}
		
		.keyboard {
			min-width: 400px; /* Further reduce for mobile */
			max-width: 100%;
		}
	}
</style>