<script>
	import { onMount, afterUpdate } from 'svelte';

	// Props
	export let ledState = [];
	export let width = 800;
	export let height = 200;
	export let responsive = true;
	export let ledSpacing = 2;
	export let ledRadius = 8;

	// Canvas and rendering
	let canvas;
	let ctx;
	let animationFrame;
	let lastUpdateTime = 0;
	const targetFPS = 60;
	const frameInterval = 1000 / targetFPS;

	// Responsive dimensions
	let containerWidth = width;
	let containerHeight = height;
	let actualWidth = width;
	let actualHeight = height;

	// Performance tracking
	let frameCount = 0;
	let fpsStartTime = Date.now();
	let currentFPS = 0;

	onMount(() => {
		if (canvas) {
			ctx = canvas.getContext('2d');
			if (responsive) {
				updateCanvasSize();
				window.addEventListener('resize', updateCanvasSize);
			}
			startAnimation();
		}

		return () => {
			if (animationFrame) {
				cancelAnimationFrame(animationFrame);
			}
			if (responsive) {
				window.removeEventListener('resize', updateCanvasSize);
			}
		};
	});

	afterUpdate(() => {
		if (ctx) {
			renderLEDs();
		}
	});

	function updateCanvasSize() {
		if (!canvas || !canvas.parentElement) return;

		const container = canvas.parentElement;
		containerWidth = container.clientWidth;
		
		// Maintain aspect ratio
		const aspectRatio = width / height;
		actualWidth = Math.min(containerWidth, width);
		actualHeight = actualWidth / aspectRatio;

		// Set canvas size with device pixel ratio for crisp rendering
		const dpr = window.devicePixelRatio || 1;
		canvas.width = actualWidth * dpr;
		canvas.height = actualHeight * dpr;
		canvas.style.width = actualWidth + 'px';
		canvas.style.height = actualHeight + 'px';

		// Scale context for high DPI displays
		ctx.scale(dpr, dpr);
	}

	function startAnimation() {
		function animate(currentTime) {
			if (currentTime - lastUpdateTime >= frameInterval) {
				renderLEDs();
				updateFPS();
				lastUpdateTime = currentTime;
			}
			animationFrame = requestAnimationFrame(animate);
		}
		animationFrame = requestAnimationFrame(animate);
	}

	function updateFPS() {
		frameCount++;
		const now = Date.now();
		if (now - fpsStartTime >= 1000) {
			currentFPS = Math.round((frameCount * 1000) / (now - fpsStartTime));
			frameCount = 0;
			fpsStartTime = now;
		}
	}

	// Helper function for rounded rectangle (polyfill for older browsers)
	function drawRoundedRect(ctx, x, y, width, height, radius) {
		ctx.beginPath();
		ctx.moveTo(x + radius, y);
		ctx.lineTo(x + width - radius, y);
		ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
		ctx.lineTo(x + width, y + height - radius);
		ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
		ctx.lineTo(x + radius, y + height);
		ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
		ctx.lineTo(x, y + radius);
		ctx.quadraticCurveTo(x, y, x + radius, y);
		ctx.closePath();
	}

	function renderLEDs() {
		if (!ctx || !ledState.length) return;

		// Clear canvas
		ctx.clearRect(0, 0, actualWidth, actualHeight);

		// Calculate LED layout
		const ledCount = ledState.length;
		const availableWidth = actualWidth - (ledSpacing * 2);
		const ledWidth = (availableWidth - (ledSpacing * (ledCount - 1))) / ledCount;
		const ledSize = Math.max(1, Math.min(ledWidth, ledRadius * 2)); // Ensure minimum size of 1
		const ledY = actualHeight / 2;

		// Skip rendering if ledSize is too small or invalid
		if (ledSize <= 0 || !isFinite(ledSize)) return;

		// Render background strip
		ctx.fillStyle = '#1a1a1a';
		if (ctx.roundRect) {
			// Use native roundRect if available
			ctx.roundRect(ledSpacing / 2, ledY - ledSize / 2 - 5, availableWidth + ledSpacing, ledSize + 10, 5);
		} else {
			// Use polyfill for older browsers
			drawRoundedRect(ctx, ledSpacing / 2, ledY - ledSize / 2 - 5, availableWidth + ledSpacing, ledSize + 10, 5);
		}
		ctx.fill();

		// Render individual LEDs
		ledState.forEach((led, index) => {
			const ledX = ledSpacing + (index * (ledWidth + ledSpacing)) + ledWidth / 2;
			
			// LED background (off state)
			ctx.fillStyle = '#333';
			ctx.beginPath();
			ctx.arc(ledX, ledY, ledSize / 2, 0, 2 * Math.PI);
			ctx.fill();

			// LED color (if active)
			if (led.brightness > 0) {
				const { r, g, b, brightness } = led;
				const alpha = brightness;

				// Inner LED color
				ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
				ctx.beginPath();
				ctx.arc(ledX, ledY, (ledSize / 2) * 0.8, 0, 2 * Math.PI);
				ctx.fill();

				// Glow effect
				if (brightness > 0.3) {
					const gradient = ctx.createRadialGradient(
						ledX, ledY, 0,
						ledX, ledY, ledSize * 1.5
					);
					gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha * 0.8})`);
					gradient.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`);
					gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

					ctx.fillStyle = gradient;
					ctx.beginPath();
					ctx.arc(ledX, ledY, ledSize * 1.5, 0, 2 * Math.PI);
					ctx.fill();
				}

				// Highlight for very bright LEDs
				if (brightness > 0.7) {
					ctx.fillStyle = `rgba(255, 255, 255, ${(brightness - 0.7) * 0.5})`;
					ctx.beginPath();
					ctx.arc(ledX, ledY, (ledSize / 2) * 0.4, 0, 2 * Math.PI);
					ctx.fill();
				}
			}

			// LED index label (for debugging/testing)
			if (ledSize > 16) {
				ctx.fillStyle = '#666';
				ctx.font = '10px monospace';
				ctx.textAlign = 'center';
				ctx.fillText(index.toString(), ledX, ledY + ledSize + 15);
			}
		});

		// Performance info overlay
		if (currentFPS > 0) {
			ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
			ctx.fillRect(actualWidth - 80, 5, 75, 25);
			ctx.fillStyle = '#fff';
			ctx.font = '12px monospace';
			ctx.textAlign = 'left';
			ctx.fillText(`${currentFPS} FPS`, actualWidth - 75, 20);
		}
	}

	// Handle canvas click/touch for LED selection (for testing)
	function handleCanvasClick(event) {
		if (!canvas || !ledState.length) return;

		const rect = canvas.getBoundingClientRect();
		let x, y;

		// Handle both mouse and touch events
		if (event.touches && event.touches.length > 0) {
			x = event.touches[0].clientX - rect.left;
			y = event.touches[0].clientY - rect.top;
		} else {
			x = event.clientX - rect.left;
			y = event.clientY - rect.top;
		}

		// Scale coordinates to canvas size
		const scaleX = actualWidth / rect.width;
		const scaleY = actualHeight / rect.height;
		const canvasX = x * scaleX;
		const canvasY = y * scaleY;

		// Find clicked LED
		const ledCount = ledState.length;
		const availableWidth = actualWidth - (ledSpacing * 2);
		const ledWidth = (availableWidth - (ledSpacing * (ledCount - 1))) / ledCount;
		const ledY = actualHeight / 2;

		for (let i = 0; i < ledCount; i++) {
			const ledX = ledSpacing + (i * (ledWidth + ledSpacing)) + ledWidth / 2;
			const distance = Math.sqrt((canvasX - ledX) ** 2 + (canvasY - ledY) ** 2);
			
			if (distance <= ledRadius) {
				// Dispatch LED click event
				const ledClickEvent = new CustomEvent('ledClick', {
					detail: {
						index: i,
						led: ledState[i],
						position: { x: ledX, y: ledY }
					}
				});
				canvas.dispatchEvent(ledClickEvent);
				break;
			}
		}
	}

	// Handle touch events
	function handleTouchStart(event) {
		event.preventDefault(); // Prevent scrolling
		handleCanvasClick(event);
	}

	// Handle touch move for dragging selection
	function handleTouchMove(event) {
		event.preventDefault(); // Prevent scrolling
		handleCanvasClick(event);
	}

	// Expose current FPS for parent component
	export function getCurrentFPS() {
		return currentFPS;
	}

	// Expose LED count for parent component
	export function getLEDCount() {
		return ledState.length;
	}
</script>

<div class="led-visualization-container">
	<canvas 
		bind:this={canvas}
		on:click={handleCanvasClick}
		on:touchstart={handleTouchStart}
		on:touchmove={handleTouchMove}
		class="led-canvas"
		{width}
		{height}
	></canvas>
	
	{#if ledState.length === 0}
		<div class="no-data-overlay">
			<p>No LED data available</p>
			<small>Connect to WebSocket to see real-time LED visualization</small>
		</div>
	{/if}
</div>

<style>
	.led-visualization-container {
		position: relative;
		width: 100%;
		max-width: 100%;
		border-radius: 8px;
		overflow: hidden;
		background: #0a0a0a;
		border: 2px solid #333;
	}

	.led-canvas {
		display: block;
		width: 100%;
		height: auto;
		cursor: pointer;
		background: #0a0a0a;
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
		min-height: 60px;
	}

	.no-data-overlay {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		color: #666;
		pointer-events: none;
	}

	.no-data-overlay p {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		font-weight: 500;
	}

	.no-data-overlay small {
		font-size: 0.9rem;
		opacity: 0.8;
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.led-visualization-container {
			border-width: 1px;
		}
		
		.led-canvas {
			min-height: 50px;
		}
	}

	@media (max-width: 480px) {
		.led-canvas {
			min-height: 40px;
		}
	}
</style>