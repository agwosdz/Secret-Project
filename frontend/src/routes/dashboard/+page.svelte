<script>
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { settings, getSetting } from '$lib/stores/settings.js';
	import LEDVisualization from '$lib/components/LEDVisualization.svelte';
	import DashboardControls from '$lib/components/DashboardControls.svelte';
	import PerformanceMonitor from '$lib/components/PerformanceMonitor.svelte';
	import MidiDeviceSelector from '$lib/components/MidiDeviceSelector.svelte';
	import NetworkMidiConfig from '$lib/components/NetworkMidiConfig.svelte';
	import MidiConnectionStatus from '$lib/components/MidiConnectionStatus.svelte';
	
	// Visualization toggle
	let visualizationEnabled = true;

	// WebSocket connection for real-time LED updates
	let websocket = null;
	let connectionStatus = 'disconnected';
	let reconnectAttempts = 0;
	let connectionError = null;
	let lastConnectionTime = null;
	const maxReconnectAttempts = 5;

	// System status from backend dashboard endpoint
	let systemStatus = null;
	let systemStatusLoading = true;
	let systemStatusError = null;

	// LED state management
	let ledState = [];
	let ledCount = 246; // Default LED count, configurable
	let performanceMetrics = {
		update_frequency: 0,
		latency_ms: 0,
		connection_health: 'unknown'
	};

	// Performance tracking
	let lastUpdateTime = 0;
	let updateCount = 0;
	let fpsInterval;
	let connectionHealthInterval;

	// MIDI device management
	let selectedMidiDevice = null;
	let midiDevicesExpanded = false;
	let networkMidiExpanded = false;

	// MIDI connection status
	let usbMidiStatus = {
		connected: false,
		deviceName: null,
		lastActivity: null,
		messageCount: 0
	};

	let networkMidiStatus = {
		connected: false,
		activeSessions: [],
		lastActivity: null,
		messageCount: 0
	};

	// Initialize LED state with default values
	function initializeLEDState(count) {
		ledState = [];
		for (let i = 0; i < count; i++) {
			ledState.push({
				index: i,
				r: 0,
				g: 0,
				b: 0,
				brightness: 0
			});
		}
	}

	// Initialize with default LED count
	initializeLEDState(ledCount);

	onMount(() => {
		initializeWebSocket();
		startPerformanceTracking();
		startConnectionHealthCheck();
		fetchSystemStatus();
		
		// Fetch saved LED count from backend settings
		fetchLEDCount();
	});

	onDestroy(() => {
		if (websocket) {
			websocket.close();
		}
		if (fpsInterval) {
			clearInterval(fpsInterval);
		}
		if (connectionHealthInterval) {
			clearInterval(connectionHealthInterval);
		}
	});

	function initializeWebSocket() {
		try {
			// Use Socket.IO client if available, otherwise fallback to WebSocket
			if (typeof io !== 'undefined') {
				websocket = io();
				
				websocket.on('connect', () => {
					console.log('Dashboard WebSocket connected');
					connectionStatus = 'connected';
					reconnectAttempts = 0;
					connectionError = null;
					lastConnectionTime = new Date();
					performanceMetrics.connection_health = 'connected';
					// Subscribe to LED updates
					websocket.emit('subscribe_led_updates');
				});
				
				websocket.on('led_update', (data) => {
				updateLEDState(data);
			});
			
			websocket.on('led_count_updated', (data) => {
				console.log('LED count updated:', data);
				// Update local LED count if different
				if (data.ledCount && data.ledCount !== ledCount) {
					ledCount = data.ledCount;
					initializeLEDState(ledCount);
				}
			});
			
			websocket.on('midi_input_status', (data) => {
				console.log('MIDI input status:', data);
				// Handle MIDI device status updates
				if (systemStatus && systemStatus.system_status) {
					systemStatus.system_status.midi_input_active = data.active;
					systemStatus.system_status.midi_device_name = data.device_name;
				}
			});
			
			websocket.on('midi_input', (data) => {
				console.log('MIDI input event:', data);
				// Handle real-time MIDI input events
				// The LED updates will come through the led_update event
			});
			
			websocket.on('unified_midi_event', (data) => {
				console.log('Unified MIDI event:', data);
				// Handle unified MIDI events from the manager
			});
			
			websocket.on('disconnect', (reason) => {
					console.log('Dashboard WebSocket disconnected:', reason);
					connectionStatus = 'disconnected';
					connectionError = `Disconnected: ${reason}`;
					performanceMetrics.connection_health = 'disconnected';
					attemptReconnect();
				});
				
				websocket.on('error', (error) => {
					console.error('Dashboard WebSocket error:', error);
					connectionStatus = 'error';
					connectionError = `Socket error: ${error.message || error}`;
					performanceMetrics.connection_health = 'error';
				});
			} else {
				console.log('Socket.IO not available for dashboard');
				connectionStatus = 'unavailable';
				connectionError = 'Socket.IO library not available';
				performanceMetrics.connection_health = 'unavailable';
			}
		} catch (error) {
			console.error('Failed to initialize dashboard WebSocket:', error);
			connectionStatus = 'error';
			connectionError = `Initialization failed: ${error.message}`;
			performanceMetrics.connection_health = 'error';
		}
	}

	function updateLEDState(data) {
		const updateStartTime = performance.now();
		
		try {
			if (data.leds && Array.isArray(data.leds)) {
				ledState = data.leds;
			}
			if (data.performance) {
				performanceMetrics = {
					...performanceMetrics,
					...data.performance,
					connection_health: connectionStatus
				};
			}
			
			// Calculate latency
			const latency = performance.now() - updateStartTime;
			performanceMetrics.latency_ms = Math.round(latency);
			
			// Track update frequency
			updateCount++;
			lastUpdateTime = performance.now();
			
		} catch (error) {
			console.error('Error handling LED update:', error);
			connectionError = `Update error: ${error.message}`;
		}
	}

	function attemptReconnect() {
		if (reconnectAttempts < maxReconnectAttempts) {
			reconnectAttempts++;
			connectionStatus = 'reconnecting';
			connectionError = `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`;
			performanceMetrics.connection_health = 'reconnecting';
			setTimeout(() => {
				initializeWebSocket();
			}, 2000 * reconnectAttempts); // Exponential backoff
		} else {
			connectionStatus = 'failed';
			connectionError = `Failed to reconnect after ${maxReconnectAttempts} attempts`;
			performanceMetrics.connection_health = 'failed';
		}
	}

	function startPerformanceTracking() {
		fpsInterval = setInterval(() => {
			// Calculate FPS based on update count
			performanceMetrics.update_frequency = updateCount;
			updateCount = 0;
		}, 1000);
	}

	function startConnectionHealthCheck() {
		connectionHealthInterval = setInterval(() => {
			// Update connection health based on recent activity
			if (connectionStatus === 'connected') {
				const timeSinceLastUpdate = performance.now() - lastUpdateTime;
				if (timeSinceLastUpdate > 5000) {
					// No updates for 5 seconds, might be stale
					performanceMetrics.connection_health = 'stale';
				} else {
					performanceMetrics.connection_health = 'connected';
				}
			}
		}, 2000);
	}

	// Manual reconnection function
	function manualReconnect() {
		if (websocket) {
			websocket.close();
		}
		connectionError = null;
		reconnectAttempts = 0;
		initializeWebSocket();
	}

	// Handle manual LED testing from controls
	function handleLEDTest(event) {
		const { ledIndex, color, brightness } = event.detail;
		if (websocket && connectionStatus === 'connected') {
			websocket.emit('test_led', {
				index: ledIndex,
				r: color.r,
				g: color.g,
				b: color.b,
				brightness: brightness
			});
		}
	}

	// Handle pattern testing
	function handlePatternTest(event) {
		const { pattern, duration } = event.detail;
		if (websocket && connectionStatus === 'connected') {
			websocket.emit('test_pattern', {
				pattern: pattern,
				duration_ms: duration
			});
		}
	}

	// Handle LED count change
	function handleLEDCountChange(event) {
		const newLedCount = event.detail.ledCount;
		if (newLedCount !== ledCount) {
			ledCount = newLedCount;
			initializeLEDState(ledCount);
			
			// Notify backend of LED count change
			if (websocket && connectionStatus === 'connected') {
				websocket.emit('led_count_change', {
					ledCount: ledCount
				});
				
				// Provide visual feedback by illuminating LEDs incrementally
				// First clear all LEDs
				websocket.emit('test_led', {
					index: -1, // -1 indicates all LEDs
					r: 0,
					g: 0,
					b: 0,
					brightness: 0
				});
				
				// Then illuminate LEDs incrementally to show the new count
				setTimeout(() => {
					// Test each LED sequentially with a delay
					for (let i = 0; i < ledCount; i++) {
						setTimeout(() => {
							websocket.emit('test_led', {
								index: i,
								r: 0,
								g: 255,
								b: 0,
								brightness: 0.8
							});
						}, i * 10); // Fast illumination
					}
				}, 100);
			}
		}
	}

	// Handle test all LEDs functionality
	function handleTestAll(event) {
		const { color, brightness, delay, ledCount: testLedCount } = event.detail;
		const actualLedCount = testLedCount || ledCount;
		
		if (websocket && connectionStatus === 'connected') {
			// Test each LED sequentially with a delay
			for (let i = 0; i < actualLedCount; i++) {
				setTimeout(() => {
					websocket.emit('test_led', {
						index: i,
						r: color.r,
						g: color.g,
						b: color.b,
						brightness: brightness
					});
				}, i * delay);
			}
			
			// Clear all LEDs after the test completes
			setTimeout(() => {
				websocket.emit('test_led', {
					index: -1, // Clear all
					r: 0,
					g: 0,
					b: 0,
					brightness: 0
				});
			}, actualLedCount * delay + 1000); // Wait for all LEDs + 1 second
		}
	}

	// Fetch system status from backend
	async function fetchSystemStatus() {
		try {
			const response = await fetch('/api/dashboard');
			if (response.ok) {
				systemStatus = await response.json();
				systemStatusError = null;
				
				// Initialize MIDI status based on system status
				if (systemStatus.system_status) {
					usbMidiStatus = {
						connected: systemStatus.system_status.midi_input_active || false,
						deviceName: systemStatus.system_status.midi_device_name || null,
						lastActivity: null,
						messageCount: 0
					};
				}
			} else {
				systemStatusError = `HTTP ${response.status}: ${response.status}`;
			}
		} catch (error) {
			systemStatusError = 'Cannot connect to backend server';
		} finally {
			systemStatusLoading = false;
		}
	}
	
	// Fetch saved LED count from backend settings
	async function fetchLEDCount() {
		try {
			const count = await getSetting('led', 'led_count');
			if (count && count !== ledCount) {
				ledCount = count;
				initializeLEDState(ledCount);
				console.log(`Retrieved LED count from settings: ${ledCount}`);
			}
		} catch (error) {
			console.warn(`Error fetching LED count: ${error.message}`);
		}
	}

	// MIDI device event handlers
	async function handleMidiDeviceSelected(event) {
		console.log('MIDI device selected:', event.detail);
		selectedMidiDevice = event.detail.id;
		
		// Connect to the selected MIDI device
		try {
			const response = await fetch('/api/midi-input/start', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					device_name: event.detail.name,
					enable_usb: true,
					enable_rtpmidi: false
				})
			});
			
			if (response.ok) {
				const result = await response.json();
				console.log('MIDI device connected successfully:', result);
				// Refresh system status to update the connection status display
				await fetchSystemStatus();
			} else {
				const error = await response.json();
				console.error('Failed to connect to MIDI device:', error);
			}
		} catch (error) {
			console.error('Error connecting to MIDI device:', error);
		}
	}

	function handleMidiDevicesUpdated(event) {
		console.log('MIDI devices updated:', event.detail);
	}

	function handleNetworkMidiConnected(event) {
		console.log('Network MIDI session connected:', event.detail);
	}

	function handleNetworkMidiDisconnected(event) {
		console.log('Network MIDI session disconnected:', event.detail);
	}

	function handleNetworkMidiSessionsUpdated(event) {
		console.log('Network MIDI sessions updated:', event.detail);
	}

	// MIDI connection status event handlers
	function handleMidiStatusConnected(event) {
		console.log('MIDI status WebSocket connected');
	}

	function handleMidiStatusDisconnected(event) {
		console.log('MIDI status WebSocket disconnected');
	}

	function handleUsbStatusUpdate(event) {
		usbMidiStatus = event.detail;
	}

	function handleNetworkStatusUpdate(event) {
		networkMidiStatus = event.detail;
	}

	// Helper functions for system status display
	function getStatusClass(available) {
		return available ? 'healthy' : 'error';
	}

	function formatDuration(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}
</script>

<svelte:head>
	<title>LED Visualization Dashboard</title>
	<meta name="description" content="Real-time LED strip visualization and control dashboard" />
</svelte:head>

<div class="dashboard-container">
	<header class="dashboard-header">
		<h1>LED Visualization Dashboard</h1>
		<div class="connection-info">
			<div class="connection-status status-{connectionStatus}">
				<span class="status-indicator"></span>
				<span class="status-text">
					{#if connectionStatus === 'connected'}
						Connected
					{:else if connectionStatus === 'reconnecting'}
						Reconnecting... ({reconnectAttempts}/{maxReconnectAttempts})
					{:else if connectionStatus === 'disconnected'}
						Disconnected
					{:else if connectionStatus === 'error'}
						Connection Error
					{:else if connectionStatus === 'failed'}
						Connection Failed
					{:else}
						Unavailable
					{/if}
				</span>
				{#if lastConnectionTime}
					<span class="connection-time">
						Last connected: {lastConnectionTime.toLocaleTimeString()}
					</span>
				{/if}
			</div>
			
			{#if connectionError}
				<div class="connection-error">
					<span class="error-icon">⚠️</span>
					<span class="error-message">{connectionError}</span>
				</div>
			{/if}
			
			{#if connectionStatus === 'failed' || connectionStatus === 'error'}
				<button class="reconnect-btn" on:click={manualReconnect}>
					🔄 Retry Connection
				</button>
			{/if}
		</div>
	</header>

	<section class="visualization-section-full-width">
		<div class="visualization-header">
			<h2>LED Strip Visualization</h2>
			<label class="toggle-switch">
				<input type="checkbox" bind:checked={visualizationEnabled}>
				<span class="toggle-slider"></span>
				<span class="toggle-label">{visualizationEnabled ? 'Enabled' : 'Disabled'}</span>
			</label>
		</div>
		{#if visualizationEnabled}
			<LEDVisualization 
				{ledState} 
				width={1200} 
				height={200}
				responsive={true}
			/>
		{/if}
	</section>

	<main class="dashboard-main">
		<section class="system-status-section">
			<h2>System Status</h2>
			
			<!-- MIDI Connection Status -->
			<div class="midi-status-container">
				<h3>🎹 MIDI Connection Status</h3>
				<MidiConnectionStatus 
					{usbMidiStatus}
					{networkMidiStatus}
					on:connected={handleMidiStatusConnected}
					on:disconnected={handleMidiStatusDisconnected}
					on:usbStatusUpdate={handleUsbStatusUpdate}
					on:networkStatusUpdate={handleNetworkStatusUpdate}
				/>
			</div>

			{#if systemStatusLoading}
				<div class="loading">Loading system status...</div>
			{:else if systemStatusError}
				<div class="error-card">
					<span class="error-icon">❌</span>
					<span class="error-message">{systemStatusError}</span>
				</div>
			{:else if systemStatus}
				<div class="system-status-grid">
					<div class="status-card">
						<h3>🔧 Components</h3>
						<div class="status-items">
							<div class="status-item">
								<span class="label">Backend:</span>
								<span class="status healthy">{systemStatus.system_status.backend_status}</span>
							</div>
							<div class="status-item">
								<span class="label">LED Controller:</span>
								<span class="status {getStatusClass(systemStatus.system_status.led_controller_available)}">
									{systemStatus.system_status.led_controller_available ? 'Available' : 'Unavailable'}
								</span>
							</div>
							<div class="status-item">
							<span class="label">MIDI Parser:</span>
							<span class="status {getStatusClass(systemStatus.system_status.midi_parser_available)}">
								{systemStatus.system_status.midi_parser_available ? 'Available' : 'Unavailable'}
							</span>
						</div>
						<div class="status-item">
							<span class="label">USB MIDI Input:</span>
							<span class="status {getStatusClass(systemStatus.system_status.midi_input_active)}">
								{systemStatus.system_status.midi_input_active ? 'Active' : 'Inactive'}
							</span>
							{#if systemStatus.system_status.midi_device_name}
								<div class="device-name">Device: {systemStatus.system_status.midi_device_name}</div>
							{/if}
						</div>
							<div class="status-item">
								<span class="label">Playback Service:</span>
								<span class="status {getStatusClass(systemStatus.system_status.playback_service_available)}">
									{systemStatus.system_status.playback_service_available ? 'Available' : 'Unavailable'}
								</span>
							</div>
						</div>
						<div class="version">Version: {systemStatus.version}</div>
					</div>

					{#if systemStatus.playback_status}
						<div class="status-card">
							<h3>🎵 Playback</h3>
							<div class="status-items">
								<div class="status-item">
									<span class="label">State:</span>
									<span class="status {systemStatus.playback_status.state === 'playing' ? 'healthy' : 'neutral'}">
										{systemStatus.playback_status.state}
									</span>
								</div>
								{#if systemStatus.playback_status.filename}
									<div class="status-item">
										<span class="label">File:</span>
										<span class="filename">{systemStatus.playback_status.filename}</span>
									</div>
								{/if}
								<div class="status-item">
									<span class="label">Progress:</span>
									<span class="progress">
										{formatDuration(systemStatus.playback_status.current_time)} / 
										{formatDuration(systemStatus.playback_status.total_duration)} 
										({systemStatus.playback_status.progress_percentage.toFixed(1)}%)
									</span>
								</div>
							</div>
						</div>
					{/if}

					<div class="status-card">
						<h3>📁 Files</h3>
						<div class="file-count">
							<span class="count">{systemStatus.uploaded_files_count}</span>
							<span class="label">MIDI files uploaded</span>
						</div>
					</div>
				</div>
			{/if}
		</section>

		<section class="midi-management-section">
			<h2>🎹 MIDI Device Management</h2>
			<div class="midi-panels">
				<div class="midi-panel">
					<div class="panel-header" role="button" tabindex="0" on:click={() => midiDevicesExpanded = !midiDevicesExpanded} on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? midiDevicesExpanded = !midiDevicesExpanded : null}>
						<h3>Device Selection</h3>
						<span class="expand-icon {midiDevicesExpanded ? 'expanded' : ''}">
							{midiDevicesExpanded ? '▼' : '▶'}
						</span>
					</div>
					{#if midiDevicesExpanded}
						<div class="panel-content">
							<MidiDeviceSelector 
								bind:selectedDevice={selectedMidiDevice}
								on:deviceSelected={handleMidiDeviceSelected}
								on:devicesUpdated={handleMidiDevicesUpdated}
							/>
						</div>
					{/if}
				</div>

				<div class="midi-panel">
					<div class="panel-header" role="button" tabindex="0" on:click={() => networkMidiExpanded = !networkMidiExpanded} on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? networkMidiExpanded = !networkMidiExpanded : null}>
						<h3>Network MIDI</h3>
						<span class="expand-icon {networkMidiExpanded ? 'expanded' : ''}">
							{networkMidiExpanded ? '▼' : '▶'}
						</span>
					</div>
					{#if networkMidiExpanded}
						<div class="panel-content">
							<NetworkMidiConfig 
								on:sessionConnected={handleNetworkMidiConnected}
								on:sessionDisconnected={handleNetworkMidiDisconnected}
								on:sessionsUpdated={handleNetworkMidiSessionsUpdated}
							/>
						</div>
					{/if}
				</div>
			</div>
		</section>

		<section class="controls-section">
			<h2>Manual Controls</h2>
			<DashboardControls 
				{connectionStatus}
				on:ledTest={handleLEDTest}
				on:patternTest={handlePatternTest}
				on:testAll={handleTestAll}
				on:ledCountChange={handleLEDCountChange}
			/>
		</section>

		<section class="performance-section">
			<h2>Performance Metrics</h2>
			<PerformanceMonitor {performanceMetrics} />
		</section>
	</main>
</div>

<style>
	.dashboard-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 2px solid #e0e0e0;
	}

	.dashboard-header h1 {
		margin: 0;
		color: #333;
		font-size: 2rem;
		font-weight: 600;
	}

	.connection-info {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		align-items: flex-end;
	}

	.connection-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-radius: 20px;
		font-weight: 500;
		font-size: 0.9rem;
		min-height: 44px;
		touch-action: manipulation;
	}

	.status-indicator {
		width: 16px;
		height: 16px;
		border-radius: 50%;
		display: inline-block;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	.connection-time {
		font-size: 0.85rem;
		opacity: 0.8;
		margin-left: 0.5rem;
		line-height: 1.4;
	}

	.connection-error {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background-color: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
		border-radius: 8px;
		font-size: 0.9rem;
		max-width: 300px;
		min-height: 44px;
		line-height: 1.4;
	}

	/* MIDI Management Section */
	.midi-management-section {
		margin-bottom: 2rem;
	}

	.midi-management-section h2 {
		margin-bottom: 1.5rem;
		color: #333;
		font-size: 1.5rem;
		font-weight: 600;
	}

	.midi-panels {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.midi-panel {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		transition: box-shadow 0.2s ease;
	}

	.midi-panel:hover {
		box-shadow: 0 4px 16px rgba(0,0,0,0.15);
	}

	.panel-header {
		padding: 1rem 1.25rem;
		background: #f8f9fa;
		border-bottom: 1px solid #e0e0e0;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: background-color 0.2s ease;
	}

	.panel-header:hover {
		background: #e9ecef;
	}

	.panel-header h3 {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #495057;
	}

	.expand-icon {
		font-size: 0.9rem;
		color: #6c757d;
		transition: transform 0.2s ease;
	}

	.expand-icon.expanded {
		transform: rotate(0deg);
	}

	.panel-content {
		padding: 1.25rem;
	}

	@media (max-width: 768px) {
		.midi-panels {
			grid-template-columns: 1fr;
			gap: 1rem;
		}
	}

	/* MIDI Status Container */
	.midi-status-container {
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.midi-status-container h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.2rem;
		font-weight: 600;
	}

	.error-icon {
		font-size: 1.2rem;
	}

	.error-message {
		flex: 1;
		word-break: break-word;
		line-height: 1.4;
	}

	.reconnect-btn {
		padding: 0.75rem 1rem;
		min-height: 44px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
		transition: all 0.2s;
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
	}

	.reconnect-btn:hover {
		background-color: #0056b3;
	}

	.reconnect-btn:active {
		transform: translateY(1px);
	}

	.status-connected {
		background-color: #e8f5e8;
		color: #2d5a2d;
		border: 1px solid #4caf50;
	}

	.status-connected .status-indicator {
		background-color: #4caf50;
		box-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
	}

	.status-disconnected,
	.status-error,
	.status-failed {
		background-color: #ffeaea;
		color: #d32f2f;
		border: 1px solid #f44336;
	}

	.status-disconnected .status-indicator,
	.status-error .status-indicator,
	.status-failed .status-indicator {
		background-color: #f44336;
	}

	.status-reconnecting {
		background-color: #fff3e0;
		color: #f57c00;
		border: 1px solid #ff9800;
	}

	.status-reconnecting .status-indicator {
		background-color: #ff9800;
		animation: pulse 1.5s infinite;
	}

	.status-unavailable {
		background-color: #f5f5f5;
		color: #666;
		border: 1px solid #ccc;
	}

	.status-unavailable .status-indicator {
		background-color: #ccc;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	/* System Status Styles */
	.system-status-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1rem;
	}

	.status-card {
		padding: 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		background: #fafafa;
	}

	.status-card h3 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #333;
	}

	.status-items {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.status-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.25rem 0;
	}

	.status-item .label {
		font-weight: 500;
		color: #555;
	}

	.status-item .status {
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.85rem;
		font-weight: 500;
	}

	.status.healthy {
		background-color: #e8f5e8;
		color: #2d5a2d;
	}

	.status.error {
		background-color: #ffeaea;
		color: #d32f2f;
	}

	.device-name {
		font-size: 0.75rem;
		color: #666;
		margin-top: 0.25rem;
		font-style: italic;
	}

	.status.neutral {
		background-color: #f0f0f0;
		color: #666;
	}

	.version {
		margin-top: 0.75rem;
		font-size: 0.85rem;
		color: #666;
		font-style: italic;
	}

	.filename {
		font-family: monospace;
		background: #f0f0f0;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.progress {
		font-family: monospace;
		font-size: 0.85rem;
	}

	.file-count {
		text-align: center;
		padding: 1rem;
	}

	.file-count .count {
		display: block;
		font-size: 2rem;
		font-weight: bold;
		color: #007bff;
		margin-bottom: 0.25rem;
	}

	.file-count .label {
		font-size: 0.9rem;
		color: #666;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: #666;
		font-style: italic;
	}

	.error-card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		background-color: #ffeaea;
		color: #d32f2f;
		border: 1px solid #f5c6cb;
		border-radius: 8px;
	}

	.dashboard-main {
		display: grid;
		grid-template-columns: 1fr;
		gap: 2rem;
	}

	.visualization-section,
	.controls-section,
	.performance-section,
	.system-status-section {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		border: 1px solid #e0e0e0;
	}

	.visualization-section-full-width h2,
	.controls-section h2,
	.performance-section h2,
	.system-status-section h2 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.25rem;
		font-weight: 600;
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.dashboard-container {
			padding: 1rem;
		}
		
		.dashboard-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 1.5rem;
			padding-bottom: 1.5rem;
		}
		
		.dashboard-header h1 {
			font-size: 1.5rem;
		}
		
		.connection-info {
			align-items: flex-start;
			width: 100%;
			gap: 1rem;
		}
		
		.connection-status {
			flex-wrap: wrap;
			padding: 0.75rem;
			gap: 0.5rem;
			min-height: 44px; /* Minimum touch target size */
		}
		
		.connection-error {
			max-width: 100%;
			padding: 0.75rem;
			flex-wrap: wrap;
		}
		
		.reconnect-btn {
			width: 100%;
			margin-top: 0.5rem;
			padding: 0.75rem;
			min-height: 44px; /* Minimum touch target size */
		}
		
		.connection-time {
			width: 100%;
			margin-left: 0;
			margin-top: 0.5rem;
		}

		.visualization-section,
		.controls-section,
		.performance-section,
		.system-status-section {
			padding: 1.25rem;
			border-radius: 10px;
		}

		/* Improve touch targets for controls */
		.control-button {
			min-height: 44px;
			padding: 0.75rem 1rem;
		}
	}

	@media (max-width: 480px) {
		.dashboard-container {
			padding: 0.75rem;
		}
		
		.dashboard-header h1 {
			font-size: 1.25rem;
		}
		
		.connection-status {
			padding: 0.5rem;
			min-height: 40px;
			font-size: 0.85rem;
		}
		
		.status-indicator {
			width: 12px;
			height: 12px;
		}
		
		.connection-error {
			padding: 0.5rem;
			min-height: 40px;
			font-size: 0.8rem;
		}
		
		.error-icon {
			font-size: 1rem;
		}
		
		.reconnect-btn {
			padding: 0.5rem;
			min-height: 40px;
			font-size: 0.9rem;
		}
		
		.connection-time {
			font-size: 0.8rem;
		}
	}

		/* Visualization toggle switch */
	.visualization-section-full-width {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		border: 1px solid #e0e0e0;
		margin-bottom: 2rem;
	}
	
	.visualization-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.visualization-header h2 {
		margin: 0;
		color: #333;
		font-size: 1.25rem;
		font-weight: 600;
	}
	
	.toggle-switch {
		display: flex;
		align-items: center;
		cursor: pointer;
	}
	
	.toggle-switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}
	
	.toggle-slider {
		position: relative;
		display: inline-block;
		width: 50px;
		height: 24px;
		background-color: #ccc;
		border-radius: 24px;
		transition: .4s;
		margin-right: 10px;
	}
	
	.toggle-slider:before {
		position: absolute;
		content: "";
		height: 18px;
		width: 18px;
		left: 3px;
		bottom: 3px;
		background-color: white;
		border-radius: 50%;
		transition: .4s;
	}
	
	.toggle-switch input:checked + .toggle-slider {
		background-color: #4caf50;
	}
	
	.toggle-switch input:checked + .toggle-slider:before {
		transform: translateX(26px);
	}
	
	.toggle-label {
		font-size: 0.9rem;
		font-weight: 500;
		color: #555;
		min-width: 60px;
	}

	@media (min-width: 768px) {
		.dashboard-main {
			grid-template-columns: 1fr 1fr;
			grid-template-areas: 
				"system-status controls"
				"performance performance";
		}

		.system-status-section {
			grid-area: system-status;
		}

		.controls-section {
			grid-area: controls;
		}

		.performance-section {
			grid-area: performance;
		}
	}

	@media (min-width: 1024px) {
		.dashboard-main {
			grid-template-columns: 1fr 1fr 1fr;
			grid-template-areas: 
				"system-status controls performance";
		}
	}
</style>