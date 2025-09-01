export interface HealthCheckResult {
	status: string;
	message: string;
	error: string | null;
}

export async function checkBackendHealth(): Promise<HealthCheckResult> {
	try {
		const response = await fetch('/health');
		
		if (response.ok) {
			try {
				const data = await response.json();
				
				// Validate response format
				if (!data.status) {
					return {
						status: 'Error',
						message: 'Invalid response format',
						error: 'Invalid response format'
					};
				}
				
				return {
					status: data.status,
					message: data.message || 'Backend is healthy',
					error: null
				};
			} catch (jsonError) {
				return {
					status: 'Error',
					message: 'Invalid response from server',
					error: 'Invalid response from server'
				};
			}
		} else {
			const errorMessage = `HTTP ${response.status}: ${response.statusText}`;
			return {
				status: 'Error',
				message: errorMessage,
				error: errorMessage
			};
		}
	} catch (error) {
		return {
			status: 'Offline',
			message: 'Cannot connect to backend server',
			error: 'Cannot connect to backend server'
		};
	}
}