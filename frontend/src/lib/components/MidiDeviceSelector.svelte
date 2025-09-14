<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { writable } from 'svelte/store';

	const dispatch = createEventDispatcher();

	interface MidiDevice {
		id: number;
		name: string;
		status: 'available' | 'connected' | 'error';
		type: 'usb' | 'network';
	}

	interface DeviceResponse {
		usb_devices: MidiDevice[];
		rtpmidi_sessions: MidiDevice[];
		total_count: number;
	}

	export let selectedDevice: number | null = null;
	export let autoRefresh = true;
	export let refreshInterval = 5000;

	let devices = writable<DeviceResponse>({
		usb_devices: [],
		rtpmidi_sessions: [],
		total_count: 0
	});
	let loading = false;
	let error: string | null = null;
	let refreshTimer: NodeJS.Timeout | null = null;

	onMount(() => {
		fetchDevices();
		if (autoRefresh) {
			startAutoRefresh();
		}

		return () => {
			if (refreshTimer) {
				clearInterval(refreshTimer);
			}
		};
	});

	async function fetchDevices() {
		loading = true;
		error = null;

		try {
			// Use relative URL to work with Vite proxy configuration
			const response = await fetch('/api/midi-input/devices');
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const response_data = await response.json();
			// Extract devices from the backend response format
			const devices_data = response_data.devices || response_data;
			// Ensure the response has the expected structure
			const safeData: DeviceResponse = {
				usb_devices: devices_data.usb_devices || [],
				rtpmidi_sessions: devices_data.rtpmidi_sessions || [],
				total_count: (devices_data.usb_devices?.length || 0) + (devices_data.rtpmidi_sessions?.length || 0)
			};
			devices.set(safeData);
			dispatch('devicesUpdated', safeData);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to fetch devices';
			console.error('Error fetching MIDI devices:', err);
		} finally {
			loading = false;
		}
	}

	function startAutoRefresh() {
		if (refreshTimer) clearInterval(refreshTimer);
		refreshTimer = setInterval(fetchDevices, refreshInterval);
	}

	function stopAutoRefresh() {
		if (refreshTimer) {
			clearInterval(refreshTimer);
			refreshTimer = null;
		}
	}

	function selectDevice(device: MidiDevice) {
		selectedDevice = device.id;
		dispatch('deviceSelected', device);
	}

	function getDeviceStatusClass(status: string): string {
		switch (status) {
			case 'connected': return 'status-connected';
			case 'available': return 'status-available';
			case 'error': return 'status-error';
			default: return 'status-unknown';
		}
	}

	function getDeviceTypeIcon(type: string): string {
		return type === 'usb' ? '🔌' : '🌐';
	}

	$: allDevices = [...($devices.usb_devices || []), ...($devices.rtpmidi_sessions || [])];
</script>

<div class="midi-device-selector">
	<div class="header">
		<h3>🎹 MIDI Devices</h3>
		<div class="controls">
			<button 
				class="refresh-btn" 
				on:click={fetchDevices} 
				disabled={loading}
				title="Refresh device list"
			>
				{loading ? '⟳' : '🔄'}
			</button>
			<button 
				class="auto-refresh-btn {autoRefresh ? 'active' : ''}" 
				on:click={() => {
					autoRefresh = !autoRefresh;
					if (autoRefresh) startAutoRefresh();
					else stopAutoRefresh();
				}}
				title="Toggle auto-refresh"
			>
				📡
			</button>
		</div>
	</div>

	{#if error}
		<div class="error-message">
			⚠️ {error}
			<button class="retry-btn" on:click={fetchDevices}>Retry</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading">Loading devices...</div>
	{/if}

	<div class="device-sections">
		{#if $devices.usb_devices && $devices.usb_devices.length > 0}
			<div class="device-section">
				<h4>🔌 USB Devices ({$devices.usb_devices.length})</h4>
				<div class="device-list">
					{#each $devices.usb_devices as device}
						<div 
							class="device-item {selectedDevice === device.id ? 'selected' : ''} {getDeviceStatusClass(device.status)}"
							on:click={() => selectDevice(device)}
							role="button"
							tabindex="0"
							on:keydown={(e) => e.key === 'Enter' && selectDevice(device)}
						>
							<div class="device-info">
								<span class="device-icon">{getDeviceTypeIcon(device.type)}</span>
								<span class="device-name">{device.name}</span>
							</div>
							<div class="device-status">
								<span class="status-indicator"></span>
								<span class="status-text">{device.status}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if $devices.rtpmidi_sessions && $devices.rtpmidi_sessions.length > 0}
			<div class="device-section">
				<h4>🌐 Network Devices ({$devices.rtpmidi_sessions.length})</h4>
				<div class="device-list">
					{#each $devices.rtpmidi_sessions as device}
						<div 
							class="device-item {selectedDevice === device.id ? 'selected' : ''} {getDeviceStatusClass(device.status)}"
							on:click={() => selectDevice(device)}
							role="button"
							tabindex="0"
							on:keydown={(e) => e.key === 'Enter' && selectDevice(device)}
						>
							<div class="device-info">
								<span class="device-icon">{getDeviceTypeIcon(device.type)}</span>
								<span class="device-name">{device.name}</span>
							</div>
							<div class="device-status">
								<span class="status-indicator"></span>
								<span class="status-text">{device.status}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if allDevices.length === 0 && !loading}
			<div class="no-devices">
				<div class="no-devices-icon">🎹</div>
				<div class="no-devices-text">
					<p>No MIDI devices found</p>
					<p class="hint">Connect a USB MIDI device or configure network MIDI</p>
				</div>
			</div>
		{/if}
	</div>

	{#if selectedDevice}
		<div class="selected-device-info">
			<span class="label">Selected:</span>
			<span class="selected-name">
				{allDevices.find(d => d.id === selectedDevice)?.name || 'Unknown Device'}
			</span>
		</div>
	{/if}


</div>

<style>
	.midi-device-selector {
		background: var(--bg-secondary, #f8f9fa);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 8px;
		padding: 16px;
		max-width: 500px;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.header h3 {
		margin: 0;
		font-size: 1.1rem;
		color: var(--text-primary, #2c3e50);
	}

	.controls {
		display: flex;
		gap: 8px;
	}

	.refresh-btn, .auto-refresh-btn {
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 4px;
		padding: 6px 8px;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.2s ease;
	}

	.refresh-btn:hover, .auto-refresh-btn:hover {
		background: var(--bg-hover, #f1f3f4);
	}

	.refresh-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		animation: spin 1s linear infinite;
	}

	.auto-refresh-btn.active {
		background: var(--accent-color, #007bff);
		color: white;
		border-color: var(--accent-color, #007bff);
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 4px;
		padding: 12px;
		margin-bottom: 16px;
		color: #c33;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.retry-btn {
		background: #c33;
		color: white;
		border: none;
		border-radius: 4px;
		padding: 4px 8px;
		cursor: pointer;
		font-size: 12px;
	}

	.loading {
		text-align: center;
		padding: 20px;
		color: var(--text-secondary, #6c757d);
		font-style: italic;
	}

	.device-section {
		margin-bottom: 20px;
	}

	.device-section h4 {
		margin: 0 0 8px 0;
		font-size: 0.9rem;
		color: var(--text-secondary, #6c757d);
		font-weight: 600;
	}

	.device-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.device-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px;
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.device-item:hover {
		background: var(--bg-hover, #f1f3f4);
		border-color: var(--accent-color, #007bff);
	}

	.device-item.selected {
		background: var(--accent-light, #e3f2fd);
		border-color: var(--accent-color, #007bff);
		box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
	}

	.device-info {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.device-icon {
		font-size: 16px;
	}

	.device-name {
		font-weight: 500;
		color: var(--text-primary, #2c3e50);
	}

	.device-status {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #ccc;
	}

	.status-connected .status-indicator {
		background: #28a745;
		box-shadow: 0 0 4px rgba(40, 167, 69, 0.5);
	}

	.status-available .status-indicator {
		background: #ffc107;
	}

	.status-error .status-indicator {
		background: #dc3545;
	}

	.status-text {
		font-size: 12px;
		color: var(--text-secondary, #6c757d);
		text-transform: capitalize;
	}

	.no-devices {
		text-align: center;
		padding: 40px 20px;
		color: var(--text-secondary, #6c757d);
	}

	.no-devices-icon {
		font-size: 48px;
		margin-bottom: 16px;
		opacity: 0.5;
	}

	.no-devices-text p {
		margin: 8px 0;
	}

	.no-devices-text .hint {
		font-size: 0.9rem;
		opacity: 0.8;
	}

	.selected-device-info {
		margin-top: 16px;
		padding: 12px;
		background: var(--accent-light, #e3f2fd);
		border-radius: 6px;
		border-left: 4px solid var(--accent-color, #007bff);
	}

	.selected-device-info .label {
		font-weight: 600;
		color: var(--text-secondary, #6c757d);
	}

	.selected-device-info .selected-name {
		color: var(--text-primary, #2c3e50);
		font-weight: 500;
	}
</style>