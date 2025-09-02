<script lang="ts">
	import { uploadMidiFile, validateMidiFile, formatFileSize, UploadError, type UploadProgress } from '$lib/upload';

	let fileInput: HTMLInputElement;
	let dropZone: HTMLDivElement;
	let selectedFile: File | null = null;
	let uploadStatus: 'idle' | 'uploading' | 'success' | 'error' = 'idle';
	let uploadMessage = '';
	let uploadProgress = 0;
	let isDragOver = false;
	let dragCounter = 0;
	let fileMetadata: {
		name: string;
		size: string;
		type: string;
		lastModified: string;
	} | null = null;

	// Handle file selection (both click and drag-drop)
	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) {
			selectedFile = null;
			fileMetadata = null;
			return;
		}

		processSelectedFile(file);
	}

	// Process a selected file (common logic for click and drag-drop)
	function processSelectedFile(file: File) {
		const validation = validateMidiFile(file);
		if (!validation.valid) {
			uploadStatus = 'error';
		uploadMessage = validation.message;
		selectedFile = null;
		fileMetadata = null;
		// Clear the input if it was from file input
		if (fileInput) {
			fileInput.value = '';
		}
		return;
		}

		selectedFile = file;
		uploadStatus = 'idle';
		uploadMessage = '';
		
		// Generate file metadata
		fileMetadata = {
			name: file.name,
			size: formatFileSize(file.size),
			type: file.type || 'audio/midi',
			lastModified: new Date(file.lastModified).toLocaleString()
		};
	}

	// Drag and drop event handlers
	function handleDragEnter(event: DragEvent) {
		event.preventDefault();
		dragCounter++;
		if (dragCounter === 1) {
			isDragOver = true;
		}
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		dragCounter--;
		if (dragCounter === 0) {
			isDragOver = false;
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		// Ensure we show the correct drop effect
		if (event.dataTransfer) {
			event.dataTransfer.dropEffect = 'copy';
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragOver = false;
		dragCounter = 0;

		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			const file = files[0];
			processSelectedFile(file);
		}
	}

	// Handle file upload with progress tracking
	async function handleUpload() {
		if (!selectedFile) return;

		uploadStatus = 'uploading';
		uploadProgress = 0;
		uploadMessage = 'Uploading...';

		try {
			const result = await uploadMidiFile(selectedFile, (progress: UploadProgress) => {
				uploadProgress = progress.percentage;
				uploadMessage = `Uploading... ${progress.percentage}%`;
			});

			uploadStatus = 'success';
			uploadMessage = `Successfully uploaded: ${result.filename}`;
			uploadProgress = 100;
			
			// Store the uploaded filename for the play page
			localStorage.setItem('lastUploadedFile', result.filename);
			
			// Reset form
			selectedFile = null;
			fileInput.value = '';
		} catch (error) {
			uploadStatus = 'error';
			if (error instanceof UploadError) {
				uploadMessage = error.message;
			} else {
				uploadMessage = 'An unexpected error occurred during upload';
				console.error('Upload error:', error);
			}
		}
	}

	// Reset upload state
	function resetUpload() {
		selectedFile = null;
		fileMetadata = null;
		uploadStatus = 'idle';
		uploadMessage = '';
		uploadProgress = 0;
		fileInput.value = '';
	}
</script>

<svelte:head>
	<title>Upload MIDI File</title>
	<meta name="description" content="Upload MIDI files for LED visualization" />
</svelte:head>

<div class="upload-container">
	<div class="upload-card">
		<h1>Upload MIDI File</h1>
		<p class="description">
			Drag and drop a MIDI file (.mid or .midi) or click to browse for LED visualization playback.
		</p>

		<div class="upload-section">
			<div 
				bind:this={dropZone}
				class="drop-zone" 
				class:drag-over={isDragOver}
				class:disabled={uploadStatus === 'uploading'}
				on:dragenter={handleDragEnter}
				on:dragleave={handleDragLeave}
				on:dragover={handleDragOver}
				on:drop={handleDrop}
			>
				<div class="file-input-wrapper">
					<input
						bind:this={fileInput}
						type="file"
						accept=".mid,.midi"
						on:change={handleFileSelect}
						disabled={uploadStatus === 'uploading'}
						class="file-input"
						id="midi-file"
					/>
					<label for="midi-file" class="file-label" class:disabled={uploadStatus === 'uploading'}>
						<svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
							<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
							<polyline points="7,10 12,15 17,10" />
							<line x1="12" y1="15" x2="12" y2="3" />
						</svg>
						<span class="upload-text">
							{#if isDragOver}
								Drop MIDI file here
							{:else if selectedFile}
								{selectedFile.name}
							{:else}
								Drag & drop MIDI file or click to browse
							{/if}
						</span>
					</label>
				</div>
				
				{#if isDragOver}
					<div class="drag-overlay">
						<div class="drag-indicator">
							<svg class="drop-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
								<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
								<polyline points="7,10 12,15 17,10" />
								<line x1="12" y1="15" x2="12" y2="3" />
							</svg>
							<p>Drop your MIDI file here</p>
						</div>
					</div>
				{/if}
			</div>

			{#if fileMetadata}
				<div class="file-metadata">
					<div class="metadata-header">
						<svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
							<path d="M9 12l2 2 4-4" />
							<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
							<path d="M3 5c0-1.66 4-3 9-3s9 1.34 9 3" />
							<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
						</svg>
						<h3>File Preview</h3>
					</div>
					<div class="metadata-grid">
						<div class="metadata-item">
							<span class="metadata-label">Name:</span>
							<span class="metadata-value">{fileMetadata.name}</span>
						</div>
						<div class="metadata-item">
							<span class="metadata-label">Size:</span>
							<span class="metadata-value">{fileMetadata.size}</span>
						</div>
						<div class="metadata-item">
							<span class="metadata-label">Type:</span>
							<span class="metadata-value">{fileMetadata.type}</span>
						</div>
						<div class="metadata-item">
							<span class="metadata-label">Modified:</span>
							<span class="metadata-value">{fileMetadata.lastModified}</span>
						</div>
					</div>
				</div>
			{/if}

			<div class="upload-actions">
				<button
					on:click={handleUpload}
					disabled={!selectedFile || uploadStatus === 'uploading'}
					class="upload-btn"
					class:uploading={uploadStatus === 'uploading'}
				>
					{#if uploadStatus === 'uploading'}
						Uploading...
					{:else}
						Upload File
					{/if}
				</button>

				{#if uploadStatus === 'success'}
					<a href="/play" class="play-btn">Play Song</a>
					<button on:click={resetUpload} class="reset-btn">Upload Another</button>
				{:else if uploadStatus === 'error'}
					<button on:click={resetUpload} class="reset-btn">Try Again</button>
				{/if}
			</div>
		</div>

		{#if uploadMessage}
			<div class="upload-status" class:success={uploadStatus === 'success'} class:error={uploadStatus === 'error'}>
				{#if uploadStatus === 'error'}
					<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<circle cx="12" cy="12" r="10"/>
						<line x1="15" y1="9" x2="9" y2="15"/>
						<line x1="9" y1="9" x2="15" y2="15"/>
					</svg>
					<div class="status-content">
						<h4>Upload Error</h4>
						<p>{uploadMessage}</p>
					</div>
				{:else if uploadStatus === 'uploading'}
					<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
						<polyline points="17,8 12,3 7,8" />
						<line x1="12" y1="3" x2="12" y2="15" />
					</svg>
					<div class="status-content">
						<h4>Uploading MIDI File</h4>
						<p>{selectedFile?.name} • {uploadProgress}% complete</p>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {uploadProgress}%"></div>
							<div class="progress-text">{uploadProgress}%</div>
						</div>
					</div>
				{:else if uploadStatus === 'success'}
					<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
						<polyline points="22,4 12,14.01 9,11.01" />
					</svg>
					<div class="status-content">
						<h4>Upload Successful</h4>
						<p>{uploadMessage}</p>
					</div>
				{:else}
					<p>{uploadMessage}</p>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.upload-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 80vh;
		padding: 2rem;
	}

	.upload-card {
		background: white;
		border-radius: 12px;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
		padding: 2rem;
		max-width: 500px;
		width: 100%;
	}

	h1 {
		text-align: center;
		color: #1f2937;
		margin-bottom: 0.5rem;
		font-size: 1.875rem;
		font-weight: 700;
	}

	.description {
		text-align: center;
		color: #6b7280;
		margin-bottom: 2rem;
		line-height: 1.5;
	}

	.upload-section {
		margin-bottom: 1.5rem;
	}

	.drop-zone {
		position: relative;
		width: 100%;
		max-width: 400px;
		margin: 0 auto 2rem auto;
		border: 2px dashed #cbd5e0;
		border-radius: 12px;
		padding: 2rem;
		transition: all 0.3s ease;
		background: #f8fafc;
	}

	.drop-zone:hover {
		border-color: #4299e1;
		background: #ebf8ff;
	}

	.drop-zone.drag-over {
		border-color: #3182ce;
		background: #bee3f8;
		box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.1);
		transform: scale(1.02);
	}

	.drop-zone.disabled {
		border-color: #e2e8f0;
		background: #f7fafc;
		opacity: 0.6;
		pointer-events: none;
	}

	.file-input-wrapper {
		position: relative;
		margin-bottom: 1rem;
	}

	.file-input {
		position: absolute;
		opacity: 0;
		width: 100%;
		height: 100%;
		cursor: pointer;
	}

	.file-label {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		padding: 1.5rem 1rem;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: #4a5568;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: center;
		width: 100%;
		box-sizing: border-box;
		max-width: 100%;
	}

	.file-label:hover {
		color: #2b6cb0;
	}

	.file-label.disabled {
		color: #a0aec0;
		cursor: not-allowed;
	}

	.upload-icon {
		width: 2rem;
		height: 2rem;
		stroke-width: 2;
	}

	.upload-text {
		display: block;
	}

	.drag-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(66, 153, 225, 0.1);
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		pointer-events: none;
		z-index: 10;
	}

	.drag-indicator {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		color: #3182ce;
		font-weight: 600;
		text-align: center;
	}

	.drop-icon {
		width: 3rem;
		height: 3rem;
		stroke-width: 2;
		animation: bounce 1s infinite;
	}

	@keyframes bounce {
		0%, 20%, 53%, 80%, 100% {
			transform: translate3d(0, 0, 0);
		}
		40%, 43% {
			transform: translate3d(0, -8px, 0);
		}
		70% {
			transform: translate3d(0, -4px, 0);
		}
		90% {
			transform: translate3d(0, -2px, 0);
		}
	}

	.file-metadata {
		background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	}

	.metadata-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid #e2e8f0;
	}

	.file-icon {
		width: 1.5rem;
		height: 1.5rem;
		stroke: #4299e1;
		stroke-width: 2;
	}

	.metadata-header h3 {
		margin: 0;
		color: #2d3748;
		font-size: 1.125rem;
		font-weight: 600;
	}

	.metadata-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 0.75rem;
	}

	.metadata-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
	}

	.metadata-label {
		font-weight: 500;
		color: #4a5568;
		font-size: 0.875rem;
	}

	.metadata-value {
		color: #2d3748;
		font-size: 0.875rem;
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
		background: #ffffff;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		border: 1px solid #e2e8f0;
		max-width: 60%;
		text-align: right;
		word-break: break-all;
	}

	.upload-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	.upload-btn {
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 0.75rem 1.5rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease;
		min-width: 120px;
	}

	.upload-btn:hover:not(:disabled) {
		background: #2563eb;
	}

	.upload-btn:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.upload-btn.uploading {
		background: #059669;
	}

	.reset-btn {
		background: #6b7280;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 0.75rem 1.5rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.reset-btn:hover {
		background: #4b5563;
	}

	.play-btn {
		display: inline-block;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 0.75rem 1.5rem;
		font-weight: 500;
		text-decoration: none;
		cursor: pointer;
		transition: background-color 0.2s ease;
		min-width: 120px;
		text-align: center;
	}

	.play-btn:hover {
		background: #059669;
	}

	.upload-status {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 8px;
		font-weight: 500;
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.upload-status.success {
		background: #d1fae5;
		color: #065f46;
		border: 1px solid #a7f3d0;
	}

	.upload-status.error {
		background: #fee2e2;
		color: #991b1b;
		border: 1px solid #fca5a5;
		box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.1);
	}

	.status-icon {
		width: 1.5rem;
		height: 1.5rem;
		stroke-width: 2;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.status-content {
		flex: 1;
	}

	.status-content h4 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		font-weight: 600;
	}

	.status-content p {
		margin: 0 0 0.75rem 0;
		line-height: 1.5;
	}

	.retry-button {
		background: #dc2626;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.retry-button:hover {
		background: #b91c1c;
	}

	.upload-status p {
		margin: 0;
		font-weight: 500;
	}

	.progress-bar {
		position: relative;
		width: 100%;
		height: 12px;
		background: #e5e7eb;
		border-radius: 6px;
		overflow: hidden;
		margin-top: 0.75rem;
		box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #1d4ed8);
		transition: width 0.3s ease;
		border-radius: 6px;
		position: relative;
		box-shadow: 0 1px 2px rgba(59, 130, 246, 0.3);
	}

	.progress-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.75rem;
		font-weight: 600;
		color: #374151;
		text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
		pointer-events: none;
	}

	/* Mobile and Touch-Friendly Responsive Styles */
	@media (max-width: 768px) {
		.upload-container {
			padding: 0.75rem;
		}

		.upload-card {
			padding: 1.25rem;
			margin: 0.5rem;
		}

		.file-label {
			padding: 2.5rem 1rem;
			min-height: 200px;
			/* Larger touch target for mobile */
			tap-highlight-color: transparent;
			-webkit-tap-highlight-color: transparent;
		}

		.drop-icon {
			width: 2.5rem;
			height: 2.5rem;
		}

		h1 {
			font-size: 1.5rem;
			margin-bottom: 1rem;
		}

		.file-metadata {
			padding: 1rem;
			margin-bottom: 1rem;
		}

		.metadata-grid {
			gap: 0.5rem;
		}

		.metadata-item {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.25rem;
		}

		.metadata-value {
			max-width: 100%;
			text-align: left;
			word-break: break-word;
		}

		.upload-actions {
			flex-direction: column;
			gap: 0.75rem;
		}

		.upload-btn, .cancel-btn, .retry-button {
			padding: 0.875rem 1.5rem;
			font-size: 1rem;
			min-height: 44px; /* iOS recommended touch target */
			width: 100%;
			/* Enhanced touch feedback */
			tap-highlight-color: transparent;
			-webkit-tap-highlight-color: transparent;
			transform: scale(1);
			transition: transform 0.1s ease, background-color 0.2s ease;
		}

		.upload-btn:active, .cancel-btn:active, .retry-button:active {
			transform: scale(0.98);
		}

		.progress-bar {
			height: 16px; /* Larger for better visibility on mobile */
		}

		.progress-text {
			font-size: 0.875rem;
		}
	}

	@media (max-width: 480px) {
		.upload-container {
			padding: 0.5rem;
		}

		.upload-card {
			padding: 1rem;
			margin: 0.25rem;
		}

		.file-label {
			padding: 2rem 0.75rem;
			min-height: 180px;
		}

		h1 {
			font-size: 1.25rem;
		}

		.file-metadata {
			padding: 0.75rem;
		}

		.metadata-header h3 {
			font-size: 1rem;
		}
	}

	/* Touch device specific enhancements */
	@media (hover: none) and (pointer: coarse) {
		.file-label {
			/* Remove hover effects on touch devices */
			transition: border-color 0.2s ease, background-color 0.2s ease;
		}

		.file-label:hover {
			border-color: #e5e7eb;
			background: #f9fafb;
		}

		/* Enhanced active state for touch */
		.file-label:active {
			border-color: #3b82f6;
			background: #eff6ff;
			transform: scale(0.99);
		}

		.upload-btn:hover, .cancel-btn:hover, .retry-button:hover {
			/* Disable hover effects on touch devices */
			background: #3b82f6;
		}

		.cancel-btn:hover {
			background: #6b7280;
		}

		.retry-button:hover {
			background: #dc2626;
		}
	}
</style>