import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock fetch globally for all tests
Object.defineProperty(window, 'fetch', {
	value: vi.fn(),
	writable: true
});

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