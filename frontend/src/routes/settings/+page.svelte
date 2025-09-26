<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { settings, settingsLoading, settingsError, loadSettings, updateSettings } from '$lib/stores/settings.js';
	import PianoKeyboardSelector from '$lib/components/PianoKeyboardSelector.svelte';
	import GPIOConfigPanel from '$lib/components/GPIOConfigPanel.svelte';
	import LEDStripConfig from '$lib/components/LEDStripConfig.svelte';
	import LEDTestSequence from '$lib/components/LEDTestSequence.svelte';
import ConfigurationManager from '$lib/components/ConfigurationManager.svelte';

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

		{#if message}
			<div class="mx-6 mt-4 p-4 rounded-md {messageType === 'success' ? 'bg-green-100 text-green-700 border border-green-300' : messageType === 'error' ? 'bg-red-100 text-red-700 border border-red-300' : 'bg-blue-100 text-blue-700 border border-blue-300'}">
				{message}
			</div>
		{/if}

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
		<div class="p-6">
			{#if activeTab === 'piano'}
				<PianoKeyboardSelector 
					bind:settings={currentSettings}
					on:change={(e) => handleSettingsChange(e.detail)}
				/>
			{:else if activeTab === 'gpio'}
				<GPIOConfigPanel 
					bind:settings={currentSettings}
					on:change={(e) => handleSettingsChange(e.detail)}
				/>
			{:else if activeTab === 'led'}
				<LEDStripConfig 
					bind:settings={currentSettings}
					on:change={(e) => handleSettingsChange(e.detail)}
				/>
			{:else if activeTab === 'test'}
				<LEDTestSequence 
					bind:settings={currentSettings}
					on:change={(e) => handleSettingsChange(e.detail)}
				/>
			{:else if activeTab === 'config'}
				<ConfigurationManager 
					bind:settings={currentSettings}
					on:change={(e) => handleSettingsChange(e.detail)}
				/>
			{:else if activeTab === 'advanced'}
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
	/* Additional custom styles if needed */
</style>