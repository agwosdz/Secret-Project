import { writable } from 'svelte/store';

export interface ToastData {
	id: string;
	type: 'success' | 'error' | 'warning' | 'info';
	title?: string;
	message: string;
	duration?: number;
	dismissible?: boolean;
	persistent?: boolean;
	position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

function createToastStore() {
	const { subscribe, update } = writable<ToastData[]>([]);

	function generateId(): string {
		return Math.random().toString(36).substr(2, 9);
	}

	function addToast(toast: Omit<ToastData, 'id'>): string {
		const id = generateId();
		const newToast: ToastData = {
			id,
			duration: 5000,
			dismissible: true,
			persistent: false,
			position: 'top-right',
			...toast
		};

		update(toasts => [...toasts, newToast]);
		return id;
	}

	function removeToast(id: string) {
		update(toasts => toasts.filter(toast => toast.id !== id));
	}

	function clearAll() {
		update(() => []);
	}

	// Convenience methods for different toast types
	function success(message: string, options?: Partial<Omit<ToastData, 'id' | 'type' | 'message'>>) {
		return addToast({ type: 'success', message, ...options });
	}

	function error(message: string, options?: Partial<Omit<ToastData, 'id' | 'type' | 'message'>>) {
		return addToast({ type: 'error', message, persistent: true, ...options });
	}

	function warning(message: string, options?: Partial<Omit<ToastData, 'id' | 'type' | 'message'>>) {
		return addToast({ type: 'warning', message, ...options });
	}

	function info(message: string, options?: Partial<Omit<ToastData, 'id' | 'type' | 'message'>>) {
		return addToast({ type: 'info', message, ...options });
	}

	// Loading toast with progress
	function loading(message: string, options?: Partial<Omit<ToastData, 'id' | 'type' | 'message'>>) {
		return addToast({ 
			type: 'info', 
			message, 
			persistent: true, 
			dismissible: false,
			...options 
		});
	}

	// Update existing toast (useful for loading states)
	function updateToast(id: string, updates: Partial<Omit<ToastData, 'id'>>) {
		update(toasts => 
			toasts.map(toast => 
				toast.id === id ? { ...toast, ...updates } : toast
			)
		);
	}

	return {
		subscribe,
		addToast,
		removeToast,
		clearAll,
		success,
		error,
		warning,
		info,
		loading,
		updateToast
	};
}

export const toastStore = createToastStore();

// Helper function for async operations with loading states
export async function withLoadingToast<T>(
	promise: Promise<T>,
	loadingMessage: string,
	successMessage?: string,
	errorMessage?: string
): Promise<T> {
	const loadingId = toastStore.loading(loadingMessage);
	
	try {
		const result = await promise;
		toastStore.removeToast(loadingId);
		
		if (successMessage) {
			toastStore.success(successMessage);
		}
		
		return result;
	} catch (error) {
		toastStore.removeToast(loadingId);
		
		const message = errorMessage || (error instanceof Error ? error.message : 'An error occurred');
		toastStore.error(message);
		
		throw error;
	}
}