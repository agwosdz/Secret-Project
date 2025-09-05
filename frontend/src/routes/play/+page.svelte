<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';

	// Playback state
	let playbackState: 'idle' | 'playing' | 'paused' | 'stopped' = 'idle';
	let currentTime = 0;
	let totalDuration = 0;
	let songInfo = {
		filename: '',
		originalFilename: '',
		size: 0
	};

	// Enhanced playback controls
	let tempoMultiplier = 1.0;
	let volumeMultiplier = 1.0;
	let loopEnabled = false;
	let loopStart = 0;
	let loopEnd = 0;
	let isDragging = false;
	let timelineElement: HTMLElement;

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
		if (!browser) return;
		
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
		
		// Add keyboard shortcuts
		const handleKeydown = (event) => {
			// Ignore if user is typing in an input field
			if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
				return;
			}
			
			switch (event.code) {
				case 'Space':
					event.preventDefault();
					if (playbackState === 'playing') {
						handlePause();
					} else {
						handlePlay();
					}
					break;
				case 'KeyS':
					event.preventDefault();
					handleStop();
					break;
				case 'KeyL':
					event.preventDefault();
					handleLoopToggle();
					break;
				case 'ArrowLeft':
					event.preventDefault();
					// Seek backward 10 seconds
					const newTimeBack = Math.max(0, currentTime - 10);
					handleSeek(newTimeBack);
					break;
				case 'ArrowRight':
					event.preventDefault();
					// Seek forward 10 seconds
					const newTimeForward = Math.min(totalDuration, currentTime + 10);
					handleSeek(newTimeForward);
					break;
				case 'ArrowUp':
					event.preventDefault();
					// Increase volume by 10%
					volumeMultiplier = Math.min(1, volumeMultiplier + 0.1);
					handleVolumeChange(volumeMultiplier);
					break;
				case 'ArrowDown':
					event.preventDefault();
					// Decrease volume by 10%
					volumeMultiplier = Math.max(0, volumeMultiplier - 0.1);
					handleVolumeChange(volumeMultiplier);
					break;
				case 'Minus':
				case 'NumpadSubtract':
					event.preventDefault();
					// Decrease tempo by 5%
					tempoMultiplier = Math.max(0.25, tempoMultiplier - 0.05);
					handleTempoChange(tempoMultiplier);
					break;
				case 'Equal':
				case 'NumpadAdd':
					event.preventDefault();
					// Increase tempo by 5%
					tempoMultiplier = Math.min(2.0, tempoMultiplier + 0.05);
					handleTempoChange(tempoMultiplier);
					break;
				case 'Digit0':
				case 'Numpad0':
					event.preventDefault();
					// Reset tempo to 1x
					tempoMultiplier = 1.0;
					handleTempoChange(tempoMultiplier);
					break;
			}
		};
		
		window.addEventListener('keydown', handleKeydown);
		
		// Store the cleanup function
		window.keydownCleanup = () => {
			window.removeEventListener('keydown', handleKeydown);
		};
	});

	onDestroy(() => {
		if (websocket) {
			websocket.close();
		}
		if (statusInterval) {
			clearInterval(statusInterval);
		}
		// Clean up keyboard event listeners
		if (browser && window.keydownCleanup) {
			window.keydownCleanup();
		}
	});

	function initWebSocket() {
		if (!browser) return;
		
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
				
				websocket.on('extended_playback_status', (data) => {
					updateExtendedPlaybackState(data);
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
	
	function updateExtendedPlaybackState(data) {
		// Handle extended WebSocket status updates
		playbackState = data.state || 'idle';
		currentTime = data.current_time || 0;
		totalDuration = data.total_duration || 0;
		progressPercentage = data.progress_percentage || 0;
		
		// Update enhanced controls
		tempoMultiplier = data.tempo_multiplier || 1.0;
		volumeMultiplier = data.volume_multiplier || 1.0;
		loopEnabled = data.loop_enabled || false;
		loopStart = data.loop_start || 0;
		loopEnd = data.loop_end || 0;
		
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
			
			// Initialize basic song info
			songInfo = {
				filename,
				originalFilename: filename.replace(/_\d+_[a-f0-9]+/, ''), // Remove timestamp and UUID
				size: 0,
				metadata: null
			};
			
			// Fetch MIDI metadata from backend
			try {
				const response = await fetch('/api/parse-midi', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ filename })
				});
				
				if (response.ok) {
					const data = await response.json();
					if (data.metadata) {
						songInfo.metadata = data.metadata;
					}
					if (data.duration) {
						totalDuration = data.duration / 1000; // Convert ms to seconds
					} else {
						totalDuration = 180; // Fallback duration
					}
				} else {
					console.warn('Failed to fetch MIDI metadata, using defaults');
					totalDuration = 180; // Fallback duration
				}
			} catch (metadataError) {
				console.warn('Error fetching MIDI metadata:', metadataError);
				totalDuration = 180; // Fallback duration
			}
			
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

	// Enhanced playback control functions
	async function handleSeek(time: number) {
		try {
			errorMessage = '';
			const response = await fetch('/api/seek', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ time })
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to seek';
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to seek';
			console.error('Seek error:', error);
		}
	}

	async function handleTempoChange(tempo: number) {
		try {
			errorMessage = '';
			const response = await fetch('/api/tempo', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ tempo })
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to set tempo';
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to set tempo';
			console.error('Tempo error:', error);
		}
	}

	async function handleVolumeChange(volume: number) {
		try {
			errorMessage = '';
			const response = await fetch('/api/volume', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ volume })
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to set volume';
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to set volume';
			console.error('Volume error:', error);
		}
	}

	async function handleLoopToggle() {
		try {
			errorMessage = '';
			const response = await fetch('/api/loop', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ 
					enabled: !loopEnabled,
					start: loopStart,
					end: loopEnd || totalDuration
				})
			});

			const data = await response.json();
			if (data.status !== 'success') {
				errorMessage = data.message || 'Failed to toggle loop';
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Network error: Failed to toggle loop';
			console.error('Loop error:', error);
		}
	}

	// Timeline interaction functions
	function handleTimelineClick(event: MouseEvent | TouchEvent) {
		if (!timelineElement || totalDuration === 0) return;
		
		const rect = timelineElement.getBoundingClientRect();
		let clientX: number;
		
		if (event instanceof TouchEvent) {
			if (event.touches.length === 0) return;
			clientX = event.touches[0].clientX;
		} else {
			clientX = event.clientX;
		}
		
		const clickX = clientX - rect.left;
		const percentage = clickX / rect.width;
		const newTime = percentage * totalDuration;
		
		handleSeek(Math.max(0, Math.min(newTime, totalDuration)));
	}

	function handleTimelineDragStart(event: MouseEvent | TouchEvent) {
		isDragging = true;
		event.preventDefault();
	}

	function handleTimelineDrag(event: MouseEvent | TouchEvent) {
		if (!isDragging || !timelineElement || totalDuration === 0) return;
		
		const rect = timelineElement.getBoundingClientRect();
		let clientX: number;
		
		if (event instanceof TouchEvent) {
			if (event.touches.length === 0) return;
			clientX = event.touches[0].clientX;
			// Prevent page scrolling while dragging the timeline
			event.preventDefault();
		} else {
			clientX = event.clientX;
		}
		
		const dragX = clientX - rect.left;
		const percentage = Math.max(0, Math.min(1, dragX / rect.width));
		const newTime = percentage * totalDuration;
		
		// Update current time immediately for visual feedback
		currentTime = newTime;
		progressPercentage = percentage * 100;
	}

	function handleTimelineDragEnd(event: MouseEvent | TouchEvent) {
		if (!isDragging) return;
		
		isDragging = false;
		handleSeek(currentTime);
	}

	function handleTimelineKeydown(event: KeyboardEvent) {
		const step = totalDuration * 0.01; // 1% of total duration
		let newTime = currentTime;
		
		switch (event.key) {
			case 'ArrowLeft':
				event.preventDefault();
				newTime = Math.max(0, currentTime - step);
				break;
			case 'ArrowRight':
				event.preventDefault();
				newTime = Math.min(totalDuration, currentTime + step);
				break;
			case 'Home':
				event.preventDefault();
				newTime = 0;
				break;
			case 'End':
				event.preventDefault();
				newTime = totalDuration;
				break;
			case ' ':
			case 'Enter':
				event.preventDefault();
				togglePlayback();
				return;
			default:
				return;
		}
		
		handleSeek(newTime);
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
					<div class="song-meta-grid">
						<div class="meta-item">
							<span class="meta-label">Duration:</span>
							<span class="meta-value">{formatTime(totalDuration)}</span>
						</div>
						{#if songInfo.size > 0}
							<div class="meta-item">
								<span class="meta-label">Size:</span>
								<span class="meta-value">{formatFileSize(songInfo.size)}</span>
							</div>
						{/if}
						{#if songInfo.metadata}
							{#if songInfo.metadata.tempo}
								<div class="meta-item">
									<span class="meta-label">Tempo:</span>
									<span class="meta-value">{songInfo.metadata.tempo} BPM</span>
								</div>
							{/if}
							{#if songInfo.metadata.tracks}
								<div class="meta-item">
									<span class="meta-label">Tracks:</span>
									<span class="meta-value">{songInfo.metadata.tracks}</span>
								</div>
							{/if}
							{#if songInfo.metadata.type !== undefined}
								<div class="meta-item">
									<span class="meta-label">Type:</span>
									<span class="meta-value">MIDI {songInfo.metadata.type}</span>
								</div>
							{/if}
							{#if songInfo.metadata.title}
								<div class="meta-item">
									<span class="meta-label">Title:</span>
									<span class="meta-value">{songInfo.metadata.title}</span>
								</div>
							{/if}
						{/if}
					</div>
				</div>
			</div>

			<!-- Interactive Timeline -->
			<div class="timeline-section">
				<div class="time-display">
					<span class="current-time">{formatTime(currentTime)}</span>
					<span class="total-time">{formatTime(totalDuration)}</span>
				</div>
				<div 
				class="timeline" 
				bind:this={timelineElement}
				role="slider"
				tabindex="0"
				aria-label="Timeline scrubber"
				aria-valuemin="0"
				aria-valuemax={totalDuration}
				aria-valuenow={currentTime}
				on:click={handleTimelineClick}
				on:keydown={handleTimelineKeydown}
				on:mousedown={handleTimelineDragStart}
				on:mousemove={handleTimelineDrag}
				on:mouseup={handleTimelineDragEnd}
				on:mouseleave={handleTimelineDragEnd}
				on:touchstart={handleTimelineDragStart}
				on:touchmove={handleTimelineDrag}
				on:touchend={handleTimelineDragEnd}
				on:touchcancel={handleTimelineDragEnd}
					class:dragging={isDragging}
					aria-valuetext="{formatTime(currentTime)}"
				>
					<div class="timeline-track">
						<div class="timeline-progress" style="width: {progressPercentage}%"></div>
						{#if loopEnabled}
							<div 
								class="loop-region" 
								style="left: {(loopStart / totalDuration) * 100}%; width: {((loopEnd - loopStart) / totalDuration) * 100}%"
							></div>
						{/if}
						<div class="timeline-handle" style="left: {progressPercentage}%"></div>
					</div>
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
					aria-label="Play"
				>
					<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
						<path d="M8 5v14l11-7z"/>
					</svg>
					<span class="btn-text">Play</span>
				</button>

				<button 
					on:click={handlePause} 
					disabled={playbackState === 'idle' || playbackState === 'stopped'}
					class="control-btn pause-btn"
					class:active={playbackState === 'paused'}
					aria-label="{playbackState === 'paused' ? 'Resume' : 'Pause'}"
				>
					<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
						<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
					</svg>
					<span class="btn-text">{playbackState === 'paused' ? 'Resume' : 'Pause'}</span>
				</button>

				<button 
					on:click={handleStop} 
					disabled={playbackState === 'idle' || playbackState === 'stopped'}
					class="control-btn stop-btn"
					aria-label="Stop"
				>
					<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
						<path d="M6 6h12v12H6z"/>
					</svg>
					<span class="btn-text">Stop</span>
				</button>
			</div>

			<!-- Enhanced Controls -->
			<div class="enhanced-controls">
				<!-- Tempo Control -->
				<div class="control-group">
					<div class="slider-header">
						<label for="tempo-slider">Tempo: {Math.round(tempoMultiplier * 100)}%</label>
						<div class="slider-buttons">
							<button 
							class="slider-btn" 
							on:click={() => {
								tempoMultiplier = Math.max(0.25, tempoMultiplier - 0.05);
								handleTempoChange(tempoMultiplier);
							}}
							aria-label="Decrease tempo"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M19 13H5v-2h14v2z"/>
							</svg>
						</button>
						<button 
							class="slider-btn" 
							on:click={() => {
								tempoMultiplier = 1;
								handleTempoChange(tempoMultiplier);
							}}
							aria-label="Reset tempo to 1x"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
							</svg>
						</button>
						<button 
							class="slider-btn" 
							on:click={() => {
								tempoMultiplier = Math.min(2.0, tempoMultiplier + 0.05);
								handleTempoChange(tempoMultiplier);
							}}
							aria-label="Increase tempo"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
							</svg>
						</button>
						</div>
					</div>
					<input 
					id="tempo-slider"
					type="range" 
					min="0.25" 
					max="2.0" 
					step="0.05" 
					bind:value={tempoMultiplier}
					on:input={() => handleTempoChange(tempoMultiplier)}
					class="slider tempo-slider"
					aria-label="Adjust tempo"
				/>
					<div class="slider-labels">
						<span>0.25x</span>
						<span>1x</span>
						<span>2x</span>
					</div>
				</div>

				<!-- Volume Control -->
				<div class="control-group">
					<div class="slider-header">
						<label for="volume-slider">Volume: {Math.round(volumeMultiplier * 100)}%</label>
						<div class="slider-buttons">
							<button 
							class="slider-btn" 
							on:click={() => {
								volumeMultiplier = Math.max(0, volumeMultiplier - 0.1);
								handleVolumeChange(volumeMultiplier);
							}}
							aria-label="Decrease volume"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M19 13H5v-2h14v2z"/>
							</svg>
						</button>
						<button 
							class="slider-btn" 
							on:click={() => {
								volumeMultiplier = 0.5;
								handleVolumeChange(volumeMultiplier);
							}}
							aria-label="Set volume to 50%"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
							</svg>
						</button>
						<button 
							class="slider-btn" 
							on:click={() => {
								volumeMultiplier = Math.min(1, volumeMultiplier + 0.1);
								handleVolumeChange(volumeMultiplier);
							}}
							aria-label="Increase volume"
						>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
								<path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
							</svg>
						</button>
						</div>
					</div>
					<input 
					id="volume-slider"
					type="range" 
					min="0" 
					max="1" 
					step="0.01" 
					bind:value={volumeMultiplier}
					on:input={() => handleVolumeChange(volumeMultiplier)}
					class="slider volume-slider"
					aria-label="Adjust volume"
				/>
					<div class="slider-labels">
						<span>0%</span>
						<span>50%</span>
						<span>100%</span>
					</div>
				</div>

				<!-- Loop Control -->
				<div class="control-group loop-control">
					<button 
						on:click={handleLoopToggle}
						class="control-btn loop-btn"
						class:active={loopEnabled}
						aria-label="Toggle loop {loopEnabled ? 'off' : 'on'}"
					>
						<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
							<path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
						</svg>
						<span class="btn-text">Loop {loopEnabled ? 'On' : 'Off'}</span>
					</button>
					{#if loopEnabled}
						<div class="loop-info">
							<span>Loop: {formatTime(loopStart)} - {formatTime(loopEnd)}</span>
						</div>
					{/if}
				</div>
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

			<!-- Keyboard Shortcuts Help -->
			<div class="keyboard-shortcuts">
				<details>
					<summary>⌨️ Keyboard Shortcuts</summary>
					<div class="shortcuts-grid">
						<div class="shortcut-item">
							<kbd>Space</kbd>
							<span>Play/Pause</span>
						</div>
						<div class="shortcut-item">
							<kbd>S</kbd>
							<span>Stop</span>
						</div>
						<div class="shortcut-item">
							<kbd>L</kbd>
							<span>Toggle Loop</span>
						</div>
						<div class="shortcut-item">
							<kbd>←</kbd>
							<span>Seek -10s</span>
						</div>
						<div class="shortcut-item">
							<kbd>→</kbd>
							<span>Seek +10s</span>
						</div>
						<div class="shortcut-item">
							<kbd>↑</kbd>
							<span>Volume +10%</span>
						</div>
						<div class="shortcut-item">
							<kbd>↓</kbd>
							<span>Volume -10%</span>
						</div>
						<div class="shortcut-item">
							<kbd>+</kbd>
							<span>Tempo +5%</span>
						</div>
						<div class="shortcut-item">
							<kbd>-</kbd>
							<span>Tempo -5%</span>
						</div>
						<div class="shortcut-item">
							<kbd>0</kbd>
							<span>Reset Tempo</span>
						</div>
					</div>
				</details>
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

	.song-meta-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 0.75rem;
		margin-top: 0.75rem;
	}

	.meta-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
		border: 1px solid #e5e7eb;
	}

	.meta-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.meta-value {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
	}

	/* Timeline Section */
	.timeline-section {
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

	.timeline {
		width: 100%;
		height: 44px; /* Increased height for better touch target */
		padding: 15px 0; /* Increased padding for better touch target */
		cursor: pointer;
		user-select: none;
		touch-action: none; /* Prevent browser handling of touch events */
	}

	.timeline.dragging {
		cursor: grabbing;
	}

	.timeline-track {
		position: relative;
		width: 100%;
		height: 12px; /* Increased height for better visibility */
		background: #e5e7eb;
		border-radius: 6px;
		overflow: visible;
	}

	.timeline-progress {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #1d4ed8);
		transition: width 0.1s ease;
		border-radius: 6px;
	}

	.timeline-handle {
		position: absolute;
		top: -6px;
		width: 24px; /* Increased size for touch */
		height: 24px; /* Increased size for touch */
		background: #1d4ed8;
		border: 2px solid white;
		border-radius: 50%;
		transform: translateX(-50%);
		cursor: grab;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
		transition: all 0.1s ease;
	}

	.timeline-handle:hover,
	.timeline-handle:active {
		transform: translateX(-50%) scale(1.2);
		box-shadow: 0 4px 8px rgba(0,0,0,0.3);
	}

	.timeline.dragging .timeline-handle {
		cursor: grabbing;
		transform: translateX(-50%) scale(1.3);
	}
	
	/* Add active state for touch devices */
	@media (hover: none) {
		.timeline:active .timeline-handle {
			transform: translateX(-50%) scale(1.3);
			box-shadow: 0 4px 8px rgba(0,0,0,0.3);
		}
	}

	.loop-region {
		position: absolute;
		top: 0;
		height: 100%;
		background: rgba(34, 197, 94, 0.3);
		border: 2px solid #22c55e;
		border-radius: 4px;
		pointer-events: none;
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

	/* Enhanced Controls */
	.enhanced-controls {
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 12px;
		display: grid;
		gap: 1.5rem;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	}

	.control-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.control-group label {
		font-weight: 600;
		color: #374151;
		font-size: 0.875rem;
	}

	.slider {
		width: 100%;
		height: 6px;
		border-radius: 3px;
		background: #e5e7eb;
		outline: none;
		cursor: pointer;
		-webkit-appearance: none;
		appearance: none;
	}

	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 18px;
		height: 18px;
		border-radius: 50%;
		background: #3b82f6;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.slider::-webkit-slider-thumb:hover {
		transform: scale(1.2);
		box-shadow: 0 4px 8px rgba(0,0,0,0.3);
	}

	.slider::-moz-range-thumb {
		width: 18px;
		height: 18px;
		border-radius: 50%;
		background: #3b82f6;
		border: 2px solid white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.tempo-slider::-webkit-slider-thumb {
		background: #8b5cf6;
	}

	.volume-slider::-webkit-slider-thumb {
		background: #10b981;
	}

	.slider-labels {
		display: flex;
		justify-content: space-between;
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.25rem;
	}

	.loop-control {
		align-items: flex-start;
	}

	.loop-btn {
		background: #6366f1;
		color: white;
		margin-bottom: 0.5rem;
	}

	.loop-btn:hover:not(:disabled) {
		background: #4f46e5;
	}

	.loop-btn.active {
		background: #22c55e;
	}

	.loop-btn.active:hover {
		background: #16a34a;
	}

	.loop-info {
		padding: 0.5rem;
		background: rgba(34, 197, 94, 0.1);
		border: 1px solid #22c55e;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #166534;
		font-weight: 500;
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

	/* Keyboard Shortcuts */
	.keyboard-shortcuts {
		margin-bottom: 2rem;
	}

	.keyboard-shortcuts details {
		background: #f8fafc;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 1rem;
	}

	.keyboard-shortcuts summary {
		cursor: pointer;
		font-weight: 600;
		color: #374151;
		user-select: none;
		padding: 0.5rem 0;
	}

	.keyboard-shortcuts summary:hover {
		color: #1f2937;
	}

	.shortcuts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.shortcut-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		background: white;
		border-radius: 6px;
		border: 1px solid #e5e7eb;
	}

	.shortcut-item kbd {
		background: #374151;
		color: white;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 600;
		min-width: 24px;
		text-align: center;
		box-shadow: 0 1px 2px rgba(0,0,0,0.1);
	}

	.shortcut-item span {
		font-size: 0.875rem;
		color: #6b7280;
		flex: 1;
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

	/* Mobile and Touch Device Optimizations */
	@media (max-width: 768px) {
		.play-container {
			padding: 1rem;
		}

		.play-card {
			padding: 1.5rem;
			border-radius: 12px;
		}

		.song-meta-grid {
			grid-template-columns: 1fr;
		}

		.enhanced-controls {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}

		.keyboard-shortcuts summary {
			padding: 0.75rem 0;
		}

		.shortcuts-grid {
			grid-template-columns: 1fr;
		}

		.shortcut-item {
			padding: 0.75rem;
		}
	}

	@media (max-width: 640px) {
		.play-container {
			padding: 0.75rem;
		}

		.play-card {
			padding: 1.25rem;
		}

		h1 {
			font-size: 1.5rem;
			margin-bottom: 1.25rem;
		}

		.controls {
			flex-direction: column;
			align-items: center;
			gap: 1rem;
		}

		.control-btn {
			width: 100%;
			max-width: 200px;
			height: 48px; /* Larger touch target */
			font-size: 1rem;
		}

		.control-group {
			width: 100%;
		}

		.slider {
			height: 44px; /* Larger touch target */
			padding: 15px 0;
		}

		.slider::-webkit-slider-thumb {
			width: 24px;
			height: 24px;
		}

		.slider::-moz-range-thumb {
			width: 24px;
			height: 24px;
		}

		.navigation {
			flex-direction: column;
			gap: 1rem;
			padding-top: 1.25rem;
		}

		.nav-link {
			padding: 0.75rem 0;
			display: block;
			width: 100%;
			text-align: center;
		}
	}

	/* Touch-specific enhancements */
	@media (hover: none) {
		.control-btn:active {
			transform: translateY(2px);
			box-shadow: 0 1px 2px rgba(0,0,0,0.1);
		}

		.slider::-webkit-slider-thumb:active {
			transform: scale(1.2);
		}

		.slider::-moz-range-thumb:active {
			transform: scale(1.2);
		}
	}
</style>