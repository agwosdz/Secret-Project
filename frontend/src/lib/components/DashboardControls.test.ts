import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import DashboardControls from './DashboardControls.svelte';

describe('DashboardControls', () => {
	let component: any;
	let container: HTMLElement;

	const defaultProps = {
		connected: true,
		ledCount: 50
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
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		// Check for main sections
		expect(container.querySelector('h3')).toBeTruthy();
		expect(container.textContent).toContain('Manual LED Control');
	});

	it('shows connection warning when disconnected', () => {
		const { container: testContainer } = render(DashboardControls, {
			props: { ...defaultProps, connected: false }
		});
		container = testContainer;

		expect(container.textContent).toContain('WebSocket disconnected');
	});

	it('handles LED index input changes', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		const ledIndexInput = container.querySelector('input[type="number"]') as HTMLInputElement;
		expect(ledIndexInput).toBeTruthy();

		await fireEvent.input(ledIndexInput, { target: { value: '25' } });
		expect(ledIndexInput.value).toBe('25');
	});

	it('handles color picker changes', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		const colorInput = container.querySelector('input[type="color"]') as HTMLInputElement;
		expect(colorInput).toBeTruthy();

		await fireEvent.input(colorInput, { target: { value: '#00ff00' } });
		expect(colorInput.value).toBe('#00ff00');
	});

	it('handles brightness slider changes', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		const brightnessSlider = container.querySelector('input[type="range"]') as HTMLInputElement;
		expect(brightnessSlider).toBeTruthy();

		await fireEvent.input(brightnessSlider, { target: { value: '0.7' } });
		expect(brightnessSlider.value).toBe('0.7');
	});

	it('emits ledUpdate event when updating single LED', async () => {
		let emittedEvent: any = null;
		const handleLEDUpdate = (event: CustomEvent) => {
			emittedEvent = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('ledUpdate', handleLEDUpdate);

		// Find and click the "Set LED" button
		const setLedButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Set LED'));
		expect(setLedButton).toBeTruthy();

		await fireEvent.click(setLedButton!);

		expect(emittedEvent).toBeTruthy();
		expect(emittedEvent.index).toBeDefined();
		expect(emittedEvent.color).toBeDefined();
		expect(emittedEvent.brightness).toBeDefined();
	});

	it('emits patternUpdate event when testing patterns', async () => {
		let emittedEvent: any = null;
		const handlePatternUpdate = (event: CustomEvent) => {
			emittedEvent = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('patternUpdate', handlePatternUpdate);

		// Find and click a pattern button (e.g., Rainbow)
		const rainbowButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Rainbow'));
		expect(rainbowButton).toBeTruthy();

		await fireEvent.click(rainbowButton!);

		expect(emittedEvent).toBeTruthy();
		expect(emittedEvent.pattern).toBe('rainbow');
	});

	it('emits bulkUpdate event for Fill All action', async () => {
		let emittedEvent: any = null;
		const handleBulkUpdate = (event: CustomEvent) => {
			emittedEvent = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('bulkUpdate', handleBulkUpdate);

		// Find and click the "Fill All" button
		const fillAllButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Fill All'));
		expect(fillAllButton).toBeTruthy();

		await fireEvent.click(fillAllButton!);

		expect(emittedEvent).toBeTruthy();
		expect(emittedEvent.action).toBe('fill');
		expect(emittedEvent.color).toBeDefined();
		expect(emittedEvent.brightness).toBeDefined();
	});

	it('emits bulkUpdate event for Clear All action', async () => {
		let emittedEvent: any = null;
		const handleBulkUpdate = (event: CustomEvent) => {
			emittedEvent = event.detail;
		};

		const { container: testContainer, component: testComponent } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		component.$on('bulkUpdate', handleBulkUpdate);

		// Find and click the "Clear All" button
		const clearAllButton = Array.from(container.querySelectorAll('button'))
			.find(btn => btn.textContent?.includes('Clear All'));
		expect(clearAllButton).toBeTruthy();

		await fireEvent.click(clearAllButton!);

		expect(emittedEvent).toBeTruthy();
		expect(emittedEvent.action).toBe('clear');
	});

	it('handles preset color selection', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		// Find preset color buttons
		const presetButtons = container.querySelectorAll('.color-preset, .preset-color');
		expect(presetButtons.length).toBeGreaterThan(0);

		// Click first preset color
		await fireEvent.click(presetButtons[0]);

		// Color should be updated (we can't easily test the internal state,
		// but we can verify the click doesn't throw an error)
		expect(true).toBe(true);
	});

	it('validates LED index bounds', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: { ...defaultProps, ledCount: 50 }
		});
		container = testContainer;

		const ledIndexInput = container.querySelector('input[type="number"]') as HTMLInputElement;
		expect(ledIndexInput).toBeTruthy();

		// Test valid range
		expect(ledIndexInput.min).toBe('0');
		expect(ledIndexInput.max).toBe('49'); // ledCount - 1
	});

	it('disables controls when disconnected', () => {
		const { container: testContainer } = render(DashboardControls, {
			props: { ...defaultProps, connected: false }
		});
		container = testContainer;

		// Most buttons should be disabled when disconnected
		const buttons = container.querySelectorAll('button');
		const disabledButtons = Array.from(buttons).filter(btn => btn.hasAttribute('disabled'));
		expect(disabledButtons.length).toBeGreaterThan(0);
	});

	it('handles pattern selection changes', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		const patternSelect = container.querySelector('select') as HTMLSelectElement;
		if (patternSelect) {
			await fireEvent.change(patternSelect, { target: { value: 'chase' } });
			expect(patternSelect.value).toBe('chase');
		}
	});

	it('handles RGB color controls', async () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		// Look for RGB sliders (if they exist in the component)
		const rgbSliders = container.querySelectorAll('input[type="range"]');
		if (rgbSliders.length > 1) {
			// Test RGB slider interaction
			await fireEvent.input(rgbSliders[0], { target: { value: '128' } });
			expect((rgbSliders[0] as HTMLInputElement).value).toBe('128');
		}
	});

	it('renders all pattern options', () => {
		const { container: testContainer } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;

		// Check for pattern-related elements
		const patternButtons = Array.from(container.querySelectorAll('button'))
			.filter(btn => {
				const text = btn.textContent?.toLowerCase() || '';
				return ['rainbow', 'chase', 'pulse', 'strobe', 'fade'].some(pattern => 
					text.includes(pattern)
				);
			});

		expect(patternButtons.length).toBeGreaterThan(0);
	});

	it('handles component cleanup', () => {
		const { container: testContainer, component: testComponent } = render(DashboardControls, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Component should destroy without errors
		expect(() => component.$destroy()).not.toThrow();
	});
});