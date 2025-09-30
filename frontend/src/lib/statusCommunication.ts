/**
 * Status Communication System
 * Provides comprehensive feedback and status communication for user actions
 */

export interface StatusMessage {
	id: string;
	type: 'success' | 'info' | 'warning' | 'error' | 'loading';
	title: string;
	message: string;
	duration?: number; // in milliseconds, 0 for persistent
	actions?: StatusAction[];
	progress?: number; // 0-100 for progress indicators
	icon?: string;
	timestamp: number;
	autoDismiss?: boolean;
	persistent?: boolean;
}

export interface StatusAction {
	label: string;
	action: () => void;
	variant?: 'primary' | 'secondary' | 'danger';
	icon?: string;
}

export interface StatusConfig {
	defaultDuration: number;
	maxMessages: number;
	animationDuration: number;
	position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
	groupSimilar: boolean;
	showProgress: boolean;
}

export interface ProgressStatus {
	id: string;
	label: string;
	progress: number;
	total?: number;
	current?: number;
	unit?: string;
	estimatedTime?: number;
	speed?: string;
}

const DEFAULT_CONFIG: StatusConfig = {
	defaultDuration: 5000,
	maxMessages: 5,
	animationDuration: 300,
	position: 'top-right',
	groupSimilar: true,
	showProgress: true
};

class StatusCommunicationManager {
	private messages: Map<string, StatusMessage> = new Map();
	private progressStatuses: Map<string, ProgressStatus> = new Map();
	private config: StatusConfig;
	private listeners: Set<(messages: StatusMessage[]) => void> = new Set();
	private progressListeners: Set<(statuses: ProgressStatus[]) => void> = new Set();
	private messageCounter = 0;

	constructor(config: Partial<StatusConfig> = {}) {
		this.config = { ...DEFAULT_CONFIG, ...config };
	}

	// Message Management
	addMessage(message: Omit<StatusMessage, 'id' | 'timestamp'>): string {
		const id = `status-${++this.messageCounter}-${Date.now()}`;
		const fullMessage: StatusMessage = {
			...message,
			id,
			timestamp: Date.now(),
			duration: message.duration ?? this.config.defaultDuration,
			autoDismiss: message.autoDismiss ?? true
		};

		// Group similar messages if enabled
		if (this.config.groupSimilar) {
			const existing = this.findSimilarMessage(fullMessage);
			if (existing) {
				this.updateMessage(existing.id, {
					timestamp: Date.now(),
					message: `${existing.message} (${this.getSimilarCount(existing) + 1})`
				});
				return existing.id;
			}
		}

		this.messages.set(id, fullMessage);

		// Limit number of messages
		if (this.messages.size > this.config.maxMessages) {
			const oldestId = Array.from(this.messages.keys())[0];
			this.removeMessage(oldestId);
		}

		// Auto-dismiss if configured
		if (fullMessage.autoDismiss && fullMessage.duration && fullMessage.duration > 0) {
			setTimeout(() => {
				this.removeMessage(id);
			}, fullMessage.duration);
		}

		this.notifyListeners();
		return id;
	}

	updateMessage(id: string, updates: Partial<StatusMessage>): void {
		const message = this.messages.get(id);
		if (message) {
			this.messages.set(id, { ...message, ...updates });
			this.notifyListeners();
		}
	}

	removeMessage(id: string): void {
		if (this.messages.delete(id)) {
			this.notifyListeners();
		}
	}

	clearMessages(type?: StatusMessage['type']): void {
		if (type) {
			for (const [id, message] of this.messages) {
				if (message.type === type) {
					this.messages.delete(id);
				}
			}
		} else {
			this.messages.clear();
		}
		this.notifyListeners();
	}

	// Progress Management
	startProgress(id: string, label: string, total?: number): void {
		const progress: ProgressStatus = {
			id,
			label,
			progress: 0,
			total,
			current: 0
		};
		this.progressStatuses.set(id, progress);
		this.notifyProgressListeners();
	}

	updateProgress(id: string, progress: number, current?: number, speed?: string): void {
		const status = this.progressStatuses.get(id);
		if (status) {
			const updatedStatus: ProgressStatus = {
				...status,
				progress: Math.max(0, Math.min(100, progress)),
				current: current ?? status.current,
				speed
			};

			// Calculate estimated time if we have speed and remaining work
			if (status.total && current !== undefined && progress < 100) {
				const remaining = status.total - current;
				const rate = current / (Date.now() - (status as any).startTime || 1);
				updatedStatus.estimatedTime = remaining / rate;
			}

			this.progressStatuses.set(id, updatedStatus);
			this.notifyProgressListeners();
		}
	}

	completeProgress(id: string, successMessage?: string): void {
		const status = this.progressStatuses.get(id);
		if (status) {
			this.progressStatuses.delete(id);
			if (successMessage) {
				this.success(status.label, successMessage);
			}
			this.notifyProgressListeners();
		}
	}

	failProgress(id: string, errorMessage: string): void {
		const status = this.progressStatuses.get(id);
		if (status) {
			this.progressStatuses.delete(id);
			this.error(status.label, errorMessage);
			this.notifyProgressListeners();
		}
	}

	// Generic showMessage method for backward compatibility
	showMessage(message: string, type: StatusMessage['type'] = 'info', options: {
		title?: string;
		duration?: number;
		actions?: StatusAction[];
		icon?: string;
		persistent?: boolean;
	} = {}): string {
		return this.addMessage({
			type,
			title: options.title || this.getDefaultTitle(type),
			message,
			duration: options.duration,
			actions: options.actions,
			icon: options.icon || this.getDefaultIcon(type),
			persistent: options.persistent
		});
	}

	private getDefaultTitle(type: StatusMessage['type']): string {
		switch (type) {
			case 'success': return 'Success';
			case 'error': return 'Error';
			case 'warning': return 'Warning';
			case 'loading': return 'Loading';
			case 'info':
			default: return 'Info';
		}
	}

	private getDefaultIcon(type: StatusMessage['type']): string {
		switch (type) {
			case 'success': return '✅';
			case 'error': return '❌';
			case 'warning': return '⚠️';
			case 'loading': return '⏳';
			case 'info':
			default: return 'ℹ️';
		}
	}

	// Convenience Methods
	success(title: string, message: string, actions?: StatusAction[]): string {
		return this.addMessage({
			type: 'success',
			title,
			message,
			actions,
			icon: '✓'
		});
	}

	info(title: string, message: string, actions?: StatusAction[]): string {
		return this.addMessage({
			type: 'info',
			title,
			message,
			actions,
			icon: 'ℹ'
		});
	}

	warning(title: string, message: string, actions?: StatusAction[]): string {
		return this.addMessage({
			type: 'warning',
			title,
			message,
			actions,
			icon: '⚠'
		});
	}

	error(title: string, message: string, actions?: StatusAction[]): string {
		return this.addMessage({
			type: 'error',
			title,
			message,
			actions,
			icon: '✕',
			duration: 0, // Errors don't auto-dismiss
			autoDismiss: false
		});
	}

	loading(title: string, message: string, progress?: number): string {
		return this.addMessage({
			type: 'loading',
			title,
			message,
			progress,
			icon: '⟳',
			duration: 0, // Loading messages don't auto-dismiss
			autoDismiss: false
		});
	}

	// Event Listeners
	onMessagesChange(callback: (messages: StatusMessage[]) => void): () => void {
		this.listeners.add(callback);
		return () => this.listeners.delete(callback);
	}

	onProgressChange(callback: (statuses: ProgressStatus[]) => void): () => void {
		this.progressListeners.add(callback);
		return () => this.progressListeners.delete(callback);
	}

	// Private Methods
	private findSimilarMessage(message: StatusMessage): StatusMessage | undefined {
		for (const existing of this.messages.values()) {
			if (existing.type === message.type && existing.title === message.title) {
				return existing;
			}
		}
		return undefined;
	}

	private getSimilarCount(message: StatusMessage): number {
		const match = message.message.match(/\((\d+)\)$/);
		return match ? parseInt(match[1]) : 1;
	}

	private notifyListeners(): void {
		const messages = Array.from(this.messages.values()).sort((a, b) => b.timestamp - a.timestamp);
		this.listeners.forEach(callback => callback(messages));
	}

	private notifyProgressListeners(): void {
		const statuses = Array.from(this.progressStatuses.values());
		this.progressListeners.forEach(callback => callback(statuses));
	}

	// Getters
	getMessages(): StatusMessage[] {
		return Array.from(this.messages.values()).sort((a, b) => b.timestamp - a.timestamp);
	}

	getProgressStatuses(): ProgressStatus[] {
		return Array.from(this.progressStatuses.values());
	}

	getConfig(): StatusConfig {
		return { ...this.config };
	}

	updateConfig(updates: Partial<StatusConfig>): void {
		this.config = { ...this.config, ...updates };
	}
}

// Global instance
export const statusManager = new StatusCommunicationManager();

// Utility functions for common status patterns
export const statusUtils = {
	// File upload status patterns
	uploadStart: (filename: string) => {
		const id = `upload-${filename}`;
		statusManager.startProgress(id, `Uploading ${filename}`);
		statusManager.loading('File Upload', `Uploading ${filename}...`);
		return id;
	},

	uploadProgress: (id: string, progress: number, speed?: string) => {
		statusManager.updateProgress(id, progress, undefined, speed);
	},

	uploadSuccess: (id: string, filename: string, actions?: StatusAction[]) => {
		statusManager.completeProgress(id);
		return statusManager.success(
			'Upload Complete',
			`${filename} has been uploaded successfully`,
			actions
		);
	},

	uploadError: (id: string, filename: string, error: string, actions?: StatusAction[]) => {
		statusManager.failProgress(id, error);
		return statusManager.error(
			'Upload Failed',
			`Failed to upload ${filename}: ${error}`,
			actions
		);
	},

	// Processing status patterns
	processingStart: (operation: string) => {
		return statusManager.loading('Processing', `${operation} in progress...`);
	},

	processingSuccess: (operation: string, result?: string) => {
		return statusManager.success(
			'Processing Complete',
			`${operation} completed successfully${result ? `: ${result}` : ''}`
		);
	},

	processingError: (operation: string, error: string, actions?: StatusAction[]) => {
		return statusManager.error(
			'Processing Failed',
			`${operation} failed: ${error}`,
			actions
		);
	},

	// Validation status patterns
	validationSuccess: (item: string) => {
		return statusManager.success(
			'Validation Passed',
			`${item} is valid and ready to use`
		);
	},

	validationWarning: (item: string, warning: string, actions?: StatusAction[]) => {
		return statusManager.warning(
			'Validation Warning',
			`${item}: ${warning}`,
			actions
		);
	},

	// Save/Load status patterns
	saveSuccess: (item: string) => {
		return statusManager.success(
			'Saved',
			`${item} has been saved successfully`
		);
	},

	loadSuccess: (item: string) => {
		return statusManager.success(
			'Loaded',
			`${item} has been loaded successfully`
		);
	},

	// Connection status patterns
	connectionSuccess: (service: string) => {
		return statusManager.success(
			'Connected',
			`Successfully connected to ${service}`
		);
	},

	connectionError: (service: string, error: string, actions?: StatusAction[]) => {
		return statusManager.error(
			'Connection Failed',
			`Failed to connect to ${service}: ${error}`,
			actions
		);
	}
};

// Export types and manager
export { StatusCommunicationManager };
export default statusManager;