<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let settings = {
		piano_size: '88-key',
		gpio_pin: 18,
		led_orientation: 'normal'
	};

	let loading = false;
	let message = '';
	let messageType = 'info'; // 'success', 'error', 'info'

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
		await loadSettings();
	});

	async function loadSettings() {
		try {
			const response = await fetch('/api/settings');
			if (response.ok) {
				settings = await response.json();
			} else {
				showMessage('Failed to load settings', 'error');
			}
		} catch (error) {
			console.error('Error loading settings:', error);
			showMessage('Error loading settings', 'error');
		}
	}

	async function saveSettings() {
		loading = true;
		try {
			const response = await fetch('/api/settings', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(settings)
			});

			if (response.ok) {
				showMessage('Settings saved successfully!', 'success');
			} else {
				const error = await response.json();
				showMessage(error.error || 'Failed to save settings', 'error');
			}
		} catch (error) {
			console.error('Error saving settings:', error);
			showMessage('Error saving settings', 'error');
		} finally {
			loading = false;
		}
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

<div class="container mx-auto px-4 py-8 max-w-2xl">
	<div class="bg-white rounded-lg shadow-lg p-6">
		<h1 class="text-3xl font-bold text-gray-800 mb-6">Hardware Settings</h1>

		{#if message}
			<div class="mb-4 p-4 rounded-md {messageType === 'success' ? 'bg-green-100 text-green-700 border border-green-300' : messageType === 'error' ? 'bg-red-100 text-red-700 border border-red-300' : 'bg-blue-100 text-blue-700 border border-blue-300'}">
				{message}
			</div>
		{/if}

		<form on:submit|preventDefault={saveSettings} class="space-y-6">
			<!-- Piano Size Selection -->
			<div>
				<label for="piano_size" class="block text-sm font-medium text-gray-700 mb-2">
					Piano Size
				</label>
				<select
					id="piano_size"
					bind:value={settings.piano_size}
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
				>
					{#each pianoSizes as size}
						<option value={size.value}>{size.label}</option>
					{/each}
				</select>
				<p class="mt-1 text-sm text-gray-500">
					Select the size of your piano keyboard for accurate LED mapping.
				</p>
			</div>

			<!-- GPIO Pin Selection -->
			<div>
				<label for="gpio_pin" class="block text-sm font-medium text-gray-700 mb-2">
					GPIO Pin
				</label>
				<input
					id="gpio_pin"
					type="number"
					min="1"
					max="40"
					bind:value={settings.gpio_pin}
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
				/>
				<p class="mt-1 text-sm text-gray-500">
					GPIO pin number for LED strip data connection (typically 18).
				</p>
			</div>

			<!-- LED Orientation Selection -->
			<div>
				<label for="led_orientation" class="block text-sm font-medium text-gray-700 mb-2">
					LED Orientation
				</label>
				<select
					id="led_orientation"
					bind:value={settings.led_orientation}
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
				>
					{#each orientations as orientation}
						<option value={orientation.value}>{orientation.label}</option>
					{/each}
				</select>
				<p class="mt-1 text-sm text-gray-500">
					Choose how the LED strip is oriented relative to your piano keys.
				</p>
			</div>

			<!-- Save Button -->
			<div class="flex justify-between items-center pt-4">
				<button
					type="button"
					on:click={() => goto('/')}
					class="px-4 py-2 text-gray-600 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={loading}
					class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					{loading ? 'Saving...' : 'Save Settings'}
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	/* Additional custom styles if needed */
</style>