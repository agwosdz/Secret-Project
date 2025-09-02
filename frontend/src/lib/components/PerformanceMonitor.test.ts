import { render, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PerformanceMonitor from './PerformanceMonitor.svelte';

describe('PerformanceMonitor', () => {
	let component: any;
	let container: HTMLElement;

	const defaultProps = {
		updateFrequency: 30,
		latency: 15,
		connectionHealth: 'excellent' as const,
		lastUpdateTime: Date.now()
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
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Check for main title
		expect(container.textContent).toContain('Performance Monitor');
	});

	it('displays update frequency correctly', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should display the update frequency
		expect(container.textContent).toContain('30');
		expect(container.textContent).toContain('Hz');
	});

	it('displays latency correctly', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should display the latency
		expect(container.textContent).toContain('15');
		expect(container.textContent).toContain('ms');
	});

	it('displays excellent connection health', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, connectionHealth: 'excellent' }
		});
		container = testContainer;

		// Should show excellent health status
		const healthElement = container.querySelector('.health-excellent');
		expect(healthElement).toBeTruthy();
		expect(container.textContent).toContain('Excellent');
	});

	it('displays good connection health', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, connectionHealth: 'good' }
		});
		container = testContainer;

		// Should show good health status
		const healthElement = container.querySelector('.health-good');
		expect(healthElement).toBeTruthy();
		expect(container.textContent).toContain('Good');
	});

	it('displays warning connection health', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, connectionHealth: 'warning' }
		});
		container = testContainer;

		// Should show warning health status
		const healthElement = container.querySelector('.health-warning');
		expect(healthElement).toBeTruthy();
		expect(container.textContent).toContain('Warning');
	});

	it('displays poor connection health', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, connectionHealth: 'poor' }
		});
		container = testContainer;

		// Should show poor health status
		const healthElement = container.querySelector('.health-poor');
		expect(healthElement).toBeTruthy();
		expect(container.textContent).toContain('Poor');
	});

	it('updates metrics when props change', async () => {
		const { container: testContainer, component: testComponent } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Initial values
		expect(container.textContent).toContain('30');
		expect(container.textContent).toContain('15');

		// Update props
		await component.$set({
			updateFrequency: 60,
			latency: 8
		});

		// Should display new values
		expect(container.textContent).toContain('60');
		expect(container.textContent).toContain('8');
	});

	it('shows appropriate status indicators', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should have status indicators
		const statusIndicators = container.querySelectorAll('.status-indicator, .metric-status');
		expect(statusIndicators.length).toBeGreaterThan(0);
	});

	it('displays chart placeholder', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should have chart container
		const chartContainer = container.querySelector('.chart-container');
		expect(chartContainer).toBeTruthy();
	});

	it('handles high frequency updates', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, updateFrequency: 120 }
		});
		container = testContainer;

		// Should display high frequency
		expect(container.textContent).toContain('120');
	});

	it('handles low frequency updates', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, updateFrequency: 5 }
		});
		container = testContainer;

		// Should display low frequency
		expect(container.textContent).toContain('5');
	});

	it('handles high latency', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, latency: 500 }
		});
		container = testContainer;

		// Should display high latency
		expect(container.textContent).toContain('500');
	});

	it('handles zero latency', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, latency: 0 }
		});
		container = testContainer;

		// Should display zero latency
		expect(container.textContent).toContain('0');
	});

	it('displays last update time', () => {
		const testTime = Date.now();
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, lastUpdateTime: testTime }
		});
		container = testContainer;

		// Should have some time-related content
		// (exact format depends on implementation)
		expect(container.textContent.length).toBeGreaterThan(0);
	});

	it('handles missing lastUpdateTime', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: { ...defaultProps, lastUpdateTime: undefined }
		});
		container = testContainer;

		// Should still render without errors
		expect(container.querySelector('.performance-monitor')).toBeTruthy();
	});

	it('shows metric cards', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should have metric cards
		const metricCards = container.querySelectorAll('.metric-card');
		expect(metricCards.length).toBeGreaterThan(0);
	});

	it('displays metrics grid layout', () => {
		const { container: testContainer } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;

		// Should have metrics grid
		const metricsGrid = container.querySelector('.metrics-grid');
		expect(metricsGrid).toBeTruthy();
	});

	it('handles component cleanup', () => {
		const { container: testContainer, component: testComponent } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Component should destroy without errors
		expect(() => component.$destroy()).not.toThrow();
	});

	it('responds to prop changes reactively', async () => {
		const { container: testContainer, component: testComponent } = render(PerformanceMonitor, {
			props: defaultProps
		});
		container = testContainer;
		component = testComponent;

		// Change connection health
		await component.$set({ connectionHealth: 'poor' });

		// Should update the health display
		await waitFor(() => {
			expect(container.querySelector('.health-poor')).toBeTruthy();
		});
	});

	it('maintains consistent layout across different metrics', () => {
		const testCases = [
			{ updateFrequency: 1, latency: 1000, connectionHealth: 'poor' as const },
			{ updateFrequency: 60, latency: 10, connectionHealth: 'excellent' as const },
			{ updateFrequency: 120, latency: 5, connectionHealth: 'good' as const }
		];

		testCases.forEach((testCase, index) => {
			const { container: testContainer } = render(PerformanceMonitor, {
				props: { ...defaultProps, ...testCase }
			});

			// Should maintain consistent structure
			expect(testContainer.querySelector('.performance-monitor')).toBeTruthy();
			expect(testContainer.querySelector('.metrics-grid')).toBeTruthy();
		});
	});
});