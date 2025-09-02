import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LEDVisualization from './LEDVisualization.svelte';

// Mock canvas context
const mockContext = {
	clearRect: vi.fn(),
	fillRect: vi.fn(),
	beginPath: vi.fn(),
	arc: vi.fn(),
	fill: vi.fn(),
	save: vi.fn(),
	restore: vi.fn(),
	setTransform: vi.fn(),
	scale: vi.fn(),
	translate: vi.fn(),
	createRadialGradient: vi.fn(() => ({
		addColorStop: vi.fn()
	})),
	fillStyle: '',
	globalAlpha: 1,
	canvas: {
		width: 800,
		height: 100
	}
};

// Mock HTMLCanvasElement.getContext
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
	value: vi.fn(() => mockContext),
	writable: true
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn()
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn((cb) => setTimeout(cb, 16));
global.cancelAnimationFrame = vi.fn();

describe('LEDVisualization', () => {
	let component: any;
	let container: HTMLElement;

	const defaultProps = {
		ledState: Array.from({ length: 50 }, (_, i) => ({
			index: i,
			color: { r: 255, g: 0, b: 0 },
			brightness: 1.0
		})),
		width: 800,
		height: 100,
		responsive: true
	};

	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		if (component) {
			component.$destroy();
		}
	});

	it('renders with default props', () => {
		const { container: testContainer } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;

		const canvas = container.querySelector('canvas');
		expect(canvas).toBeTruthy();
		expect(canvas?.width).toBe(800);
		expect(canvas?.height).toBe(100);
	});

	it('renders correct number of LEDs', async () => {
		const { container: testContainer } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;

		// Wait for initial render
		await waitFor(() => {
			expect(mockContext.arc).toHaveBeenCalled();
		});

		// Should call arc for each LED (50 LEDs)
		expect(mockContext.arc).toHaveBeenCalledTimes(50);
	});

	it('handles LED click events', async () => {
		let clickedLED: any = null;
		const handleLEDClick = (event: CustomEvent) => {
			clickedLED = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('ledClick', handleLEDClick);

		const canvas = container.querySelector('canvas');
		expect(canvas).toBeTruthy();

		// Simulate click on first LED (approximate position)
		await fireEvent.click(canvas!, {
			clientX: 50, // Approximate position of first LED
			clientY: 50
		});

		// Should emit ledClick event
		expect(clickedLED).toBeTruthy();
		expect(clickedLED.index).toBeGreaterThanOrEqual(0);
	});

	it('handles touch events on mobile', async () => {
		let touchedLED: any = null;
		const handleLEDClick = (event: CustomEvent) => {
			touchedLED = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('ledClick', handleLEDClick);

		const canvas = container.querySelector('canvas');
		expect(canvas).toBeTruthy();

		// Simulate touch start
		await fireEvent.touchStart(canvas!, {
			touches: [{ clientX: 50, clientY: 50 }]
		});

		// Should emit ledClick event
		expect(touchedLED).toBeTruthy();
		expect(touchedLED.index).toBeGreaterThanOrEqual(0);
	});

	it('updates LED colors correctly', async () => {
		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Clear previous calls
		vi.clearAllMocks();

		// Update LED state with different colors
		const newLedState = Array.from({ length: 50 }, (_, i) => ({
			index: i,
			color: { r: 0, g: 255, b: 0 }, // Green instead of red
			brightness: 0.8
		}));

		await component.$set({ ledState: newLedState });

		// Wait for re-render
		await waitFor(() => {
			expect(mockContext.arc).toHaveBeenCalled();
		});

		// Should render all LEDs again with new colors
		expect(mockContext.arc).toHaveBeenCalledTimes(50);
	});

	it('handles responsive resizing', async () => {
		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: { ...defaultProps, responsive: true }
		});
		container = testContainer;
		component = testComponent;

		// Verify ResizeObserver was called
		expect(global.ResizeObserver).toHaveBeenCalled();

		// Update dimensions
		await component.$set({ width: 1200, height: 150 });

		const canvas = container.querySelector('canvas');
		expect(canvas?.width).toBe(1200);
		expect(canvas?.height).toBe(150);
	});

	it('tracks FPS correctly', async () => {
		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Wait for animation frames
		await new Promise(resolve => setTimeout(resolve, 100));

		// FPS should be calculated (mock implementation)
		expect(requestAnimationFrame).toHaveBeenCalled();
	});

	it('handles different LED counts', async () => {
		const smallLedState = Array.from({ length: 10 }, (_, i) => ({
			index: i,
			color: { r: 255, g: 255, b: 255 },
			brightness: 1.0
		}));

		const { container: testContainer } = render(LEDVisualization, {
			props: { ...defaultProps, ledState: smallLedState }
		});
		container = testContainer;

		// Wait for render
		await waitFor(() => {
			expect(mockContext.arc).toHaveBeenCalled();
		});

		// Should render 10 LEDs
		expect(mockContext.arc).toHaveBeenCalledTimes(10);
	});

	it('handles brightness variations', async () => {
		const varyingBrightnessLeds = Array.from({ length: 5 }, (_, i) => ({
			index: i,
			color: { r: 255, g: 0, b: 0 },
			brightness: i * 0.2 // 0, 0.2, 0.4, 0.6, 0.8
		}));

		const { container: testContainer } = render(LEDVisualization, {
			props: { ...defaultProps, ledState: varyingBrightnessLeds }
		});
		container = testContainer;

		// Wait for render
		await waitFor(() => {
			expect(mockContext.arc).toHaveBeenCalled();
		});

		// Should handle different brightness levels
		// globalAlpha should be modified during rendering
		expect(mockContext.arc).toHaveBeenCalledTimes(5);
	});

	it('cleans up on destroy', () => {
		const { container: testContainer, component: testComponent } = render(LEDVisualization, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Destroy component
		component.$destroy();

		// Should clean up animation frame
		expect(cancelAnimationFrame).toHaveBeenCalled();
	});

	it('handles empty LED state', async () => {
		const { container: testContainer } = render(LEDVisualization, {
			props: { ...defaultProps, ledState: [] }
		});
		container = testContainer;

		// Should still render canvas but no LEDs
		const canvas = container.querySelector('canvas');
		expect(canvas).toBeTruthy();
		expect(mockContext.clearRect).toHaveBeenCalled();
	});
});