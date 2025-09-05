import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Help system configuration
const HELP_STORAGE_KEY = 'midi-app-help-preferences';
const TOUR_STORAGE_KEY = 'midi-app-tour-completed';

// Default help preferences
const defaultPreferences = {
	showTooltips: true,
	tooltipDelay: 500,
	showOnboarding: true,
	autoShowHelp: true,
	helpTheme: 'dark',
	reducedMotion: false
};

// Load preferences from localStorage
function loadPreferences() {
	if (!browser) return defaultPreferences;
	
	try {
		const stored = localStorage.getItem(HELP_STORAGE_KEY);
		if (stored) {
			return { ...defaultPreferences, ...JSON.parse(stored) };
		}
	} catch (error) {
		console.warn('Failed to load help preferences:', error);
	}
	
	return defaultPreferences;
}

// Save preferences to localStorage
function savePreferences(preferences) {
	if (!browser) return;
	
	try {
		localStorage.setItem(HELP_STORAGE_KEY, JSON.stringify(preferences));
	} catch (error) {
		console.warn('Failed to save help preferences:', error);
	}
}

// Check if tour has been completed
function hasTourBeenCompleted() {
	if (!browser) return false;
	
	try {
		return localStorage.getItem(TOUR_STORAGE_KEY) === 'true';
	} catch (error) {
		console.warn('Failed to check tour completion:', error);
		return false;
	}
}

// Mark tour as completed
function markTourCompleted() {
	if (!browser) return;
	
	try {
		localStorage.setItem(TOUR_STORAGE_KEY, 'true');
	} catch (error) {
		console.warn('Failed to mark tour as completed:', error);
	}
}

// Reset tour completion status
function resetTourCompletion() {
	if (!browser) return;
	
	try {
		localStorage.removeItem(TOUR_STORAGE_KEY);
	} catch (error) {
		console.warn('Failed to reset tour completion:', error);
	}
}

// Create stores
export const helpPreferences = writable(loadPreferences());
export const tourCompleted = writable(hasTourBeenCompleted());
export const activeTour = writable(null);
export const activeTooltip = writable(null);
export const helpContext = writable('upload'); // Current page/context

// Derived stores
export const shouldShowOnboarding = derived(
	[helpPreferences, tourCompleted],
	([$preferences, $tourCompleted]) => {
		return $preferences.showOnboarding && !$tourCompleted;
	}
);

export const tooltipConfig = derived(
	helpPreferences,
	($preferences) => ({
		enabled: $preferences.showTooltips,
		delay: $preferences.tooltipDelay,
		theme: $preferences.helpTheme,
		reducedMotion: $preferences.reducedMotion
	})
);

// Subscribe to preferences changes and save them
helpPreferences.subscribe((preferences) => {
	savePreferences(preferences);
});

// Help system actions
export const helpActions = {
	// Update preferences
	updatePreferences(updates) {
		helpPreferences.update(current => ({ ...current, ...updates }));
	},

	// Toggle specific preference
	togglePreference(key) {
		helpPreferences.update(current => ({
			...current,
			[key]: !current[key]
		}));
	},

	// Start a tour
	startTour(tourId, steps = []) {
		activeTour.set({ id: tourId, steps, currentStep: 0 });
	},

	// Complete current tour
	completeTour() {
		activeTour.set(null);
		tourCompleted.set(true);
		markTourCompleted();
	},

	// Skip current tour
	skipTour() {
		activeTour.set(null);
		tourCompleted.set(true);
		markTourCompleted();
	},

	// Reset tour (for testing or re-onboarding)
	resetTour() {
		tourCompleted.set(false);
		resetTourCompletion();
	},

	// Show tooltip
	showTooltip(id, config) {
		activeTooltip.set({ id, ...config });
	},

	// Hide tooltip
	hideTooltip() {
		activeTooltip.set(null);
	},

	// Set help context
	setContext(context) {
		helpContext.set(context);
	},

	// Get context-specific help content
	getContextHelp(context) {
		const helpContent = {
			upload: {
				title: 'Upload MIDI Files',
				description: 'Learn how to upload and process MIDI files for LED visualization.',
				tips: [
					'Drag and drop files for quick upload',
					'Supported formats: .mid, .midi',
					'Use Ctrl+Z to undo actions',
					'File metadata shows tracks and duration'
				]
			},
			play: {
				title: 'LED Visualization',
				description: 'Control and customize your LED light show.',
				tips: [
					'Use spacebar to play/pause',
					'Adjust speed with +/- keys',
					'Click timeline to seek',
					'Press F for fullscreen'
				]
			}
		};

		return helpContent[context] || null;
	},

	// Reset all preferences to defaults
	resetPreferences() {
		helpPreferences.set(defaultPreferences);
	}
};

// Keyboard shortcuts for help system
export function setupHelpKeyboardShortcuts() {
	if (!browser) return;

	function handleKeydown(event) {
		// F1 - Show help
		if (event.key === 'F1') {
			event.preventDefault();
			// Dispatch custom event for help
			window.dispatchEvent(new CustomEvent('show-help'));
		}

		// Ctrl/Cmd + ? - Show keyboard shortcuts
		if ((event.ctrlKey || event.metaKey) && event.key === '/') {
			event.preventDefault();
			window.dispatchEvent(new CustomEvent('show-shortcuts'));
		}

		// Ctrl/Cmd + Shift + ? - Start tour
		if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === '/') {
			event.preventDefault();
			helpActions.resetTour();
			window.dispatchEvent(new CustomEvent('start-tour'));
		}
	}

	document.addEventListener('keydown', handleKeydown);

	// Return cleanup function
	return () => {
		document.removeEventListener('keydown', handleKeydown);
	};
}

// Utility functions
export const helpUtils = {
	// Check if user prefers reduced motion
	prefersReducedMotion() {
		if (!browser) return false;
		return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	},

	// Get appropriate animation duration based on preferences
	getAnimationDuration(defaultDuration = 300) {
		let preferences;
		helpPreferences.subscribe(p => preferences = p)();
		
		if (preferences?.reducedMotion || this.prefersReducedMotion()) {
			return 0;
		}
		return defaultDuration;
	},

	// Format help content for accessibility
	formatForScreenReader(text) {
		return text.replace(/\n/g, '. ').replace(/\s+/g, ' ').trim();
	},

	// Generate unique IDs for help elements
	generateHelpId(prefix = 'help') {
		return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
	}
};