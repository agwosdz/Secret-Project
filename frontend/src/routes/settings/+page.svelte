<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { settings, settingsLoading, settingsError, loadSettings, updateSettings } from '$lib/stores/settings.js';
	import PianoKeyboardSelector from '$lib/components/PianoKeyboardSelector.svelte';
	import GPIOConfigPanel from '$lib/components/GPIOConfigPanel.svelte';
	import LEDStripConfig from '$lib/components/LEDStripConfig.svelte';
	import LEDTestSequence from '$lib/components/LEDTestSequence.svelte';
	import ConfigurationManager from '$lib/components/ConfigurationManager.svelte';
	import DashboardControls from '$lib/components/DashboardControls.svelte';
	import SettingsSection from '$lib/components/SettingsSection.svelte';
	import SettingsValidationMessage from '$lib/components/SettingsValidationMessage.svelte';

	// Component state
	let message = '';
	let messageType = 'info';
	let activeTab = 'piano';
	let hasUnsavedChanges = false;
	let originalSettings = {};

	// Reactive statements
	$: loading = $settingsLoading;
	$: error = $settingsError;
	$: currentSettings = $settings;

	// Watch for changes to detect unsaved changes
	$: {
		if (Object.keys(originalSettings).length > 0) {
			hasUnsavedChanges = JSON.stringify(currentSettings) !== JSON.stringify(originalSettings);
		}
	}

	const tabs = [
		{ id: 'piano', label: 'Piano Setup', icon: '🎹' },
		{ id: 'gpio', label: 'GPIO Config', icon: '🔌' },
		{ id: 'led', label: 'LED Strip', icon: '💡' },
		{ id: 'mapping', label: 'Key Mapping', icon: '🗂️' },
    { id: 'test', label: 'LED Test', icon: '🧪' },
    { id: 'advanced', label: 'Advanced', icon: '⚙️' },
    { id: 'config', label: 'Config Management', icon: '📁' }
  ];

	const pianoSizes = [
		{ value: '25-key', label: '25 Key (2 Octaves)' },
		{ value: '37-key', label: '37 Key (3 Octaves)' },
		{ value: '49-key', label: '49 Key (4 Octaves)' },
		{ value: '61-key', label: '61 Key (5 Octaves)' },
		{ value: '76-key', label: '76 Key (6+ Octaves)' },
		{ value: '88-key', label: '88 Key (Full Piano)' }
	];

	const orientations = [
		{ value: 'normal', label: 'Normal (Low to High)' },
		{ value: 'reversed', label: 'Reversed (High to Low)' }
	];

	onMount(async () => {
		await loadSettingsData();
	});

	async function loadSettingsData() {
		try {
			await loadSettings();
			originalSettings = JSON.parse(JSON.stringify($settings));
			hasUnsavedChanges = false;
		} catch (error) {
			console.error('Error loading settings:', error);
			showMessage('Error loading settings', 'error');
		}
	}

	async function saveSettings() {
		try {
			await updateSettings(currentSettings);
			originalSettings = JSON.parse(JSON.stringify(currentSettings));
			hasUnsavedChanges = false;
			showMessage('Settings saved successfully!', 'success');
		} catch (error) {
			console.error('Error saving settings:', error);
			showMessage(error.message || 'Failed to save settings', 'error');
		}
	}

function resetSettings() {
	if (confirm('Are you sure you want to reset all changes?')) {
		// Reset to original settings by updating the store
		updateSettings(originalSettings);
		hasUnsavedChanges = false;
		showMessage('Settings reset to last saved state', 'info');
	}
}

async function testHardware() {
	try {
		showMessage('Testing hardware configuration...', 'info');
		
		const response = await fetch('/api/test-hardware', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(currentSettings)
		});

		if (response.ok) {
			const result = await response.json();
			showMessage(`Hardware test ${result.success ? 'passed' : 'failed'}: ${result.message}`, result.success ? 'success' : 'error');
		} else {
			showMessage('Hardware test failed', 'error');
		}
	} catch (error) {
		console.error('Error testing hardware:', error);
		showMessage('Error testing hardware', 'error');
	}
}

function handleSettingsChange(newSettings) {
	updateSettings({ ...currentSettings, ...newSettings });
}

function handleLEDSettingsChange(newLEDSettings) {
	// Map the enhanced LED settings back to the backend format
	// Group all LED settings under the 'led' category as expected by the backend schema
	const updatedSettings = {
		...currentSettings,
		led: {
			...currentSettings.led,
			enabled: currentSettings.led?.enabled ?? true,
			led_count: newLEDSettings.ledCount,
			max_led_count: newLEDSettings.maxLedCount,
			led_type: newLEDSettings.ledType,
			led_orientation: newLEDSettings.ledOrientation,
			led_strip_type: newLEDSettings.ledStripType,
			power_supply_voltage: newLEDSettings.powerSupplyVoltage,
			power_supply_current: newLEDSettings.powerSupplyCurrent,
			brightness: newLEDSettings.brightness / 100, // Convert from 0-100 to 0-1 for backend
			color_profile: newLEDSettings.colorProfile,
			performance_mode: newLEDSettings.performanceMode,
			gamma_correction: newLEDSettings.advancedSettings?.gamma,
			white_balance: newLEDSettings.advancedSettings?.whiteBalance,
			color_temperature: newLEDSettings.advancedSettings?.colorTemp,
			dither_enabled: newLEDSettings.advancedSettings?.dither,
			update_rate: newLEDSettings.advancedSettings?.updateRate,
			power_limiting_enabled: newLEDSettings.advancedSettings?.powerLimiting,
			max_power_watts: newLEDSettings.advancedSettings?.maxPower,
			thermal_protection_enabled: newLEDSettings.advancedSettings?.thermalProtection,
			max_temperature_celsius: newLEDSettings.advancedSettings?.maxTemperature
		}
	};
	updateSettings(updatedSettings);
}

function showMessage(text, type) {
	message = text;
	messageType = type;
	setTimeout(() => {
		message = '';
	}, 5000);
}
</script>

<svelte:head>
	<title>Settings - Piano LED</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
	<div class="bg-white rounded-lg shadow-lg">
		<div class="p-6 border-b border-gray-200">
			<h1 class="text-3xl font-bold text-gray-800 mb-2">Piano LED Configuration</h1>
			<p class="text-gray-600">Configure your piano LED system hardware and settings</p>
		</div>

		<div class="mx-6 mt-4">
			<SettingsValidationMessage 
				type={messageType} 
				message={message} 
				dismissible={true}
				on:dismiss={() => message = ''}
			/>
		</div>

		<!-- Tab Navigation -->
		<div class="border-b border-gray-200">
			<nav class="flex space-x-8 px-6" aria-label="Tabs">
				{#each tabs as tab}
					<button
						on:click={() => activeTab = tab.id}
						class="{activeTab === tab.id ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
					>
						<span class="mr-2">{tab.icon}</span>
						{tab.label}
					</button>
				{/each}
			</nav>
		</div>

		<!-- Tab Content -->
		<div class="p-6 space-y-6">
			{#if activeTab === 'piano'}
				<SettingsSection
					title="Piano Configuration"
					description="Configure your piano keyboard settings and key mapping"
					icon="🎹"
					loading={loading}
					error={error}
					hasUnsavedChanges={hasUnsavedChanges}
					on:save={() => saveSettings()}
					on:reset={() => resetSettings()}
				>
					<PianoKeyboardSelector 
						settings={{
							piano: {
								size: currentSettings.piano_size || '88-key',
								keys: currentSettings.piano_keys || 88,
								octaves: currentSettings.piano_octaves || 7,
								startNote: currentSettings.piano_start_note || 'A0',
								endNote: currentSettings.piano_end_note || 'C8',
								keyMapping: currentSettings.key_mapping_mode || 'chromatic'
							},
							led: {
								ledCount: currentSettings.led_count || 246,
								ledOrientation: currentSettings.led_orientation || 'normal'
							}
						}}
						on:change={(e) => handleSettingsChange(e.detail)}
					/>
				</SettingsSection>
			{:else if activeTab === 'gpio'}
				<SettingsSection
					title="GPIO Configuration"
					description="Configure GPIO pins and hardware settings for LED control"
					icon="🔌"
					loading={loading}
					error={error}
					hasUnsavedChanges={hasUnsavedChanges}
					on:save={() => saveSettings()}
					on:reset={() => resetSettings()}
				>
					<GPIOConfigPanel 
						settings={{
							gpio_pin: currentSettings.gpio_pin || 19,
							gpio_power_pin: currentSettings.gpio_power_pin || null,
							gpio_ground_pin: currentSettings.gpio_ground_pin || null,
							signal_level: currentSettings.signal_level || 3.3,
							led_frequency: currentSettings.led_frequency || 800000,
							dma_channel: currentSettings.dma_channel || 10,
							auto_detect_hardware: currentSettings.auto_detect_hardware || false,
							validate_gpio_pins: currentSettings.validate_gpio_pins || true,
							hardware_test_enabled: currentSettings.hardware_test_enabled || false,
							gpio_pull_up: currentSettings.gpio_pull_up || [],
							gpio_pull_down: currentSettings.gpio_pull_down || [],
							pwm_range: currentSettings.pwm_range || 4096,
							spi_speed: currentSettings.spi_speed || 8000000
						}}
						on:change={(e) => handleSettingsChange(e.detail)}
					/>
				</SettingsSection>
			{:else if activeTab === 'led'}
				<SettingsSection
					title="LED Strip Configuration"
					description="Configure LED strip settings, power management, and visual effects"
					icon="💡"
					loading={loading}
					error={error}
					hasUnsavedChanges={hasUnsavedChanges}
					on:save={() => saveSettings()}
					on:reset={() => resetSettings()}
				>
				<LEDStripConfig 
					settings={{
						ledCount: currentSettings.led?.ledCount || currentSettings.led?.led_count || currentSettings.led?.count || currentSettings.led_count || 246,
						maxLedCount: currentSettings.led?.max_led_count || currentSettings.max_led_count || 300,
						ledType: currentSettings.led?.ledType || currentSettings.led?.led_type || currentSettings.led_type || 'WS2812B',
						ledOrientation: currentSettings.led?.ledOrientation || currentSettings.led?.led_orientation || currentSettings.led_orientation || 'normal',
						ledStripType: currentSettings.led?.led_strip_type || currentSettings.led_strip_type || 'WS2811_STRIP_GRB',
						powerSupplyVoltage: currentSettings.led?.power_supply_voltage || currentSettings.power_supply_voltage || 5.0,
						powerSupplyCurrent: currentSettings.led?.power_supply_current || currentSettings.power_supply_current || 10.0,
						brightness: (currentSettings.led?.brightness || currentSettings.brightness || 0.5) * 100, // Convert from 0-1 to 0-100 for frontend
						colorProfile: currentSettings.led?.color_profile || currentSettings.color_profile || 'standard',
						performanceMode: currentSettings.led?.performance_mode || currentSettings.performance_mode || 'balanced',
						advancedSettings: {
							gamma: currentSettings.led?.gammaCorrection || currentSettings.led?.gamma_correction || currentSettings.gamma_correction || 2.2,
							whiteBalance: currentSettings.led?.white_balance || currentSettings.white_balance || { r: 1.0, g: 1.0, b: 1.0 },
							colorTemp: currentSettings.led?.color_temperature || currentSettings.color_temperature || 6500,
							dither: currentSettings.led?.dither_enabled || currentSettings.dither_enabled || true,
							updateRate: currentSettings.led?.update_rate || currentSettings.update_rate || 60,
							powerLimiting: currentSettings.led?.power_limiting_enabled || currentSettings.power_limiting_enabled || false,
							maxPower: currentSettings.led?.max_power_watts || currentSettings.max_power_watts || 100,
							thermalProtection: currentSettings.led?.thermal_protection_enabled || currentSettings.thermal_protection_enabled || true,
							maxTemperature: currentSettings.led?.max_temperature_celsius || currentSettings.max_temperature_celsius || 85
						}
					}}
					on:configChange={(e) => handleLEDSettingsChange(e.detail)}
				/>
				</SettingsSection>
			{:else if activeTab === 'test'}
				<SettingsSection
					title="LED Testing & Diagnostics"
					description="Test LED functionality and run diagnostic sequences"
					icon="🧪"
					loading={loading}
					error={error}
					showActions={false}
				>
					<div class="led-test-container">
						<LEDTestSequence 
							bind:settings={currentSettings}
							on:change={(e) => handleSettingsChange(e.detail)}
						/>
						
						<!-- Manual LED Control Section -->
						<div class="manual-control-section">
							<h3 class="text-lg font-medium text-gray-900 mb-4">Manual LED Control</h3>
							<p class="text-sm text-gray-600 mb-6">Test individual LEDs and patterns for troubleshooting and validation.</p>
							
							<div class="manual-controls-wrapper">
								<DashboardControls 
									connected={true}
									ledCount={currentSettings.led?.ledCount || 246}
									on:ledTest={(e) => console.log('LED Test:', e.detail)}
									on:patternTest={(e) => console.log('Pattern Test:', e.detail)}
									on:ledCountChange={(e) => console.log('LED Count Change:', e.detail)}
								/>
							</div>
						</div>
					</div>
				</SettingsSection>
			{:else if activeTab === 'config'}
				<SettingsSection
					title="Configuration Management"
					description="Import, export, and manage configuration presets"
					icon="📁"
					loading={loading}
					error={error}
					showActions={false}
				>
					<ConfigurationManager 
						bind:settings={currentSettings}
						on:change={(e) => handleSettingsChange(e.detail)}
					/>
				</SettingsSection>
			{:else if activeTab === 'advanced'}
				<SettingsSection
					title="Advanced Settings"
					description="Fine-tune color correction, gamma, and performance settings"
					icon="⚙️"
					loading={loading}
					error={error}
					hasUnsavedChanges={hasUnsavedChanges}
					on:save={() => saveSettings()}
					on:reset={() => resetSettings()}
				>
				<div class="space-y-6">
					<h3 class="text-lg font-medium text-gray-900">Advanced Settings</h3>
					
					<!-- Color Temperature -->
					<div>
						<label for="color_temperature" class="block text-sm font-medium text-gray-700 mb-2">
							Color Temperature (K)
						</label>
						<input
							id="color_temperature"
							type="number"
							min="2700"
							max="10000"
							step="100"
							bind:value={currentSettings.color_temperature}
							on:input={() => handleSettingsChange({})}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
						<p class="mt-1 text-sm text-gray-500">
							Adjust the color temperature of white light (2700K = warm, 6500K = daylight, 10000K = cool)
						</p>
					</div>

					<!-- Gamma Correction -->
					<div>
						<label for="gamma_correction" class="block text-sm font-medium text-gray-700 mb-2">
							Gamma Correction
						</label>
						<input
							id="gamma_correction"
							type="number"
							min="1.0"
							max="3.0"
							step="0.1"
							bind:value={currentSettings.gamma_correction}
							on:input={() => handleSettingsChange({})}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
						<p class="mt-1 text-sm text-gray-500">
							Gamma correction for more natural color perception (2.2 is standard)
						</p>
					</div>

					<!-- Hardware Detection -->
					<div class="space-y-4">
						<h4 class="text-md font-medium text-gray-900">Hardware Detection</h4>
						
						<div class="flex items-center">
							<input
								id="auto_detect_hardware"
								type="checkbox"
								bind:checked={currentSettings.auto_detect_hardware}
								on:change={() => handleSettingsChange({})}
								class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
							/>
							<label for="auto_detect_hardware" class="ml-2 block text-sm text-gray-900">
								Auto-detect hardware configuration
							</label>
						</div>

						<div class="flex items-center">
							<input
								id="validate_gpio_pins"
								type="checkbox"
								bind:checked={currentSettings.validate_gpio_pins}
								on:change={() => handleSettingsChange({})}
								class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
							/>
							<label for="validate_gpio_pins" class="ml-2 block text-sm text-gray-900">
								Validate GPIO pin assignments
							</label>
						</div>

						<div class="flex items-center">
							<input
								id="hardware_test_enabled"
								type="checkbox"
								bind:checked={currentSettings.hardware_test_enabled}
								on:change={() => handleSettingsChange({})}
								class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
							/>
							<label for="hardware_test_enabled" class="ml-2 block text-sm text-gray-900">
								Enable hardware testing
							</label>
						</div>
					</div>
				</div>
				</SettingsSection>
			{:else if activeTab === 'mapping'}
				<SettingsSection
					title="Key Mapping Configuration"
					description="Configure how piano keys map to LED positions"
					icon="🗂️"
					loading={loading}
					error={error}
					hasUnsavedChanges={hasUnsavedChanges}
					on:save={() => saveSettings()}
					on:reset={() => resetSettings()}
				>
					<div class="space-y-6">
						<p class="text-gray-600">Key mapping configuration will be available in a future update.</p>
					</div>
				</SettingsSection>
			{/if}
		</div>

		<!-- Action Buttons -->
		<div class="bg-gray-50 px-6 py-4 flex justify-between items-center rounded-b-lg">
			<div class="flex space-x-3">
				<button
					type="button"
					on:click={() => goto('/')}
					class="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
				>
					Back to Home
				</button>
				
				{#if hasUnsavedChanges}
					<button
						type="button"
						on:click={resetSettings}
						class="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
					>
						Reset Changes
					</button>
				{/if}
			</div>

			<div class="flex space-x-3">
				{#if currentSettings.hardware_test_enabled}
					<button
						type="button"
						on:click={testHardware}
						disabled={loading}
						class="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						{loading ? 'Testing...' : 'Test Hardware'}
					</button>
				{/if}
				
				<button
					type="button"
					on:click={saveSettings}
					disabled={loading || !hasUnsavedChanges}
					class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					{loading ? 'Saving...' : hasUnsavedChanges ? 'Save Settings' : 'Settings Saved'}
				</button>
			</div>
		</div>
	</div>
</div>

<style>
	/* LED Test Container Styles */
	.led-test-container {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.manual-control-section {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-top: 1rem;
	}

	.manual-controls-wrapper {
		background: white;
		border-radius: 0.375rem;
		padding: 1rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.led-test-container {
			gap: 1rem;
		}
		
		.manual-control-section {
			padding: 1rem;
		}
		
		.manual-controls-wrapper {
			padding: 0.75rem;
		}
	}
</style>