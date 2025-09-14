<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let config = {
		gpio_pin: 19,
		gpio_power_pin: null,
		gpio_ground_pin: null,
		signal_level: 3.3,
		led_frequency: 800000,
		led_dma: 10,
		led_channel: 0,
		led_invert: false
	};
	export let disabled = false;

	// GPIO pin layout for Raspberry Pi 4
	const gpioPinout = [
		{ pin: 1, name: '3.3V', type: 'power', available: false },
		{ pin: 2, name: '5V', type: 'power', available: false },
		{ pin: 3, name: 'GPIO2 (SDA)', type: 'gpio', available: true },
		{ pin: 4, name: '5V', type: 'power', available: false },
		{ pin: 5, name: 'GPIO3 (SCL)', type: 'gpio', available: true },
		{ pin: 6, name: 'GND', type: 'ground', available: false },
		{ pin: 7, name: 'GPIO4', type: 'gpio', available: true },
		{ pin: 8, name: 'GPIO14 (TXD)', type: 'gpio', available: false },
		{ pin: 9, name: 'GND', type: 'ground', available: false },
		{ pin: 10, name: 'GPIO15 (RXD)', type: 'gpio', available: false },
		{ pin: 11, name: 'GPIO17', type: 'gpio', available: true },
		{ pin: 12, name: 'GPIO18 (PWM)', type: 'gpio', available: true },
		{ pin: 13, name: 'GPIO27', type: 'gpio', available: true },
		{ pin: 14, name: 'GND', type: 'ground', available: false },
		{ pin: 15, name: 'GPIO22', type: 'gpio', available: true },
		{ pin: 16, name: 'GPIO23', type: 'gpio', available: true },
		{ pin: 17, name: '3.3V', type: 'power', available: false },
		{ pin: 18, name: 'GPIO24', type: 'gpio', available: true },
		{ pin: 19, name: 'GPIO10 (MOSI)', type: 'gpio', available: true },
		{ pin: 20, name: 'GND', type: 'ground', available: false },
		{ pin: 21, name: 'GPIO9 (MISO)', type: 'gpio', available: true },
		{ pin: 22, name: 'GPIO25', type: 'gpio', available: true },
		{ pin: 23, name: 'GPIO11 (SCLK)', type: 'gpio', available: true },
		{ pin: 24, name: 'GPIO8 (CE0)', type: 'gpio', available: true },
		{ pin: 25, name: 'GND', type: 'ground', available: false },
		{ pin: 26, name: 'GPIO7 (CE1)', type: 'gpio', available: true },
		{ pin: 27, name: 'GPIO0 (ID_SD)', type: 'gpio', available: false },
		{ pin: 28, name: 'GPIO1 (ID_SC)', type: 'gpio', available: false },
		{ pin: 29, name: 'GPIO5', type: 'gpio', available: true },
		{ pin: 30, name: 'GND', type: 'ground', available: false },
		{ pin: 31, name: 'GPIO6', type: 'gpio', available: true },
		{ pin: 32, name: 'GPIO12 (PWM)', type: 'gpio', available: true },
		{ pin: 33, name: 'GPIO13 (PWM)', type: 'gpio', available: true },
		{ pin: 34, name: 'GND', type: 'ground', available: false },
		{ pin: 35, name: 'GPIO19 (PWM)', type: 'gpio', available: true },
		{ pin: 36, name: 'GPIO16', type: 'gpio', available: true },
		{ pin: 37, name: 'GPIO26', type: 'gpio', available: true },
		{ pin: 38, name: 'GPIO20 (PWM)', type: 'gpio', available: true },
		{ pin: 39, name: 'GND', type: 'ground', available: false },
		{ pin: 40, name: 'GPIO21 (PWM)', type: 'gpio', available: true }
	];

	let validationErrors = {};

	// Extract GPIO number from pin name (e.g., "GPIO19 (PWM)" -> 19)
	function extractGpioNumber(pinName) {
		const match = pinName.match(/GPIO(\d+)/);
		return match ? parseInt(match[1]) : null;
	}

	// Get GPIO number for a board pin
	function getBoardPinGpio(boardPin) {
		const pin = gpioPinout.find(p => p.pin === boardPin);
		return pin ? extractGpioNumber(pin.name) : null;
	}

	// Find board pin by GPIO number
	function findBoardPinByGpio(gpioNumber) {
		const pin = gpioPinout.find(p => extractGpioNumber(p.name) === gpioNumber);
		return pin ? pin.pin : null;
	}

	function validatePin(pinNumber, pinType) {
		const pin = gpioPinout.find(p => p.pin === pinNumber);
		
		if (!pin) {
			return 'Invalid pin number';
		}
		
		if (!pin.available) {
			return `Pin ${pinNumber} is reserved (${pin.name})`;
		}
		
		// Check for conflicts with other assigned pins (convert GPIO numbers to board pins for comparison)
		const currentBoardPins = [
			findBoardPinByGpio(config.gpio_pin),
			findBoardPinByGpio(config.gpio_power_pin), 
			findBoardPinByGpio(config.gpio_ground_pin)
		].filter(p => p !== null && p !== pinNumber);
		
		if (currentBoardPins.includes(pinNumber)) {
			return 'Pin already in use';
		}
		
		return null;
	}

	function handleConfigChange(key, value) {
		// Convert board pin number to GPIO number for pin-related configs
		if (key.includes('pin') && value !== null) {
			const gpioNumber = getBoardPinGpio(value);
			if (gpioNumber !== null) {
				config = { ...config, [key]: gpioNumber };
			} else {
				config = { ...config, [key]: value };
			}
			
			// Validate using board pin number
			const error = validatePin(value, key);
			validationErrors = { ...validationErrors, [key]: error };
		} else if (key.includes('pin')) {
			// Clear error if pin is set to null
			config = { ...config, [key]: null };
			const { [key]: removed, ...rest } = validationErrors;
			validationErrors = rest;
		} else {
			config = { ...config, [key]: value };
		}
		
		dispatch('change', config);
	}

	function getPinStatus(pinNumber) {
		// Convert GPIO numbers to board pins for comparison
		const dataBoardPin = findBoardPinByGpio(config.gpio_pin);
		const powerBoardPin = findBoardPinByGpio(config.gpio_power_pin);
		const groundBoardPin = findBoardPinByGpio(config.gpio_ground_pin);
		
		if (pinNumber === dataBoardPin) return 'data';
		if (pinNumber === powerBoardPin) return 'power';
		if (pinNumber === groundBoardPin) return 'ground';
		return null;
	}

	function getPinClass(pin) {
		const status = getPinStatus(pin.pin);
		if (status) return `assigned assigned-${status}`;
		if (!pin.available) return 'unavailable';
		return 'available';
	}

	$: hasErrors = Object.values(validationErrors).some(error => error !== null);
	
	// Computed values for select bindings (convert GPIO numbers to board pins for display)
	$: selectedDataPin = findBoardPinByGpio(config.gpio_pin) || config.gpio_pin;
	$: selectedPowerPin = config.gpio_power_pin ? findBoardPinByGpio(config.gpio_power_pin) : null;
	$: selectedGroundPin = config.gpio_ground_pin ? findBoardPinByGpio(config.gpio_ground_pin) : null;
</script>

<div class="gpio-config-panel">
	<div class="config-section">
		<h3>GPIO Pin Configuration</h3>
		
		<div class="pin-configs">
			<div class="pin-config">
				<label for="gpio-data-pin">Data Pin (Required)</label>
				<select
					id="gpio-data-pin"
					bind:value={selectedDataPin}
					on:change={(e) => handleConfigChange('gpio_pin', parseInt(e.target.value))}
					{disabled}
					class:error={validationErrors.gpio_pin}
				>
					{#each gpioPinout.filter(p => p.available) as pin}
						<option value={pin.pin}>Pin {pin.pin} - {pin.name}</option>
					{/each}
				</select>
				{#if validationErrors.gpio_pin}
					<span class="error-message">{validationErrors.gpio_pin}</span>
				{/if}
			</div>

			<div class="pin-config">
				<label for="gpio-power-pin">Power Control Pin (Optional)</label>
				<select
					id="gpio-power-pin"
					bind:value={selectedPowerPin}
					on:change={(e) => handleConfigChange('gpio_power_pin', e.target.value === '' ? null : parseInt(e.target.value))}
					{disabled}
					class:error={validationErrors.gpio_power_pin}
				>
					<option value={null}>None</option>
					{#each gpioPinout.filter(p => p.available) as pin}
						<option value={pin.pin}>Pin {pin.pin} - {pin.name}</option>
					{/each}
				</select>
				{#if validationErrors.gpio_power_pin}
					<span class="error-message">{validationErrors.gpio_power_pin}</span>
				{/if}
			</div>

			<div class="pin-config">
				<label for="gpio-ground-pin">Ground Reference Pin (Optional)</label>
				<select
					id="gpio-ground-pin"
					bind:value={selectedGroundPin}
					on:change={(e) => handleConfigChange('gpio_ground_pin', e.target.value === '' ? null : parseInt(e.target.value))}
					{disabled}
					class:error={validationErrors.gpio_ground_pin}
				>
					<option value={null}>None</option>
					{#each gpioPinout.filter(p => p.available) as pin}
						<option value={pin.pin}>Pin {pin.pin} - {pin.name}</option>
					{/each}
				</select>
				{#if validationErrors.gpio_ground_pin}
					<span class="error-message">{validationErrors.gpio_ground_pin}</span>
				{/if}
			</div>
		</div>

		<div class="signal-config">
			<div class="config-row">
				<label for="signal-level">Signal Level</label>
				<select
					id="signal-level"
					bind:value={config.signal_level}
					on:change={(e) => handleConfigChange('signal_level', parseFloat(e.target.value))}
					{disabled}
				>
					<option value={3.3}>3.3V (Raspberry Pi GPIO)</option>
					<option value={5.0}>5.0V (Arduino/External)</option>
				</select>
			</div>

			<div class="config-row">
				<label for="led-frequency">LED Frequency</label>
				<select
					id="led-frequency"
					bind:value={config.led_frequency}
					on:change={(e) => handleConfigChange('led_frequency', parseInt(e.target.value))}
					{disabled}
				>
					<option value={400000}>400 kHz (Slower, more stable)</option>
					<option value={800000}>800 kHz (Standard)</option>
				</select>
			</div>

			<div class="config-row">
				<label for="led-dma">DMA Channel</label>
				<input
					id="led-dma"
					type="number"
					min="0"
					max="14"
					bind:value={config.led_dma}
					on:input={(e) => handleConfigChange('led_dma', parseInt(e.target.value))}
					{disabled}
				/>
			</div>

			<div class="config-row">
				<label for="led-channel">PWM Channel</label>
				<select
					id="led-channel"
					bind:value={config.led_channel}
					on:change={(e) => handleConfigChange('led_channel', parseInt(e.target.value))}
					{disabled}
				>
					<option value={0}>Channel 0</option>
					<option value={1}>Channel 1</option>
				</select>
			</div>

			<div class="config-row checkbox-row">
				<label for="led-invert">
					<input
						id="led-invert"
						type="checkbox"
						bind:checked={config.led_invert}
						on:change={(e) => handleConfigChange('led_invert', e.target.checked)}
						{disabled}
					/>
					Invert Signal Polarity
				</label>
			</div>
		</div>
	</div>

	<div class="pinout-diagram">
		<h4>Raspberry Pi GPIO Pinout</h4>
		<div class="pinout-grid">
			{#each gpioPinout as pin}
				<div
					class="pin {getPinClass(pin)}"
					title="{pin.name} - {pin.available ? 'Available' : 'Reserved'}"
				>
					<span class="pin-number">{pin.pin}</span>
					<span class="pin-name">{pin.name.split(' ')[0]}</span>
				</div>
			{/each}
		</div>
		<div class="pinout-legend">
			<div class="legend-item">
				<div class="legend-color assigned assigned-data"></div>
				<span>Data Pin</span>
			</div>
			<div class="legend-item">
				<div class="legend-color assigned assigned-power"></div>
				<span>Power Control</span>
			</div>
			<div class="legend-item">
				<div class="legend-color assigned assigned-ground"></div>
				<span>Ground Reference</span>
			</div>
			<div class="legend-item">
				<div class="legend-color available"></div>
				<span>Available</span>
			</div>
			<div class="legend-item">
				<div class="legend-color unavailable"></div>
				<span>Reserved</span>
			</div>
		</div>
	</div>

	{#if hasErrors}
		<div class="validation-summary">
			<h4>⚠️ Configuration Issues</h4>
			<ul>
				{#each Object.entries(validationErrors) as [key, error]}
					{#if error}
						<li>{key.replace('_', ' ')}: {error}</li>
					{/if}
				{/each}
			</ul>
		</div>
	{/if}
</div>

<style>
	.gpio-config-panel {
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

	.pin-configs {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.pin-config {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.pin-config label {
		font-weight: 500;
		color: #333;
		font-size: 0.9rem;
	}

	.pin-config select, .config-row input, .config-row select {
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		background: white;
		font-size: 0.9rem;
	}

	.pin-config select.error, .config-row input.error {
		border-color: #dc3545;
		box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.1);
	}

	.error-message {
		color: #dc3545;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.signal-config {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		padding: 1rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}

	.config-row {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.config-row label {
		font-weight: 500;
		color: #333;
		font-size: 0.9rem;
	}

	.checkbox-row {
		flex-direction: row;
		align-items: center;
	}

	.checkbox-row label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}

	.pinout-diagram {
		padding: 1rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}

	.pinout-diagram h4 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1rem;
		font-weight: 600;
	}

	.pinout-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 2px;
		max-width: 400px;
		margin: 0 auto 1rem auto;
		border: 2px solid #333;
		border-radius: 8px;
		padding: 4px;
		background: #333;
	}

	.pin {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.25rem;
		border-radius: 3px;
		font-size: 0.7rem;
		min-height: 30px;
		justify-content: center;
		cursor: help;
	}

	.pin.available {
		background: #e8f5e8;
		color: #2d5a2d;
		border: 1px solid #4caf50;
	}

	.pin.unavailable {
		background: #f5f5f5;
		color: #666;
		border: 1px solid #ccc;
	}

	.pin.assigned {
		font-weight: 600;
		border-width: 2px;
	}

	.pin.assigned-data {
		background: #e3f2fd;
		color: #1565c0;
		border-color: #2196f3;
	}

	.pin.assigned-power {
		background: #fff3e0;
		color: #e65100;
		border-color: #ff9800;
	}

	.pin.assigned-ground {
		background: #fce4ec;
		color: #ad1457;
		border-color: #e91e63;
	}

	.pin-number {
		font-weight: 600;
		font-size: 0.6rem;
	}

	.pin-name {
		font-size: 0.55rem;
		text-align: center;
		line-height: 1;
	}

	.pinout-legend {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		justify-content: center;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
	}

	.legend-color {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		border: 1px solid #ccc;
	}

	.validation-summary {
		padding: 1rem;
		background: #fff3cd;
		border: 1px solid #ffeaa7;
		border-radius: 6px;
	}

	.validation-summary h4 {
		margin: 0 0 0.5rem 0;
		color: #856404;
		font-size: 1rem;
	}

	.validation-summary ul {
		margin: 0;
		padding-left: 1.5rem;
		color: #856404;
	}

	@media (max-width: 768px) {
		.pin-configs, .signal-config {
			grid-template-columns: 1fr;
		}
		
		.pinout-grid {
			max-width: 300px;
		}
		
		.pin {
			min-height: 25px;
			padding: 0.2rem;
		}
	}
</style>