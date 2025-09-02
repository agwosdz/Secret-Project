<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Props
	export let connectionStatus = 'disconnected';

	// Control state
	let selectedLEDIndex = 0;
	let selectedColor = { r: 255, g: 0, b: 0 };
	let selectedBrightness = 0.8;
	let testPattern = 'rainbow';
	let patternDuration = 5000;

	// Available test patterns
	const patterns = [
		{ value: 'rainbow', label: 'Rainbow Cycle' },
		{ value: 'chase', label: 'Color Chase' },
		{ value: 'pulse', label: 'Pulse Effect' },
		{ value: 'strobe', label: 'Strobe Light' },
		{ value: 'fade', label: 'Fade In/Out' },
		{ value: 'solid', label: 'Solid Color' }
	];

	// Predefined colors for quick selection
	const presetColors = [
		{ name: 'Red', r: 255, g: 0, b: 0 },
		{ name: 'Green', r: 0, g: 255, b: 0 },
		{ name: 'Blue', r: 0, g: 0, b: 255 },
		{ name: 'Yellow', r: 255, g: 255, b: 0 },
		{ name: 'Cyan', r: 0, g: 255, b: 255 },
		{ name: 'Magenta', r: 255, g: 0, b: 255 },
		{ name: 'White', r: 255, g: 255, b: 255 },
		{ name: 'Orange', r: 255, g: 165, b: 0 }
	];

	// Convert RGB to hex for color input
	$: hexColor = `#${selectedColor.r.toString(16).padStart(2, '0')}${selectedColor.g.toString(16).padStart(2, '0')}${selectedColor.b.toString(16).padStart(2, '0')}`;

	// Handle hex color input change
	function handleHexColorChange(event) {
		const hex = event.target.value;
		const r = parseInt(hex.slice(1, 3), 16);
		const g = parseInt(hex.slice(3, 5), 16);
		const b = parseInt(hex.slice(5, 7), 16);
		
		if (!isNaN(r) && !isNaN(g) && !isNaN(b)) {
			selectedColor = { r, g, b };
		}
	}

	// Handle preset color selection
	function selectPresetColor(color) {
		selectedColor = { ...color };
	}

	// Test individual LED
	function testLED() {
		if (connectionStatus !== 'connected') return;
		
		dispatch('ledTest', {
			ledIndex: selectedLEDIndex,
			color: selectedColor,
			brightness: selectedBrightness
		});
	}

	// Test pattern
	function runTestPattern() {
		if (connectionStatus !== 'connected') return;
		
		dispatch('patternTest', {
			pattern: testPattern,
			duration: patternDuration
		});
	}

	// Clear all LEDs
	function clearAllLEDs() {
		if (connectionStatus !== 'connected') return;
		
		dispatch('ledTest', {
			ledIndex: -1, // -1 indicates all LEDs
			color: { r: 0, g: 0, b: 0 },
			brightness: 0
		});
	}

	// Fill all LEDs with current color
	function fillAllLEDs() {
		if (connectionStatus !== 'connected') return;
		
		dispatch('ledTest', {
			ledIndex: -1, // -1 indicates all LEDs
			color: selectedColor,
			brightness: selectedBrightness
		});
	}

	// Test all LEDs sequentially
	function testAllLEDs() {
		if (connectionStatus !== 'connected') return;
		
		dispatch('testAll', {
			color: selectedColor,
			brightness: selectedBrightness,
			delay: 100 // 100ms delay between each LED
		});
	}

	$: isConnected = connectionStatus === 'connected';
</script>

<div class="dashboard-controls">
	<!-- Connection Status Alert -->
	{#if !isConnected}
		<div class="connection-alert">
			<span class="alert-icon">⚠️</span>
			<span>Controls disabled - WebSocket not connected</span>
		</div>
	{/if}

	<!-- Individual LED Control -->
	<div class="control-section">
		<h3>Individual LED Control</h3>
		
		<div class="control-group">
			<label for="led-index">LED Index:</label>
			<input 
				id="led-index"
				type="number" 
				bind:value={selectedLEDIndex} 
				min="0" 
				max="59"
				disabled={!isConnected}
				class="number-input"
			/>
		</div>

		<div class="control-group">
			<label for="color-picker">Color:</label>
			<div class="color-controls">
				<input 
					id="color-picker"
					type="color" 
					value={hexColor}
					on:input={handleHexColorChange}
					disabled={!isConnected}
					class="color-input"
				/>
				<span class="color-value">{hexColor.toUpperCase()}</span>
			</div>
		</div>

		<div class="control-group">
			<label>RGB Values:</label>
			<div class="rgb-controls">
				<div class="rgb-input">
					<label>R:</label>
					<input 
						type="range" 
						bind:value={selectedColor.r} 
						min="0" 
						max="255"
						disabled={!isConnected}
					/>
					<span>{selectedColor.r}</span>
				</div>
				<div class="rgb-input">
					<label>G:</label>
					<input 
						type="range" 
						bind:value={selectedColor.g} 
						min="0" 
						max="255"
						disabled={!isConnected}
					/>
					<span>{selectedColor.g}</span>
				</div>
				<div class="rgb-input">
					<label>B:</label>
					<input 
						type="range" 
						bind:value={selectedColor.b} 
						min="0" 
						max="255"
						disabled={!isConnected}
					/>
					<span>{selectedColor.b}</span>
				</div>
			</div>
		</div>

		<div class="control-group">
			<label for="brightness">Brightness:</label>
			<div class="brightness-control">
				<input 
					id="brightness"
					type="range" 
					bind:value={selectedBrightness} 
					min="0" 
					max="1" 
					step="0.1"
					disabled={!isConnected}
					class="brightness-slider"
				/>
				<span class="brightness-value">{Math.round(selectedBrightness * 100)}%</span>
			</div>
		</div>

		<button 
			on:click={testLED}
			disabled={!isConnected}
			class="test-button primary"
		>
			Test LED {selectedLEDIndex}
		</button>
	</div>

	<!-- Preset Colors -->
	<div class="control-section">
		<h3>Preset Colors</h3>
		<div class="preset-colors">
			{#each presetColors as color}
				<button 
					on:click={() => selectPresetColor(color)}
					disabled={!isConnected}
					class="preset-color"
					style="background-color: rgb({color.r}, {color.g}, {color.b})"
					title={color.name}
				>
					{color.name}
				</button>
			{/each}
		</div>
	</div>

	<!-- Pattern Testing -->
	<div class="control-section">
		<h3>Pattern Testing</h3>
		
		<div class="control-group">
			<label for="pattern-select">Pattern:</label>
			<select 
				id="pattern-select"
				bind:value={testPattern}
				disabled={!isConnected}
				class="pattern-select"
			>
				{#each patterns as pattern}
					<option value={pattern.value}>{pattern.label}</option>
				{/each}
			</select>
		</div>

		<div class="control-group">
			<label for="duration">Duration (ms):</label>
			<input 
				id="duration"
				type="number" 
				bind:value={patternDuration} 
				min="1000" 
				max="60000"
				step="1000"
				disabled={!isConnected}
				class="number-input"
			/>
		</div>

		<button 
			on:click={runTestPattern}
			disabled={!isConnected}
			class="test-button primary"
		>
			Run Pattern
		</button>
	</div>

	<!-- Quick Actions -->
	<div class="control-section">
		<h3>Quick Actions</h3>
		<div class="quick-actions">
			<button 
				on:click={fillAllLEDs}
				disabled={!isConnected}
				class="test-button secondary"
			>
				Fill All
			</button>
			<button 
				on:click={testAllLEDs}
				disabled={!isConnected}
				class="test-button primary"
			>
				Test All
			</button>
			<button 
				on:click={clearAllLEDs}
				disabled={!isConnected}
				class="test-button danger"
			>
				Clear All
			</button>
		</div>
	</div>
</div>

<style>
	.dashboard-controls {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.connection-alert {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem;
		background-color: #fff3cd;
		color: #856404;
		border: 1px solid #ffeaa7;
		border-radius: 6px;
		font-size: 0.9rem;
	}

	.control-section {
		padding: 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		background: #fafafa;
	}

	.control-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #333;
	}

	.control-group {
		margin-bottom: 1rem;
	}

	.control-group:last-child {
		margin-bottom: 0;
	}

	.control-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #555;
		font-size: 0.9rem;
	}

	.number-input,
	.pattern-select {
		width: 100%;
		padding: 0.75rem; /* Larger touch targets */
		border: 1px solid #ccc;
		border-radius: 6px;
		font-size: 1rem; /* Prevent zoom on iOS */
		min-height: 44px; /* Minimum touch target size */
		touch-action: manipulation;
	}

	.number-input:disabled,
	.pattern-select:disabled {
		background-color: #f5f5f5;
		color: #999;
	}

	.color-controls {
		display: flex;
		align-items: center;
		gap: 0.75rem; /* Larger gaps for touch */
	}

	.color-input {
		width: 60px; /* Larger for touch */
		height: 44px;
		border: 1px solid #ccc;
		border-radius: 8px;
		cursor: pointer;
		touch-action: manipulation;
	}

	.color-input:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	.color-value {
		font-family: monospace;
		font-size: 0.9rem;
		color: #666;
	}

	.rgb-controls {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.rgb-input {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-height: 44px; /* Minimum touch target size */
	}

	.rgb-input label {
		width: 20px;
		margin: 0;
		font-weight: 600;
		font-size: 0.8rem;
	}

	.rgb-input input[type="range"] {
		flex: 1;
		min-height: 44px;
		-webkit-appearance: none;
		appearance: none;
		background: #ddd;
		border-radius: 22px;
		outline: none;
	}

	.rgb-input input[type="range"]::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #007bff;
		cursor: pointer;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	.rgb-input input[type="range"]::-moz-range-thumb {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #007bff;
		cursor: pointer;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	.rgb-input span {
		width: 30px;
		text-align: right;
		font-size: 0.8rem;
		color: #666;
	}

	.brightness-control {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-height: 44px;
	}

	.brightness-slider {
		flex: 1;
		min-height: 44px;
		-webkit-appearance: none;
		appearance: none;
		background: #ddd;
		border-radius: 22px;
		outline: none;
	}

	.brightness-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #007bff;
		cursor: pointer;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	.brightness-slider::-moz-range-thumb {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #007bff;
		cursor: pointer;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	.brightness-value {
		width: 40px;
		text-align: right;
		font-size: 0.9rem;
		color: #666;
	}

	.preset-colors {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
		gap: 0.75rem; /* Larger gaps for touch */
	}

	.preset-color {
		padding: 0.75rem; /* Larger touch targets */
		min-height: 44px;
		border: 2px solid #ccc;
		border-radius: 8px;
		color: white;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
	}

	.preset-color:hover:not(:disabled) {
		border-color: #333;
		transform: translateY(-1px);
	}

	.preset-color:active {
		transform: scale(0.95);
	}

	.preset-color:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.test-button {
		width: 100%;
		padding: 0.75rem;
		min-height: 44px; /* Minimum touch target size */
		border: none;
		border-radius: 6px;
		font-weight: 600;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.2s;
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
	}

	.test-button.primary {
		background-color: #007bff;
		color: white;
	}

	.test-button.primary:hover:not(:disabled) {
		background-color: #0056b3;
	}

	.test-button.primary:active {
		transform: translateY(1px);
	}

	.test-button.secondary {
		background-color: #6c757d;
		color: white;
	}

	.test-button.secondary:hover:not(:disabled) {
		background-color: #545b62;
	}

	.test-button.secondary:active {
		transform: translateY(1px);
	}

	.test-button.danger {
		background-color: #dc3545;
		color: white;
	}

	.test-button.danger:hover:not(:disabled) {
		background-color: #c82333;
	}

	.test-button.danger:active {
		transform: translateY(1px);
	}

	.test-button:disabled {
		background-color: #e9ecef;
		color: #6c757d;
		cursor: not-allowed;
	}

	.quick-actions {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem; /* Larger gaps for touch */
	}

	/* Mobile-specific optimizations */
	@media (max-width: 768px) {
		.dashboard-controls {
			gap: 1rem;
		}
		
		.control-section {
			padding: 0.75rem;
		}
		
		.preset-colors {
			grid-template-columns: repeat(4, 1fr);
			justify-items: center;
		}
		
		.rgb-controls {
			gap: 0.5rem;
		}
		
		.color-controls {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
		}
		
		.color-input {
			width: 100%;
			height: 50px;
		}
		
		.quick-actions {
			grid-template-columns: 1fr;
			gap: 0.5rem;
		}
	}

	@media (max-width: 480px) {
		.control-section {
			padding: 0.5rem;
		}
		
		.control-section h3 {
			font-size: 0.9rem;
		}
		
		.preset-colors {
			grid-template-columns: repeat(3, 1fr);
		}
		
		.preset-color {
			padding: 0.5rem;
			font-size: 0.7rem;
		}
		
		.rgb-input {
			gap: 0.5rem;
		}
		
		.brightness-control {
			gap: 0.5rem;
		}
	}
</style>