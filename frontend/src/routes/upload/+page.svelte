<script lang="ts">
	import { uploadMidiFile, validateMidiFile, formatFileSize, UploadError, type UploadProgress } from '$lib/upload';

	let fileInput: HTMLInputElement;
	let selectedFile: File | null = null;
	let uploadStatus: 'idle' | 'uploading' | 'success' | 'error' = 'idle';
	let uploadMessage = '';
	let uploadProgress = 0;

	// Handle file selection
	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) {
			selectedFile = null;
			return;
		}

		const validation = validateMidiFile(file);
		if (!validation.valid) {
			uploadStatus = 'error';
			uploadMessage = validation.message;
			selectedFile = null;
			// Clear the input
			target.value = '';
			return;
		}

		selectedFile = file;
		uploadStatus = 'idle';
		uploadMessage = '';
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
			Select a MIDI file (.mid or .midi) to upload for LED visualization playback.
		</p>

		<div class="upload-section">
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
					{selectedFile ? selectedFile.name : 'Choose MIDI file'}
				</label>
			</div>

			{#if selectedFile}
				<div class="file-info">
					<p><strong>File:</strong> {selectedFile.name}</p>
					<p><strong>Size:</strong> {formatFileSize(selectedFile.size)}</p>
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
				<p>{uploadMessage}</p>
				{#if uploadStatus === 'uploading'}
					<div class="progress-bar">
						<div class="progress-fill" style="width: {uploadProgress}%"></div>
					</div>
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
		padding: 3rem 2rem;
		border: 2px dashed #d1d5db;
		border-radius: 8px;
		background: #f9fafb;
		color: #374151;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.file-label:hover {
		border-color: #3b82f6;
		background: #eff6ff;
		color: #1d4ed8;
	}

	.file-label.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.upload-icon {
		width: 2rem;
		height: 2rem;
		stroke-width: 2;
	}

	.file-info {
		background: #f3f4f6;
		border-radius: 6px;
		padding: 1rem;
		margin-bottom: 1rem;
	}

	.file-info p {
		margin: 0.25rem 0;
		color: #374151;
		font-size: 0.875rem;
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
		padding: 1rem;
		border-radius: 6px;
		text-align: center;
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
	}

	.upload-status p {
		margin: 0;
		font-weight: 500;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
		margin-top: 0.75rem;
	}

	.progress-fill {
		height: 100%;
		background: #059669;
		transition: width 0.3s ease;
	}

	@media (max-width: 640px) {
		.upload-container {
			padding: 1rem;
		}

		.upload-card {
			padding: 1.5rem;
		}

		.file-label {
			padding: 2rem 1rem;
		}

		h1 {
			font-size: 1.5rem;
		}
	}
</style>