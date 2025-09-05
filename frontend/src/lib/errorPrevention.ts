import type { ValidationResult } from './upload';
import { validateValue, VALIDATION_PRESETS, VALIDATION_PATTERNS } from './validation';

export interface ErrorPreventionConfig {
	enabled: boolean;
	showPreventiveTips: boolean;
	showRealTimeValidation: boolean;
	showProgressiveDisclosure: boolean;
	debounceMs: number;
}

export interface PreventiveTip {
	id: string;
	title: string;
	message: string;
	type: 'info' | 'warning' | 'success';
	trigger: 'focus' | 'input' | 'blur' | 'hover';
	condition?: (value: any) => boolean;
}

export interface ErrorPreventionState {
	showTips: boolean;
	activeTips: PreventiveTip[];
	validationResult: ValidationResult | null;
	isValidating: boolean;
	lastValidated: number;
}

/**
 * Error Prevention Manager
 * Provides proactive validation and helpful guidance
 */
export class ErrorPreventionManager {
	private config: ErrorPreventionConfig;
	private state: ErrorPreventionState;
	private validationTimer: number | null = null;
	private callbacks: Map<string, Function[]> = new Map();

	constructor(config: Partial<ErrorPreventionConfig> = {}) {
		this.config = {
			enabled: true,
			showPreventiveTips: true,
			showRealTimeValidation: true,
			showProgressiveDisclosure: true,
			debounceMs: 300,
			...config
		};

		this.state = {
			showTips: false,
			activeTips: [],
			validationResult: null,
			isValidating: false,
			lastValidated: 0
		};
	}

	/**
	 * Register event callback
	 */
	on(event: string, callback: Function): void {
		if (!this.callbacks.has(event)) {
			this.callbacks.set(event, []);
		}
		this.callbacks.get(event)!.push(callback);
	}

	/**
	 * Emit event to callbacks
	 */
	private emit(event: string, data?: any): void {
		const callbacks = this.callbacks.get(event) || [];
		callbacks.forEach(callback => callback(data));
	}

	/**
	 * Handle input focus - show preventive tips
	 */
	onFocus(fieldType: string, value: any, tips: PreventiveTip[]): void {
		if (!this.config.enabled || !this.config.showPreventiveTips) return;

		const relevantTips = tips.filter(tip => 
			tip.trigger === 'focus' && 
			(!tip.condition || tip.condition(value))
		);

		this.state.activeTips = relevantTips;
		this.state.showTips = relevantTips.length > 0;
		this.emit('tipsChanged', this.state.activeTips);
	}

	/**
	 * Handle input change - validate with debouncing
	 */
	onInput(value: any, validationOptions: any, tips: PreventiveTip[]): void {
		if (!this.config.enabled) return;

		// Show input-triggered tips
		if (this.config.showPreventiveTips) {
			const inputTips = tips.filter(tip => 
				tip.trigger === 'input' && 
				(!tip.condition || tip.condition(value))
			);

			if (inputTips.length > 0) {
				this.state.activeTips = [...this.state.activeTips, ...inputTips];
				this.emit('tipsChanged', this.state.activeTips);
			}
		}

		// Debounced validation
		if (this.config.showRealTimeValidation) {
			this.debounceValidation(value, validationOptions);
		}
	}

	/**
	 * Handle input blur - final validation
	 */
	onBlur(value: any, validationOptions: any, tips: PreventiveTip[]): void {
		if (!this.config.enabled) return;

		// Clear input tips
		this.state.activeTips = this.state.activeTips.filter(tip => tip.trigger !== 'input');
		this.state.showTips = this.state.activeTips.length > 0;

		// Show blur-triggered tips
		const blurTips = tips.filter(tip => 
			tip.trigger === 'blur' && 
			(!tip.condition || tip.condition(value))
		);

		if (blurTips.length > 0) {
			this.state.activeTips = [...this.state.activeTips, ...blurTips];
			this.state.showTips = true;
		}

		// Final validation
		this.validateImmediate(value, validationOptions);
		this.emit('tipsChanged', this.state.activeTips);
	}

	/**
	 * Debounced validation
	 */
	private debounceValidation(value: any, validationOptions: any): void {
		if (this.validationTimer) {
			clearTimeout(this.validationTimer);
		}

		this.state.isValidating = true;
		this.emit('validationStateChanged', this.state);

		this.validationTimer = window.setTimeout(() => {
			this.validateImmediate(value, validationOptions);
		}, this.config.debounceMs);
	}

	/**
	 * Immediate validation
	 */
	private validateImmediate(value: any, validationOptions: any): void {
		const result = validateValue(value, validationOptions);
		this.state.validationResult = result;
		this.state.isValidating = false;
		this.state.lastValidated = Date.now();
		this.emit('validationResult', result);
		this.emit('validationStateChanged', this.state);
	}

	/**
	 * Get current state
	 */
	getState(): ErrorPreventionState {
		return { ...this.state };
	}

	/**
	 * Clear all tips and validation
	 */
	clear(): void {
		this.state.activeTips = [];
		this.state.showTips = false;
		this.state.validationResult = null;
		this.state.isValidating = false;
		this.emit('tipsChanged', []);
		this.emit('validationResult', null);
	}

	/**
	 * Update configuration
	 */
	updateConfig(newConfig: Partial<ErrorPreventionConfig>): void {
		this.config = { ...this.config, ...newConfig };
	}
}

/**
 * Predefined preventive tips for common scenarios
 */
export const PREVENTIVE_TIPS = {
	fileUpload: [
		{
			id: 'file-format-tip',
			title: 'Supported Formats',
			message: 'Only MIDI files (.mid, .midi) are supported',
			type: 'info' as const,
			trigger: 'focus' as const
		},
		{
			id: 'file-size-tip',
			title: 'File Size Limit',
			message: 'Maximum file size is 1MB, minimum is 100 bytes',
			type: 'info' as const,
			trigger: 'focus' as const
		},
		{
			id: 'file-too-large',
			title: 'File Too Large',
			message: 'This file exceeds the 1MB limit. Try compressing or choosing a smaller file.',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (file: File) => file && file.size > 1024 * 1024
		},
		{
			id: 'file-wrong-type',
			title: 'Unsupported Format',
			message: 'This file type is not supported. Please select a MIDI file (.mid or .midi).',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (file: File) => {
				if (!file) return false;
				const ext = file.name.split('.').pop()?.toLowerCase();
				return ext !== 'mid' && ext !== 'midi';
			}
		}
	],

	email: [
		{
			id: 'email-format-tip',
			title: 'Email Format',
			message: 'Enter a valid email address (e.g., user@example.com)',
			type: 'info' as const,
			trigger: 'focus' as const
		},
		{
			id: 'email-missing-at',
			title: 'Missing @ Symbol',
			message: 'Email addresses must contain an @ symbol',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (value: string) => value && value.length > 3 && !value.includes('@')
		},
		{
			id: 'email-missing-domain',
			title: 'Missing Domain',
			message: 'Email addresses must include a domain (e.g., @example.com)',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (value: string) => value && value.includes('@') && !value.includes('.')
		}
	],

	password: [
		{
			id: 'password-strength-tip',
			title: 'Password Requirements',
			message: 'Use at least 8 characters with a mix of letters, numbers, and symbols',
			type: 'info' as const,
			trigger: 'focus' as const
		},
		{
			id: 'password-too-short',
			title: 'Password Too Short',
			message: 'Password must be at least 8 characters long',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (value: string) => value && value.length > 0 && value.length < 8
		},
		{
			id: 'password-weak',
			title: 'Weak Password',
			message: 'Consider adding numbers or symbols for better security',
			type: 'warning' as const,
			trigger: 'blur' as const,
			condition: (value: string) => {
				if (!value || value.length < 8) return false;
				return !/\d/.test(value) || !/[!@#$%^&*]/.test(value);
			}
		}
	],

	filename: [
		{
			id: 'filename-chars-tip',
			title: 'Allowed Characters',
			message: 'Use only letters, numbers, dots, hyphens, and underscores',
			type: 'info' as const,
			trigger: 'focus' as const
		},
		{
			id: 'filename-invalid-chars',
			title: 'Invalid Characters',
			message: 'Remove special characters like spaces, slashes, or symbols',
			type: 'warning' as const,
			trigger: 'input' as const,
			condition: (value: string) => value && !VALIDATION_PATTERNS.filename.test(value)
		}
	]
};

/**
 * Create error prevention manager with common presets
 */
export function createErrorPrevention(type: keyof typeof PREVENTIVE_TIPS, config?: Partial<ErrorPreventionConfig>): {
	manager: ErrorPreventionManager;
	tips: PreventiveTip[];
} {
	const manager = new ErrorPreventionManager(config);
	const tips = PREVENTIVE_TIPS[type] || [];

	return { manager, tips };
}

/**
 * Smart error prevention for file uploads
 */
export function createFileUploadPrevention(config?: Partial<ErrorPreventionConfig>) {
	return createErrorPrevention('fileUpload', config);
}

/**
 * Smart error prevention for email inputs
 */
export function createEmailPrevention(config?: Partial<ErrorPreventionConfig>) {
	return createErrorPrevention('email', config);
}

/**
 * Smart error prevention for password inputs
 */
export function createPasswordPrevention(config?: Partial<ErrorPreventionConfig>) {
	return createErrorPrevention('password', config);
}

/**
 * Smart error prevention for filename inputs
 */
export function createFilenamePrevention(config?: Partial<ErrorPreventionConfig>) {
	return createErrorPrevention('filename', config);
}