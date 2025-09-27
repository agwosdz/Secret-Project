<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	let isOpen = false;
	let mounted = false;
	let isMobile = false;

	function toggleMenu() {
		isOpen = !isOpen;
	}

	function closeMenu() {
		isOpen = false;
	}

	function handleResize() {
		isMobile = window.innerWidth <= 768;
		if (!isMobile) {
			isOpen = false; // Close mobile menu when switching to desktop
		}
	}

	onMount(() => {
		mounted = true;
		handleResize();
		window.addEventListener('resize', handleResize);
		
		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});

	$: currentPath = $page.url.pathname;

	const navigationItems = [
		{ href: '/', icon: '🏠', text: 'Home', description: 'Main dashboard and overview' },
		{ href: '/play', icon: '🎹', text: 'Play', description: 'MIDI playback and visualization' },
		{ href: '/upload', icon: '📤', text: 'Upload', description: 'Upload MIDI files' },
		{ href: '/settings', icon: '⚙️', text: 'Settings', description: 'Configuration and preferences' }
	];
</script>

<!-- Desktop Sidebar Navigation -->
<nav class="desktop-nav {mounted ? 'mounted' : ''}" aria-label="Main navigation">
	<div class="nav-header">
		<div class="logo">
			<span class="logo-icon">🎹</span>
			<span class="logo-text">Piano LED</span>
		</div>
	</div>
	
	<ul class="nav-list">
		{#each navigationItems as item}
			<li>
				<a 
					href={item.href}
					class:active={currentPath === item.href}
					title={item.description}
				>
					<span class="nav-icon">{item.icon}</span>
					<span class="nav-text">{item.text}</span>
				</a>
			</li>
		{/each}
	</ul>
	
	<div class="nav-footer">
		<div class="version-info">
			<span class="version-text">v1.0.0</span>
		</div>
	</div>
</nav>

<!-- Mobile Navigation -->
<div class="mobile-nav-container {mounted ? 'mounted' : ''}">
	<button 
		class="menu-toggle" 
		on:click={toggleMenu}
		aria-label="{isOpen ? 'Close menu' : 'Open menu'}"
		aria-expanded={isOpen}
	>
		<div class="hamburger {isOpen ? 'open' : ''}">
			<span></span>
			<span></span>
			<span></span>
		</div>
	</button>

	<nav class="mobile-nav {isOpen ? 'open' : ''}" aria-hidden={!isOpen} aria-label="Mobile navigation">
		<div class="mobile-nav-header">
			<div class="mobile-logo">
				<span class="logo-icon">🎹</span>
				<span class="logo-text">Piano LED Visualizer</span>
			</div>
		</div>
		
		<ul class="mobile-nav-list">
			{#each navigationItems as item}
				<li>
					<a 
						href={item.href}
						class:active={currentPath === item.href}
						on:click={closeMenu}
					>
						<span class="icon">{item.icon}</span>
						<div class="nav-content">
							<span class="text">{item.text}</span>
							<span class="description">{item.description}</span>
						</div>
					</a>
				</li>
			{/each}
		</ul>
	</nav>

	{#if isOpen}
		<div class="overlay" on:click={closeMenu} aria-hidden="true"></div>
	{/if}
</div>

<style>
	/* Desktop Navigation Styles */
	.desktop-nav {
		position: fixed;
		top: 0;
		left: 0;
		width: 280px;
		height: 100vh;
		background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
		border-right: 1px solid #334155;
		display: flex;
		flex-direction: column;
		z-index: 100;
		opacity: 0;
		transform: translateX(-100%);
		transition: all 0.3s ease;
	}

	.desktop-nav.mounted {
		opacity: 1;
		transform: translateX(0);
	}

	.nav-header {
		padding: 2rem 1.5rem 1.5rem;
		border-bottom: 1px solid #334155;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.logo-icon {
		font-size: 2rem;
		filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
	}

	.logo-text {
		font-size: 1.25rem;
		font-weight: 700;
		color: #f8fafc;
		letter-spacing: -0.025em;
	}

	.nav-list {
		flex: 1;
		list-style: none;
		padding: 1rem 0;
		margin: 0;
		overflow-y: auto;
	}

	.nav-list li {
		margin: 0.25rem 0;
	}

	.nav-list a {
		display: flex;
		align-items: center;
		padding: 0.875rem 1.5rem;
		color: #cbd5e1;
		text-decoration: none;
		font-weight: 500;
		transition: all 0.2s ease;
		border-radius: 0.5rem;
		margin: 0 0.75rem;
		position: relative;
	}

	.nav-list a:hover {
		background: rgba(59, 130, 246, 0.1);
		color: #93c5fd;
		transform: translateX(4px);
	}

	.nav-list a.active {
		background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
	}

	.nav-list a.active::before {
		content: '';
		position: absolute;
		left: -0.75rem;
		top: 50%;
		transform: translateY(-50%);
		width: 4px;
		height: 24px;
		background: #60a5fa;
		border-radius: 2px;
	}

	.nav-icon {
		font-size: 1.25rem;
		margin-right: 0.875rem;
		width: 24px;
		text-align: center;
		filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
	}

	.nav-text {
		font-size: 0.95rem;
		letter-spacing: 0.01em;
	}

	.nav-footer {
		padding: 1rem 1.5rem;
		border-top: 1px solid #334155;
	}

	.version-info {
		text-align: center;
	}

	.version-text {
		font-size: 0.75rem;
		color: #64748b;
		font-weight: 500;
	}

	/* Mobile Navigation Styles */
	.mobile-nav-container {
		display: none;
		position: fixed;
		top: 0;
		right: 0;
		z-index: 1000;
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.mobile-nav-container.mounted {
		opacity: 1;
	}

	.menu-toggle {
		position: fixed;
		top: 1rem;
		right: 1rem;
		width: 56px;
		height: 56px;
		border-radius: 50%;
		background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
		z-index: 1001;
		padding: 0;
		transition: all 0.2s ease;
	}

	.menu-toggle:hover {
		transform: scale(1.05);
		box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
	}

	.menu-toggle:active {
		transform: scale(0.95);
	}

	.hamburger {
		width: 24px;
		height: 18px;
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}

	.hamburger span {
		display: block;
		height: 2px;
		width: 100%;
		background: white;
		border-radius: 2px;
		transition: all 0.3s ease;
	}

	.hamburger.open span:nth-child(1) {
		transform: translateY(8px) rotate(45deg);
	}

	.hamburger.open span:nth-child(2) {
		opacity: 0;
	}

	.hamburger.open span:nth-child(3) {
		transform: translateY(-8px) rotate(-45deg);
	}

	.mobile-nav {
		position: fixed;
		top: 0;
		right: -320px;
		width: 320px;
		height: 100vh;
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
		box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
		transition: right 0.3s ease;
		z-index: 1000;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
	}

	.mobile-nav.open {
		right: 0;
	}

	.mobile-nav-header {
		padding: 2rem 1.5rem 1.5rem;
		border-bottom: 1px solid #e2e8f0;
		background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
		color: white;
	}

	.mobile-logo {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.mobile-logo .logo-icon {
		font-size: 1.75rem;
	}

	.mobile-logo .logo-text {
		font-size: 1.125rem;
		font-weight: 700;
		letter-spacing: -0.025em;
	}

	.overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.5);
		z-index: 999;
		backdrop-filter: blur(2px);
	}

	.mobile-nav-list {
		list-style: none;
		padding: 1rem 0;
		margin: 0;
		flex: 1;
	}

	.mobile-nav-list li {
		margin: 0.25rem 0;
	}

	.mobile-nav-list a {
		display: flex;
		align-items: center;
		padding: 1rem 1.5rem;
		color: #1f2937;
		text-decoration: none;
		font-weight: 500;
		transition: all 0.2s ease;
		min-height: 72px;
		border-radius: 0.5rem;
		margin: 0 0.75rem;
	}

	.mobile-nav-list a:hover,
	.mobile-nav-list a:focus {
		background: #f1f5f9;
		transform: translateX(4px);
	}

	.mobile-nav-list a.active {
		background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
		color: #1d4ed8;
		border-left: 4px solid #3b82f6;
		box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
	}

	.mobile-nav-list .icon {
		font-size: 1.25rem;
		margin-right: 1rem;
		width: 28px;
		text-align: center;
		flex-shrink: 0;
	}

	.nav-content {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-content .text {
		font-size: 1rem;
		font-weight: 600;
		line-height: 1.2;
	}

	.nav-content .description {
		font-size: 0.8rem;
		color: #64748b;
		line-height: 1.3;
	}

	.mobile-nav-list a.active .description {
		color: #475569;
	}

	/* Responsive Breakpoints */
	@media (max-width: 768px) {
		.desktop-nav {
			display: none;
		}

		.mobile-nav-container {
			display: block;
		}
	}

	@media (min-width: 769px) {
		.mobile-nav-container {
			display: none;
		}

		.desktop-nav {
			display: flex;
		}
	}

	/* Accessibility Improvements */
	@media (prefers-reduced-motion: reduce) {
		.desktop-nav,
		.mobile-nav,
		.menu-toggle,
		.hamburger span,
		.nav-list a,
		.mobile-nav-list a {
			transition: none;
		}
	}

	/* Focus Styles */
	.nav-list a:focus,
	.mobile-nav-list a:focus,
	.menu-toggle:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}

	/* High Contrast Mode Support */
	@media (prefers-contrast: high) {
		.desktop-nav {
			border-right: 2px solid;
		}
		
		.nav-list a.active,
		.mobile-nav-list a.active {
			border: 2px solid;
		}
	}
</style>