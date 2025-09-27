<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	let isOpen = false;
	let mounted = false;

	function toggleMenu() {
		isOpen = !isOpen;
	}

	function closeMenu() {
		isOpen = false;
	}

	onMount(() => {
		mounted = true;
	});

	$: currentPath = $page.url.pathname;
</script>

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

	<nav class="mobile-nav {isOpen ? 'open' : ''}" aria-hidden={!isOpen}>
		<ul>
			<li>
				<a 
					href="/" 
					class:active={currentPath === '/'}
					on:click={closeMenu}
				>
					<span class="icon">🏠</span>
					<span class="text">Home</span>
				</a>
			</li>
			<li>
				<a 
					href="/play" 
					class:active={currentPath === '/play'}
					on:click={closeMenu}
				>
					<span class="icon">🎹</span>
					<span class="text">Play</span>
				</a>
			</li>
			<li>
				<a 
					href="/upload" 
					class:active={currentPath === '/upload'}
					on:click={closeMenu}
				>
					<span class="icon">📤</span>
					<span class="text">Upload</span>
				</a>
			</li>
			<li>
				<a 
					href="/settings" 
					class:active={currentPath === '/settings'}
					on:click={closeMenu}
				>
					<span class="icon">⚙️</span>
					<span class="text">Settings</span>
				</a>
			</li>
		</ul>
	</nav>

	{#if isOpen}
		<div class="overlay" on:click={closeMenu} aria-hidden="true"></div>
	{/if}
</div>

<style>
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
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: #3b82f6;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		z-index: 1001;
		padding: 0;
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
		right: -280px;
		width: 280px;
		height: 100vh;
		background: white;
		box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
		transition: right 0.3s ease;
		z-index: 1000;
		padding-top: 5rem;
		overflow-y: auto;
	}

	.mobile-nav.open {
		right: 0;
	}

	.overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.5);
		z-index: 999;
	}

	.mobile-nav ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.mobile-nav li {
		margin: 0;
	}

	.mobile-nav a {
		display: flex;
		align-items: center;
		padding: 1rem 1.5rem;
		color: #1f2937;
		text-decoration: none;
		font-weight: 500;
		transition: background-color 0.2s ease;
		min-height: 60px; /* Larger touch target */
	}

	.mobile-nav a:hover,
	.mobile-nav a:focus {
		background-color: #f3f4f6;
	}

	.mobile-nav a.active {
		background-color: #eff6ff;
		color: #2563eb;
		border-left: 4px solid #2563eb;
	}

	.icon {
		font-size: 1.25rem;
		margin-right: 1rem;
		width: 24px;
		text-align: center;
	}

	@media (max-width: 768px) {
		.mobile-nav-container {
			display: block;
		}
	}
</style>