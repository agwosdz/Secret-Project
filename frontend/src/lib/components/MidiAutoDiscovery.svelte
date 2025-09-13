<script>
	import { onMount, onDestroy } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Discovery state
	let isDiscovering = false;
	let discoveredDevices = [];
	let discoveryProgress = 0;
	let discoveryStatus = 'idle'; // idle, scanning, completed, error
	let lastDiscoveryTime = null;
	let autoDiscoveryEnabled = false;
	let discoveryInterval = null;

	// Discovery settings
	let discoveryTimeout = 10000; // 10 seconds
	let autoDiscoveryIntervalMs = 30000; // 30 seconds
	let includeBonjour = true;
	let includeUPnP = true;
	let customPorts = '5004,5005,21928';

	// Error handling
	let discoveryError = null;

	async function startDiscovery() {
		if (isDiscovering) return;

		isDiscovering = true;
		discoveryStatus = 'scanning';
		discoveryProgress = 0;
		discoveryError = null;
		discoveredDevices = [];

		try {
			// Start discovery process
			const response = await fetch('/api/rtpmidi/discover', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					timeout: discoveryTimeout,
					include_bonjour: includeBonjour,
					include_upnp: includeUPnP,
					custom_ports: customPorts.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p))
				})
			});

			if (!response.ok) {
				throw new Error(`Discovery failed: ${response.statusText}`);
			}

			// Poll for discovery progress
			const pollInterval = setInterval(async () => {
				try {
					const progressResponse = await fetch('/api/rtpmidi/discovery-status');
					if (progressResponse.ok) {
						const progressData = await progressResponse.json();
						discoveryProgress = progressData.progress || 0;
						discoveredDevices = progressData.devices || [];

						if (progressData.completed) {
							clearInterval(pollInterval);
							completeDiscovery();
						}
					}
				} catch (error) {
					console.error('Error polling discovery status:', error);
				}
			}, 500);

			// Set timeout for discovery
			setTimeout(() => {
				clearInterval(pollInterval);
				if (isDiscovering) {
					completeDiscovery();
				}
			}, discoveryTimeout + 1000);

		} catch (error) {
			console.error('Discovery error:', error);
			discoveryError = error.message;
			discoveryStatus = 'error';
			isDiscovering = false;
			dispatch('discoveryError', { error: error.message });
		}
	}

	function completeDiscovery() {
		isDiscovering = false;
		discoveryStatus = 'completed';
		lastDiscoveryTime = new Date();
		dispatch('discoveryCompleted', { 
			devices: discoveredDevices,
			count: discoveredDevices.length
		});
	}

	function stopDiscovery() {
		isDiscovering = false;
		discoveryStatus = 'idle';
		discoveryProgress = 0;
	}

	async function connectToDevice(device) {
		try {
			const response = await fetch('/api/rtpmidi/connect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					host: device.host,
					port: device.port,
					name: device.name
				})
			});

			if (response.ok) {
				const result = await response.json();
				dispatch('deviceConnected', { device, result });
			} else {
				throw new Error(`Connection failed: ${response.statusText}`);
			}
		} catch (error) {
			console.error('Connection error:', error);
			dispatch('connectionError', { device, error: error.message });
		}
	}

	function toggleAutoDiscovery() {
		autoDiscoveryEnabled = !autoDiscoveryEnabled;
		
		if (autoDiscoveryEnabled) {
			startAutoDiscovery();
		} else {
			stopAutoDiscovery();
		}
	}

	function startAutoDiscovery() {
		if (discoveryInterval) return;
		
		discoveryInterval = setInterval(() => {
			if (!isDiscovering) {
				startDiscovery();
			}
		}, autoDiscoveryIntervalMs);
	}

	function stopAutoDiscovery() {
		if (discoveryInterval) {
			clearInterval(discoveryInterval);
			discoveryInterval = null;
		}
	}

	function formatLastDiscovery() {
		if (!lastDiscoveryTime) return 'Never';
		const now = new Date();
		const diff = now - lastDiscoveryTime;
		const minutes = Math.floor(diff / 60000);
		const seconds = Math.floor((diff % 60000) / 1000);
		
		if (minutes > 0) return `${minutes}m ${seconds}s ago`;
		return `${seconds}s ago`;
	}

	function getDeviceTypeIcon(device) {
		if (device.type === 'bonjour') return '🔍';
		if (device.type === 'upnp') return '🌐';
		if (device.type === 'manual') return '⚙️';
		return '📱';
	}

	onMount(() => {
		// Auto-start discovery if enabled
		if (autoDiscoveryEnabled) {
			startAutoDiscovery();
		}
	});

	onDestroy(() => {
		stopAutoDiscovery();
	});
</script>

<div class="auto-discovery">
	<div class="discovery-header">
		<div class="header-info">
			<h3>🔍 Auto-Discovery</h3>
			<div class="discovery-stats">
				<span class="device-count">{discoveredDevices.length} devices found</span>
				<span class="last-scan">Last scan: {formatLastDiscovery()}</span>
			</div>
		</div>
		<div class="discovery-controls">
			<label class="auto-toggle">
				<input type="checkbox" bind:checked={autoDiscoveryEnabled} on:change={toggleAutoDiscovery}>
				<span class="toggle-text">Auto-scan</span>
			</label>
			<button 
				class="scan-button {discoveryStatus}"
				on:click={startDiscovery}
				disabled={isDiscovering}
			>
				{#if isDiscovering}
					<span class="spinner"></span>
					Scanning...
				{:else}
					🔍 Scan Now
				{/if}
			</button>
		</div>
	</div>

	{#if isDiscovering}
		<div class="discovery-progress">
			<div class="progress-bar">
				<div class="progress-fill" style="width: {discoveryProgress}%"></div>
			</div>
			<div class="progress-text">{Math.round(discoveryProgress)}% complete</div>
		</div>
	{/if}

	{#if discoveryError}
		<div class="error-message">
			<span class="error-icon">❌</span>
			{discoveryError}
		</div>
	{/if}

	{#if discoveredDevices.length > 0}
		<div class="discovered-devices">
			<h4>Discovered Devices</h4>
			<div class="device-list">
				{#each discoveredDevices as device}
					<div class="device-item">
						<div class="device-info">
							<div class="device-header">
								<span class="device-icon">{getDeviceTypeIcon(device)}</span>
								<span class="device-name">{device.name}</span>
								<span class="device-type">{device.type}</span>
							</div>
							<div class="device-details">
								<span class="device-host">{device.host}:{device.port}</span>
								{#if device.services}
									<span class="device-services">{device.services.join(', ')}</span>
								{/if}
							</div>
						</div>
						<button 
							class="connect-button"
							on:click={() => connectToDevice(device)}
						>
							🔗 Connect
						</button>
					</div>
				{/each}
			</div>
		</div>
	{:else if discoveryStatus === 'completed'}
		<div class="no-devices">
			<span class="no-devices-icon">🔍</span>
			<span class="no-devices-text">No network MIDI devices found</span>
			<span class="no-devices-hint">Try adjusting discovery settings or ensure devices are on the same network</span>
		</div>
	{/if}

	<!-- Discovery Settings -->
	<details class="discovery-settings">
		<summary>Discovery Settings</summary>
		<div class="settings-content">
			<div class="setting-group">
				<label>
					<input type="checkbox" bind:checked={includeBonjour}>
					Bonjour/mDNS Discovery
				</label>
				<label>
					<input type="checkbox" bind:checked={includeUPnP}>
					UPnP Discovery
				</label>
			</div>
			<div class="setting-group">
				<label>
					Discovery Timeout (ms):
					<input type="number" bind:value={discoveryTimeout} min="5000" max="30000" step="1000">
				</label>
			</div>
			<div class="setting-group">
				<label>
					Auto-Discovery Interval (ms):
					<input type="number" bind:value={autoDiscoveryIntervalMs} min="10000" max="300000" step="5000">
				</label>
			</div>
			<div class="setting-group">
				<label>
					Custom Ports (comma-separated):
					<input type="text" bind:value={customPorts} placeholder="5004,5005,21928">
				</label>
			</div>
		</div>
	</details>
</div>

<style>
	.auto-discovery {
		padding: 1rem;
		background: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 8px;
	}

	.discovery-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
		gap: 1rem;
	}

	.header-info h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #495057;
	}

	.discovery-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.85rem;
		color: #6c757d;
	}

	.discovery-controls {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.auto-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		color: #495057;
		cursor: pointer;
	}

	.scan-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: background-color 0.2s ease;
	}

	.scan-button:hover:not(:disabled) {
		background: #0056b3;
	}

	.scan-button:disabled {
		background: #6c757d;
		cursor: not-allowed;
	}

	.spinner {
		width: 12px;
		height: 12px;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.discovery-progress {
		margin-bottom: 1rem;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e9ecef;
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.progress-fill {
		height: 100%;
		background: #007bff;
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.85rem;
		color: #6c757d;
		text-align: center;
	}

	.error-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem;
		background: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
		border-radius: 6px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.discovered-devices h4 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #495057;
	}

	.device-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.device-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: white;
		border: 1px solid #dee2e6;
		border-radius: 6px;
		gap: 1rem;
	}

	.device-info {
		flex: 1;
		min-width: 0;
	}

	.device-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.device-name {
		font-weight: 600;
		color: #212529;
	}

	.device-type {
		padding: 0.125rem 0.375rem;
		background: #e9ecef;
		color: #495057;
		border-radius: 12px;
		font-size: 0.75rem;
		text-transform: uppercase;
	}

	.device-details {
		display: flex;
		gap: 1rem;
		font-size: 0.85rem;
		color: #6c757d;
	}

	.device-host {
		font-family: monospace;
	}

	.connect-button {
		padding: 0.5rem 0.75rem;
		background: #28a745;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.85rem;
		transition: background-color 0.2s ease;
	}

	.connect-button:hover {
		background: #1e7e34;
	}

	.no-devices {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2rem;
		text-align: center;
		color: #6c757d;
	}

	.no-devices-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.no-devices-text {
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.no-devices-hint {
		font-size: 0.85rem;
		color: #868e96;
	}

	.discovery-settings {
		margin-top: 1rem;
		border-top: 1px solid #dee2e6;
		padding-top: 1rem;
	}

	.discovery-settings summary {
		cursor: pointer;
		font-weight: 500;
		color: #495057;
		margin-bottom: 0.75rem;
	}

	.settings-content {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.setting-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.setting-group label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		color: #495057;
	}

	.setting-group input[type="number"],
	.setting-group input[type="text"] {
		padding: 0.375rem 0.5rem;
		border: 1px solid #ced4da;
		border-radius: 4px;
		font-size: 0.85rem;
		max-width: 200px;
	}

	@media (max-width: 768px) {
		.discovery-header {
			flex-direction: column;
			align-items: stretch;
		}

		.discovery-controls {
			justify-content: space-between;
		}

		.device-item {
			flex-direction: column;
			align-items: stretch;
			gap: 0.75rem;
		}

		.device-details {
			flex-direction: column;
			gap: 0.25rem;
		}
	}
</style>