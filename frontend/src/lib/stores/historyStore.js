import { writable } from 'svelte/store';

// History store for undo/redo functionality
function createHistoryStore() {
	const { subscribe, set, update } = writable({
		history: [],
		currentIndex: -1,
		maxHistorySize: 50
	});

	return {
		subscribe,
		
		// Add a new state to history
		pushState: (state, description) => {
			update(store => {
				// Remove any future states if we're not at the end
				if (store.currentIndex < store.history.length - 1) {
					store.history = store.history.slice(0, store.currentIndex + 1);
				}
				
				// Add new state
				store.history.push({
					state: JSON.parse(JSON.stringify(state)), // Deep clone
					description,
					timestamp: Date.now()
				});
				
				// Maintain max history size
				if (store.history.length > store.maxHistorySize) {
					store.history.shift();
				} else {
					store.currentIndex++;
				}
				
				return store;
			});
		},
		
		// Undo to previous state
		undo: () => {
			let undoState = null;
			update(store => {
				if (store.currentIndex > 0) {
					store.currentIndex--;
					undoState = store.history[store.currentIndex];
				}
				return store;
			});
			return undoState;
		},
		
		// Redo to next state
		redo: () => {
			let redoState = null;
			update(store => {
				if (store.currentIndex < store.history.length - 1) {
					store.currentIndex++;
					redoState = store.history[store.currentIndex];
				}
				return store;
			});
			return redoState;
		},
		
		// Check if undo is available
		canUndo: () => {
			let canUndo = false;
			update(store => {
				canUndo = store.currentIndex > 0;
				return store;
			});
			return canUndo;
		},
		
		// Check if redo is available
		canRedo: () => {
			let canRedo = false;
			update(store => {
				canRedo = store.currentIndex < store.history.length - 1;
				return store;
			});
			return canRedo;
		},
		
		// Clear history
		clear: () => {
			set({
				history: [],
				currentIndex: -1,
				maxHistorySize: 50
			});
		},
		
		// Get current state info
		getCurrentStateInfo: () => {
			let info = null;
			update(store => {
				if (store.currentIndex >= 0 && store.currentIndex < store.history.length) {
					info = {
						description: store.history[store.currentIndex].description,
						timestamp: store.history[store.currentIndex].timestamp,
						index: store.currentIndex,
						total: store.history.length
					};
				}
				return store;
			});
			return info;
		}
	};
}

export const historyStore = createHistoryStore();

// Keyboard shortcut handler
export function setupHistoryKeyboardShortcuts(undoCallback, redoCallback) {
	function handleKeydown(event) {
		// Ctrl+Z or Cmd+Z for undo
		if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
			event.preventDefault();
			const undoState = historyStore.undo();
			if (undoState && undoCallback) {
				undoCallback(undoState.state, undoState.description);
			}
		}
		
		// Ctrl+Shift+Z or Cmd+Shift+Z for redo
		if ((event.ctrlKey || event.metaKey) && event.key === 'z' && event.shiftKey) {
			event.preventDefault();
			const redoState = historyStore.redo();
			if (redoState && redoCallback) {
				redoCallback(redoState.state, redoState.description);
			}
		}
		
		// Ctrl+Y or Cmd+Y for redo (alternative)
		if ((event.ctrlKey || event.metaKey) && event.key === 'y') {
			event.preventDefault();
			const redoState = historyStore.redo();
			if (redoState && redoCallback) {
				redoCallback(redoState.state, redoState.description);
			}
		}
	}
	
	document.addEventListener('keydown', handleKeydown);
	
	// Return cleanup function
	return () => {
		document.removeEventListener('keydown', handleKeydown);
	};
}