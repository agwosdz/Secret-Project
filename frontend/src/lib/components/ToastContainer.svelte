<script lang="ts">
	import { toastStore } from '$lib/stores/toastStore';
	import Toast from './Toast.svelte';

	// Group toasts by position for better organization
	$: toastsByPosition = $toastStore.reduce((acc, toast) => {
		const position = toast.position || 'top-right';
		if (!acc[position]) {
			acc[position] = [];
		}
		acc[position].push(toast);
		return acc;
	}, {} as Record<string, typeof $toastStore>);

	function handleDismiss(toastId: string) {
		toastStore.removeToast(toastId);
	}
</script>

<!-- Render toast containers for each position -->
{#each Object.entries(toastsByPosition) as [position, toasts]}
	<div class="toast-container toast-container-{position}" aria-live="polite" aria-label="Notifications">
		{#each toasts as toast (toast.id)}
			<Toast
				type={toast.type}
				title={toast.title}
				message={toast.message}
				duration={toast.duration}
				dismissible={toast.dismissible}
				persistent={toast.persistent}
				position={toast.position}
				on:dismiss={() => handleDismiss(toast.id)}
			/>
		{/each}
	</div>
{/each}

<style>
	.toast-container {
		position: fixed;
		z-index: var(--z-toast, 1000);
		pointer-events: none;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		max-height: 100vh;
		overflow: hidden;
	}

	/* Position-specific containers */
	.toast-container-top-right {
		top: var(--space-4);
		right: var(--space-4);
		align-items: flex-end;
	}

	.toast-container-top-left {
		top: var(--space-4);
		left: var(--space-4);
		align-items: flex-start;
	}

	.toast-container-bottom-right {
		bottom: var(--space-4);
		right: var(--space-4);
		align-items: flex-end;
		flex-direction: column-reverse;
	}

	.toast-container-bottom-left {
		bottom: var(--space-4);
		left: var(--space-4);
		align-items: flex-start;
		flex-direction: column-reverse;
	}

	.toast-container-top-center {
		top: var(--space-4);
		left: 50%;
		transform: translateX(-50%);
		align-items: center;
	}

	.toast-container-bottom-center {
		bottom: var(--space-4);
		left: 50%;
		transform: translateX(-50%);
		align-items: center;
		flex-direction: column-reverse;
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.toast-container {
			left: var(--space-4) !important;
			right: var(--space-4) !important;
			transform: none !important;
			align-items: stretch !important;
		}
	}
</style>