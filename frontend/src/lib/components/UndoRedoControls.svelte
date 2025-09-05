<script>
	import { historyStore } from '../stores/historyStore.js';
	import { createEventDispatcher, onMount } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	let canUndo = false;
	let canRedo = false;
	let currentStateInfo = null;
	
	// Subscribe to history store changes
	$: {
		historyStore.subscribe(store => {
			canUndo = store.currentIndex > 0;
			canRedo = store.currentIndex < store.history.length - 1;
			currentStateInfo = store.currentIndex >= 0 ? {
				description: store.history[store.currentIndex]?.description,
				index: store.currentIndex,
				total: store.history.length
			} : null;
		});
	}
	
	function handleUndo() {
		const undoState = historyStore.undo();
		if (undoState) {
			dispatch('undo', {
				state: undoState.state,
				description: undoState.description
			});
		}
	}
	
	function handleRedo() {
		const redoState = historyStore.redo();
		if (redoState) {
			dispatch('redo', {
				state: redoState.state,
				description: redoState.description
			});
		}
	}
</script>

<div class="undo-redo-controls">
	<div class="controls-group">
		<button 
			class="control-btn" 
			class:disabled={!canUndo}
			on:click={handleUndo}
			disabled={!canUndo}
			data-tooltip="Undo (Ctrl+Z)"
			aria-label="Undo last action"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M3 7v6h6"/>
				<path d="m21 17a9 9 0 00-9-9 9 9 0 00-6 2.3L3 13"/>
			</svg>
		</button>
		
		<button 
			class="control-btn" 
			class:disabled={!canRedo}
			on:click={handleRedo}
			disabled={!canRedo}
			data-tooltip="Redo (Ctrl+Shift+Z)"
			aria-label="Redo last undone action"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="m21 7-6-6v6h-6a9 9 0 00-9 9 9 9 0 009 9h6"/>
				<path d="m21 13v6h-6"/>
			</svg>
		</button>
	</div>
	
	{#if currentStateInfo}
		<div class="state-info">
			<span class="state-description">{currentStateInfo.description}</span>
			<span class="state-position">{currentStateInfo.index + 1}/{currentStateInfo.total}</span>
		</div>
	{/if}
</div>

<style>
	.undo-redo-controls {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-2);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
	}
	
	.controls-group {
		display: flex;
		gap: var(--space-1);
	}
	
	.control-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		background: transparent;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		color: var(--color-text);
		cursor: pointer;
		transition: all var(--transition-fast);
		position: relative;
	}
	
	.control-btn:hover:not(.disabled) {
		background: var(--color-surface-hover);
		border-color: var(--color-primary);
		color: var(--color-primary);
		transform: translateY(-1px);
		box-shadow: var(--shadow-sm);
	}
	
	.control-btn:active:not(.disabled) {
		transform: translateY(0);
		box-shadow: none;
	}
	
	.control-btn.disabled {
		opacity: 0.4;
		cursor: not-allowed;
		color: var(--color-text-muted);
	}
	
	.control-btn svg {
		transition: transform var(--transition-fast);
	}
	
	.control-btn:hover:not(.disabled) svg {
		transform: scale(1.1);
	}
	
	.state-info {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
		font-size: var(--text-sm);
		min-width: 120px;
	}
	
	.state-description {
		color: var(--color-text);
		font-weight: 500;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 150px;
	}
	
	.state-position {
		color: var(--color-text-muted);
		font-size: var(--text-xs);
		font-family: var(--font-mono);
	}
	
	/* Responsive adjustments */
	@media (max-width: 640px) {
		.undo-redo-controls {
			padding: var(--space-1);
			gap: var(--space-2);
		}
		
		.state-info {
			display: none;
		}
		
		.control-btn {
			width: 28px;
			height: 28px;
		}
		
		.control-btn svg {
			width: 14px;
			height: 14px;
		}
	}
	
	/* Animation for state changes */
	.state-description {
		animation: fadeIn var(--transition-normal) ease-out;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(-2px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>