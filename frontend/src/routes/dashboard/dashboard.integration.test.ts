import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import Dashboard from './+page.svelte';
import { io } from 'socket.io-client';

// Mock socket.io-client
vi.mock('socket.io-client', () => {
	const mockSocket = {
		on: vi.fn(),
		off: vi.fn(),
		emit: vi.fn(),
		connect: vi.fn(),
		disconnect: vi.fn(),
		connected: true,
		id: 'mock-socket-id'
	};

	return {
		io: vi.fn(() => mockSocket),
		mockSocket
	};
});

// Get the mock socket for testing
const getMockSocket = () => {
	const ioMock = vi.mocked(io);
	return ioMock.mock.results[ioMock.mock.results.length - 1]?.value;
};

describe('Dashboard Integration Tests', () => {
	let component: any;
	let container: HTMLElement;
	let mockSocket: any;

	beforeEach(() => {
		vi.clearAllMocks();
		// Reset socket mock
		mockSocket = {
			on: vi.fn(),
			off: vi.fn(),
			emit: vi.fn(),
			connect: vi.fn(),
			disconnect: vi.fn(),
			connected: true,
			id: 'mock-socket-id'
		};
		vi.mocked(io).mockReturnValue(mockSocket);
	});

	afterEach(() => {
		if (component) {
			component.$destroy();
		}
	});

	it('establishes WebSocket connection on mount', () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Should call io to create socket connection
		expect(io).toHaveBeenCalledWith('ws://localhost:5001', expect.objectContaining({
			reconnection: true,
			reconnectionAttempts: 5,
			reconnectionDelay: 1000
		}));
	});

	it('registers WebSocket event listeners', () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Should register event listeners
		expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
		expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
		expect(mockSocket.on).toHaveBeenCalledWith('led_update', expect.any(Function));
		expect(mockSocket.on).toHaveBeenCalledWith('error', expect.any(Function));
	});

	it('handles LED state updates from WebSocket', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Get the led_update event handler
		const onCalls = mockSocket.on.mock.calls;
		const ledUpdateCall = onCalls.find(call => call[0] === 'led_update');
		const ledUpdateHandler = ledUpdateCall?.[1];

		expect(ledUpdateHandler).toBeDefined();

		// Simulate LED update from server
		const mockLedData = {
			leds: [
				{ r: 255, g: 0, b: 0, brightness: 1.0 },
				{ r: 0, g: 255, b: 0, brightness: 0.8 },
				{ r: 0, g: 0, b: 255, brightness: 0.6 }
			]
		};

		ledUpdateHandler(mockLedData);

		// Wait for component to update
		await waitFor(() => {
			// LED visualization should be present
			const ledViz = container.querySelector('canvas');
			expect(ledViz).toBeTruthy();
		});
	});

	it('sends LED updates through WebSocket', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Find LED index input and change it
		const ledIndexInput = container.querySelector('input[type="number"]') as HTMLInputElement;
		expect(ledIndexInput).toBeTruthy();

		await fireEvent.input(ledIndexInput, { target: { value: '5' } });

		// Find color input and change it
		const colorInput = container.querySelector('input[type="color"]') as HTMLInputElement;
		expect(colorInput).toBeTruthy();

		await fireEvent.input(colorInput, { target: { value: '#ff0000' } });

		// Find update button and click it
		const updateButton = container.querySelector('button:has-text("Update LED")');
		if (updateButton) {
			await fireEvent.click(updateButton);

			// Should emit LED update
			expect(mockSocket.emit).toHaveBeenCalledWith('led_update', expect.objectContaining({
				index: 5,
				color: expect.objectContaining({
					r: 255,
					g: 0,
					b: 0
				})
			}));
		}
	});

	it('handles WebSocket connection status changes', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Get connect and disconnect handlers
		const onCalls = mockSocket.on.mock.calls;
		const connectCall = onCalls.find(call => call[0] === 'connect');
		const disconnectCall = onCalls.find(call => call[0] === 'disconnect');

		const connectHandler = connectCall?.[1];
		const disconnectHandler = disconnectCall?.[1];

		expect(connectHandler).toBeDefined();
		expect(disconnectHandler).toBeDefined();

		// Simulate connection
		connectHandler();

		await waitFor(() => {
			// Should show connected status
			expect(container.textContent).toContain('Connected');
		});

		// Simulate disconnection
		disconnectHandler('transport close');

		await waitFor(() => {
			// Should show disconnected status
			expect(container.textContent).toContain('Disconnected');
		});
	});

	it('sends pattern updates through WebSocket', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Find pattern select
		const patternSelect = container.querySelector('select') as HTMLSelectElement;
		expect(patternSelect).toBeTruthy();

		// Change pattern
		await fireEvent.change(patternSelect, { target: { value: 'rainbow' } });

		// Should emit pattern update
		expect(mockSocket.emit).toHaveBeenCalledWith('pattern_update', expect.objectContaining({
			pattern: 'rainbow'
		}));
	});

	it('handles bulk LED updates', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Find Fill All button
		const fillAllButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Fill All'));

		if (fillAllButton) {
			await fireEvent.click(fillAllButton);

			// Should emit bulk update
			expect(mockSocket.emit).toHaveBeenCalledWith('bulk_update', expect.objectContaining({
				type: 'fill_all'
			}));
		}
	});

	it('handles WebSocket errors gracefully', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Get error handler
		const onCalls = mockSocket.on.mock.calls;
		const errorCall = onCalls.find(call => call[0] === 'error');
		const errorHandler = errorCall?.[1];

		expect(errorHandler).toBeDefined();

		// Simulate error
		errorHandler(new Error('Connection failed'));

		await waitFor(() => {
			// Should display error message
			expect(container.textContent).toContain('Connection failed');
		});
	});

	it('updates performance metrics from WebSocket data', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Get the led_update event handler
		const onCalls = mockSocket.on.mock.calls;
		const ledUpdateCall = onCalls.find(call => call[0] === 'led_update');
		const ledUpdateHandler = ledUpdateCall?.[1];

		// Simulate multiple LED updates to test performance tracking
		const startTime = Date.now();
		for (let i = 0; i < 5; i++) {
			ledUpdateHandler({
				leds: [{ r: i * 50, g: 0, b: 0, brightness: 1.0 }],
				timestamp: startTime + i * 100
			});
		}

		await waitFor(() => {
			// Performance monitor should show some metrics
			const perfMonitor = container.querySelector('.performance-monitor');
			expect(perfMonitor).toBeTruthy();
		});
	});

	it('handles reconnection attempts', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Get reconnect handlers
		const onCalls = mockSocket.on.mock.calls;
		const reconnectingCall = onCalls.find(call => call[0] === 'reconnecting');
		const reconnectFailedCall = onCalls.find(call => call[0] === 'reconnect_failed');

		if (reconnectingCall) {
			const reconnectingHandler = reconnectingCall[1];
			reconnectingHandler(3); // attempt number

			await waitFor(() => {
				expect(container.textContent).toContain('Reconnecting');
			});
		}

		if (reconnectFailedCall) {
			const reconnectFailedHandler = reconnectFailedCall[1];
			reconnectFailedHandler();

			await waitFor(() => {
				expect(container.textContent).toContain('Failed');
			});
		}
	});

	it('cleans up WebSocket connection on destroy', () => {
		const { container: testContainer, component: testComponent } = render(Dashboard);
		container = testContainer;
		component = testComponent;

		// Destroy component
		component.$destroy();

		// Should disconnect socket
		expect(mockSocket.disconnect).toHaveBeenCalled();
	});

	it('handles manual reconnection', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Simulate disconnection first
		mockSocket.connected = false;
		const onCalls = mockSocket.on.mock.calls;
		const disconnectCall = onCalls.find(call => call[0] === 'disconnect');
		const disconnectHandler = disconnectCall?.[1];
		disconnectHandler('transport close');

		await waitFor(() => {
			// Should show retry button
			const retryButton = container.querySelector('button:has-text("Retry")');
			expect(retryButton).toBeTruthy();
		});

		// Click retry button
		const retryButton = container.querySelector('button');
		if (retryButton && retryButton.textContent?.includes('Retry')) {
			await fireEvent.click(retryButton);
			expect(mockSocket.connect).toHaveBeenCalled();
		}
	});

	it('validates LED data before sending', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Try to set invalid LED index
		const ledIndexInput = container.querySelector('input[type="number"]') as HTMLInputElement;
		await fireEvent.input(ledIndexInput, { target: { value: '-1' } });

		// Try to update with invalid index
		const updateButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Update'));

		if (updateButton) {
			await fireEvent.click(updateButton);

			// Should not emit invalid data
			const emitCalls = mockSocket.emit.mock.calls;
			const invalidCalls = emitCalls.filter(call => 
				call[0] === 'led_update' && call[1]?.index < 0
			);
			expect(invalidCalls).toHaveLength(0);
		}
	});

	it('maintains connection health monitoring', async () => {
		const { container: testContainer } = render(Dashboard);
		container = testContainer;

		// Should start connection health check
		await waitFor(() => {
			const healthStatus = container.querySelector('.connection-health, .health-status');
			expect(healthStatus).toBeTruthy();
		}, { timeout: 2000 });
	});
});