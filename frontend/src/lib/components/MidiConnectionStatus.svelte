<script>
	import { onMount, onDestroy } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Connection status data
	export let usbMidiStatus = {
		connected: false,
		deviceName: null,
		lastActivity: null,
		messageCount: 0
	};

	export let networkMidiStatus = {
		connected: false,
		activeSessions: [],
		lastActivity: null,
		messageCount: 0
	};

	// WebSocket connection for real-time updates
	let ws = null;
	let reconnectInterval = null;
	let connectionAttempts = 0;
	const maxReconnectAttempts = 5;

	function connectWebSocket() {
		if (ws && ws.readyState === WebSocket.OPEN) return;

		try {
			const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
			const wsUrl = `${protocol}//${window.location.host}/ws/midi-status`;
			ws = new WebSocket(wsUrl);

			ws.onopen = () => {
				console.log('MIDI status WebSocket connected');
				connectionAttempts = 0;
				dispatch('connected');
			};

			ws.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					handleMidiStatusUpdate(data);
				} catch (error) {
					console.error('Error parsing MIDI status message:', error);
				}
			};

			ws.onclose = () => {
				console.log('MIDI status WebSocket disconnected');
				dispatch('disconnected');
				scheduleReconnect();
			};

			ws.onerror = (error) => {
				console.error('MIDI status WebSocket error:', error);
				dispatch('error', { error });
			};
		} catch (error) {
			console.error('Failed to create MIDI status WebSocket:', error);
			scheduleReconnect();
		}
	}

	function scheduleReconnect() {
		if (connectionAttempts >= maxReconnectAttempts) {
			console.log('Max reconnection attempts reached for MIDI status');
			return;
		}

		connectionAttempts++;
		const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
		
		reconnectInterval = setTimeout(() => {
			console.log(`Attempting to reconnect MIDI status WebSocket (attempt ${connectionAttempts})`);
			connectWebSocket();
		}, delay);
	}

	function handleMidiStatusUpdate(data) {
		if (data.type === 'usb_midi_status') {
			usbMidiStatus = {
				...usbMidiStatus,
				...data.status
			};
			dispatch('usbStatusUpdate', usbMidiStatus);
		} else if (data.type === 'network_midi_status') {
			networkMidiStatus = {
				...networkMidiStatus,
				...data.status
			};
			dispatch('networkStatusUpdate', networkMidiStatus);
		}
	}

	function formatLastActivity(timestamp) {
		if (!timestamp) return 'Never';
		const now = new Date();
		const activity = new Date(timestamp);
		const diffMs = now - activity;
		const diffSecs = Math.floor(diffMs / 1000);
		const diffMins = Math.floor(diffSecs / 60);
		const diffHours = Math.floor(diffMins / 60);

		if (diffSecs < 60) return `${diffSecs}s ago`;
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		return activity.toLocaleDateString();
	}

	onMount(() => {
		connectWebSocket();
	});

	onDestroy(() => {
		if (reconnectInterval) {
			clearTimeout(reconnectInterval);
		}
		if (ws) {
			ws.close();
		}
	});
</script>

<div class="midi-connection-status">
	<div class="status-section">
		<h3>🔌 USB MIDI</h3>
		<div class="connection-indicator">
			<div class="status-dot {usbMidiStatus.connected ? 'connected' : 'disconnected'}"></div>
			<div class="status-info">
				<div class="status-text">
					{usbMidiStatus.connected ? 'Connected' : 'Disconnected'}
				</div>
				{#if usbMidiStatus.deviceName}
					<div class="device-info">{usbMidiStatus.deviceName}</div>
				{/if}
				<div class="activity-info">
					<span class="message-count">{usbMidiStatus.messageCount} messages</span>
					<span class="last-activity">Last: {formatLastActivity(usbMidiStatus.lastActivity)}</span>
				</div>
			</div>
		</div>
	</div>

	<div class="status-section">
		<h3>🌐 Network MIDI</h3>
		<div class="connection-indicator">
			<div class="status-dot {networkMidiStatus.connected ? 'connected' : 'disconnected'}"></div>
			<div class="status-info">
				<div class="status-text">
					{networkMidiStatus.connected ? 'Connected' : 'Disconnected'}
				</div>
				{#if networkMidiStatus.activeSessions.length > 0}
					<div class="sessions-info">
						{networkMidiStatus.activeSessions.length} active session{networkMidiStatus.activeSessions.length !== 1 ? 's' : ''}
					</div>
					<div class="session-list">
						{#each networkMidiStatus.activeSessions as session}
							<div class="session-item">
								<span class="session-name">{session.name}</span>
								<span class="session-status {session.status}">{session.status}</span>
							</div>
						{/each}
					</div>
				{/if}
				<div class="activity-info">
					<span class="message-count">{networkMidiStatus.messageCount} messages</span>
					<span class="last-activity">Last: {formatLastActivity(networkMidiStatus.lastActivity)}</span>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.midi-connection-status {
		display: flex;
		gap: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border: 1px solid #e9ecef;
	}

	.status-section {
		flex: 1;
		min-width: 0;
	}

	.status-section h3 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #495057;
	}

	.connection-indicator {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.status-dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		margin-top: 0.25rem;
		box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
		transition: all 0.3s ease;
	}

	.status-dot.connected {
		background: #28a745;
		box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3), 0 0 8px rgba(40, 167, 69, 0.6);
		animation: pulse 2s infinite;
	}

	.status-dot.disconnected {
		background: #dc3545;
		box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.3);
	}

	@keyframes pulse {
		0% { transform: scale(1); }
		50% { transform: scale(1.1); }
		100% { transform: scale(1); }
	}

	.status-info {
		flex: 1;
		min-width: 0;
	}

	.status-text {
		font-weight: 600;
		color: #212529;
		margin-bottom: 0.25rem;
	}

	.device-info {
		font-size: 0.9rem;
		color: #6c757d;
		margin-bottom: 0.5rem;
		font-family: monospace;
	}

	.sessions-info {
		font-size: 0.9rem;
		color: #495057;
		margin-bottom: 0.5rem;
	}

	.session-list {
		margin-bottom: 0.5rem;
	}

	.session-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.25rem 0.5rem;
		background: white;
		border-radius: 4px;
		margin-bottom: 0.25rem;
		font-size: 0.85rem;
	}

	.session-name {
		font-family: monospace;
		color: #495057;
	}

	.session-status {
		padding: 0.125rem 0.375rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.session-status.connected {
		background: #d4edda;
		color: #155724;
	}

	.session-status.connecting {
		background: #fff3cd;
		color: #856404;
	}

	.session-status.disconnected {
		background: #f8d7da;
		color: #721c24;
	}

	.activity-info {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		color: #6c757d;
		gap: 1rem;
	}

	.message-count {
		font-weight: 500;
	}

	.last-activity {
		font-style: italic;
	}

	@media (max-width: 768px) {
		.midi-connection-status {
			flex-direction: column;
			gap: 1rem;
		}

		.activity-info {
			flex-direction: column;
			gap: 0.25rem;
		}
	}
</style>