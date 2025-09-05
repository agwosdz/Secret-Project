<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import MobileNavigation from '$lib/components/MobileNavigation.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
</svelte:head>

<div class="app-container">
	<MobileNavigation />
	<main>
		{@render children?.()}
	</main>
</div>

<style>
	.app-container {
		position: relative;
		min-height: 100vh;
	}

	main {
		padding-bottom: 2rem;
	}

	@media (max-width: 768px) {
		main {
			padding-top: 1rem;
			padding-bottom: 5rem; /* Space for mobile navigation */
		}
	}
</style>
