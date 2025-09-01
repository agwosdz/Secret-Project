import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { checkBackendHealth } from './health';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Health Service', () => {
	beforeEach(() => {
		mockFetch.mockClear();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('should return healthy status when backend responds correctly', async () => {
		const mockResponse = {
			status: 'healthy',
			message: 'Piano LED Visualizer Backend is running',
			timestamp: '2024-01-20T10:30:00.000Z'
		};

		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockResponse
		});

		const result = await checkBackendHealth();

		expect(mockFetch).toHaveBeenCalledWith('/health');
		expect(result).toEqual({
			status: 'healthy',
			message: 'Piano LED Visualizer Backend is running',
			error: null
		});
	});

	it('should return error status when backend responds with HTTP error', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
			statusText: 'Internal Server Error'
		});

		const result = await checkBackendHealth();

		expect(result).toEqual({
			status: 'Error',
			message: 'HTTP 500: Internal Server Error',
			error: 'HTTP 500: Internal Server Error'
		});
	});

	it('should return offline status when network request fails', async () => {
		mockFetch.mockRejectedValueOnce(new Error('Network error'));

		const result = await checkBackendHealth();

		expect(result).toEqual({
			status: 'Offline',
			message: 'Cannot connect to backend server',
			error: 'Cannot connect to backend server'
		});
	});

	it('should handle malformed JSON response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => {
				throw new Error('Invalid JSON');
			}
		});

		const result = await checkBackendHealth();

		expect(result).toEqual({
			status: 'Error',
			message: 'Invalid response from server',
			error: 'Invalid response from server'
		});
	});

	it('should handle missing status field in response', async () => {
		const mockResponse = {
			message: 'Backend is running',
			timestamp: '2024-01-20T10:30:00.000Z'
			// missing status field
		};

		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockResponse
		});

		const result = await checkBackendHealth();

		expect(result).toEqual({
			status: 'Error',
			message: 'Invalid response format',
			error: 'Invalid response format'
		});
	});
});