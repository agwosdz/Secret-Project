import type { ValidationResult } from './upload';
import { toastStore } from './stores/toastStore';
import { errorAnalytics } from './analytics/errorAnalytics.js';

export interface RecoveryAction {
	id: string;
	label: string;
	description?: string;
	icon?: string;
	variant: 'primary' | 'secondary' | 'danger';
	action: () => void | Promise<void>;
	disabled?: boolean;
}

export interface ErrorContext {
	id: string;
	type: 'validation' | 'upload' | 'network' | 'permission' | 'file' | 'server' | 'unknown';
	severity: 'low' | 'medium' | 'high' | 'critical';
	title: string;
	message: string;
	timestamp: Date;
	userFriendlyType: string;
	icon: string;
	code?: string;
	originalError?: Error;
	userMessage: string;
	technicalMessage?: string;
	suggestions?: string[];
	recoveryActions: RecoveryAction[];
	preventionTips?: string[];
	helpUrl?: string;
	
	// Recovery actions
	primaryAction?: RecoveryAction;
	secondaryActions?: RecoveryAction[];
	
	// Progressive disclosure
	quickSuggestions?: string[];
	contextInfo?: string[];
	technicalDetails?: string[];
	helpLinks?: Array<{ label: string; url: string }>;
	
	// Contextual help integration
	helpContext?: 'file-upload' | 'validation' | 'network' | 'general';
	showInlineHelp?: boolean;
	helpPriority?: 'low' | 'medium' | 'high';
	
	// Context data
	fileInfo?: {
		name: string;
		size: number;
		type: string;
	};
	networkInfo?: {
		status: number;
		endpoint: string;
		retryCount: number;
	};
	validationInfo?: {
		field: string;
		expectedFormat: string;
		actualValue: string;
	};
}

export interface ErrorRecoveryConfig {
	enableAutoRetry: boolean;
	maxRetryAttempts: number;
	retryDelayMs: number;
	showTechnicalDetails: boolean;
	enableErrorReporting: boolean;
	showPreventionTips: boolean;
}

const DEFAULT_CONFIG: ErrorRecoveryConfig = {
	enableAutoRetry: true,
	maxRetryAttempts: 3,
	retryDelayMs: 1000,
	showTechnicalDetails: false,
	enableErrorReporting: true,
	showPreventionTips: true
};

/**
 * Enhanced Error Recovery Manager
 * Provides intelligent error handling with actionable recovery suggestions
 */
export class ErrorRecoveryManager {
	private config: ErrorRecoveryConfig;
	private retryAttempts: Map<string, number> = new Map();

	constructor(config?: Partial<ErrorRecoveryConfig>) {
		this.config = { ...DEFAULT_CONFIG, ...config };
	}

	/**
	 * Process error with enhanced categorization and create comprehensive error context
	 */
	processError(
		error: any, 
		context?: Partial<ErrorContext>, 
		retryCallback?: () => void,
		clearCallback?: () => void
	): ErrorContext {
		// Enhanced error categorization
		const errorContext = this.categorizeError(error, context);
		
		// Track error for analytics
		errorAnalytics.trackError({
			type: errorContext.type,
			severity: errorContext.severity,
			message: errorContext.message,
			code: errorContext.code,
			timestamp: errorContext.timestamp,
			context: {
				userAgent: navigator.userAgent,
				url: window.location.href,
				fileInfo: errorContext.fileInfo,
				networkInfo: errorContext.networkInfo,
				validationInfo: errorContext.validationInfo
			}
		});
		
		// Add recovery actions based on error type
		errorContext.recoveryActions = this.generateRecoveryActions(errorContext, error);
		
		// Add prevention tips
		if (this.config.showPreventionTips) {
			errorContext.preventionTips = this.generatePreventionTips(errorContext);
		}

		return errorContext;
	}

	/**
	 * Display error with recovery options
	 */
	displayError(errorContext: ErrorContext): void {
		// Show toast with primary recovery action
		const primaryAction = errorContext.recoveryActions.find(a => a.variant === 'primary');
		
		toastStore.error(errorContext.userMessage, {
			title: this.getErrorTitle(errorContext),
			description: errorContext.suggestions?.[0],
			persistent: errorContext.severity === 'high' || errorContext.severity === 'critical',
			duration: this.getErrorDuration(errorContext.severity)
		});

		// Log technical details for debugging
		if (errorContext.technicalMessage) {
			console.error(`[${errorContext.type.toUpperCase()}] ${errorContext.technicalMessage}`, errorContext.originalError);
		}
	}

	/**
	 * Attempt automatic retry with exponential backoff
	 */
	async attemptRetry(
		operation: () => Promise<any>, 
		errorId: string, 
		onRetry?: (attempt: number) => void
	): Promise<any> {
		if (!this.config.enableAutoRetry) {
			throw new Error('Auto-retry is disabled');
		}

		const attempts = this.retryAttempts.get(errorId) || 0;
		
		if (attempts >= this.config.maxRetryAttempts) {
			this.retryAttempts.delete(errorId);
			throw new Error(`Maximum retry attempts (${this.config.maxRetryAttempts}) exceeded`);
		}

		this.retryAttempts.set(errorId, attempts + 1);
		
		if (onRetry) {
			onRetry(attempts + 1);
		}

		// Exponential backoff delay
		const delay = this.config.retryDelayMs * Math.pow(2, attempts);
		await new Promise(resolve => setTimeout(resolve, delay));

		try {
			const result = await operation();
			this.retryAttempts.delete(errorId); // Reset on success
			
			// Track successful recovery
			errorAnalytics.trackRecovery({
				errorId,
				method: 'retry',
				attemptNumber: attempts + 1,
				timestamp: new Date(),
				success: true
			});
			
			return result;
		} catch (error) {
			// Track failed recovery attempt
			errorAnalytics.trackRecovery({
				errorId,
				method: 'retry',
				attemptNumber: attempts + 1,
				timestamp: new Date(),
				success: false
			});
			
			// Will retry on next call or throw if max attempts reached
			throw error;
		}
	}

	/**
	 * Categorize error and create base context with enhanced intelligence
	 */
	private categorizeError(error: any, context?: Partial<ErrorContext>): ErrorContext {
		const errorMessage = error?.message || error?.toString() || '';
		const errorCode = error?.code || error?.status;
		
		let errorType: ErrorContext['type'] = 'unknown';
		let severity: ErrorContext['severity'] = 'medium';
		let userMessage = 'An unexpected error occurred';
		let technicalMessage = '';
		let suggestions: string[] = [];

		// Handle validation errors (including ValidationResult objects)
		if (error && typeof error === 'object' && 'valid' in error) {
			const validationError = error as ValidationResult;
			errorType = 'validation';
			severity = 'medium';
			userMessage = validationError.message;
			if (validationError.suggestion) {
				suggestions.push(validationError.suggestion);
			}
		}
		// Enhanced validation error detection
		else if (errorMessage.includes('validation') || errorMessage.includes('invalid') || 
				 errorMessage.includes('required') || errorMessage.includes('format') ||
				 errorCode === 'VALIDATION_ERROR' || (errorCode >= 400 && errorCode < 500)) {
			errorType = 'validation';
			severity = context?.fileName ? 'medium' : 'low';
			userMessage = errorMessage.includes('file') ? 'File validation failed' : 'Input validation failed';
			technicalMessage = error.stack || '';
			suggestions.push('Please check the input requirements and try again');
		}
		// Enhanced upload error detection
		else if (error?.name === 'UploadError' || errorMessage.includes('upload') || 
				 errorCode === 'UPLOAD_FAILED') {
			errorType = 'upload';
			severity = 'high';
			userMessage = context?.fileName ? `Failed to upload ${context.fileName}` : 'Upload failed';
			technicalMessage = error.stack || '';
			suggestions.push('Check file size and format requirements');
			suggestions.push('Ensure stable internet connection');
		}
		// Enhanced network error detection
		else if (error?.name === 'NetworkError' || errorMessage.includes('fetch') ||
				 errorMessage.includes('network') || errorMessage.includes('connection') ||
				 errorCode === 'NETWORK_ERROR' || errorMessage.includes('timeout')) {
			errorType = 'network';
			severity = errorMessage.includes('timeout') ? 'medium' : 'high';
			userMessage = errorMessage.includes('timeout') ? 'Request timed out' : 'Network connection failed';
			technicalMessage = error.message;
			suggestions.push('Check your internet connection and try again');
			if (errorMessage.includes('timeout')) {
				suggestions.push('Try again - the server may be busy');
			}
		}
		// Enhanced file error detection with smart categorization
		else if (errorMessage.includes('file') || errorMessage.includes('File') ||
				 errorCode === 'FILE_ERROR') {
			// File size errors
			if (errorMessage.includes('size') || errorMessage.includes('large') || 
				errorMessage.includes('limit') || errorCode === 'FILE_TOO_LARGE') {
				errorType = 'file';
				severity = 'medium';
				userMessage = 'File is too large';
				suggestions.push('Try compressing the file or selecting a smaller one');
			}
			// File type errors
			else if (errorMessage.includes('type') || errorMessage.includes('format') ||
					 errorMessage.includes('unsupported') || errorCode === 'INVALID_FILE_TYPE') {
				errorType = 'validation';
				severity = 'medium';
				userMessage = 'File type not supported';
				suggestions.push('Please select a supported file format');
			}
			// General file errors
			else {
				errorType = 'file';
				severity = 'medium';
				userMessage = error.message || 'File operation failed';
				suggestions.push('Ensure the file is not corrupted or in use by another application');
			}
		}
		// Enhanced permission error detection
		else if (errorCode === 401 || errorCode === 403 || 
				 errorMessage.includes('permission') || errorMessage.includes('access') ||
				 errorMessage.includes('unauthorized') || errorMessage.includes('forbidden')) {
			errorType = 'permission';
			severity = 'high';
			userMessage = errorCode === 401 ? 'Authentication required' : 'Permission denied';
			suggestions.push('Check your access permissions and try again');
			if (errorCode === 401) {
				suggestions.push('You may need to log in again');
			}
		}
		// Enhanced server error detection
		else if (errorCode >= 500 || errorMessage.includes('server') ||
				 errorMessage.includes('internal') || errorCode === 'SERVER_ERROR') {
			errorType = 'server';
			severity = 'critical';
			userMessage = 'Server error occurred';
			technicalMessage = errorCode ? `Status: ${errorCode}, Message: ${errorMessage}` : errorMessage;
			suggestions.push('Please try again in a few minutes');
			suggestions.push('If the problem persists, contact support');
		}
		// Generic error handling with better messaging
		else if (error instanceof Error) {
			userMessage = error.message || 'An unexpected error occurred';
			technicalMessage = error.stack || '';
			suggestions.push('Please try again or contact support if the problem persists');
		}

		// Determine contextual help settings
		const helpContext = this.determineHelpContext(errorType, context);
		const helpPriority = this.determineHelpPriority(errorType, severity);
		const showInlineHelp = severity === 'high' || severity === 'critical';

		return {
			id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
			type: errorType,
			severity,
			title: this.getErrorTitle({ type: errorType, severity, userMessage } as ErrorContext),
			message: userMessage,
			timestamp: new Date(),
			userFriendlyType: this.getUserFriendlyType(errorType),
			icon: this.getErrorIcon(errorType),
			code: errorCode?.toString(),
			userMessage,
			technicalMessage,
			suggestions,
			recoveryActions: [],
			originalError: error instanceof Error ? error : undefined,
			helpContext,
			showInlineHelp,
			helpPriority,
			...context
		};
	}

	/**
	 * Determine appropriate help context based on error type and context
	 */
	private determineHelpContext(
		errorType: ErrorContext['type'], 
		context?: Partial<ErrorContext>
	): 'file-upload' | 'validation' | 'network' | 'general' {
		// Check if we have file-related context
		if (context?.fileInfo || context?.fileName || errorType === 'file') {
			return 'file-upload';
		}
		
		// Map error types to help contexts
		switch (errorType) {
			case 'validation':
				return 'validation';
			case 'network':
			case 'server':
				return 'network';
			case 'upload':
				return 'file-upload';
			default:
				return 'general';
		}
	}

	/**
	 * Determine help priority based on error characteristics
	 */
	private determineHelpPriority(
		errorType: ErrorContext['type'], 
		severity: ErrorContext['severity']
	): 'low' | 'medium' | 'high' {
		// High priority for critical errors or user-blocking issues
		if (severity === 'critical' || errorType === 'permission') {
			return 'high';
		}
		
		// Medium priority for common user errors
		if (errorType === 'validation' || errorType === 'file' || errorType === 'upload') {
			return 'medium';
		}
		
		// Low priority for technical/system errors
		return 'low';
	}

	/**
	 * Get user-friendly error type name
	 */
	private getUserFriendlyType(errorType: ErrorContext['type']): string {
		const typeMap = {
			validation: 'Input Error',
			upload: 'Upload Error',
			network: 'Connection Error',
			permission: 'Access Error',
			file: 'File Error',
			server: 'Server Error',
			unknown: 'Unexpected Error'
		};
		return typeMap[errorType] || 'Error';
	}

	/**
	 * Get appropriate icon for error type
	 */
	private getErrorIcon(errorType: ErrorContext['type']): string {
		const iconMap = {
			validation: '⚠️',
			upload: '📤',
			network: '🌐',
			permission: '🔒',
			file: '📁',
			server: '🖥️',
			unknown: '❓'
		};
		return iconMap[errorType] || '❓';
	}

	/**
	 * Generate contextual recovery actions
	 */
	private generateRecoveryActions(errorContext: ErrorContext, originalError: any): RecoveryAction[] {
		const actions: RecoveryAction[] = [];

		switch (errorContext.type) {
			case 'validation':
				actions.push({
					id: 'fix-validation',
					label: 'Fix Issues',
					description: 'Review and correct the validation errors',
					icon: '🔧',
					variant: 'primary',
					action: () => {
						// Focus on first invalid field or show validation details
						console.log('Focusing on validation issues');
					}
				});
				break;

			case 'upload':
				actions.push({
					id: 'retry-upload',
					label: 'Retry Upload',
					description: 'Try uploading the file again',
					icon: '🔄',
					variant: 'primary',
					action: async () => {
						// Retry upload logic would be passed in
						console.log('Retrying upload...');
					}
				});
				actions.push({
					id: 'choose-different-file',
					label: 'Choose Different File',
					description: 'Select a different file to upload',
					icon: '📁',
					variant: 'secondary',
					action: () => {
						// Reset file selection
						console.log('Choosing different file...');
					}
				});
				break;

			case 'network':
				actions.push({
					id: 'retry-connection',
					label: 'Retry Connection',
					description: 'Attempt to reconnect',
					icon: '🌐',
					variant: 'primary',
					action: async () => {
						// Retry network operation
						console.log('Retrying connection...');
					}
				});
				actions.push({
					id: 'work-offline',
					label: 'Work Offline',
					description: 'Continue working in offline mode',
					icon: '📴',
					variant: 'secondary',
					action: () => {
						// Enable offline mode
						console.log('Switching to offline mode...');
					}
				});
				break;

			case 'file':
				actions.push({
					id: 'select-new-file',
					label: 'Select New File',
					description: 'Choose a different file',
					icon: '📄',
					variant: 'primary',
					action: () => {
						// Open file picker
						console.log('Opening file picker...');
					}
				});
				break;

			case 'permission':
				actions.push({
					id: 'request-permission',
					label: 'Request Permission',
					description: 'Request necessary permissions',
					icon: '🔐',
					variant: 'primary',
					action: () => {
						// Request permissions
						console.log('Requesting permissions...');
					}
				});
				break;

			case 'server':
				actions.push({
					id: 'retry-later',
					label: 'Retry Later',
					description: 'Try again in a few minutes',
					icon: '⏰',
					variant: 'primary',
					action: () => {
						// Schedule retry
						console.log('Scheduling retry...');
					}
				});
				actions.push({
					id: 'report-issue',
					label: 'Report Issue',
					description: 'Report this problem to support',
					icon: '📧',
					variant: 'secondary',
					action: () => {
						// Open support form
						console.log('Opening support form...');
					}
				});
				break;
		}

		// Always add a generic "Get Help" action
		actions.push({
			id: 'get-help',
			label: 'Get Help',
			description: 'View troubleshooting guide',
			icon: '❓',
			variant: 'secondary',
			action: () => {
				// Open help documentation
				window.open('/help/troubleshooting', '_blank');
			}
		});

		return actions;
	}

	/**
	 * Generate prevention tips based on error type
	 */
	private generatePreventionTips(errorContext: ErrorContext): string[] {
		const tips: string[] = [];

		switch (errorContext.type) {
			case 'validation':
				tips.push('Double-check file format and size requirements before selecting');
				tips.push('Use the file preview to verify content before uploading');
				break;

			case 'upload':
				tips.push('Ensure stable internet connection before large uploads');
				tips.push('Close other applications that might interfere with file access');
				break;

			case 'network':
				tips.push('Check your internet connection stability');
				tips.push('Try using a wired connection for better reliability');
				break;

			case 'file':
				tips.push('Ensure the file is not open in another application');
				tips.push('Check that the file is not corrupted or damaged');
				break;

			case 'permission':
				tips.push('Run the application with appropriate permissions');
				tips.push('Check file and folder access rights');
				break;

			case 'server':
				tips.push('Try during off-peak hours for better server availability');
				tips.push('Keep your files backed up in case of server issues');
				break;
		}

		return tips;
	}

	/**
	 * Get appropriate error title based on context
	 */
	private getErrorTitle(errorContext: ErrorContext): string {
		const titles = {
			validation: 'Validation Error',
			upload: 'Upload Failed',
			network: 'Connection Problem',
			file: 'File Error',
			permission: 'Access Denied',
			server: 'Server Error',
			unknown: 'Error Occurred'
		};

		return titles[errorContext.type] || 'Something Went Wrong';
	}

	/**
	 * Get error display duration based on severity
	 */
	private getErrorDuration(severity: ErrorContext['severity']): number {
		const durations = {
			low: 3000,
			medium: 5000,
			high: 8000,
			critical: 0 // Persistent
		};

		return durations[severity];
	}
}

// Export singleton instance
export const errorRecovery = new ErrorRecoveryManager();

// Utility functions for common error scenarios
export function handleValidationError(
	validationResult: ValidationResult, 
	onRetry?: () => void
): ErrorContext {
	const context = errorRecovery.processError(validationResult, {
		type: 'validation'
	});

	if (onRetry) {
		context.recoveryActions.unshift({
			id: 'retry-validation',
			label: 'Try Again',
			icon: '🔄',
			variant: 'primary',
			action: onRetry
		});
	}

	errorRecovery.displayError(context);
	return context;
}

export function handleUploadError(
	error: Error, 
	fileName: string,
	onRetry?: () => Promise<void>,
	onSelectNew?: () => void
): ErrorContext {
	const context = errorRecovery.processError(error, {
		type: 'upload',
		userMessage: `Failed to upload ${fileName}`
	});

	// Replace generic actions with specific ones
	context.recoveryActions = [];
	
	if (onRetry) {
		context.recoveryActions.push({
			id: 'retry-upload',
			label: 'Retry Upload',
			description: `Try uploading ${fileName} again`,
			icon: '🔄',
			variant: 'primary',
			action: onRetry
		});
	}

	if (onSelectNew) {
		context.recoveryActions.push({
			id: 'select-new-file',
			label: 'Choose Different File',
			description: 'Select a different file to upload',
			icon: '📁',
			variant: 'secondary',
			action: onSelectNew
		});
	}

	errorRecovery.displayError(context);
	return context;
}

export function handleNetworkError(
	error: Error,
	operation: string,
	onRetry?: () => Promise<void>
): ErrorContext {
	const context = errorRecovery.processError(error, {
		type: 'network',
		userMessage: `Network error during ${operation}`
	});

	if (onRetry) {
		context.recoveryActions.unshift({
			id: 'retry-operation',
			label: 'Retry',
			description: `Retry ${operation}`,
			icon: '🔄',
			variant: 'primary',
			action: onRetry
		});
	}

	errorRecovery.displayError(context);
	return context;
}