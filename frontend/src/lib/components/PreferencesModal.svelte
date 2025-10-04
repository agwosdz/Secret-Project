<script>
	import { createEventDispatcher } from 'svelte';
	import { settings, settingsAPI } from '$lib/stores/settings.js';
	import { derived } from 'svelte/store';
	
	// Create derived stores for preference categories from unified settings
	const preferences = derived(settings, ($settings) => ({
		upload: $settings.upload || {},
		ui: $settings.ui || {},
		a11y: $settings.a11y || {},
		help: $settings.help || {},
		history: $settings.history || {}
	}));
	import { InteractiveButton } from '$lib/components';
	
	const dispatch = createEventDispatcher();
	
	// Local copy of preferences for editing
	let localPrefs = { ...$preferences };
	
	// Track if changes have been made
	$: hasChanges = JSON.stringify(localPrefs) !== JSON.stringify($preferences);
	
	async function handleSave() {
		try {
			// Update each preference category using the unified settings API
			await settingsAPI.updateSettings({
				upload: localPrefs.upload,
				ui: localPrefs.ui,
				a11y: localPrefs.a11y,
				help: localPrefs.help,
				history: localPrefs.history
			});
			dispatch('close');
		} catch (error) {
			console.error('Failed to save preferences:', error);
			alert('Failed to save preferences. Please try again.');
		}
	}
	
	function handleCancel() {
		if (hasChanges) {
			const confirmed = confirm('You have unsaved changes. Are you sure you want to cancel?');
			if (!confirmed) return;
		}
		dispatch('close');
	}
	
	async function handleReset() {
		const confirmed = confirm('This will reset all preferences to their default values. Are you sure?');
		if (confirmed) {
			try {
				// Reset preference categories using the unified settings API
				await settingsAPI.resetCategory('upload');
				await settingsAPI.resetCategory('ui');
				await settingsAPI.resetCategory('a11y');
				await settingsAPI.resetCategory('help');
				await settingsAPI.resetCategory('history');
				localPrefs = { ...$preferences };
			} catch (error) {
				console.error('Failed to reset preferences:', error);
				alert('Failed to reset preferences. Please try again.');
			}
		}
	}
	
	async function handleApplySmartDefaults() {
		try {
			// Apply smart defaults by updating with optimized settings
			const smartDefaults = {
				upload: {
					...localPrefs.upload,
					autoProcess: true,
					showPreview: true
				},
				ui: {
					...localPrefs.ui,
					theme: 'auto',
					animations: true
				},
				a11y: {
					...localPrefs.a11y,
					highContrast: false,
					reducedMotion: false
				}
			};
			
			await settingsAPI.updateSettings(smartDefaults);
			localPrefs = { ...$preferences };
		} catch (error) {
			console.error('Failed to apply smart defaults:', error);
			alert('Failed to apply smart defaults. Please try again.');
		}
	}
	
	async function handleExport() {
		try {
			const exportedSettings = await settingsAPI.exportSettings();
			const data = JSON.stringify(exportedSettings, null, 2);
			const blob = new Blob([data], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = 'midi-visualizer-settings.json';
			a.click();
			URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Failed to export settings:', error);
			alert('Failed to export settings. Please try again.');
		}
	}
	
	async function handleImport(event) {
		const file = event.target.files[0];
		if (!file) return;
		
		const reader = new FileReader();
		reader.onload = async (e) => {
			try {
				const importedSettings = JSON.parse(e.target.result);
				await settingsAPI.importSettings(importedSettings);
				localPrefs = { ...$preferences };
				alert('Settings imported successfully!');
			} catch (error) {
				console.error('Failed to import settings:', error);
				alert('Failed to import settings. Please check the file format.');
			}
		};
		reader.readAsText(file);
	}
</script>

<div class="modal-backdrop" on:click={handleCancel}>
	<div class="modal-content" on:click|stopPropagation>
		<div class="modal-header">
			<h2>Preferences</h2>
			<button class="close-btn" on:click={handleCancel} aria-label="Close preferences">
				×
			</button>
		</div>
		
		<div class="modal-body">
			<div class="preference-sections">
				<!-- Upload Preferences -->
				<section class="preference-section">
					<h3>Upload Settings</h3>
					<div class="preference-group">
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.upload.autoUpload}
							/>
							<span>Auto-upload files when selected</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.upload.rememberLastDirectory}
							/>
							<span>Remember last directory</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.upload.showFilePreview}
							/>
							<span>Show file preview</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.upload.confirmBeforeReset}
							/>
							<span>Confirm before resetting</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.upload.enableValidationPreview}
							/>
							<span>Show validation preview before upload</span>
						</label>
					</div>
				</section>
				
				<!-- UI Preferences -->
				<section class="preference-section">
					<h3>Interface</h3>
					<div class="preference-group">
						<label class="select-label">
							<span>Theme</span>
							<select bind:value={localPrefs.ui.theme}>
								<option value="auto">Auto (System)</option>
								<option value="light">Light</option>
								<option value="dark">Dark</option>
							</select>
						</label>
						
						<label class="select-label">
							<span>Animation Speed</span>
							<select bind:value={localPrefs.ui.animationSpeed}>
								<option value="slow">Slow</option>
								<option value="normal">Normal</option>
								<option value="fast">Fast</option>
							</select>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.ui.reducedMotion}
							/>
							<span>Reduce motion</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.ui.showTooltips}
							/>
							<span>Show tooltips</span>
						</label>
						
						<label class="range-label">
							<span>Tooltip Delay: {localPrefs.ui.tooltipDelay}ms</span>
							<input 
								type="range" 
								min="0" 
								max="1000" 
								step="50"
								bind:value={localPrefs.ui.tooltipDelay}
							/>
						</label>
					</div>
				</section>
				
				<!-- Accessibility Preferences -->
				<section class="preference-section">
					<h3>Accessibility</h3>
					<div class="preference-group">
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.a11y.highContrast}
							/>
							<span>High contrast mode</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.a11y.largeText}
							/>
							<span>Large text</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.a11y.keyboardNavigation}
							/>
							<span>Enhanced keyboard navigation</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.a11y.screenReaderOptimized}
							/>
							<span>Screen reader optimizations</span>
						</label>
					</div>
				</section>
				
				<!-- Help Preferences -->
				<section class="preference-section">
					<h3>Help & Onboarding</h3>
					<div class="preference-group">
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.help.showOnboarding}
							/>
							<span>Show onboarding tour</span>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.help.showHints}
							/>
							<span>Show helpful hints</span>
						</label>
					</div>
				</section>
				
				<!-- History Preferences -->
				<section class="preference-section">
					<h3>History & Undo</h3>
					<div class="preference-group">
						<label class="range-label">
							<span>Max History Size: {localPrefs.history.maxHistorySize}</span>
							<input 
								type="range" 
								min="10" 
								max="100" 
								step="5"
								bind:value={localPrefs.history.maxHistorySize}
							/>
						</label>
						
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={localPrefs.history.persistHistory}
							/>
							<span>Persist history between sessions</span>
						</label>
					</div>
				</section>
			</div>
		</div>
		
		<div class="modal-footer">
			<div class="footer-left">
				<InteractiveButton 
					variant="ghost" 
					size="small"
					on:click={handleApplySmartDefaults}
				>
					Apply Smart Defaults
				</InteractiveButton>
				
				<InteractiveButton 
					variant="ghost" 
					size="small"
					on:click={handleExport}
				>
					Export
				</InteractiveButton>
				
				<label class="import-btn">
					<InteractiveButton 
						variant="ghost" 
						size="small"
					>
						Import
					</InteractiveButton>
					<input 
						type="file" 
						accept=".json"
						on:change={handleImport}
						style="display: none;"
					/>
				</label>
				
				<InteractiveButton 
					variant="ghost" 
					size="small"
					on:click={handleReset}
				>
					Reset All
				</InteractiveButton>
			</div>
			
			<div class="footer-right">
				<InteractiveButton 
					variant="ghost" 
					size="medium"
					on:click={handleCancel}
				>
					Cancel
				</InteractiveButton>
				
				<InteractiveButton 
					variant="primary" 
					size="medium"
					disabled={!hasChanges}
					on:click={handleSave}
				>
					Save Changes
				</InteractiveButton>
			</div>
		</div>
	</div>
</div>

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}
	
	.modal-content {
		background: var(--color-surface);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xl);
		max-width: 800px;
		width: 100%;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.modal-header {
		padding: 1.5rem;
		border-bottom: 1px solid var(--color-border);
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	
	.modal-header h2 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--color-text-primary);
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 1.5rem;
		cursor: pointer;
		padding: 0.25rem;
		border-radius: var(--radius-sm);
		color: var(--color-text-secondary);
		transition: all var(--duration-fast) var(--easing-standard);
	}
	
	.close-btn:hover {
		background: var(--color-surface-hover);
		color: var(--color-text-primary);
	}
	
	.modal-body {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}
	
	.preference-sections {
		display: grid;
		gap: 2rem;
	}
	
	.preference-section {
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 1.5rem;
	}
	
	.preference-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--color-text-primary);
	}
	
	.preference-group {
		display: grid;
		gap: 1rem;
	}
	
	.checkbox-label,
	.select-label,
	.range-label {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: var(--radius-sm);
		transition: background-color var(--duration-fast) var(--easing-standard);
	}
	
	.checkbox-label:hover,
	.select-label:hover,
	.range-label:hover {
		background: var(--color-surface-hover);
	}
	
	.checkbox-label input[type="checkbox"] {
		width: 1.125rem;
		height: 1.125rem;
		accent-color: var(--color-primary);
	}
	
	.select-label {
		justify-content: space-between;
	}
	
	.select-label select {
		padding: 0.5rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text-primary);
		font-size: 0.875rem;
		min-width: 120px;
	}
	
	.range-label {
		flex-direction: column;
		align-items: stretch;
		gap: 0.5rem;
	}
	
	.range-label input[type="range"] {
		width: 100%;
		accent-color: var(--color-primary);
	}
	
	.modal-footer {
		padding: 1.5rem;
		border-top: 1px solid var(--color-border);
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	
	.footer-left,
	.footer-right {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.import-btn {
		position: relative;
		cursor: pointer;
	}
	
	@media (max-width: 768px) {
		.modal-content {
			max-width: 100%;
			margin: 0;
			border-radius: 0;
			height: 100vh;
			max-height: 100vh;
		}
		
		.modal-footer {
			flex-direction: column;
			align-items: stretch;
		}
		
		.footer-left,
		.footer-right {
			justify-content: center;
			flex-wrap: wrap;
		}
	}
</style>