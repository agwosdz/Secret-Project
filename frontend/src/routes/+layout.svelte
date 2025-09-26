<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import Navigation from '$lib/components/Navigation.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import '$lib/styles/global.css';
	import { page } from '$app/stores';

	let { children } = $props();
	
	// Force page re-render when route changes to prevent content stacking
	let currentPath = $derived($page.url.pathname);
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
</svelte:head>

<div class="app-container">
	<Navigation />
	<main class="main-content" key={currentPath}>
		{@render children?.()}
	</main>
</div>

<!-- Global Toast Container -->
<ToastContainer />

<style>
	.app-container {
		position: relative;
		min-height: 100vh;
		display: flex;
	}

	.main-content {
		flex: 1;
		padding: 2rem;
		min-height: 100vh;
		overflow-x: auto;
	}

	/* Desktop Layout */
	@media (min-width: 769px) {
		.main-content {
			margin-left: 280px; /* Width of desktop sidebar */
			padding: 2rem 3rem;
		}
	}

	/* Mobile Layout */
	@media (max-width: 768px) {
		.app-container {
			display: block;
		}
		
		.main-content {
			margin-left: 0;
			padding: 1rem;
			padding-bottom: 5rem; /* Space for mobile navigation */
			min-height: calc(100vh - 5rem);
		}
	}

	/* Tablet Layout */
	@media (min-width: 769px) and (max-width: 1024px) {
		.main-content {
			padding: 2rem;
		}
	}

	/* Large Screen Layout */
	@media (min-width: 1200px) {
		.main-content {
			padding: 3rem 4rem;
			max-width: calc(100vw - 280px);
		}
	}
</style>
