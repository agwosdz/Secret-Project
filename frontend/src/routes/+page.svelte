<script lang="ts">
	import { onMount } from 'svelte';

	let backendStatus = 'Checking...';
	let backendMessage = '';

	onMount(async () => {
		try {
			const response = await fetch('/health');
			if (response.ok) {
				const data = await response.json();
				backendStatus = data.status;
				backendMessage = data.message;
			} else {
				backendStatus = 'Error';
				backendMessage = `HTTP ${response.status}: ${response.statusText}`;
			}
		} catch (error) {
			backendStatus = 'Offline';
			backendMessage = 'Cannot connect to backend server';
		}
	});
</script>

<main>
	<h1>🎹 Piano LED Visualizer</h1>
	<p>Welcome to the Piano LED Visualizer - Transform your MIDI files into stunning LED light shows!</p>
	
	<div class="status-card">
		<h2>System Status</h2>
		<div class="status-item">
			<span class="label">Frontend:</span>
			<span class="status healthy">Running</span>
		</div>
		<div class="status-item">
			<span class="label">Backend:</span>
			<span class="status {backendStatus === 'healthy' ? 'healthy' : 'error'}">
				{backendStatus === 'healthy' ? 'Healthy' : backendStatus}
			</span>
		</div>
		{#if backendMessage}
			<p class="status-message">{backendMessage}</p>
		{/if}
	</div>

	<div class="navigation-card">
		<h2>Navigation</h2>
		<p>Access all available features of the Piano LED Visualizer:</p>
		<div class="nav-buttons">
			<a href="/dashboard" class="nav-button primary">
				<span class="nav-icon">📊</span>
				<div class="nav-content">
					<h3>Dashboard</h3>
					<p>Monitor system status and control LED visualizations</p>
				</div>
			</a>
			<a href="/upload" class="nav-button">
				<span class="nav-icon">📁</span>
				<div class="nav-content">
					<h3>Upload</h3>
					<p>Upload MIDI files for LED visualization</p>
				</div>
			</a>
			<a href="/play" class="nav-button">
				<span class="nav-icon">▶️</span>
				<div class="nav-content">
					<h3>Play</h3>
					<p>Play and control MIDI file playback</p>
				</div>
			</a>
			<a href="/settings" class="nav-button">
				<span class="nav-icon">⚙️</span>
				<div class="nav-content">
					<h3>Settings</h3>
					<p>Configure system preferences and LED settings</p>
				</div>
			</a>
		</div>
	</div>

	<div class="info-card">
		<h2>Getting Started</h2>
		<p>This is the foundation setup for the Piano LED Visualizer. The system is ready for development!</p>
		<ul>
			<li>✅ Monorepo structure initialized</li>
			<li>✅ Flask backend running on port 5001</li>
			<li>✅ SvelteKit frontend running on port 5173</li>
			<li>✅ Health check endpoint working</li>
		</ul>
	</div>
</main>

<style>
	main {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	h1 {
		color: #333;
		text-align: center;
		margin-bottom: 1rem;
		font-size: 2.5rem;
	}

	.status-card, .info-card, .navigation-card {
		background: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 8px;
		padding: 1.5rem;
		margin: 1.5rem 0;
	}

	.status-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin: 0.5rem 0;
	}

	.label {
		font-weight: 600;
		color: #495057;
	}

	.status {
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-weight: 600;
		text-transform: uppercase;
		font-size: 0.875rem;
	}

	.status.healthy {
		background-color: #d4edda;
		color: #155724;
	}

	.status.error {
		background-color: #f8d7da;
		color: #721c24;
	}

	.status-message {
		margin-top: 1rem;
		padding: 0.75rem;
		background: #e2e3e5;
		border-radius: 4px;
		font-size: 0.875rem;
		color: #495057;
	}

	ul {
		list-style-type: none;
		padding: 0;
	}

	li {
		padding: 0.5rem 0;
		font-size: 1.1rem;
	}

	.nav-buttons {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.nav-button {
		display: flex;
		align-items: center;
		padding: 1.25rem;
		background: white;
		border: 2px solid #e9ecef;
		border-radius: 8px;
		text-decoration: none;
		color: inherit;
		transition: all 0.2s ease;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.nav-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		border-color: #007bff;
	}

	.nav-button.primary {
		border-color: #007bff;
		background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
		color: white;
	}

	.nav-button.primary:hover {
		background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
	}

	.nav-icon {
		font-size: 2rem;
		margin-right: 1rem;
		flex-shrink: 0;
	}

	.nav-content h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.25rem;
		font-weight: 600;
	}

	.nav-content p {
		margin: 0;
		font-size: 0.9rem;
		opacity: 0.8;
		line-height: 1.4;
	}

	.nav-button.primary .nav-content p {
		opacity: 0.9;
	}

	@media (max-width: 640px) {
		.nav-buttons {
			grid-template-columns: 1fr;
		}
		
		.nav-button {
			padding: 1rem;
		}
		
		.nav-icon {
			font-size: 1.5rem;
			margin-right: 0.75rem;
		}
	}
</style>
