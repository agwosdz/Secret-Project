<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { writable } from 'svelte/store';
	import MidiAutoDiscovery from './MidiAutoDiscovery.svelte';

	const dispatch = createEventDispatcher();

	interface RtpMidiSession {
		id: string;
		name: string;
		ip_address: string;
		port: number;
		status: 'discovered' | 'connected' | 'connecting' | 'disconnected' | 'error';
		latency?: number;
		last_seen?: string;
	}

	interface SessionsResponse {
		sessions: RtpMidiSession[];
		count: number;
	}

	export let autoDiscovery = true;
	export let discoveryInterval = 10000;

	let sessions = writable<SessionsResponse>({ sessions: [], count: 0 });
	let loading = false;
	let error: string | null = null;
	let discoveryTimer: NodeJS.Timeout | null = null;
	let connectingSession: string | null = null;

	// Manual connection form
	let showManualForm = false;
	let manualIp = '';
	let manualPort = 5004;
	let manualName = '';

	// Auto-discovery toggle
	let showAutoDiscovery = false;

	onMount(() => {
		fetchSessions();
		if (autoDiscovery) {
			startAutoDiscovery();
		}

		return () => {
			if (discoveryTimer) {
				clearInterval(discoveryTimer);
			}
		};
	});

	async function fetchSessions() {
		loading = true;
		error = null;

		try {
			const response = await fetch('/api/rtpmidi/sessions');
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data: SessionsResponse = await response.json();
			sessions.set(data);
			dispatch('sessionsUpdated', data);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to fetch sessions';
			console.error('Error fetching rtpMIDI sessions:', err);
		} finally {
			loading = false;
		}
	}

	async function connectToSession(session: RtpMidiSession) {
		if (connectingSession) return;
		
		connectingSession = session.id;
		error = null;

		try {
			const response = await fetch('/api/rtpmidi/connect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
				session_name: session.name || session.id,
				host: session.ip_address,
				port: session.port
			})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.message || `HTTP ${response.status}`);
			}

			const result = await response.json();
			dispatch('sessionConnected', { session, result });
			
			// Refresh sessions to get updated status
			setTimeout(fetchSessions, 1000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to connect to session';
			console.error('Error connecting to rtpMIDI session:', err);
		} finally {
			connectingSession = null;
		}
	}

	async function disconnectFromSession(session: RtpMidiSession) {
		error = null;

		try {
			const response = await fetch('/api/rtpmidi/disconnect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					session_id: session.id
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.message || `HTTP ${response.status}`);
			}

			const result = await response.json();
			dispatch('sessionDisconnected', { session, result });
			
			// Refresh sessions to get updated status
			setTimeout(fetchSessions, 1000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to disconnect from session';
			console.error('Error disconnecting from rtpMIDI session:', err);
		}
	}

	async function connectManually() {
		if (!manualIp || !manualName) {
			error = 'Please provide IP address and session name';
			return;
		}

		error = null;

		try {
			const response = await fetch('/api/rtpmidi/connect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
				session_name: manualName,
				host: manualIp,
				port: manualPort
			})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.message || `HTTP ${response.status}`);
			}

			const result = await response.json();
			dispatch('manualConnectionSuccess', result);
			
			// Reset form and refresh sessions
			manualIp = '';
			manualPort = 5004;
			manualName = '';
			showManualForm = false;
			setTimeout(fetchSessions, 1000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to connect manually';
			console.error('Error with manual connection:', err);
		}
	}

	function startAutoDiscovery() {
		if (discoveryTimer) clearInterval(discoveryTimer);
		discoveryTimer = setInterval(fetchSessions, discoveryInterval);
	}

	function stopAutoDiscovery() {
		if (discoveryTimer) {
			clearInterval(discoveryTimer);
			discoveryTimer = null;
		}
	}

	function getSessionStatusClass(status: string): string {
		switch (status) {
			case 'connected': return 'status-connected';
			case 'connecting': return 'status-connecting';
			case 'discovered': return 'status-discovered';
			case 'disconnected': return 'status-disconnected';
			case 'error': return 'status-error';
			default: return 'status-unknown';
		}
	}

	function formatLatency(latency?: number): string {
		if (!latency) return 'N/A';
		return `${latency}ms`;
	}

	function formatLastSeen(lastSeen?: string): string {
		if (!lastSeen) return 'Never';
		try {
			const date = new Date(lastSeen);
			const now = new Date();
			const diffMs = now.getTime() - date.getTime();
			const diffSecs = Math.floor(diffMs / 1000);
			
			if (diffSecs < 60) return `${diffSecs}s ago`;
			if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
			return `${Math.floor(diffSecs / 3600)}h ago`;
		} catch {
			return 'Unknown';
		}
	}

	// Auto-discovery event handlers
	function handleDiscoveryCompleted(event) {
		console.log('Auto-discovery completed:', event.detail);
	}

	function handleDeviceConnected(event) {
		console.log('Device connected from auto-discovery:', event.detail);
		// Refresh sessions after auto-connection
		fetchSessions();
	}

	function handleConnectionError(event) {
		console.error('Auto-discovery connection error:', event.detail);
	}
</script>

<div class="network-midi-config">
	<div class="header">
		<h3>🌐 Network MIDI (rtpMIDI)</h3>
		<div class="controls">
			<button 
				class="refresh-btn" 
				on:click={fetchSessions} 
				disabled={loading}
				title="Refresh sessions"
			>
				{loading ? '⟳' : '🔄'}
			</button>
			<button 
				class="discovery-btn {autoDiscovery ? 'active' : ''}" 
				on:click={() => {
					autoDiscovery = !autoDiscovery;
					if (autoDiscovery) startAutoDiscovery();
					else stopAutoDiscovery();
				}}
				title="Toggle auto-discovery"
			>
				🔍
			</button>
			<button 
				class="manual-btn" 
				on:click={() => showManualForm = !showManualForm}
				title="Manual connection"
			>
				➕
			</button>
		</div>
	</div>

	{#if error}
		<div class="error-message">
			⚠️ {error}
			<button class="retry-btn" on:click={fetchSessions}>Retry</button>
		</div>
	{/if}

	{#if showManualForm}
		<div class="manual-form">
			<h4>Manual Connection</h4>
			<div class="form-row">
				<label>
					IP Address:
					<input 
						type="text" 
						bind:value={manualIp} 
						placeholder="192.168.1.100"
						required
					/>
				</label>
				<label>
					Port:
					<input 
						type="number" 
						bind:value={manualPort} 
						min="1" 
						max="65535"
						required
					/>
				</label>
			</div>
			<div class="form-row">
				<label>
					Session Name:
					<input 
						type="text" 
						bind:value={manualName} 
						placeholder="My MIDI Session"
						required
					/>
				</label>
			</div>
			<div class="form-actions">
				<button class="connect-btn" on:click={connectManually}>Connect</button>
				<button class="cancel-btn" on:click={() => showManualForm = false}>Cancel</button>
			</div>
		</div>
	{/if}

	<!-- Auto-Discovery Section -->
	<div class="auto-discovery-section">
		<div class="section-header" on:click={() => showAutoDiscovery = !showAutoDiscovery}>
			<h4>🔍 Auto-Discovery</h4>
			<span class="expand-icon {showAutoDiscovery ? 'expanded' : ''}">
				{showAutoDiscovery ? '▼' : '▶'}
			</span>
		</div>
		{#if showAutoDiscovery}
			<div class="auto-discovery-content">
				<MidiAutoDiscovery 
					on:discoveryCompleted={handleDiscoveryCompleted}
					on:deviceConnected={handleDeviceConnected}
					on:connectionError={handleConnectionError}
				/>
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="loading">Discovering sessions...</div>
	{/if}

	<div class="sessions-list">
		{#if $sessions.sessions.length > 0}
			<div class="sessions-header">
				<span>Found {$sessions.count} session{$sessions.count !== 1 ? 's' : ''}</span>
			</div>
			{#each $sessions.sessions as session}
				<div class="session-item {getSessionStatusClass(session.status)}">
					<div class="session-info">
						<div class="session-name">{session.name}</div>
						<div class="session-details">
							<span class="address">{session.ip_address}:{session.port}</span>
							<span class="latency">Latency: {formatLatency(session.latency)}</span>
							<span class="last-seen">Last seen: {formatLastSeen(session.last_seen)}</span>
						</div>
					</div>
					<div class="session-status">
						<div class="status-info">
							<span class="status-indicator"></span>
							<span class="status-text">{session.status}</span>
						</div>
						<div class="session-actions">
							{#if session.status === 'discovered' || session.status === 'disconnected'}
								<button 
									class="action-btn connect-btn"
									on:click={() => connectToSession(session)}
									disabled={connectingSession === session.id}
								>
									{connectingSession === session.id ? 'Connecting...' : 'Connect'}
								</button>
							{:else if session.status === 'connected'}
								<button 
									class="action-btn disconnect-btn"
									on:click={() => disconnectFromSession(session)}
								>
									Disconnect
								</button>
							{:else if session.status === 'connecting'}
								<button class="action-btn connecting-btn" disabled>
									Connecting...
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		{:else if !loading}
			<div class="no-sessions">
				<div class="no-sessions-icon">🌐</div>
				<div class="no-sessions-text">
					<p>No network MIDI sessions found</p>
					<p class="hint">Make sure rtpMIDI is enabled on other devices</p>
					<button class="manual-connect-btn" on:click={() => showManualForm = true}>
						Connect Manually
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.network-midi-config {
		background: var(--bg-secondary, #f8f9fa);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 8px;
		padding: 16px;
		max-width: 600px;
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

	.refresh-btn, .discovery-btn, .manual-btn {
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 4px;
		padding: 6px 8px;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.2s ease;
	}

	.refresh-btn:hover, .discovery-btn:hover, .manual-btn:hover {
		background: var(--bg-hover, #f1f3f4);
	}

	.refresh-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		animation: spin 1s linear infinite;
	}

	.discovery-btn.active {
		background: var(--success-color, #28a745);
		color: white;
		border-color: var(--success-color, #28a745);
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

	.manual-form {
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 6px;
		padding: 16px;
		margin-bottom: 16px;
	}

	.manual-form h4 {
		margin: 0 0 12px 0;
		font-size: 1rem;
		color: var(--text-primary, #2c3e50);
	}

	.form-row {
		display: flex;
		gap: 12px;
		margin-bottom: 12px;
	}

	.form-row label {
		display: flex;
		flex-direction: column;
		flex: 1;
		font-size: 0.9rem;
		color: var(--text-secondary, #6c757d);
		font-weight: 500;
	}

	.form-row input {
		margin-top: 4px;
		padding: 8px;
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 4px;
		font-size: 0.9rem;
	}

	.form-row input:focus {
		outline: none;
		border-color: var(--accent-color, #007bff);
		box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
	}

	.form-actions {
		display: flex;
		gap: 8px;
		justify-content: flex-end;
	}

	.connect-btn, .cancel-btn {
		padding: 8px 16px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: all 0.2s ease;
	}

	.connect-btn {
		background: var(--accent-color, #007bff);
		color: white;
	}

	.connect-btn:hover {
		background: var(--accent-dark, #0056b3);
	}

	.cancel-btn {
		background: var(--bg-secondary, #f8f9fa);
		color: var(--text-secondary, #6c757d);
		border: 1px solid var(--border-color, #e1e5e9);
	}

	.cancel-btn:hover {
		background: var(--bg-hover, #f1f3f4);
	}

	.loading {
		text-align: center;
		padding: 20px;
		color: var(--text-secondary, #6c757d);
		font-style: italic;
	}

	.sessions-header {
		margin-bottom: 12px;
		font-size: 0.9rem;
		color: var(--text-secondary, #6c757d);
		font-weight: 500;
	}

	.session-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 16px;
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 6px;
		margin-bottom: 8px;
		transition: all 0.2s ease;
	}

	.session-item:hover {
		border-color: var(--accent-color, #007bff);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.session-info {
		flex: 1;
	}

	.session-name {
		font-weight: 600;
		color: var(--text-primary, #2c3e50);
		margin-bottom: 4px;
	}

	.session-details {
		display: flex;
		gap: 16px;
		font-size: 0.8rem;
		color: var(--text-secondary, #6c757d);
	}

	.session-status {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 8px;
	}

	.status-info {
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

	.status-connecting .status-indicator {
		background: #ffc107;
		animation: pulse 1s infinite;
	}

	.status-discovered .status-indicator {
		background: #17a2b8;
	}

	.status-disconnected .status-indicator {
		background: #6c757d;
	}

	.status-error .status-indicator {
		background: #dc3545;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.status-text {
		font-size: 12px;
		color: var(--text-secondary, #6c757d);
		text-transform: capitalize;
	}

	.action-btn {
		padding: 6px 12px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.8rem;
		transition: all 0.2s ease;
	}

	.action-btn.connect-btn {
		background: var(--success-color, #28a745);
		color: white;
	}

	.action-btn.connect-btn:hover {
		background: var(--success-dark, #1e7e34);
	}

	.action-btn.disconnect-btn {
		background: var(--danger-color, #dc3545);
		color: white;
	}

	.action-btn.disconnect-btn:hover {
		background: var(--danger-dark, #c82333);
	}

	.action-btn.connecting-btn {
		background: var(--warning-color, #ffc107);
		color: var(--text-primary, #2c3e50);
		cursor: not-allowed;
	}

	.action-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.no-sessions {
		text-align: center;
		padding: 40px 20px;
		color: var(--text-secondary, #6c757d);
	}

	.no-sessions-icon {
		font-size: 48px;
		margin-bottom: 16px;
		opacity: 0.5;
	}

	.no-sessions-text p {
		margin: 8px 0;
	}

	.no-sessions-text .hint {
		font-size: 0.9rem;
		opacity: 0.8;
		margin-bottom: 16px;
	}

	.manual-connect-btn {
		background: var(--accent-color, #007bff);
		color: white;
		border: none;
		border-radius: 4px;
		padding: 8px 16px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: all 0.2s ease;
	}

	.manual-connect-btn:hover {
		background: var(--accent-dark, #0056b3);
	}

	.auto-discovery-section {
		margin-bottom: 16px;
	}

	.section-header {
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

	.section-header:hover {
		background: var(--bg-hover, #f1f3f4);
	}

	.section-header h4 {
		margin: 0;
		font-size: 1rem;
		color: var(--text-primary, #2c3e50);
	}

	.expand-icon {
		font-size: 12px;
		color: var(--text-secondary, #6c757d);
		transition: transform 0.2s ease;
	}

	.expand-icon.expanded {
		transform: rotate(0deg);
	}

	.auto-discovery-content {
		margin-top: 8px;
		padding: 16px;
		background: var(--bg-primary, #ffffff);
		border: 1px solid var(--border-color, #e1e5e9);
		border-radius: 6px;
	}
</style>