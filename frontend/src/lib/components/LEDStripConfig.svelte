<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let settings = {
		led_count: 246,
		max_led_count: 300,
		led_type: 'WS2812B',
		led_orientation: 'normal',
		led_strip_type: 'WS2811_STRIP_GRB',
		power_supply_voltage: 5.0,
		power_supply_current: 10.0,
		brightness: 0.5
	};
	export let disabled = false;

	const ledTypes = [
		{
			value: 'WS2812B',
			label: 'WS2812B',
			description: 'Most common, integrated controller',
			voltage: 5.0,
			current_per_led: 60,
			frequency: 800000,
			color_order: 'GRB'
		},
		{
			value: 'WS2813',
			label: 'WS2813',
			description: 'Backup data line, more reliable',
			voltage: 5.0,
			current_per_led: 60,
			frequency: 800000,
			color_order: 'GRB'
		},
		{
			value: 'WS2815',
			label: 'WS2815',
			description: '12V version, longer runs possible',
			voltage: 12.0,
			current_per_led: 20,
			frequency: 800000,
			color_order: 'GRB'
		},
		{
			value: 'APA102',
			label: 'APA102 (DotStar)',
			description: 'Clock + data, higher refresh rate',
			voltage: 5.0,
			current_per_led: 60,
			frequency: 1000000,
			color_order: 'BGR'
		},
		{
			value: 'SK6812',
			label: 'SK6812 (RGBW)',
			description: 'RGB + White channel',
			voltage: 5.0,
			current_per_led: 80,
			frequency: 800000,
			color_order: 'GRBW'
		}
	];

	const colorOrders = {
		'GRB': 'WS2811_STRIP_GRB',
		'RGB': 'WS2811_STRIP_RGB',
		'BGR': 'WS2811_STRIP_BGR',
		'BRG': 'WS2811_STRIP_BRG',
		'RBG': 'WS2811_STRIP_RBG',
		'GBR': 'WS2811_STRIP_GBR',
		'GRBW': 'SK6812_STRIP_GRBW',
		'RGBW': 'SK6812_STRIP_RGBW'
	};

	let powerCalculation = {};
	let validationErrors = {};

	function calculatePower() {
		const selectedType = ledTypes.find(type => type.value === settings.led_type);
		if (!selectedType) return;

		const totalCurrentMa = settings.led_count * selectedType.current_per_led * settings.brightness;
		const totalCurrentA = totalCurrentMa / 1000;
		const totalWatts = totalCurrentA * selectedType.voltage;
		const recommendedSupplyA = totalCurrentA * 1.2; // 20% safety margin
		const recommendedSupplyW = recommendedSupplyA * selectedType.voltage;

		// Voltage drop calculation (approximate)
		const stripLengthM = settings.led_count * 0.0167; // Assume 60 LEDs/meter
		const voltageDrop = (totalCurrentA * stripLengthM * 0.1); // Rough estimate
		const effectiveVoltage = selectedType.voltage - voltageDrop;

		powerCalculation = {
			current_ma: Math.round(totalCurrentMa),
			current_a: Math.round(totalCurrentA * 100) / 100,
			power_watts: Math.round(totalWatts * 100) / 100,
			recommended_supply_a: Math.round(recommendedSupplyA * 100) / 100,
			recommended_supply_w: Math.round(recommendedSupplyW * 100) / 100,
			strip_length_m: Math.round(stripLengthM * 100) / 100,
			voltage_drop: Math.round(voltageDrop * 100) / 100,
			effective_voltage: Math.round(effectiveVoltage * 100) / 100,
			supply_adequate: settings.power_supply_current >= recommendedSupplyA,
			voltage_adequate: effectiveVoltage >= (selectedType.voltage * 0.9)
		};
	}

	function validateConfig() {
		const errors = {};

		if (settings.led_count <= 0) {
			errors.led_count = 'LED count must be greater than 0';
		}

		if (settings.led_count > settings.max_led_count) {
			errors.led_count = `LED count cannot exceed ${settings.max_led_count}`;
		}

		if (settings.brightness < 0 || settings.brightness > 1) {
			errors.brightness = 'Brightness must be between 0 and 1';
		}

		if (settings.power_supply_voltage < 3 || settings.power_supply_voltage > 24) {
			errors.power_supply_voltage = 'Voltage must be between 3V and 24V';
		}

		if (settings.power_supply_current < 0.5 || settings.power_supply_current > 100) {
			errors.power_supply_current = 'Current must be between 0.5A and 100A';
		}

		validationErrors = errors;
	}

	function handleConfigChange(key, value) {
		settings = { ...settings, [key]: value };
		
		// Auto-update strip type when LED type changes
		if (key === 'led_type') {
			const selectedType = ledTypes.find(type => type.value === value);
			if (selectedType) {
				settings.led_strip_type = colorOrders[selectedType.color_order];
			}
		}
		
		calculatePower();
		validateConfig();
		dispatch('change', settings);
	}

	function handleLEDCountInput(event) {
		const value = parseInt(event.target.value) || 0;
		handleConfigChange('led_count', Math.min(value, settings.max_led_count));
	}

	// Initialize calculations
	$: if (settings) {
		calculatePower();
		validateConfig();
	}

	$: selectedLEDType = ledTypes.find(type => type.value === settings.led_type);
	$: hasErrors = Object.keys(validationErrors).length > 0;
	$: powerWarnings = powerCalculation.supply_adequate === false || powerCalculation.voltage_adequate === false;
</script>

<div class="led-strip-config">
	<div class="config-section">
		<h3>LED Strip Specification</h3>
		
		<div class="strip-basic-config">
			<div class="config-group">
				<label for="led-type">LED Strip Type</label>
				<select
					id="led-type"
					bind:value={settings.led_type}
					on:change={(e) => handleConfigChange('led_type', e.target.value)}
					{disabled}
				>
					{#each ledTypes as type}
						<option value={type.value}>{type.label} - {type.description}</option>
					{/each}
				</select>
				{#if selectedLEDType}
					<div class="type-specs">
						<span>Voltage: {selectedLEDType.voltage}V</span>
						<span>Current: {selectedLEDType.current_per_led}mA/LED</span>
						<span>Order: {selectedLEDType.color_order}</span>
					</div>
				{/if}
			</div>

			<div class="config-group">
				<label for="led-count">Number of LEDs</label>
				<div class="led-count-input">
					<input
						id="led-count"
						type="number"
						min="1"
						max={settings.max_led_count}
						bind:value={settings.led_count}
						on:input={handleLEDCountInput}
						{disabled}
						class:error={validationErrors.led_count}
					/>
					<span class="max-indicator">/ {settings.max_led_count} max</span>
				</div>
				{#if validationErrors.led_count}
					<span class="error-message">{validationErrors.led_count}</span>
				{/if}
			</div>

			<div class="config-group">
				<label for="led-orientation">LED Orientation</label>
				<select
					id="led-orientation"
					bind:value={settings.led_orientation}
					on:change={(e) => handleConfigChange('led_orientation', e.target.value)}
					{disabled}
				>
					<option value="normal">Normal (Left to Right)</option>
					<option value="reversed">Reversed (Right to Left)</option>
				</select>
			</div>

			<div class="config-group">
				<label for="brightness">Default Brightness</label>
				<div class="brightness-control">
					<input
						id="brightness"
						type="range"
						min="0"
						max="1"
						step="0.01"
						bind:value={settings.brightness}
						on:input={(e) => handleConfigChange('brightness', parseFloat(e.target.value))}
						{disabled}
						class:error={validationErrors.brightness}
					/>
					<span class="brightness-value">{Math.round(settings.brightness * 100)}%</span>
				</div>
				{#if validationErrors.brightness}
					<span class="error-message">{validationErrors.brightness}</span>
				{/if}
			</div>
		</div>
	</div>

	<div class="power-section">
		<h3>Power Supply Configuration</h3>
		
		<div class="power-config">
			<div class="config-group">
				<label for="supply-voltage">Supply Voltage (V)</label>
				<input
					id="supply-voltage"
					type="number"
					min="3"
					max="24"
					step="0.1"
					bind:value={settings.power_supply_voltage}
					on:input={(e) => handleConfigChange('power_supply_voltage', parseFloat(e.target.value))}
					{disabled}
					class:error={validationErrors.power_supply_voltage}
				/>
				{#if validationErrors.power_supply_voltage}
					<span class="error-message">{validationErrors.power_supply_voltage}</span>
				{/if}
			</div>

			<div class="config-group">
				<label for="supply-current">Supply Current Capacity (A)</label>
				<input
					id="supply-current"
					type="number"
					min="0.5"
					max="100"
					step="0.1"
					bind:value={settings.power_supply_current}
					on:input={(e) => handleConfigChange('power_supply_current', parseFloat(e.target.value))}
					{disabled}
					class:error={validationErrors.power_supply_current}
				/>
				{#if validationErrors.power_supply_current}
					<span class="error-message">{validationErrors.power_supply_current}</span>
				{/if}
			</div>
		</div>
	</div>

	{#if powerCalculation.current_a}
		<div class="power-analysis" class:warning={powerWarnings}>
			<h4>Power Analysis</h4>
			
			<div class="analysis-grid">
				<div class="analysis-item">
					<span class="label">Current Draw:</span>
					<span class="value">{powerCalculation.current_a}A ({powerCalculation.current_ma}mA)</span>
				</div>
				
				<div class="analysis-item">
					<span class="label">Power Consumption:</span>
					<span class="value">{powerCalculation.power_watts}W</span>
				</div>
				
				<div class="analysis-item">
					<span class="label">Recommended Supply:</span>
					<span class="value">{powerCalculation.recommended_supply_a}A ({powerCalculation.recommended_supply_w}W)</span>
				</div>
				
				<div class="analysis-item">
					<span class="label">Strip Length:</span>
					<span class="value">{powerCalculation.strip_length_m}m (estimated)</span>
				</div>
				
				<div class="analysis-item">
					<span class="label">Voltage Drop:</span>
					<span class="value">{powerCalculation.voltage_drop}V</span>
				</div>
				
				<div class="analysis-item">
					<span class="label">Effective Voltage:</span>
					<span class="value">{powerCalculation.effective_voltage}V</span>
				</div>
			</div>

			<div class="power-status">
				<div class="status-item" class:good={powerCalculation.supply_adequate} class:bad={!powerCalculation.supply_adequate}>
					<span class="status-icon">{powerCalculation.supply_adequate ? '✅' : '⚠️'}</span>
					<span>Power Supply {powerCalculation.supply_adequate ? 'Adequate' : 'Insufficient'}</span>
				</div>
				
				<div class="status-item" class:good={powerCalculation.voltage_adequate} class:bad={!powerCalculation.voltage_adequate}>
					<span class="status-icon">{powerCalculation.voltage_adequate ? '✅' : '⚠️'}</span>
					<span>Voltage Level {powerCalculation.voltage_adequate ? 'Adequate' : 'Too Low'}</span>
				</div>
			</div>

			{#if !powerCalculation.supply_adequate}
				<div class="recommendation">
					<strong>Recommendation:</strong> Increase power supply capacity to at least {powerCalculation.recommended_supply_a}A
					or reduce LED count/brightness.
				</div>
			{/if}

			{#if !powerCalculation.voltage_adequate}
				<div class="recommendation">
					<strong>Recommendation:</strong> Consider power injection every 100-150 LEDs or use higher voltage strips (WS2815).
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.led-strip-config {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		padding: 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		background: #fafafa;
	}

	.config-section h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.2rem;
		font-weight: 600;
	}

	.strip-basic-config, .power-config {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
		padding: 1rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}

	.config-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.config-group label {
		font-weight: 500;
		color: #333;
		font-size: 0.9rem;
	}

	.config-group input, .config-group select {
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		background: white;
		font-size: 0.9rem;
	}

	.config-group input.error, .config-group select.error {
		border-color: #dc3545;
		box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.1);
	}

	.error-message {
		color: #dc3545;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.type-specs {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		font-size: 0.8rem;
		color: #666;
		margin-top: 0.25rem;
	}

	.type-specs span {
		padding: 0.2rem 0.4rem;
		background: #f0f8ff;
		border-radius: 3px;
		color: #0066cc;
	}

	.led-count-input {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.led-count-input input {
		flex: 1;
	}

	.max-indicator {
		font-size: 0.8rem;
		color: #666;
		white-space: nowrap;
	}

	.brightness-control {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.brightness-control input[type="range"] {
		flex: 1;
	}

	.brightness-value {
		font-weight: 600;
		color: #333;
		min-width: 40px;
		text-align: right;
	}

	.power-analysis {
		padding: 1rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}

	.power-analysis.warning {
		border-color: #ffc107;
		background: #fff8e1;
	}

	.power-analysis h4 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1rem;
		font-weight: 600;
	}

	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.analysis-item {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem;
		background: #f8f9fa;
		border-radius: 4px;
	}

	.analysis-item .label {
		font-weight: 500;
		color: #666;
	}

	.analysis-item .value {
		font-weight: 600;
		color: #333;
	}

	.power-status {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		border-radius: 4px;
		font-weight: 500;
	}

	.status-item.good {
		background: #d4edda;
		color: #155724;
		border: 1px solid #c3e6cb;
	}

	.status-item.bad {
		background: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
	}

	.recommendation {
		padding: 0.75rem;
		background: #fff3cd;
		border: 1px solid #ffeaa7;
		border-radius: 4px;
		color: #856404;
		font-size: 0.9rem;
	}

	@media (max-width: 768px) {
		.strip-basic-config, .power-config, .analysis-grid {
			grid-template-columns: 1fr;
		}
		
		.power-status {
			flex-direction: column;
		}
		
		.brightness-control {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>