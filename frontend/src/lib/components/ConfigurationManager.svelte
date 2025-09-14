<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';

    // Stores
    const validationResult = writable(null);
    const configHistory = writable([]);
    const isLoading = writable(false);
    const message = writable('');
    const messageType = writable('info'); // 'success', 'error', 'info', 'warning'

    // Component state
    let showValidation = false;
    let showHistory = false;
    let exportPath = '';
    let importFile = null;

    // Load configuration history on mount
    onMount(async () => {
        await loadConfigHistory();
    });

    async function loadConfigHistory() {
        try {
            $isLoading = true;
            const response = await fetch('/api/config/history');
            const data = await response.json();
            
            if (data.success) {
                $configHistory = data.history;
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Failed to load configuration history: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    async function validateCurrentConfig() {
        try {
            $isLoading = true;
            showMessage('Validating configuration...', 'info');
            
            // Get current config first
            const configResponse = await fetch('/api/config');
            const configData = await configResponse.json();
            
            if (!configData.success) {
                showMessage('Failed to get current configuration', 'error');
                return;
            }
            
            // Validate the configuration
            const response = await fetch('/api/config/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData.config)
            });
            
            const data = await response.json();
            
            if (data.success) {
                $validationResult = data.validation;
                showValidation = true;
                
                if (data.validation.is_valid) {
                    showMessage('Configuration is valid!', 'success');
                } else {
                    showMessage(`Configuration has ${data.validation.errors.length} error(s)`, 'warning');
                }
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Validation failed: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    async function backupConfig() {
        try {
            $isLoading = true;
            showMessage('Creating backup...', 'info');
            
            const response = await fetch('/api/config/backup', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage(data.message, 'success');
                await loadConfigHistory();
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Backup failed: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    async function restoreConfig() {
        if (!confirm('Are you sure you want to restore from backup? This will overwrite your current configuration.')) {
            return;
        }
        
        try {
            $isLoading = true;
            showMessage('Restoring from backup...', 'info');
            
            const response = await fetch('/api/config/restore', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage(data.message, 'success');
                await loadConfigHistory();
                // Reload page to reflect changes
                setTimeout(() => window.location.reload(), 2000);
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Restore failed: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    async function resetConfig() {
        if (!confirm('Are you sure you want to reset to default configuration? This cannot be undone.')) {
            return;
        }
        
        try {
            $isLoading = true;
            showMessage('Resetting to defaults...', 'info');
            
            const response = await fetch('/api/config/reset', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage(data.message, 'success');
                await loadConfigHistory();
                // Reload page to reflect changes
                setTimeout(() => window.location.reload(), 2000);
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Reset failed: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    async function exportConfig() {
        try {
            $isLoading = true;
            showMessage('Exporting configuration...', 'info');
            
            const response = await fetch('/api/config/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: exportPath || undefined })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage(`${data.message}`, 'success');
                exportPath = ''; // Clear the input
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            showMessage(`Export failed: ${error.message}`, 'error');
        } finally {
            $isLoading = false;
        }
    }

    function showMessage(msg, type) {
        $message = msg;
        $messageType = type;
        setTimeout(() => {
            $message = '';
        }, 5000);
    }

    function formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }
</script>

<div class="config-manager">
    <h3>Configuration Management</h3>
    
    <!-- Message Display -->
    {#if $message}
        <div class="message {$messageType}">
            {$message}
        </div>
    {/if}
    
    <!-- Action Buttons -->
    <div class="actions">
        <button 
            class="btn btn-primary" 
            on:click={validateCurrentConfig}
            disabled={$isLoading}
        >
            {$isLoading ? 'Validating...' : 'Validate Configuration'}
        </button>
        
        <button 
            class="btn btn-secondary" 
            on:click={backupConfig}
            disabled={$isLoading}
        >
            {$isLoading ? 'Backing up...' : 'Create Backup'}
        </button>
        
        <button 
            class="btn btn-warning" 
            on:click={restoreConfig}
            disabled={$isLoading}
        >
            {$isLoading ? 'Restoring...' : 'Restore from Backup'}
        </button>
        
        <button 
            class="btn btn-danger" 
            on:click={resetConfig}
            disabled={$isLoading}
        >
            {$isLoading ? 'Resetting...' : 'Reset to Defaults'}
        </button>
    </div>
    
    <!-- Export Section -->
    <div class="export-section">
        <h4>Export Configuration</h4>
        <div class="export-controls">
            <input 
                type="text" 
                bind:value={exportPath} 
                placeholder="Optional: custom export path"
                class="export-input"
            />
            <button 
                class="btn btn-secondary" 
                on:click={exportConfig}
                disabled={$isLoading}
            >
                {$isLoading ? 'Exporting...' : 'Export'}
            </button>
        </div>
    </div>
    
    <!-- Validation Results -->
    {#if showValidation && $validationResult}
        <div class="validation-results">
            <h4>Validation Results</h4>
            <div class="validation-status {$validationResult.is_valid ? 'valid' : 'invalid'}">
                Status: {$validationResult.is_valid ? 'Valid' : 'Invalid'}
            </div>
            
            {#if $validationResult.errors.length > 0}
                <div class="errors">
                    <h5>Errors:</h5>
                    <ul>
                        {#each $validationResult.errors as error}
                            <li class="error">{error}</li>
                        {/each}
                    </ul>
                </div>
            {/if}
            
            {#if $validationResult.warnings.length > 0}
                <div class="warnings">
                    <h5>Warnings:</h5>
                    <ul>
                        {#each $validationResult.warnings as warning}
                            <li class="warning">{warning}</li>
                        {/each}
                    </ul>
                </div>
            {/if}
            
            <button class="btn btn-small" on:click={() => showValidation = false}>
                Close
            </button>
        </div>
    {/if}
    
    <!-- Configuration History -->
    <div class="history-section">
        <div class="history-header">
            <h4>Configuration History</h4>
            <button 
                class="btn btn-small" 
                on:click={() => showHistory = !showHistory}
            >
                {showHistory ? 'Hide' : 'Show'} History
            </button>
        </div>
        
        {#if showHistory}
            <div class="history-list">
                {#if $configHistory.length === 0}
                    <p class="no-history">No configuration history available.</p>
                {:else}
                    {#each $configHistory as entry}
                        <div class="history-entry">
                            <div class="history-timestamp">
                                {formatTimestamp(entry.timestamp)}
                            </div>
                            <div class="history-action">
                                {entry.action}
                            </div>
                            {#if entry.description}
                                <div class="history-description">
                                    {entry.description}
                                </div>
                            {/if}
                        </div>
                    {/each}
                {/if}
            </div>
        {/if}
    </div>
</div>

<style>
    .config-manager {
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 20px 0;
    }
    
    h3 {
        margin: 0 0 20px 0;
        color: #333;
    }
    
    h4 {
        margin: 20px 0 10px 0;
        color: #555;
    }
    
    .message {
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-weight: 500;
    }
    
    .message.success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .message.error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .message.warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .message.info {
        background: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    
    .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    
    .btn {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.2s;
    }
    
    .btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .btn-primary {
        background: #007bff;
        color: white;
    }
    
    .btn-primary:hover:not(:disabled) {
        background: #0056b3;
    }
    
    .btn-secondary {
        background: #6c757d;
        color: white;
    }
    
    .btn-secondary:hover:not(:disabled) {
        background: #545b62;
    }
    
    .btn-warning {
        background: #ffc107;
        color: #212529;
    }
    
    .btn-warning:hover:not(:disabled) {
        background: #e0a800;
    }
    
    .btn-danger {
        background: #dc3545;
        color: white;
    }
    
    .btn-danger:hover:not(:disabled) {
        background: #c82333;
    }
    
    .btn-small {
        padding: 4px 8px;
        font-size: 12px;
        background: #e9ecef;
        color: #495057;
    }
    
    .btn-small:hover:not(:disabled) {
        background: #dee2e6;
    }
    
    .export-section {
        border-top: 1px solid #dee2e6;
        padding-top: 20px;
    }
    
    .export-controls {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .export-input {
        flex: 1;
        padding: 8px;
        border: 1px solid #ced4da;
        border-radius: 4px;
        font-size: 14px;
    }
    
    .validation-results {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 15px;
        margin: 20px 0;
    }
    
    .validation-status {
        font-weight: bold;
        margin-bottom: 10px;
        padding: 5px;
        border-radius: 4px;
    }
    
    .validation-status.valid {
        background: #d4edda;
        color: #155724;
    }
    
    .validation-status.invalid {
        background: #f8d7da;
        color: #721c24;
    }
    
    .errors, .warnings {
        margin: 10px 0;
    }
    
    .errors ul, .warnings ul {
        margin: 5px 0;
        padding-left: 20px;
    }
    
    .error {
        color: #721c24;
    }
    
    .warning {
        color: #856404;
    }
    
    .history-section {
        border-top: 1px solid #dee2e6;
        padding-top: 20px;
    }
    
    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .history-list {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        background: white;
    }
    
    .history-entry {
        padding: 10px;
        border-bottom: 1px solid #f8f9fa;
    }
    
    .history-entry:last-child {
        border-bottom: none;
    }
    
    .history-timestamp {
        font-size: 12px;
        color: #6c757d;
    }
    
    .history-action {
        font-weight: 500;
        margin: 2px 0;
    }
    
    .history-description {
        font-size: 14px;
        color: #495057;
    }
    
    .no-history {
        padding: 20px;
        text-align: center;
        color: #6c757d;
        font-style: italic;
    }
</style>