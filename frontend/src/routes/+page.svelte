<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { settings, getSetting } from '$lib/stores/settings.js';
	import LEDVisualization from '$lib/components/LEDVisualization.svelte';
	import DashboardControls from '$lib/components/DashboardControls.svelte';
	import PerformanceMonitor from '$lib/components/PerformanceMonitor.svelte';
	import MidiDeviceSelector from '$lib/components/MidiDeviceSelector.svelte';
	import NetworkMidiConfig from '$lib/components/NetworkMidiConfig.svelte';
	import MidiConnectionStatus from '$lib/components/MidiConnectionStatus.svelte';

	let backendStatus = 'Checking...';
	let backendMessage = '';
	
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

	onMount(async () => {
		// Check backend health first
		try {
			const response = await fetch('http://localhost:5000/health');
			if (response.ok) {
				const data = await response.json();
				backendStatus = data.status;
				backendMessage = data.message;
			} else {
				backendStatus = 'Error';
				backendMessage = `HTTP ${response.status}: ${response.statusText}`;
			}
		} catch (error) {
			backendStatus = 'Offline';
			backendMessage = 'Cannot connect to backend server';
		}

		// Initialize dashboard functionality if backend is healthy
		if (backendStatus === 'healthy') {
			initializeWebSocket();
			startPerformanceTracking();
			startConnectionHealthCheck();
			fetchSystemStatus();
			fetchLEDCount();
		}
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
			const count = await getSetting('led', 'ledCount');
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
	<title>Piano LED Visualizer - Home</title>
	<meta name="description" content="Piano LED Visualizer - Transform your MIDI files into stunning LED light shows!" />
</svelte:head>

<main>
	<div class="hero-section">
		<h1>🎹 Piano LED Visualizer</h1>
		<p>Welcome to the Piano LED Visualizer - Transform your MIDI files into stunning LED light shows!</p>
	</div>
	
	<div class="status-card">
		<h2>System Status</h2>
		<div class="status-item">
			<span class="label">Frontend:</span>
			<span class="status healthy">Running</span>
		</div>
		<div class="status-item">
			<span class="label">Backend:</span>
			<span class="status {backendStatus === 'healthy' ? 'healthy' : 'error'}">
				{backendStatus === 'healthy' ? 'Healthy' : backendStatus}
			</span>
		</div>
		{#if backendMessage}
			<p class="status-message">{backendMessage}</p>
		{/if}
	</div>

	{#if backendStatus === 'healthy'}
		<!-- LED Visualization Section -->
		<section class="visualization-section">
			<div class="visualization-header">
				<h2>LED Strip Visualization</h2>
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

		<!-- Dashboard Controls Section -->
		<section class="controls-section">
			<h2>LED Controls</h2>
			<DashboardControls 
				{ledCount}
				{connectionStatus}
				on:ledTest={handleLEDTest}
				on:patternTest={handlePatternTest}
				on:ledCountChange={handleLEDCountChange}
				on:testAll={handleTestAll}
			/>
		</section>

		<!-- Performance Monitor Section -->
		<section class="performance-section">
			<h2>Performance Monitor</h2>
			<PerformanceMonitor {performanceMetrics} />
		</section>

		<!-- MIDI Configuration Section -->
		<section class="midi-section">
			<h2>MIDI Configuration</h2>
			
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

			<div class="midi-panels">
				<div class="midi-panel">
					<div class="panel-header" on:click={() => midiDevicesExpanded = !midiDevicesExpanded}>
						<h3>USB MIDI Devices</h3>
						<span class="expand-icon {midiDevicesExpanded ? 'expanded' : ''}">
							{midiDevicesExpanded ? '▼' : '▶'}
						</span>
					</div>
					{#if midiDevicesExpanded}
						<div class="panel-content">
							<MidiDeviceSelector 
								on:deviceSelected={handleMidiDeviceSelected}
								on:devicesUpdated={handleMidiDevicesUpdated}
							/>
						</div>
					{/if}
				</div>

				<div class="midi-panel">
					<div class="panel-header" on:click={() => networkMidiExpanded = !networkMidiExpanded}>
						<h3>Network MIDI (RTP-MIDI)</h3>
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

		<!-- System Status Details -->
		{#if systemStatusLoading}
			<div class="loading">Loading system status...</div>
		{:else if systemStatusError}
			<div class="error-card">
				<span class="error-icon">❌</span>
				<span class="error-message">{systemStatusError}</span>
			</div>
		{:else if systemStatus}
			<section class="system-details-section">
				<h2>System Details</h2>
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
					</div>
				</div>
			</section>
		{/if}
	{/if}

	<div class="navigation-card">
		<h2>Navigation</h2>
		<p>Access all available features of the Piano LED Visualizer:</p>
		<div class="nav-buttons">
			<a href="/upload" class="nav-button">
				<span class="nav-icon">📁</span>
				<div class="nav-content">
					<h3>Upload</h3>
					<p>Upload MIDI files for LED visualization</p>
				</div>
			</a>
			<a href="/play" class="nav-button">
				<span class="nav-icon">▶️</span>
				<div class="nav-content">
					<h3>Play</h3>
					<p>Play and control MIDI file playback</p>
				</div>
			</a>
			<a href="/settings" class="nav-button">
				<span class="nav-icon">⚙️</span>
				<div class="nav-content">
					<h3>Settings</h3>
					<p>Configure system preferences and LED settings</p>
				</div>
			</a>
		</div>
	</div>

	<div class="info-card">
		<h2>Getting Started</h2>
		<p>This is the foundation setup for the Piano LED Visualizer. The system is ready for development!</p>
		<ul>
			<li>✅ Monorepo structure initialized</li>
			<li>✅ Flask backend running on port 5001</li>
			<li>✅ SvelteKit frontend running on port 5173</li>
			<li>✅ Health check endpoint working</li>
		</ul>
	</div>
</main>

<style>
	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.hero-section {
		text-align: center;
		margin-bottom: 2rem;
	}

	.hero-section h1 {
		color: #333;
		margin-bottom: 1rem;
		font-size: 2.5rem;
	}

	.hero-section p {
		font-size: 1.1rem;
		color: #666;
		margin-bottom: 0;
	}

	.status-card, .info-card, .navigation-card {
		background: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 8px;
		padding: 1.5rem;
		margin: 1.5rem 0;
	}

	.status-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin: 0.5rem 0;
	}

	.label {
		font-weight: 600;
		color: #495057;
	}

	.status {
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-weight: 600;
		text-transform: uppercase;
		font-size: 0.875rem;
	}

	.status.healthy {
		background-color: #d4edda;
		color: #155724;
	}

	.status.error {
		background-color: #f8d7da;
		color: #721c24;
	}

	.status-message {
		margin-top: 1rem;
		padding: 0.75rem;
		background: #e2e3e5;
		border-radius: 4px;
		font-size: 0.875rem;
		color: #495057;
	}

	/* Dashboard-specific styles */
	.visualization-section, .controls-section, .performance-section, .midi-section, .system-details-section {
		background: white;
		border: 1px solid #e9ecef;
		border-radius: 12px;
		padding: 2rem;
		margin: 2rem 0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.visualization-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.visualization-header h2 {
		margin: 0;
		color: #333;
	}

	.connection-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.connection-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		display: inline-block;
	}

	.status-connected .status-indicator {
		background-color: #28a745;
		animation: pulse 2s infinite;
	}

	.status-disconnected .status-indicator {
		background-color: #dc3545;
	}

	.status-reconnecting .status-indicator {
		background-color: #ffc107;
		animation: pulse 1s infinite;
	}

	.status-error .status-indicator,
	.status-failed .status-indicator {
		background-color: #dc3545;
	}

	.status-unavailable .status-indicator {
		background-color: #6c757d;
	}

	.status-connected {
		background-color: #d4edda;
		color: #155724;
	}

	.status-disconnected {
		background-color: #f8d7da;
		color: #721c24;
	}

	.status-reconnecting {
		background-color: #fff3cd;
		color: #856404;
	}

	.status-error,
	.status-failed {
		background-color: #f8d7da;
		color: #721c24;
	}

	.status-unavailable {
		background-color: #e2e3e5;
		color: #495057;
	}

	@keyframes pulse {
		0% { opacity: 1; }
		50% { opacity: 0.5; }
		100% { opacity: 1; }
	}

	.connection-error {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background-color: #f8d7da;
		color: #721c24;
		border-radius: 6px;
		font-size: 0.875rem;
	}

	.reconnect-btn {
		padding: 0.5rem 1rem;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 600;
		transition: background-color 0.2s;
	}

	.reconnect-btn:hover {
		background-color: #0056b3;
	}

	.toggle-switch {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}

	.toggle-switch input[type="checkbox"] {
		display: none;
	}

	.toggle-slider {
		width: 50px;
		height: 24px;
		background-color: #ccc;
		border-radius: 12px;
		position: relative;
		transition: background-color 0.3s;
	}

	.toggle-slider::before {
		content: '';
		position: absolute;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background-color: white;
		top: 2px;
		left: 2px;
		transition: transform 0.3s;
	}

	.toggle-switch input[type="checkbox"]:checked + .toggle-slider {
		background-color: #007bff;
	}

	.toggle-switch input[type="checkbox"]:checked + .toggle-slider::before {
		transform: translateX(26px);
	}

	.toggle-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: #495057;
	}

	.midi-section h2 {
		margin-bottom: 1.5rem;
		color: #333;
	}

	.midi-status-container {
		margin-bottom: 2rem;
	}

	.midi-status-container h3 {
		margin-bottom: 1rem;
		color: #495057;
	}

	.midi-panels {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.midi-panel {
		border: 1px solid #e9ecef;
		border-radius: 8px;
		overflow: hidden;
	}

	.panel-header {
		background-color: #f8f9fa;
		padding: 1rem;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: background-color 0.2s;
	}

	.panel-header:hover {
		background-color: #e9ecef;
	}

	.panel-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #495057;
	}

	.expand-icon {
		font-size: 0.875rem;
		color: #6c757d;
		transition: transform 0.2s;
	}

	.expand-icon.expanded {
		transform: rotate(0deg);
	}

	.panel-content {
		padding: 1rem;
		border-top: 1px solid #e9ecef;
	}

	.system-status-grid {
		display: grid;
		gap: 1.5rem;
	}

	.system-status-grid .status-card {
		background: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 8px;
		padding: 1.5rem;
		margin: 0;
	}

	.system-status-grid .status-card h3 {
		margin-top: 0;
		margin-bottom: 1rem;
		color: #495057;
	}

	.status-items {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.device-name {
		font-size: 0.875rem;
		color: #6c757d;
		margin-top: 0.25rem;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: #6c757d;
		font-style: italic;
	}

	.error-card {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem;
		background-color: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
		border-radius: 8px;
		margin: 1rem 0;
	}

	ul {
		list-style-type: none;
		padding: 0;
	}

	li {
		padding: 0.5rem 0;
		font-size: 1.1rem;
	}

	.nav-buttons {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.nav-button {
		display: flex;
		align-items: center;
		padding: 1.25rem;
		background: white;
		border: 2px solid #e9ecef;
		border-radius: 8px;
		text-decoration: none;
		color: inherit;
		transition: all 0.2s ease;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.nav-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		border-color: #007bff;
	}

	.nav-icon {
		font-size: 2rem;
		margin-right: 1rem;
		flex-shrink: 0;
	}

	.nav-content h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.25rem;
		font-weight: 600;
	}

	.nav-content p {
		margin: 0;
		font-size: 0.9rem;
		opacity: 0.8;
		line-height: 1.4;
	}

	@media (max-width: 768px) {
		main {
			padding: 1rem;
		}

		.midi-panels {
			grid-template-columns: 1fr;
		}

		.visualization-header {
			flex-direction: column;
			align-items: stretch;
		}

		.connection-info {
			justify-content: center;
		}

		.nav-buttons {
			grid-template-columns: 1fr;
		}
		
		.nav-button {
			padding: 1rem;
		}
		
		.nav-icon {
			font-size: 1.5rem;
			margin-right: 0.75rem;
		}
	}
</style>
