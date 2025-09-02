<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	// Playback state
	let playbackState: 'idle' | 'playing' | 'paused' | 'stopped' = 'idle';
	let currentTime = 0;
	let totalDuration = 0;
	let songInfo = {
		filename: '',
		originalFilename: '',
		size: 0
	};

	// UI state
	let isLoading = false;
	let errorMessage = '';
	let progressPercentage = 0;

	// WebSocket connection for real-time updates
	let websocket: WebSocket | null = null;
	let statusInterval: NodeJS.Timeout | null = null;
	let reconnectAttempts = 0;
	const maxReconnectAttempts = 5;

	onMount(() => {
		// Get song info from URL params or localStorage
		const urlParams = new URLSearchParams(window.location.search);
		const filename = urlParams.get('file') || localStorage.getItem('lastUploadedFile');
		
		if (!filename) {
			// No file specified, redirect to upload
			goto('/upload');
			return;
		}

		// Load song information
		loadSongInfo(filename);
		
		// Initialize WebSocket connection
		initWebSocket();
		
		// Fallback polling in case WebSocket fails
		startStatusPolling();
	});

	onDestroy(() => {
		if (websocket) {
			websocket.close();
		}
		if (statusInterval) {
			clearInterval(statusInterval);
		}
	});

	function initWebSocket() {
		try {
			const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
			const wsUrl = `${protocol}//${window.location.host}/socket.io/?EIO=4&transport=websocket`;
			
			// Use Socket.IO client if available, otherwise fallback to WebSocket
			if (typeof io !== 'undefined') {
				// Socket.IO connection to backend server (use relative path for proxy)
				websocket = io();
				
				websocket.on('connect', () => {
					console.log('WebSocket connected');
					reconnectAttempts = 0;
					// Stop polling when WebSocket is connected
					if (statusInterval) {
						clearInterval(statusInterval);
						statusInterval = null;
					}
					// Request current status
					websocket.emit('get_status');
				});
				
				websocket.on('playback_status', (data) => {
					updatePlaybackState(data);
				});
				
				websocket.on('disconnect', () => {
					console.log('WebSocket disconnected');
					// Resume polling as fallback
					if (!statusInterval) {
						startStatusPolling();
					}
				});
				
				websocket.on('error', (error) => {
					console.error('WebSocket error:', error);
					// Resume polling as fallback
					if (!statusInterval) {
						startStatusPolling();
					}
				});
			} else {
				console.log('Socket.IO not available, using polling');
			}
		} catch (error) {
			console.error('Failed to initialize WebSocket:', error);
		}
	}
	
	function startStatusPolling() {
		// Poll status every 500ms (reduced frequency when WebSocket is primary)
		statusInterval = setInterval(async () => {
			await updateStatus();
		}, 500);
	}

	function updatePlaybackState(data) {
		// Handle WebSocket status updates
		playbackState = data.state || 'idle';
		currentTime = data.current_time || 0;
		totalDuration = data.total_duration || 0;
		progressPercentage = data.progress_percentage || 0;
		
		if (data.filename && data.filename !== songInfo.filename) {
			songInfo.filename = data.filename;
			songInfo.originalFilename = data.filename.replace(/_\d+_[a-f0-9]+/, '');
		}
		
		if (data.error_message) {
			errorMessage = data.error_message;
		} else {
			errorMessage = '';
		}
	}
	
	async function updateStatus() {
		try {
			const response = await fetch('/api/playback-status');
			const data = await response.json();
			
			if (data.status === 'success' && data.playback) {
				updatePlaybackState(data.playback);
			}
		} catch (err) {
			console.error('Failed to get playback status:', err);
		}
	}

	async function loadSongInfo(filename: string) {
		try {
			isLoading = true;
			errorMessage = '';
			
			// For now, we'll use the filename and simulate song info
			// In a real implementation, this would fetch parsed MIDI data
			songInfo = {
				filename,
				originalFilename: filename.replace(/_\d+_[a-f0-9]+/, ''), // Remove timestamp and UUID
				size: 0 // Will be populated when we have actual file info
			};
			
			// Simulate total duration (will be replaced with actual MIDI parsing)
			totalDuration = 180; // 3 minutes for demo
			
		} catch (error) {
			errorMessage = 'Failed to load song information';
			console.error('Error loading song info:', error);
		} finally {
			isLoading = false;
		}
	}

	async function handlePlay() {
		try {
			isLoading = true;
			errorMessage = '';
			
			const response = await fetch('/api/play', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					filename: songInfo.filename
				})
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to start playback';
			}
			
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to start playback';
			console.error('Playback error:', error);
		} finally {
			isLoading = false;
		}
	}

	async function handlePause() {
		try {
			errorMessage = '';
			const response = await fetch('/api/pause', {
				method: 'POST'
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to pause/resume playback';
			}
			
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to pause/resume playback';
			console.error('Pause error:', error);
		}
	}

	async function handleStop() {
		try {
			errorMessage = '';
			const response = await fetch('/api/stop', {
				method: 'POST'
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to stop playback';
			}
			
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to stop playback';
			console.error('Stop error:', error);
		}
	}



	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const sizes = ['Bytes', 'KB', 'MB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<svelte:head>
	<title>Play MIDI - Piano LED Visualizer</title>
	<meta name="description" content="Play MIDI file with LED visualization" />
</svelte:head>

<div class="play-container">
	<div class="play-card">
		<h1>🎹 Piano LED Visualizer</h1>
		
		{#if isLoading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Loading...</p>
			</div>
		{:else}
			<!-- Song Information -->
			<div class="song-info">
				<h2>Now Playing</h2>
				<div class="song-details">
					<p class="song-title">{songInfo.originalFilename || 'Unknown Song'}</p>
					<p class="song-meta">
						Duration: {formatTime(totalDuration)}
						{#if songInfo.size > 0}
							• Size: {formatFileSize(songInfo.size)}
						{/if}
					</p>
				</div>
			</div>

			<!-- Progress Bar -->
			<div class="progress-section">
				<div class="time-display">
					<span class="current-time">{formatTime(currentTime)}</span>
					<span class="total-time">{formatTime(totalDuration)}</span>
				</div>
				<div class="progress-bar">
					<div class="progress-fill" style="width: {progressPercentage}%"></div>
				</div>
				<div class="progress-info">
					<span class="time">{formatTime(currentTime)} / {formatTime(totalDuration)}</span>
					<span class="percentage">{Math.round(progressPercentage)}%</span>
				</div>
			</div>

			<!-- Playback Controls -->
			<div class="controls">
				<button 
					on:click={handlePlay} 
					disabled={playbackState === 'playing' || isLoading}
					class="control-btn play-btn"
					class:active={playbackState === 'playing'}
				>
					<svg viewBox="0 0 24 24" fill="currentColor">
						<path d="M8 5v14l11-7z"/>
					</svg>
					Play
				</button>

				<button 
					on:click={handlePause} 
					disabled={playbackState === 'idle' || playbackState === 'stopped'}
					class="control-btn pause-btn"
					class:active={playbackState === 'paused'}
				>
					<svg viewBox="0 0 24 24" fill="currentColor">
						<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
					</svg>
					{playbackState === 'paused' ? 'Resume' : 'Pause'}
				</button>

				<button 
					on:click={handleStop} 
					disabled={playbackState === 'idle' || playbackState === 'stopped'}
					class="control-btn stop-btn"
				>
					<svg viewBox="0 0 24 24" fill="currentColor">
						<path d="M6 6h12v12H6z"/>
					</svg>
					Stop
				</button>
			</div>

			<!-- Status Display -->
			<div class="status-section">
				<div class="status-indicator" class:playing={playbackState === 'playing'} class:paused={playbackState === 'paused'}>
					<div class="status-dot"></div>
					<span class="status-text">
						{#if playbackState === 'playing'}
							Playing
						{:else if playbackState === 'paused'}
							Paused
						{:else if playbackState === 'stopped'}
							Stopped
						{:else}
							Ready
						{/if}
					</span>
				</div>
			</div>

			<!-- Error Display -->
			{#if errorMessage}
				<div class="error-message">
					<p>{errorMessage}</p>
					<button on:click={() => errorMessage = ''} class="dismiss-btn">Dismiss</button>
				</div>
			{/if}

			<!-- Navigation -->
			<div class="navigation">
				<a href="/upload" class="nav-link">Upload Another File</a>
				<a href="/" class="nav-link">Home</a>
			</div>
		{/if}
	</div>
</div>

<style>
	.play-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 100vh;
		padding: 2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.play-card {
		background: white;
		border-radius: 16px;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
		padding: 2.5rem;
		max-width: 600px;
		width: 100%;
		text-align: center;
	}

	h1 {
		color: #1f2937;
		margin-bottom: 2rem;
		font-size: 2rem;
		font-weight: 700;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		padding: 2rem;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #e5e7eb;
		border-top: 4px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.song-info {
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 12px;
	}

	.song-info h2 {
		color: #374151;
		margin-bottom: 1rem;
		font-size: 1.25rem;
		font-weight: 600;
	}

	.song-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.song-meta {
		color: #6b7280;
		font-size: 0.875rem;
		margin: 0;
	}

	.progress-section {
		margin-bottom: 2rem;
	}

	.time-display {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
		color: #6b7280;
		font-weight: 500;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #1d4ed8);
		transition: width 0.3s ease;
	}

	.progress-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 8px;
		font-size: 0.9em;
		color: #666;
	}

	.time {
		font-family: 'Courier New', monospace;
	}

	.percentage {
		font-weight: bold;
	}

	.controls {
		display: flex;
		justify-content: center;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.control-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		min-width: 100px;
	}

	.control-btn svg {
		width: 20px;
		height: 20px;
	}

	.play-btn {
		background: #10b981;
		color: white;
	}

	.play-btn:hover:not(:disabled) {
		background: #059669;
	}

	.play-btn.active {
		background: #065f46;
	}

	.pause-btn {
		background: #f59e0b;
		color: white;
	}

	.pause-btn:hover:not(:disabled) {
		background: #d97706;
	}

	.pause-btn.active {
		background: #92400e;
	}

	.stop-btn {
		background: #ef4444;
		color: white;
	}

	.stop-btn:hover:not(:disabled) {
		background: #dc2626;
	}

	.control-btn:disabled {
		background: #9ca3af;
		cursor: not-allowed;
		opacity: 0.6;
	}

	.status-section {
		margin-bottom: 2rem;
	}

	.status-indicator {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}

	.status-dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: #9ca3af;
		transition: background-color 0.2s ease;
	}

	.status-indicator.playing .status-dot {
		background: #10b981;
		animation: pulse 2s infinite;
	}

	.status-indicator.paused .status-dot {
		background: #f59e0b;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.status-text {
		font-weight: 600;
		color: #374151;
	}

	.error-message {
		background: #fee2e2;
		color: #991b1b;
		border: 1px solid #fca5a5;
		border-radius: 8px;
		padding: 1rem;
		margin-bottom: 1.5rem;
		text-align: left;
	}

	.error-message p {
		margin: 0 0 0.5rem 0;
		font-weight: 500;
	}

	.dismiss-btn {
		background: #dc2626;
		color: white;
		border: none;
		border-radius: 4px;
		padding: 0.25rem 0.75rem;
		font-size: 0.875rem;
		cursor: pointer;
	}

	.dismiss-btn:hover {
		background: #b91c1c;
	}

	.navigation {
		display: flex;
		justify-content: center;
		gap: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.nav-link {
		color: #3b82f6;
		text-decoration: none;
		font-weight: 500;
		transition: color 0.2s ease;
	}

	.nav-link:hover {
		color: #1d4ed8;
		text-decoration: underline;
	}

	@media (max-width: 640px) {
		.play-container {
			padding: 1rem;
		}

		.play-card {
			padding: 1.5rem;
		}

		h1 {
			font-size: 1.5rem;
		}

		.controls {
			flex-direction: column;
			align-items: center;
		}

		.control-btn {
			width: 100%;
			max-width: 200px;
		}

		.navigation {
			flex-direction: column;
			gap: 1rem;
		}
	}
</style>