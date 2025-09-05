import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Default preferences
const DEFAULT_PREFERENCES = {
	// Upload preferences
	upload: {
		autoUpload: false,
		rememberLastDirectory: true,
		showFilePreview: true,
		confirmBeforeReset: true
	},
	// UI preferences
	ui: {
		theme: 'auto', // 'light', 'dark', 'auto'
		reducedMotion: false,
		showTooltips: true,
		tooltipDelay: 300,
		animationSpeed: 'normal' // 'slow', 'normal', 'fast'
	},
	// Accessibility preferences
	a11y: {
		highContrast: false,
		largeText: false,
		keyboardNavigation: true,
		screenReaderOptimized: false
	},
	// Help preferences
	help: {
		showOnboarding: true,
		showHints: true,
		completedTours: [],
		skippedTours: []
	},
	// History preferences
	history: {
		maxHistorySize: 50,
		autosaveInterval: 30000, // 30 seconds
		persistHistory: true
	}
};

// Load preferences from localStorage
function loadPreferences() {
	if (!browser) return DEFAULT_PREFERENCES;
	
	try {
		const stored = localStorage.getItem('midi-visualizer-preferences');
		if (stored) {
			const parsed = JSON.parse(stored);
			// Merge with defaults to ensure all properties exist
			return mergeDeep(DEFAULT_PREFERENCES, parsed);
		}
	} catch (error) {
		console.warn('Failed to load preferences:', error);
	}
	
	return DEFAULT_PREFERENCES;
}

// Save preferences to localStorage
function savePreferences(preferences) {
	if (!browser) return;
	
	try {
		localStorage.setItem('midi-visualizer-preferences', JSON.stringify(preferences));
	} catch (error) {
		console.warn('Failed to save preferences:', error);
	}
}

// Deep merge utility
function mergeDeep(target, source) {
	const result = { ...target };
	
	for (const key in source) {
		if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
			result[key] = mergeDeep(target[key] || {}, source[key]);
		} else {
			result[key] = source[key];
		}
	}
	
	return result;
}

// Create the main preferences store
export const preferences = writable(loadPreferences());

// Subscribe to changes and save to localStorage
if (browser) {
	preferences.subscribe(savePreferences);
}

// Derived stores for specific preference categories
export const uploadPreferences = derived(
	preferences,
	$preferences => $preferences.upload
);

export const uiPreferences = derived(
	preferences,
	$preferences => $preferences.ui
);

export const a11yPreferences = derived(
	preferences,
	$preferences => $preferences.a11y
);

export const helpPreferences = derived(
	preferences,
	$preferences => $preferences.help
);

export const historyPreferences = derived(
	preferences,
	$preferences => $preferences.history
);

// Preference actions
export const preferenceActions = {
	// Update a specific preference
	update(category, key, value) {
		preferences.update(prefs => ({
			...prefs,
			[category]: {
				...prefs[category],
				[key]: value
			}
		}));
	},
	
	// Update multiple preferences at once
	updateMultiple(updates) {
		preferences.update(prefs => {
			const newPrefs = { ...prefs };
			
			for (const [category, categoryUpdates] of Object.entries(updates)) {
				newPrefs[category] = {
					...newPrefs[category],
					...categoryUpdates
				};
			}
			
			return newPrefs;
		});
	},
	
	// Reset to defaults
	reset() {
		preferences.set(DEFAULT_PREFERENCES);
	},
	
	// Reset specific category
	resetCategory(category) {
		preferences.update(prefs => ({
			...prefs,
			[category]: DEFAULT_PREFERENCES[category]
		}));
	},
	
	// Import preferences
	import(importedPrefs) {
		try {
			const merged = mergeDeep(DEFAULT_PREFERENCES, importedPrefs);
			preferences.set(merged);
			return true;
		} catch (error) {
			console.error('Failed to import preferences:', error);
			return false;
		}
	},
	
	// Export preferences
	export() {
		let currentPrefs;
		preferences.subscribe(prefs => currentPrefs = prefs)();
		return currentPrefs;
	},
	
	// Toggle boolean preference
	toggle(category, key) {
		preferences.update(prefs => ({
			...prefs,
			[category]: {
				...prefs[category],
				[key]: !prefs[category][key]
			}
		}));
	}
};

// Smart defaults based on user environment
export function applySmartDefaults() {
	if (!browser) return;
	
	const updates = {};
	
	// Detect reduced motion preference
	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
		updates.ui = { reducedMotion: true, animationSpeed: 'slow' };
	}
	
	// Detect high contrast preference
	if (window.matchMedia('(prefers-contrast: high)').matches) {
		updates.a11y = { highContrast: true };
	}
	
	// Detect color scheme preference
	if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
		updates.ui = { ...updates.ui, theme: 'dark' };
	} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
		updates.ui = { ...updates.ui, theme: 'light' };
	}
	
	// Apply updates if any
	if (Object.keys(updates).length > 0) {
		preferenceActions.updateMultiple(updates);
	}
}

// Initialize smart defaults on first load
if (browser) {
	// Check if this is the first time loading
	const hasStoredPrefs = localStorage.getItem('midi-visualizer-preferences');
	if (!hasStoredPrefs) {
		applySmartDefaults();
	}
}

// Utility functions for common preference checks
export const preferenceUtils = {
	// Check if animations should be reduced
	shouldReduceMotion() {
		let currentPrefs;
		preferences.subscribe(prefs => currentPrefs = prefs)();
		return currentPrefs.ui.reducedMotion || 
			   (browser && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
	},
	
	// Get animation duration based on speed preference
	getAnimationDuration(baseMs = 300) {
		let currentPrefs;
		preferences.subscribe(prefs => currentPrefs = prefs)();
		
		if (this.shouldReduceMotion()) return 0;
		
		switch (currentPrefs.ui.animationSpeed) {
			case 'slow': return baseMs * 1.5;
			case 'fast': return baseMs * 0.7;
			default: return baseMs;
		}
	},
	
	// Check if tooltips should be shown
	shouldShowTooltips() {
		let currentPrefs;
		preferences.subscribe(prefs => currentPrefs = prefs)();
		return currentPrefs.ui.showTooltips;
	},
	
	// Get tooltip delay
	getTooltipDelay() {
		let currentPrefs;
		preferences.subscribe(prefs => currentPrefs = prefs)();
		return currentPrefs.ui.tooltipDelay;
	}
};