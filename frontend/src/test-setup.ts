import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Configure environment for Svelte 5 client-side rendering
Object.defineProperty(globalThis, 'window', {
	value: global.window || {},
	writable: true
});

Object.defineProperty(globalThis, 'document', {
	value: global.document || {},
	writable: true
});

// Mock fetch globally for all tests
Object.defineProperty(window, 'fetch', {
	value: vi.fn(),
	writable: true
});

// Mock browser APIs for Svelte 5
Object.defineProperty(window, 'requestAnimationFrame', {
	value: vi.fn((cb) => setTimeout(cb, 16)),
	writable: true
});

Object.defineProperty(window, 'cancelAnimationFrame', {
	value: vi.fn(),
	writable: true
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn()
}));

// Mock File and FileList for file upload tests
global.File = class MockFile {
	constructor(bits, name, options = {}) {
		this.bits = bits;
		this.name = name;
		this.size = bits.reduce((acc, bit) => acc + (bit.length || bit.byteLength || 0), 0);
		this.type = options.type || '';
		this.lastModified = options.lastModified || Date.now();
	}
};

global.FileList = class MockFileList {
	constructor(files = []) {
		this.length = files.length;
		files.forEach((file, index) => {
			this[index] = file;
		});
	}
	item(index) {
		return this[index] || null;
	}
};