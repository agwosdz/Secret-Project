import { vi } from 'vitest';

// Mock fetch globally for all tests
Object.defineProperty(window, 'fetch', {
	value: vi.fn(),
	writable: true
});