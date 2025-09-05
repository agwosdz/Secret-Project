<script lang="ts">
	import { uploadMidiFile, validateMidiFile, formatFileSize, UploadError, type UploadProgress, type ValidationResult } from '$lib/upload';
	import { toastStore } from '$lib/stores/toastStore.js';
import { historyStore, setupHistoryKeyboardShortcuts } from '$lib/stores/historyStore.js';
import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
import ProgressBar from '$lib/components/ProgressBar.svelte';
import InteractiveButton from '$lib/components/InteractiveButton.svelte';
import UndoRedoControls from '$lib/components/UndoRedoControls.svelte';
import Tooltip from '$lib/components/Tooltip.svelte';
import OnboardingTour from '$lib/components/OnboardingTour.svelte';
import PreferencesModal from '$lib/components/PreferencesModal.svelte';
import ValidationMessage from '$lib/components/ValidationMessage.svelte';
import SmartInput from '$lib/components/SmartInput.svelte';
import StatusDisplay from '$lib/components/StatusDisplay.svelte';
import { createFileUploadPrevention } from '$lib/errorPrevention';
import { VALIDATION_PRESETS } from '$lib/validation';
import { statusManager, statusUtils } from '$lib/statusCommunication';
import { helpActions, shouldShowOnboarding, setupHelpKeyboardShortcuts } from '$lib/stores/helpStore.js';
import { uploadPreferences, uiPreferences, preferenceActions, preferenceUtils } from '$lib/stores/preferencesStore.js';
import { onMount } from 'svelte';

	let fileInput: HTMLInputElement;
	let dropZone: HTMLDivElement;
	let selectedFile: File | null = null;
	let uploadStatus: 'idle' | 'uploading' | 'success' | 'error' = 'idle';
	let uploadMessage = '';
	let uploadProgress = 0;
	let isDragOver = false;
	let dragCounter = 0;
	let showOnboardingTour = false;
	let helpKeyboardCleanup = null;
	let showPreferencesModal = false;
	let validationResult: ValidationResult | null = null;
	
	// Smart input configuration
	const { manager: fileUploadPrevention, tips: fileUploadTips } = createFileUploadPrevention({
		showPreventiveTips: true,
		showRealTimeValidation: true,
		debounceMs: 300
	});
	
	const fileValidationOptions = {
		rules: VALIDATION_PRESETS.file('1MB', ['mid', 'midi']),
		field: 'MIDI file',
		showSuggestions: true
	};
	
	// Preference variables
	$: uploadPrefs = $uploadPreferences;
	$: uiPrefs = $uiPreferences;
	$: shouldShowTooltips = preferenceUtils.shouldShowTooltips();
	$: tooltipDelay = preferenceUtils.getTooltipDelay();
	$: shouldReduceMotion = preferenceUtils.shouldReduceMotion();
	
	// Smart defaults based on preferences
	$: if (uploadPrefs?.autoUpload && selectedFile && !uploadStatus) {
		// Auto-upload if enabled and file is selected
		setTimeout(() => {
			if (uploadStatus === 'idle') {
				handleUpload();
			}
		}, 1000);
	}
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

		// Remember last directory if preference is enabled
		if (uploadPrefs?.rememberLastDirectory && file.webkitRelativePath) {
			preferenceActions.update('upload', 'lastDirectory', file.webkitRelativePath);
		}

		processSelectedFile(file);
		
		// Save state after file selection
		if (file) {
			saveState(`Selected file: ${file.name}`);
		}
	}

	// Handler for SmartInput validation
	function handleSmartValidation(event: CustomEvent) {
		const { detail } = event;
		validationResult = detail;
		
		// If validation passes, process the file
		if (detail && detail.valid && selectedFile) {
			uploadMessage = '';
			uploadStatus = 'idle';
			statusUtils.validationSuccess(selectedFile.name);
		} else if (detail && !detail.valid) {
			uploadMessage = detail.message;
			uploadStatus = 'error';
			// Don't show status message for validation errors as they're handled by ValidationMessage component
		}
	}
	
	// Handler for SmartInput file change
	function handleSmartFileChange(event: CustomEvent) {
		const { detail } = event;
		if (detail.value instanceof File) {
			selectedFile = detail.value;
			// Remember last directory if preference is enabled
			if (uploadPrefs?.rememberLastDirectory && detail.value.webkitRelativePath) {
				preferenceActions.update('upload', 'lastDirectory', detail.value.webkitRelativePath);
			}
			processSelectedFile(detail.value);
		} else {
			selectedFile = null;
			fileMetadata = null;
		}
	}

	// Process a selected file (common logic for click and drag-drop)
	function processSelectedFile(file: File) {
		// Start processing status
		const processingId = statusUtils.processingStart(file.name, 'Validating MIDI file...');
		
		const validation = validateMidiFile(file);
		validationResult = validation;
		
		if (!validation.valid) {
			uploadStatus = 'error';
			uploadMessage = validation.message + (validation.suggestion ? ` ${validation.suggestion}` : '');
			selectedFile = null;
			fileMetadata = null;
			
			// Show validation error toast with suggestion
			toastStore.error(validation.message, {
				title: 'Invalid File',
				description: validation.suggestion
			});
			
			statusUtils.processingError(processingId, file.name, validation.message);
			
			// Clear the input if it was from file input
			if (fileInput) {
				fileInput.value = '';
			}
			return;
		}

		selectedFile = file;
		uploadStatus = 'idle';
		uploadMessage = '';
		validationResult = null; // Clear validation on success
		
		statusUtils.processingSuccess(processingId, file.name, 'File validated successfully');
		
		// Generate file metadata
		fileMetadata = {
			name: file.name,
			size: formatFileSize(file.size),
			type: file.type || 'audio/midi',
			lastModified: new Date(file.lastModified).toLocaleString()
		};
		
		// Save state after processing file
		saveState(`Processed file: ${file.name}`);
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
			
			// Save state after drag and drop
			if (file) {
				saveState(`Dropped file: ${file.name}`);
			}
		}
	}

	// Handle file upload with progress tracking
	async function handleUpload() {
		if (!selectedFile) return;

		// Start upload progress tracking
		const progressId = statusUtils.uploadStart(selectedFile.name);
		uploadStatus = 'uploading';
			uploadProgress = 0;
			uploadMessage = 'Uploading...';
			
			// Save state before upload
			saveState(`Started upload: ${selectedFile.name}`);

		try {
			const result = await uploadMidiFile(selectedFile, (progress: UploadProgress) => {
				uploadProgress = progress.percentage;
				uploadMessage = `Uploading... ${progress.percentage}%`;
				statusUtils.uploadProgress(progressId, progress.percentage, `${progress.percentage}%`);
			});

			uploadStatus = 'success';
			uploadMessage = `Successfully uploaded: ${result.filename}`;
			uploadProgress = 100;
			
			// Complete upload with success status
			statusUtils.uploadSuccess(progressId, result.filename, [
				{
					label: 'Play Visualization',
					action: () => window.location.href = '/play',
					variant: 'primary',
					icon: '▶'
				},
				{
					label: 'Upload Another',
					action: () => resetUpload(),
					variant: 'secondary',
					icon: '📁'
				}
			]);
			
			// Store the uploaded filename for the play page
			localStorage.setItem('lastUploadedFile', result.filename);
			
			// Save successful upload state
			saveState(`Upload completed: ${result.filename}`);
			
			// Reset form after a short delay
			setTimeout(() => {
				resetUpload();
				saveState('Reset upload form');
			}, 2000);
		} catch (error) {
			uploadStatus = 'error';
			let errorMessage = 'An unexpected error occurred during upload';
			
			if (error instanceof UploadError) {
				errorMessage = error.message;
			} else {
				console.error('Upload error:', error);
			}
			
			uploadMessage = errorMessage;
			
			// Show upload error with retry action
			statusUtils.uploadError(progressId, selectedFile.name, errorMessage, [
				{
					label: 'Retry Upload',
					action: () => handleUpload(),
					variant: 'primary',
					icon: '🔄'
				},
				{
					label: 'Choose Different File',
					action: () => resetUpload(),
					variant: 'secondary',
					icon: '📁'
				}
			]);
			
			// Save error state
			saveState(`Upload failed: ${errorMessage}`);
		}
	}

	// Reset upload state
	function resetUpload() {
		// Show confirmation if preference is enabled and there's content to lose
		if (uploadPrefs?.confirmBeforeReset && (selectedFile || uploadStatus === 'success')) {
			const confirmed = confirm('Are you sure you want to reset? This will clear your current file and progress.');
			if (!confirmed) return;
		}
		
		selectedFile = null;
		fileMetadata = null;
		uploadStatus = 'idle';
		uploadMessage = '';
			uploadProgress = 0;
			validationResult = null;
			fileInput.value = '';
			
			// Clear status messages
			statusManager.clearAll();
			
			// Save reset state
			saveState('Reset upload form');
	}

	// State management functions
	function saveState(description: string) {
		const state = {
			selectedFile: selectedFile ? {
				name: selectedFile.name,
				size: selectedFile.size,
				type: selectedFile.type,
				lastModified: selectedFile.lastModified
			} : null,
			fileMetadata,
			uploadStatus,
			uploadMessage,
			uploadProgress
		};
		historyStore.pushState(state, description);
	}

	function restoreState(state: any, description: string) {
		selectedFile = state.selectedFile ? new File([], state.selectedFile.name, {
			type: state.selectedFile.type,
			lastModified: state.selectedFile.lastModified
		}) : null;
		fileMetadata = state.fileMetadata;
		uploadStatus = state.uploadStatus;
		uploadMessage = state.uploadMessage;
		uploadProgress = state.uploadProgress;
		
		toastStore.info(description, {
			title: 'State Restored'
		});
	}

	// Onboarding tour handlers
	function handleTourComplete() {
		helpActions.completeTour();
		showOnboardingTour = false;
	}

	function handleTourSkip() {
		helpActions.skipTour();
		showOnboardingTour = false;
	}

	// Preferences modal handlers
	function openPreferences() {
		showPreferencesModal = true;
	}

	function closePreferences() {
		showPreferencesModal = false;
	}

	onMount(() => {
		// Auto-focus the file input when component mounts
		if (fileInput) {
			fileInput.focus();
		}
		
		// Setup keyboard shortcuts for undo/redo
		const cleanupKeyboardShortcuts = setupHistoryKeyboardShortcuts(
			(state, description) => {
				// Undo callback - restore previous state
				restoreState(state, `Undid: ${description}`);
			},
			(state, description) => {
				// Redo callback - restore next state
				restoreState(state, `Redid: ${description}`);
			}
		);
		
		// Set up help system keyboard shortcuts
		helpKeyboardCleanup = setupHelpKeyboardShortcuts();
		
		// Set help context
		helpActions.setContext('upload');
		
		// Check if onboarding should be shown
		const unsubscribe = shouldShowOnboarding.subscribe(shouldShow => {
			if (shouldShow) {
				// Delay to ensure DOM is ready
				setTimeout(() => {
					showOnboardingTour = true;
				}, 1000);
			}
		});
		
		// Listen for help events
		function handleShowHelp() {
			showOnboardingTour = true;
		}
		
		function handleStartTour() {
			showOnboardingTour = true;
		}
		
		window.addEventListener('show-help', handleShowHelp);
		window.addEventListener('start-tour', handleStartTour);
		
		// Cleanup on component destroy
		return () => {
			cleanupKeyboardShortcuts();
			unsubscribe();
			if (helpKeyboardCleanup) helpKeyboardCleanup();
			window.removeEventListener('show-help', handleShowHelp);
			window.removeEventListener('start-tour', handleStartTour);
		};
	});
</script>

<svelte:head>
	<title>Upload MIDI - Piano LED Visualizer</title>
	<meta name="description" content="Upload MIDI files for LED visualization" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
</svelte:head>

<a href="#main-content" class="skip-link">Skip to main content</a>

<div class="upload-container">
	{#if shouldShowTooltips}
		<Tooltip text="Use Ctrl+Z/Ctrl+Y or these buttons to undo/redo actions" position="left" delay={tooltipDelay}>
			<UndoRedoControls 
				on:undo={(event) => restoreState(event.detail.state, `Undid: ${event.detail.description}`)}
				on:redo={(event) => restoreState(event.detail.state, `Redid: ${event.detail.description}`)}
			/>
		</Tooltip>
	{:else}
		<UndoRedoControls 
			on:undo={(event) => restoreState(event.detail.state, `Undid: ${event.detail.description}`)}
			on:redo={(event) => restoreState(event.detail.state, `Redid: ${event.detail.description}`)}
		/>
	{/if}

	<!-- Preferences Button -->
	<div class="preferences-button-container">
		{#if shouldShowTooltips}
			<Tooltip text="Open preferences to customize upload settings" position="left" delay={tooltipDelay}>
				<InteractiveButton
					variant="ghost"
					size="small"
					class="preferences-btn"
					on:click={openPreferences}
					aria-label="Open preferences"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="preferences-icon">
						<circle cx="12" cy="12" r="3"/>
						<path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m17-4a4 4 0 0 1-8 0 4 4 0 0 1 8 0zM7 21a4 4 0 0 1-8 0 4 4 0 0 1 8 0z"/>
					</svg>
				</InteractiveButton>
			</Tooltip>
		{:else}
			<InteractiveButton
				variant="ghost"
				size="small"
				class="preferences-btn"
				on:click={openPreferences}
				aria-label="Open preferences"
			>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="preferences-icon">
					<circle cx="12" cy="12" r="3"/>
					<path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m17-4a4 4 0 0 1-8 0 4 4 0 0 1 8 0zM7 21a4 4 0 0 1-8 0 4 4 0 0 1 8 0z"/>
				</svg>
			</InteractiveButton>
		{/if}
	</div>
	<!-- Status Display -->
<StatusDisplay />

<main id="main-content" class="upload-card" role="main" aria-labelledby="page-title">
		<h1 id="page-title">Upload MIDI File</h1>
		<p class="description" role="doc-subtitle">
			Drag and drop a MIDI file (.mid or .midi) or click to browse for LED visualization playback.
		</p>

		<div class="upload-section">
			{#if shouldShowTooltips}
			<Tooltip text="Click to browse or drag and drop MIDI files (.mid, .midi)" position="bottom" delay={tooltipDelay}>
				<div 
					bind:this={dropZone}
					class="drop-zone interactive" 
					class:drag-over={isDragOver}
					class:has-file={selectedFile}
					class:disabled={uploadStatus === 'uploading'}
					on:dragenter={handleDragEnter}
					on:dragleave={handleDragLeave}
					on:dragover={handleDragOver}
					on:drop={handleDrop}
					on:click={() => fileInput.click()}
					on:keydown={(e) => {
						if (e.key === 'Enter' || e.key === ' ') {
							e.preventDefault();
							fileInput.click();
						}
					}}
					role="button"
					aria-label="Click to select MIDI file or drag and drop"
					aria-describedby="drop-zone-help"
					tabindex="0"
				>
				<div class="file-input-wrapper">
					<SmartInput
						bind:this={fileInput}
						type="file"
						accept=".mid,.midi"
						id="midi-file"
						label="MIDI File"
						placeholder="Choose a MIDI file to upload"
						validationOptions={fileValidationOptions}
						errorPrevention={fileUploadPrevention}
						disabled={uploadStatus === 'uploading'}
						required
						helpText="Supported formats: .mid, .midi (max 1MB)"
						on:validation={handleSmartValidation}
						on:change={handleSmartFileChange}
						aria-label="Select MIDI file"
						aria-describedby="file-input-help"
						class="smart-file-input"
					/>
					
					<!-- Hidden help text for screen readers -->
					<div id="drop-zone-help" class="sr-only">
						Select a MIDI file by clicking this area or dragging and dropping a file. Supported formats: .mid, .midi
					</div>
					<div id="file-input-help" class="sr-only">
						Choose a MIDI file from your computer. Only .mid and .midi files are accepted.
					</div>
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
			</Tooltip>
		{:else}
			<div 
				bind:this={dropZone}
				class="drop-zone interactive" 
				class:drag-over={isDragOver}
				class:has-file={selectedFile}
				class:disabled={uploadStatus === 'uploading'}
				on:dragenter={handleDragEnter}
				on:dragleave={handleDragLeave}
				on:dragover={handleDragOver}
				on:drop={handleDrop}
				on:click={() => fileInput.click()}
				on:keydown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') {
						e.preventDefault();
						fileInput.click();
					}
				}}
				role="button"
				aria-label="Click to select MIDI file or drag and drop"
				aria-describedby="drop-zone-help"
				tabindex="0"
			>
			<div class="file-input-wrapper">
				<SmartInput
					bind:this={fileInput}
					type="file"
					accept=".mid,.midi"
					id="midi-file"
					label="MIDI File"
					placeholder="Choose a MIDI file to upload"
					validationOptions={fileValidationOptions}
					errorPrevention={fileUploadPrevention}
					disabled={uploadStatus === 'uploading'}
					required
					helpText="Supported formats: .mid, .midi (max 1MB)"
					on:validation={handleSmartValidation}
					on:change={handleSmartFileChange}
					aria-label="Select MIDI file"
					aria-describedby="file-input-help"
					class="smart-file-input"
				/>
				
				<!-- Hidden help text for screen readers -->
				<div id="drop-zone-help" class="sr-only">
					Select a MIDI file by clicking this area or dragging and dropping a file. Supported formats: .mid, .midi
				</div>
				<div id="file-input-help" class="sr-only">
					Choose a MIDI file from your computer. Only .mid and .midi files are accepted.
				</div>
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
		{/if}

			{#if fileMetadata}
			<section class="file-metadata card-interactive" role="region" aria-labelledby="file-preview-title">
				<div class="metadata-header">
					<svg class="file-icon pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
						<path d="M9 12l2 2 4-4" />
						<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
						<path d="M3 5c0-1.66 4-3 9-3s9 1.34 9 3" />
						<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
					</svg>
					<h3 id="file-preview-title">File Preview</h3>
				</div>
					<div class="metadata-grid" role="list" aria-label="File properties">
						<div class="metadata-item" role="listitem">
							<span class="metadata-label">Name:</span>
							<span class="metadata-value" aria-label="File name: {fileMetadata.name}">{fileMetadata.name}</span>
						</div>
						<div class="metadata-item" role="listitem">
							<span class="metadata-label">Size:</span>
							<span class="metadata-value" aria-label="File size: {fileMetadata.size}">{fileMetadata.size}</span>
						</div>
						<div class="metadata-item" role="listitem">
							<span class="metadata-label">Type:</span>
							<span class="metadata-value" aria-label="File type: {fileMetadata.type}">{fileMetadata.type}</span>
						</div>
						<div class="metadata-item" role="listitem">
							<span class="metadata-label">Modified:</span>
							<span class="metadata-value" aria-label="Last modified: {fileMetadata.lastModified}">{fileMetadata.lastModified}</span>
						</div>
					</div>
				</section>
			{/if}

			<div class="upload-actions" role="group" aria-labelledby="upload-actions-title">
				<h3 id="upload-actions-title" class="sr-only">Upload Actions</h3>
				{#if shouldShowTooltips}
				<Tooltip text={selectedFile ? 'Upload your MIDI file for LED visualization' : 'Select a MIDI file first'} position="top" delay={tooltipDelay}>
					<InteractiveButton 
						variant="primary"
						size="large"
						disabled={!selectedFile || uploadStatus === 'uploading'}
						loading={uploadStatus === 'uploading'}
						class="upload-btn"
						on:click={handleUpload}
						aria-describedby={selectedFile ? 'file-preview-title' : undefined}
					>
						{uploadStatus === 'uploading' ? 'Uploading...' : 'Upload File'}
					</InteractiveButton>
				</Tooltip>
			{:else}
				<InteractiveButton 
					variant="primary"
					size="large"
					disabled={!selectedFile || uploadStatus === 'uploading'}
					loading={uploadStatus === 'uploading'}
					class="upload-btn"
					on:click={handleUpload}
					aria-describedby={selectedFile ? 'file-preview-title' : undefined}
				>
					{uploadStatus === 'uploading' ? 'Uploading...' : 'Upload File'}
				</InteractiveButton>
			{/if}

				{#if uploadStatus === 'uploading'}
					<div class="progress-section">
						<ProgressBar 
							progress={uploadProgress} 
							label="Upload Progress"
							showPercentage={true}
							size="md"
							variant="default"
							animated={true}
						/>
					</div>
				{/if}

				{#if uploadStatus === 'success'}
					{#if shouldShowTooltips}
					<Tooltip text="Start the LED visualization with your uploaded MIDI file" position="top" delay={tooltipDelay}>
						<a href="/play" class="play-btn" role="button" aria-label="Navigate to play page to start LED visualization">Play Song</a>
					</Tooltip>
				{:else}
					<a href="/play" class="play-btn" role="button" aria-label="Navigate to play page to start LED visualization">Play Song</a>
				{/if}
					{#if shouldShowTooltips}
						<Tooltip text="Upload another MIDI file" position="top" delay={tooltipDelay}>
							<InteractiveButton 
								variant="ghost"
								size="medium"
								class="reset-btn"
								aria-label="Reset form to upload another MIDI file"
								on:click={resetUpload}
							>
								Upload Another
							</InteractiveButton>
						</Tooltip>
					{:else}
						<InteractiveButton 
							variant="ghost"
							size="medium"
							class="reset-btn"
							aria-label="Reset form to upload another MIDI file"
							on:click={resetUpload}
						>
							Upload Another
						</InteractiveButton>
					{/if}
				{:else if uploadStatus === 'error'}
					{#if shouldShowTooltips}
					<Tooltip text="Clear the error and try uploading again" position="top" delay={tooltipDelay}>
						<InteractiveButton 
							variant="ghost"
							size="medium"
							class="reset-btn"
							aria-label="Clear error and reset form to try uploading again"
							on:click={resetUpload}
						>
							Try Again
						</InteractiveButton>
					</Tooltip>
				{:else}
					<InteractiveButton 
						variant="ghost"
						size="medium"
						class="reset-btn"
						aria-label="Clear error and reset form to try uploading again"
						on:click={resetUpload}
					>
						Try Again
					</InteractiveButton>
				{/if}
				{/if}
			</div>
		</div>

		<ValidationMessage 
			validation={validationResult} 
			variant="card" 
			showDetails={true}
		/>
		
		{#if uploadMessage && uploadStatus !== 'error'}
			<div class="upload-status" class:success={uploadStatus === 'success'}>
				{#if uploadStatus === 'uploading'}
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
	</main>
	
	<!-- Onboarding Tour -->
	{#if showOnboardingTour}
		<OnboardingTour 
			on:complete={handleTourComplete}
			on:skip={handleTourSkip}
		/>
	{/if}

	<!-- Preferences Modal -->
	{#if showPreferencesModal}
		<PreferencesModal
			on:close={closePreferences}
		/>
	{/if}
	
	<!-- Live regions for screen readers -->
	<div aria-live="polite" aria-atomic="true" class="sr-only">
		{#if uploadMessage && uploadStatus !== 'error'}
			{uploadMessage}
		{/if}
	</div>
	
	<div aria-live="assertive" aria-atomic="true" class="sr-only">
		{#if uploadStatus === 'success'}
			File uploaded successfully! You can now play your song.
		{:else if uploadStatus === 'error'}
			Upload failed: {message}
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
		position: relative;
	}

	.upload-container :global(.undo-redo-controls) {
		position: absolute;
		top: 1rem;
		right: 1rem;
		z-index: 10;
	}

	.preferences-button-container {
		position: absolute;
		top: 1rem;
		left: 1rem;
		z-index: 10;
	}

	.preferences-button-container :global(.preferences-btn) {
		padding: 0.5rem;
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: all 0.2s ease;
	}

	.preferences-button-container :global(.preferences-btn:hover) {
		background: white;
		border-color: #cbd5e0;
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
	}

	.preferences-icon {
		width: 1.25rem;
		height: 1.25rem;
		stroke-width: 2;
		color: #4a5568;
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
		overflow: hidden;
	}

	.drop-zone::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(66, 153, 225, 0.1), transparent);
		transition: left 0.6s ease;
		pointer-events: none;
	}

	.drop-zone:hover {
		border-color: #4299e1;
		background: #ebf8ff;
		transform: translateY(-2px);
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
	}

	.drop-zone:hover::before {
		left: 100%;
	}

	.drop-zone.drag-over {
		border-color: #3182ce;
		background: #bee3f8;
		box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.1);
		transform: scale(1.02);
		animation: pulse 1s ease-in-out infinite;
	}

	.drop-zone:active {
		transform: translateY(0) scale(0.98);
		transition: transform 0.1s ease;
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
		transition: all 0.2s ease;
	}

	.file-metadata:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		border-color: #cbd5e0;
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
		transition: all 0.2s ease;
	}

	.file-metadata:hover .file-icon {
		transform: scale(1.1) rotate(5deg);
		stroke: #3182ce;
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
		transition: all 0.2s ease;
		cursor: help;
	}

	.metadata-value:hover {
		background: #ebf8ff;
		border-color: #4299e1;
		transform: translateY(-1px);
		box-shadow: 0 2px 4px rgba(66, 153, 225, 0.1);
	}

	.upload-actions {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		align-items: center;
		justify-content: center;
		margin-top: 1.5rem;
	}

	.progress-section {
		width: 100%;
		margin-top: 1rem;
	}

	.upload-btn {
		background: linear-gradient(135deg, #3b82f6, #1d4ed8);
		color: white;
		border: none;
		padding: 0.875rem 2rem;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
		min-width: 140px;
		position: relative;
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
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

	.error-suggestions {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #fca5a5;
		font-size: 0.875rem;
		line-height: 1.4;
	}

	.error-suggestions p {
		margin: 0.25rem 0;
		color: #7f1d1d;
	}

	.error-suggestions strong {
		color: #991b1b;
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

	/* Screen Reader Only */
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}
	
	/* Focus Management */
	.drop-zone:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
		box-shadow: 0 0 0 4px rgba(var(--color-primary-rgb), 0.1);
	}
	
	.file-label:focus-within {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
	
	/* Skip to content link for keyboard users */
	.skip-link {
		position: absolute;
		top: -40px;
		left: 6px;
		background: var(--color-primary);
		color: white;
		padding: 8px;
		text-decoration: none;
		border-radius: 4px;
		z-index: 1000;
		transition: top 0.3s;
	}
	
	.skip-link:focus {
		top: 6px;
	}
	
	/* Mobile and Touch-Friendly Responsive Styles */
	@media (max-width: 768px) {
		.upload-container {
			padding: 0.75rem;
		}

		.upload-card {
			padding: 1.25rem;
			margin: 0.5rem;
			border-radius: 12px;
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
			grid-template-columns: 1fr;
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

		.upload-btn, .play-btn, .cancel-btn, .retry-button {
			padding: 0.875rem 1.5rem;
			font-size: 1rem;
			min-height: 48px; /* iOS recommended touch target */
			width: 100%;
			/* Enhanced touch feedback */
			tap-highlight-color: transparent;
			-webkit-tap-highlight-color: transparent;
			transform: scale(1);
			transition: transform 0.1s ease, background-color 0.2s ease;
		}

		.upload-btn:active, .cancel-btn:active, .retry-button:active, .play-btn:active {
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
	}
	
	/* SmartInput integration styles */
	:global(.smart-file-input) {
		width: 100%;
		background: transparent;
		border: none;
		padding: 0;
		margin: 0;
	}
	
	:global(.smart-file-input .form-field) {
		background: transparent;
		border: none;
		padding: 0;
		margin: 0;
	}
	
	:global(.smart-file-input .form-field input[type="file"]) {
		opacity: 0;
		position: absolute;
		width: 100%;
		height: 100%;
		cursor: pointer;
		z-index: 1;
	}
	
	:global(.smart-file-input .validation-message) {
		margin-top: 0.5rem;
		position: relative;
		z-index: 2;
	}
	
	:global(.smart-file-input .preventive-tips) {
		margin-top: 0.5rem;
		position: relative;
		z-index: 2;
		background: rgba(255, 255, 255, 0.95);
		border-radius: 8px;
		padding: 0.75rem;
		border: 1px solid #e5e7eb;
		}
</style>