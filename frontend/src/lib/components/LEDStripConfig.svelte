<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import SettingsFormField from './SettingsFormField.svelte';
	import { createCategoryValidation } from '../utils/settingsValidation.js';

	const dispatch = createEventDispatcher();

	export let settings = {
		ledCount: 246,
		maxLedCount: 300,
		ledType: 'WS2812B',
		ledOrientation: 'normal',
		ledStripType: 'WS2811_STRIP_GRB',
		powerSupplyVoltage: 5.0,
		powerSupplyCurrent: 10.0,
		brightness: 0.5,
		colorProfile: 'Standard RGB',
		performanceMode: 'Balanced',
		advancedSettings: {
			gamma: 2.2,
			whiteBalance: { r: 1.0, g: 1.0, b: 1.0 },
			colorTemp: 6500,
			dither: false,
			updateRate: 30,
			powerLimiting: true,
			maxPowerWatts: 50,
			thermalProtection: true,
			maxTemp: 70
		}
	};
	// Initialize validation for LED settings
	const categoryValidation = createCategoryValidation('led');

	// Validate individual field with proper category and field mapping
	async function validateFieldMapped(field, value) {
		const mappedField = fieldMapping[field] || field;
		return await categoryValidation.validateField(mappedField, value);
	}
	
	// Map frontend field names to backend schema field names
	const fieldMapping = {
		'ledCount': 'count',
		'ledType': 'strip_type',
		'ledOrientation': 'reverse_order',
		'brightness': 'brightness',
		'gamma': 'gamma_correction',
		'colorTemp': 'color_temperature'
	};

	export let disabled = false;

	// Enhanced LED types with more detailed specifications
	const ledTypes = [
		{
			name: 'WS2812B',
			value: 'WS2812B',
			label: 'WS2812B',
			voltage: 5.0,
			currentPerLED: 0.06,
			frequency: 800000,
			colorOrder: 'GRB',
			timing: { t0h: 0.4, t0l: 0.85, t1h: 0.8, t1l: 0.45, reset: 50 },
			description: 'Standard addressable RGB LED'
		},
		{
			name: 'WS2811',
			value: 'WS2811',
			label: 'WS2811',
			voltage: 12.0,
			currentPerLED: 0.06,
			frequency: 400000,
			colorOrder: 'RGB',
			timing: { t0h: 0.5, t0l: 2.0, t1h: 1.2, t1l: 1.3, reset: 50 },
			description: 'External driver chip, 12V operation'
		},
		{
			name: 'SK6812',
			value: 'SK6812',
			label: 'SK6812',
			voltage: 5.0,
			currentPerLED: 0.06,
			frequency: 800000,
			colorOrder: 'GRB',
			timing: { t0h: 0.3, t0l: 0.9, t1h: 0.6, t1l: 0.6, reset: 80 },
			description: 'Similar to WS2812B with RGBW variants'
		},
		{
			name: 'APA102',
			value: 'APA102',
			label: 'APA102',
			voltage: 5.0,
			currentPerLED: 0.06,
			frequency: 1000000,
			colorOrder: 'BGR',
			timing: { clockBased: true },
			description: 'Clock-based protocol, higher refresh rates'
		},
		{
			name: 'WS2815',
			value: 'WS2815',
			label: 'WS2815',
			voltage: 12.0,
			currentPerLED: 0.012,
			frequency: 800000,
			colorOrder: 'GRB',
			timing: { t0h: 0.3, t0l: 1.09, t1h: 1.09, t1l: 0.32, reset: 280 },
			description: 'Dual signal, backup data line'
		}
	];

	// Color profiles for different applications
	const colorProfiles = [
		{
			name: 'Standard RGB',
			description: 'Standard sRGB color space',
			gamma: 2.2,
			whiteBalance: { r: 1.0, g: 1.0, b: 1.0 },
			colorTemp: 6500
		},
		{
			name: 'Warm White',
			description: 'Warm white bias for cozy lighting',
			gamma: 2.4,
			whiteBalance: { r: 1.0, g: 0.9, b: 0.7 },
			colorTemp: 3000
		},
		{
			name: 'Cool White',
			description: 'Cool white bias for task lighting',
			gamma: 2.0,
			whiteBalance: { r: 0.9, g: 1.0, b: 1.1 },
			colorTemp: 8000
		},
		{
			name: 'Music Visualization',
			description: 'Enhanced colors for music reactive lighting',
			gamma: 1.8,
			whiteBalance: { r: 1.1, g: 1.0, b: 1.2 },
			colorTemp: 6500
		}
	];

	// Performance optimization options
	const performanceOptions = [
		{ name: 'Quality', description: 'Best color accuracy, higher CPU usage', dither: true, updateRate: 60 },
		{ name: 'Balanced', description: 'Good balance of quality and performance', dither: false, updateRate: 30 },
		{ name: 'Performance', description: 'Fastest updates, basic color processing', dither: false, updateRate: 120 }
	];

	const colorOrderToStripType = {
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

	// Enhanced power calculation with thermal considerations
	function calculatePower() {
		const ledType = ledTypes.find(type => type.name === settings.ledType);
		if (!ledType) return;

		const brightnessMultiplier = settings.brightness;
		const currentPerLED = ledType.currentPerLED * brightnessMultiplier;
		const totalCurrent = settings.ledCount * currentPerLED;
		const totalWattage = totalCurrent * ledType.voltage;
		
		// Wire resistance calculation (assuming 22 AWG wire)
		const wireResistancePerMeter = 0.052; // ohms per meter for 22 AWG
		const estimatedLength = settings.ledCount * 0.0167; // ~16.7mm per LED
		const wireResistance = wireResistancePerMeter * estimatedLength;
		const voltageDrop = totalCurrent * wireResistance;
		const effectiveVoltage = settings.powerSupplyVoltage - voltageDrop;
		
		// Thermal calculations
		const ambientTemp = 25; // °C
		const thermalResistance = 50; // °C/W (estimated for LED strip)
		const estimatedTemp = ambientTemp + (totalWattage * thermalResistance / 1000);
		
		// Power supply recommendations
		const recommendedSupply = Math.ceil(totalWattage * 1.2); // 20% headroom
		const supplyAdequacy = settings.powerSupplyCurrent * settings.powerSupplyVoltage >= totalWattage * 1.1;
		const voltageAdequacy = effectiveVoltage >= ledType.voltage * 0.9;
		const thermalOk = estimatedTemp <= (settings.advancedSettings?.maxTemp || 70);

		powerCalculation = {
			current_a: totalCurrent.toFixed(2),
			current_ma: (totalCurrent * 1000).toFixed(0),
			power_watts: totalWattage.toFixed(1),
			recommended_supply_a: (totalWattage * 1.2 / settings.powerSupplyVoltage).toFixed(2),
			recommended_supply_w: recommendedSupply,
			strip_length_m: (estimatedLength).toFixed(2),
			voltage_drop: voltageDrop.toFixed(2),
			effective_voltage: effectiveVoltage.toFixed(1),
			estimated_temp: estimatedTemp.toFixed(1),
			supply_adequate: supplyAdequacy,
			voltage_adequate: voltageAdequacy,
			thermal_ok: thermalOk,
			efficiency: ((effectiveVoltage / ledType.voltage) * 100).toFixed(1)
		};
	}

	// Enhanced validation with thermal and performance checks
	function validateConfig() {
		const errors = {};
		
		if (settings.ledCount <= 0) {
			errors.ledCount = 'LED count must be greater than 0';
		}
		
		if (settings.ledCount > settings.maxLedCount) {
			errors.ledCount = `LED count cannot exceed ${settings.maxLedCount}`;
		}
		
		if (settings.brightness < 0 || settings.brightness > 1) {
			errors.brightness = 'Brightness must be between 0 and 1';
		}
		
		if (settings.powerSupplyVoltage < 3 || settings.powerSupplyVoltage > 24) {
			errors.powerSupplyVoltage = 'Voltage must be between 3V and 24V';
		}
		
		if (settings.powerSupplyCurrent < 0.5 || settings.powerSupplyCurrent > 100) {
			errors.powerSupplyCurrent = 'Current must be between 0.5A and 100A';
		}

		validationErrors = errors;
	}

	// Handle configuration changes with validation
	function handleConfigChange(field, value) {
		if (field && value !== undefined) {
			settings[field] = value;
			validateFieldMapped(field, value);
		}
		calculatePower();
		validateConfig();
		dispatch('configChange', settings);
	}

	// Handle input changes for real-time validation
	function handleInput(field, value) {
		settings[field] = value;
		validateFieldMapped(field, value);
	}

	// Initialize calculations on component mount
	onMount(() => {
		calculatePower();
		validateConfig();
	});

	// Reactive calculations when settings change
	$: if (settings) {
		calculatePower();
		validateConfig();
	}

	$: selectedLEDType = ledTypes.find(type => type.value === settings.ledType);
	$: hasErrors = Object.keys(validationErrors).length > 0;
	$: powerWarnings = powerCalculation.supply_adequate === false || powerCalculation.voltage_adequate === false;
</script>

<div class="led-strip-config">
	<h3>LED Strip Configuration</h3>
	
	<!-- LED Type Selection -->
	<div class="config-section">
		<h4>LED Strip Type</h4>
		
		<SettingsFormField
			type="select"
			label="LED Type"
			id="led-type"
			bind:value={settings.ledType}
			options={ledTypes.map(type => ({ value: type.value, label: type.label }))}
			{disabled}
			validationState={$categoryValidation.errors?.strip_type ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.strip_type}
			helpText="Select the type of LED strip you're using"
			on:change={(e) => handleConfigChange('ledType', e.detail)}
		/>
		
		<!-- LED Type Specifications -->
		{#if settings.ledType}
			{@const selectedType = ledTypes.find(type => type.value === settings.ledType)}
			{#if selectedType}
				<div class="led-specs">
					<div class="spec-item">
						<span class="spec-label">Voltage:</span>
						<span class="spec-value">{selectedType.voltage}V</span>
					</div>
					<div class="spec-item">
						<span class="spec-label">Current per LED:</span>
						<span class="spec-value">{selectedType.currentPerLED * 1000}mA</span>
					</div>
					<div class="spec-item">
						<span class="spec-label">Frequency:</span>
						<span class="spec-value">{selectedType.frequency}</span>
					</div>
					<div class="spec-item">
						<span class="spec-label">Color Order:</span>
						<span class="spec-value">{selectedType.colorOrder}</span>
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<!-- LED Count -->
	<div class="config-section">
		<SettingsFormField
			type="number"
			label="LED Count"
			id="led-count"
			bind:value={settings.ledCount}
			min="1"
			max="1000"
			{disabled}
			validationState={$categoryValidation.errors?.count ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.count}
			helpText="Number of LEDs in your strip (1-1000)"
			on:change={(e) => handleConfigChange('ledCount', e.detail)}
		/>
	</div>

	<!-- LED Configuration -->
	<div class="config-section">
		<h4>LED Configuration</h4>
		
		<SettingsFormField
			type="select"
			label="LED Orientation"
			id="orientation"
			bind:value={settings.ledOrientation}
			options={[
				{ value: 'normal', label: 'Normal (Start to End)' },
				{ value: 'reversed', label: 'Reversed (End to Start)' }
			]}
			{disabled}
			validationState={$categoryValidation.errors?.reverse_order ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.reverse_order}
			helpText="Reverse the order of LEDs if your strip is wired backwards"
			on:change={(e) => handleConfigChange('ledOrientation', e.detail)}
		/>

		<SettingsFormField
			type="range"
			label="Brightness"
			id="brightness"
			bind:value={settings.brightness}
			min="0"
			max="100"
			step="1"
			{disabled}
			validationState={$categoryValidation.errors?.brightness ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.brightness}
			helpText="Overall brightness level (0-100%)"
			on:change={(e) => handleConfigChange('brightness', e.detail)}
		/>
	</div>

	<!-- Power Supply Configuration -->
	<div class="config-section">
		<h4>Power Supply</h4>
		
		<SettingsFormField
			type="number"
			label="Supply Voltage (V)"
			id="supply-voltage"
			bind:value={settings.powerSupplyVoltage}
			min="3"
			max="24"
			step="0.1"
			{disabled}
			validationState={$categoryValidation.errors?.powerSupplyVoltage ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.powerSupplyVoltage}
			helpText="Voltage rating of your power supply (3V - 24V)"
			on:input={(e) => handleInput('powerSupplyVoltage', e.detail)}
			on:change={(e) => handleConfigChange('powerSupplyVoltage', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Supply Current Capacity (A)"
			id="supply-current"
			bind:value={settings.powerSupplyCurrent}
			min="0.1"
			max="100"
			step="0.1"
			{disabled}
			validationState={$categoryValidation.errors?.powerSupplyCurrent ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.powerSupplyCurrent}
			helpText="Maximum current capacity of your power supply (A)"
			on:input={(e) => handleInput('powerSupplyCurrent', e.detail)}
			on:change={(e) => handleConfigChange('powerSupplyCurrent', e.detail)}
		/>
	</div>

	<!-- Advanced Settings -->
	<div class="config-section">
		<h4>Advanced Settings</h4>
		
		<SettingsFormField
			type="select"
			label="Color Profile"
			id="color-profile"
			bind:value={settings.colorProfile}
			options={colorProfiles.map(profile => ({ 
				value: profile.name, 
				label: profile.name,
				description: profile.description 
			}))}
			{disabled}
			validationState={$categoryValidation.errors?.colorProfile ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.colorProfile}
			helpText="Color profile affects gamma, white balance, and color temperature"
			on:change={(e) => handleConfigChange('colorProfile', e.detail)}
		/>

		<SettingsFormField
			type="select"
			label="Performance Mode"
			id="performance-mode"
			bind:value={settings.performanceMode}
			options={performanceOptions.map(option => ({ 
				value: option.name, 
				label: option.name,
				description: option.description 
			}))}
			{disabled}
			validationState={$categoryValidation.errors?.performanceMode ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.performanceMode}
			helpText="Performance mode affects dithering and update rate"
			on:change={(e) => handleConfigChange('performanceMode', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Gamma Correction"
			id="gamma"
			bind:value={settings.gamma}
			min="1.0"
			max="3.0"
			step="0.1"
			{disabled}
			validationState={$categoryValidation.errors?.gamma_correction ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.gamma_correction}
			helpText="Gamma correction for color accuracy (1.0 - 3.0)"
			on:input={(e) => handleInput('gamma', e.detail)}
			on:change={(e) => handleConfigChange('gamma', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Color Temperature (K)"
			id="color-temp"
			bind:value={settings.colorTemp}
			min="2700"
			max="6500"
			step="100"
			{disabled}
			validationState={$categoryValidation.errors?.color_temperature ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.color_temperature}
			helpText="White balance color temperature (2700K-6500K)"
			on:input={(e) => handleInput('colorTemp', e.detail)}
			on:change={(e) => handleConfigChange('colorTemp', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Update Rate (Hz)"
			id="update-rate"
			bind:value={settings.updateRate}
			min="1"
			max="120"
			{disabled}
			validationState={$categoryValidation.errors?.updateRate ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.updateRate}
			helpText="LED update rate in Hz (1-120)"
			on:input={(e) => handleInput('updateRate', e.detail)}
			on:change={(e) => handleConfigChange('updateRate', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Max Power (Watts)"
			id="max-power"
			bind:value={settings.maxPowerWatts}
			min="1"
			max="1000"
			{disabled}
			validationState={$categoryValidation.errors?.maxPowerWatts ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.maxPowerWatts}
			helpText="Maximum power consumption limit"
			on:input={(e) => handleInput('maxPowerWatts', e.detail)}
			on:change={(e) => handleConfigChange('maxPowerWatts', e.detail)}
		/>

		<SettingsFormField
			type="number"
			label="Max Temperature (°C)"
			id="max-temp"
			bind:value={settings.maxTemp}
			min="40"
			max="100"
			{disabled}
			validationState={$categoryValidation.errors?.maxTemp ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.maxTemp}
			helpText="Maximum operating temperature"
			on:input={(e) => handleInput('maxTemp', e.detail)}
			on:change={(e) => handleConfigChange('maxTemp', e.detail)}
		/>

		<SettingsFormField
			type="checkbox"
			label="Enable Dithering"
			id="dither"
			bind:value={settings.dither}
			{disabled}
			validationState={$categoryValidation.errors?.dither ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.dither}
			helpText="Improve color accuracy with dithering"
			on:change={(e) => handleConfigChange('dither', e.detail)}
		/>

		<SettingsFormField
			type="checkbox"
			label="Power Limiting"
			id="power-limiting"
			bind:value={settings.powerLimiting}
			{disabled}
			validationState={$categoryValidation.errors?.powerLimiting ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.powerLimiting}
			helpText="Automatically limit power consumption"
			on:change={(e) => handleConfigChange('powerLimiting', e.detail)}
		/>

		<SettingsFormField
			type="checkbox"
			label="Thermal Protection"
			id="thermal-protection"
			bind:value={settings.thermalProtection}
			{disabled}
			validationState={$categoryValidation.errors?.thermalProtection ? 'invalid' : 'valid'}
			error={$categoryValidation.errors?.thermalProtection}
			helpText="Enable thermal protection to prevent overheating"
			on:change={(e) => handleConfigChange('thermalProtection', e.detail)}
		/>
	</div>

	<!-- Power Analysis -->
	{#if powerCalculation && Object.keys(powerCalculation).length > 0}
		<div class="config-section">
			<h4>Power Analysis</h4>
			<div class="power-analysis">
				<div class="power-grid">
					<div class="power-item">
						<span class="power-label">Current Draw:</span>
						<span class="power-value">{powerCalculation.current_a}A ({powerCalculation.current_ma}mA)</span>
					</div>
					<div class="power-item">
						<span class="power-label">Power Consumption:</span>
						<span class="power-value">{powerCalculation.power_watts}W</span>
					</div>
					<div class="power-item">
						<span class="power-label">Recommended Supply:</span>
						<span class="power-value">{powerCalculation.recommended_supply_a}A ({powerCalculation.recommended_supply_w}W)</span>
					</div>
					<div class="power-item">
						<span class="power-label">Strip Length:</span>
						<span class="power-value">{powerCalculation.strip_length_m}m</span>
					</div>
					<div class="power-item">
						<span class="power-label">Voltage Drop:</span>
						<span class="power-value">{powerCalculation.voltage_drop}V</span>
					</div>
					<div class="power-item">
						<span class="power-label">Effective Voltage:</span>
						<span class="power-value">{powerCalculation.effective_voltage}V</span>
					</div>
					<div class="power-item">
						<span class="power-label">Estimated Temperature:</span>
						<span class="power-value">{powerCalculation.estimated_temp}°C</span>
					</div>
					<div class="power-item">
						<span class="power-label">Efficiency:</span>
						<span class="power-value">{powerCalculation.efficiency}%</span>
					</div>
				</div>

				<!-- Status Indicators -->
				<div class="status-indicators">
					<div class="status-item" class:warning={!powerCalculation.supply_adequate}>
						<span class="status-icon">{powerCalculation.supply_adequate ? '✓' : '⚠'}</span>
						<span class="status-text">
							{powerCalculation.supply_adequate ? 'Power Supply Adequate' : 'Power Supply Insufficient'}
						</span>
					</div>
					<div class="status-item" class:warning={!powerCalculation.voltage_adequate}>
						<span class="status-icon">{powerCalculation.voltage_adequate ? '✓' : '⚠'}</span>
						<span class="status-text">
							{powerCalculation.voltage_adequate ? 'Voltage Level Good' : 'Voltage Drop Too High'}
						</span>
					</div>
					<div class="status-item" class:warning={!powerCalculation.thermal_ok}>
						<span class="status-icon">{powerCalculation.thermal_ok ? '✓' : '⚠'}</span>
						<span class="status-text">
							{powerCalculation.thermal_ok ? 'Temperature Safe' : 'Temperature Too High'}
						</span>
					</div>
				</div>

				<!-- Recommendations -->
				{#if !powerCalculation.supply_adequate || !powerCalculation.voltage_adequate || !powerCalculation.thermal_ok}
					<div class="recommendations">
						<h5>Recommendations:</h5>
						<ul>
							{#if !powerCalculation.supply_adequate}
								<li>Increase power supply capacity to at least {powerCalculation.recommended_supply_a}A</li>
							{/if}
							{#if !powerCalculation.voltage_adequate}
								<li>Use thicker wire gauge or shorter cable runs to reduce voltage drop</li>
								<li>Consider using a higher supply voltage if supported</li>
							{/if}
							{#if !powerCalculation.thermal_ok}
								<li>Reduce brightness or LED count to lower power consumption</li>
								<li>Improve ventilation or add heat sinks</li>
							{/if}
						</ul>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.led-strip-config {
		background: var(--surface-color);
		border-radius: 8px;
		padding: 1.5rem;
		border: 1px solid var(--border-color);
	}

	.led-strip-config h3 {
		margin: 0 0 1.5rem 0;
		color: var(--text-primary);
		font-size: 1.25rem;
		font-weight: 600;
	}

	.config-section {
		margin-bottom: 2rem;
	}

	.config-section:last-child {
		margin-bottom: 0;
	}

	.config-section h4 {
		margin: 0 0 1rem 0;
		color: var(--text-primary);
		font-size: 1.1rem;
		font-weight: 500;
		border-bottom: 1px solid var(--border-color);
		padding-bottom: 0.5rem;
	}

	.config-row {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.config-row label {
		font-weight: 500;
		color: var(--text-primary);
		font-size: 0.9rem;
	}

	.config-row select,
	.config-row input[type="number"] {
		padding: 0.5rem;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background: var(--input-bg);
		color: var(--text-primary);
		font-size: 0.9rem;
	}

	.config-row select:focus,
	.config-row input:focus {
		outline: none;
		border-color: var(--accent-color);
		box-shadow: 0 0 0 2px var(--accent-color-alpha);
	}

	.config-row .error {
		border-color: var(--error-color);
	}

	.input-hint {
		font-size: 0.8rem;
		color: var(--text-secondary);
		margin-top: 0.25rem;
	}

	.error-message {
		color: var(--error-color);
		font-size: 0.8rem;
		margin-top: 0.25rem;
	}

	/* LED Specifications */
	.led-specs {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.75rem;
		margin-top: 1rem;
		padding: 1rem;
		background: var(--surface-secondary);
		border-radius: 6px;
		border: 1px solid var(--border-color);
	}

	.spec-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.spec-label {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.spec-value {
		font-size: 0.85rem;
		color: var(--text-primary);
		font-weight: 500;
	}

	/* Brightness Control */
	.brightness-control {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.brightness-control input[type="range"] {
		flex: 1;
		height: 6px;
		background: var(--surface-secondary);
		border-radius: 3px;
		outline: none;
		-webkit-appearance: none;
	}

	.brightness-control input[type="range"]::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 18px;
		height: 18px;
		background: var(--accent-color);
		border-radius: 50%;
		cursor: pointer;
	}

	.brightness-control input[type="range"]::-moz-range-thumb {
		width: 18px;
		height: 18px;
		background: var(--accent-color);
		border-radius: 50%;
		cursor: pointer;
		border: none;
	}

	.brightness-value {
		font-weight: 500;
		color: var(--text-primary);
		min-width: 40px;
		text-align: right;
	}

	/* Power Analysis */
	.power-analysis {
		background: var(--surface-secondary);
		border-radius: 6px;
		padding: 1.5rem;
		border: 1px solid var(--border-color);
	}

	.power-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.power-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: var(--surface-color);
		border-radius: 4px;
		border: 1px solid var(--border-color);
	}

	.power-label {
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.power-value {
		font-size: 0.9rem;
		color: var(--text-primary);
		font-weight: 500;
	}

	/* Status Indicators */
	.status-indicators {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: var(--surface-color);
		border-radius: 4px;
		border: 1px solid var(--border-color);
	}

	.status-item.warning {
		background: var(--warning-bg);
		border-color: var(--warning-color);
	}

	.status-icon {
		font-size: 1.1rem;
		font-weight: bold;
	}

	.status-item:not(.warning) .status-icon {
		color: var(--success-color);
	}

	.status-item.warning .status-icon {
		color: var(--warning-color);
	}

	.status-text {
		font-size: 0.9rem;
		color: var(--text-primary);
	}

	/* Recommendations */
	.recommendations {
		background: var(--info-bg);
		border: 1px solid var(--info-color);
		border-radius: 4px;
		padding: 1rem;
	}

	.recommendations h5 {
		margin: 0 0 0.75rem 0;
		color: var(--info-color);
		font-size: 0.95rem;
		font-weight: 600;
	}

	.recommendations ul {
		margin: 0;
		padding-left: 1.25rem;
	}

	.recommendations li {
		color: var(--text-primary);
		font-size: 0.85rem;
		margin-bottom: 0.5rem;
	}

	.recommendations li:last-child {
		margin-bottom: 0;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.led-strip-config {
			padding: 1rem;
		}

		.led-specs {
			grid-template-columns: 1fr;
		}

		.power-grid {
			grid-template-columns: 1fr;
		}

		.brightness-control {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
		}

		.brightness-value {
			text-align: center;
		}

		.status-indicators {
			gap: 0.5rem;
		}
	}

	@media (max-width: 480px) {
		.config-row {
			gap: 0.25rem;
		}

		.power-item {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
		}

		.power-item .power-label {
			font-weight: 500;
		}
	}
</style>