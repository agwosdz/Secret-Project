<script lang="ts">
	import { onMount } from 'svelte';
	import { analyticsReporter } from '../analytics/analyticsReporter.js';
	import type { AnalyticsReport } from '../analytics/errorAnalytics.js';

	let report: AnalyticsReport | null = null;
	let loading = true;
	let selectedTab = 'overview';

	onMount(() => {
		loadReport();
	});

	function loadReport() {
		loading = true;
		try {
			report = analyticsReporter.generateReport();
		} catch (error) {
			console.error('Failed to load analytics report:', error);
		} finally {
			loading = false;
		}
	}

	function downloadReport(format: 'json' | 'csv') {
		analyticsReporter.downloadReport(format);
	}

	function clearData() {
		if (confirm('Are you sure you want to clear all analytics data? This action cannot be undone.')) {
			analyticsReporter.clearData();
			loadReport();
		}
	}

	function formatDuration(ms: number): string {
		if (ms < 1000) return `${ms}ms`;
		if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
		return `${(ms / 60000).toFixed(1)}m`;
	}

	function getErrorSeverityColor(severity: string): string {
		switch (severity) {
			case 'critical': return '#dc2626';
			case 'high': return '#ea580c';
			case 'medium': return '#d97706';
			case 'low': return '#65a30d';
			default: return '#6b7280';
		}
	}
</script>

<div class="analytics-dashboard">
	<header class="dashboard-header">
		<h2>Error Analytics Dashboard</h2>
		<div class="header-actions">
			<button on:click={loadReport} class="refresh-btn">
				🔄 Refresh
			</button>
			<button on:click={() => downloadReport('json')} class="download-btn">
				📥 JSON
			</button>
			<button on:click={() => downloadReport('csv')} class="download-btn">
				📊 CSV
			</button>
			<button on:click={clearData} class="clear-btn">
				🗑️ Clear Data
			</button>
		</div>
	</header>

	<nav class="dashboard-tabs">
		<button 
			class="tab" 
			class:active={selectedTab === 'overview'}
			on:click={() => selectedTab = 'overview'}
		>
			Overview
		</button>
		<button 
			class="tab" 
			class:active={selectedTab === 'patterns'}
			on:click={() => selectedTab = 'patterns'}
		>
			Error Patterns
		</button>
		<button 
			class="tab" 
			class:active={selectedTab === 'recovery'}
			on:click={() => selectedTab = 'recovery'}
		>
			Recovery Stats
		</button>
		<button 
			class="tab" 
			class:active={selectedTab === 'prevention'}
			on:click={() => selectedTab = 'prevention'}
		>
			Prevention
		</button>
	</nav>

	{#if loading}
		<div class="loading">Loading analytics data...</div>
	{:else if !report}
		<div class="error">Failed to load analytics data</div>
	{:else}
		{#if selectedTab === 'overview'}
			<div class="overview-section">
				<div class="stats-grid">
					<div class="stat-card">
						<h3>Total Errors</h3>
						<div class="stat-value">{report.errorEvents.length}</div>
					</div>
					<div class="stat-card">
						<h3>Recovery Attempts</h3>
						<div class="stat-value">{report.recoveryEvents.length}</div>
					</div>
					<div class="stat-card">
						<h3>Prevention Actions</h3>
						<div class="stat-value">{report.preventionEvents.length}</div>
					</div>
					<div class="stat-card">
						<h3>Error Patterns</h3>
						<div class="stat-value">{report.patterns.length}</div>
					</div>
				</div>

				<div class="recent-errors">
					<h3>Recent Errors</h3>
					<div class="error-list">
						{#each report.errorEvents.slice(-10).reverse() as error}
							<div class="error-item">
								<div class="error-header">
									<span class="error-type" style="color: {getErrorSeverityColor(error.severity)}">
										{error.type}
									</span>
									<span class="error-severity severity-{error.severity}">
										{error.severity}
									</span>
									<span class="error-time">
										{error.timestamp.toLocaleString()}
									</span>
								</div>
								<div class="error-message">{error.message}</div>
								{#if error.code}
									<div class="error-code">Code: {error.code}</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
		{:else if selectedTab === 'patterns'}
			<div class="patterns-section">
				<h3>Error Patterns</h3>
				<div class="patterns-list">
					{#each report.patterns as pattern}
						<div class="pattern-card">
							<div class="pattern-header">
								<h4>{pattern.type}</h4>
								<span class="pattern-count">{pattern.count} occurrences</span>
							</div>
							<div class="pattern-timeline">
								<span>First: {pattern.firstSeen.toLocaleString()}</span>
								<span>Last: {pattern.lastSeen.toLocaleString()}</span>
							</div>
							<div class="common-messages">
								<h5>Common Messages:</h5>
								<ul>
									{#each pattern.commonMessages as message}
										<li>{message}</li>
									{/each}
								</ul>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if selectedTab === 'recovery'}
			<div class="recovery-section">
				<h3>Recovery Statistics</h3>
				<div class="recovery-stats">
					{#each report.recoveryEvents as recovery}
						<div class="recovery-item">
							<div class="recovery-header">
								<span class="recovery-method">{recovery.method}</span>
								<span class="recovery-status" class:success={recovery.success} class:failure={!recovery.success}>
									{recovery.success ? '✅ Success' : '❌ Failed'}
								</span>
								<span class="recovery-time">{recovery.timestamp.toLocaleString()}</span>
							</div>
							<div class="recovery-details">
								Error ID: {recovery.errorId} | Attempt: {recovery.attemptNumber}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if selectedTab === 'prevention'}
			<div class="prevention-section">
				<h3>Prevention Actions</h3>
				<div class="prevention-list">
					{#each report.preventionEvents as prevention}
						<div class="prevention-item">
							<div class="prevention-header">
								<span class="prevention-type">{prevention.type}</span>
								<span class="prevention-action">{prevention.action}</span>
								<span class="prevention-time">{prevention.timestamp.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.analytics-dashboard {
		max-width: 1200px;
		margin: 0 auto;
		padding: 20px;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
		padding-bottom: 15px;
		border-bottom: 2px solid #e5e7eb;
	}

	.dashboard-header h2 {
		margin: 0;
		color: #1f2937;
	}

	.header-actions {
		display: flex;
		gap: 10px;
	}

	.refresh-btn, .download-btn, .clear-btn {
		padding: 8px 16px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		background: white;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.2s;
	}

	.refresh-btn:hover, .download-btn:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}

	.clear-btn {
		background: #fef2f2;
		border-color: #fca5a5;
		color: #dc2626;
	}

	.clear-btn:hover {
		background: #fee2e2;
	}

	.dashboard-tabs {
		display: flex;
		gap: 2px;
		margin-bottom: 20px;
		border-bottom: 1px solid #e5e7eb;
	}

	.tab {
		padding: 12px 20px;
		border: none;
		background: transparent;
		cursor: pointer;
		border-bottom: 3px solid transparent;
		font-weight: 500;
		color: #6b7280;
		transition: all 0.2s;
	}

	.tab:hover {
		color: #374151;
		background: #f9fafb;
	}

	.tab.active {
		color: #3b82f6;
		border-bottom-color: #3b82f6;
	}

	.loading, .error {
		text-align: center;
		padding: 40px;
		color: #6b7280;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 20px;
		margin-bottom: 30px;
	}

	.stat-card {
		background: white;
		padding: 20px;
		border-radius: 8px;
		border: 1px solid #e5e7eb;
		text-align: center;
	}

	.stat-card h3 {
		margin: 0 0 10px 0;
		color: #6b7280;
		font-size: 14px;
		font-weight: 500;
	}

	.stat-value {
		font-size: 32px;
		font-weight: bold;
		color: #1f2937;
	}

	.recent-errors, .patterns-section, .recovery-section, .prevention-section {
		background: white;
		border-radius: 8px;
		border: 1px solid #e5e7eb;
		padding: 20px;
	}

	.recent-errors h3, .patterns-section h3, .recovery-section h3, .prevention-section h3 {
		margin: 0 0 15px 0;
		color: #1f2937;
	}

	.error-item, .recovery-item, .prevention-item {
		padding: 12px;
		border-bottom: 1px solid #f3f4f6;
		margin-bottom: 8px;
	}

	.error-item:last-child, .recovery-item:last-child, .prevention-item:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	.error-header, .recovery-header, .prevention-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 5px;
	}

	.error-type {
		font-weight: 600;
		text-transform: capitalize;
	}

	.error-severity {
		padding: 2px 8px;
		border-radius: 12px;
		font-size: 12px;
		font-weight: 500;
		text-transform: uppercase;
	}

	.severity-critical {
		background: #fef2f2;
		color: #dc2626;
	}

	.severity-high {
		background: #fff7ed;
		color: #ea580c;
	}

	.severity-medium {
		background: #fffbeb;
		color: #d97706;
	}

	.severity-low {
		background: #f0fdf4;
		color: #65a30d;
	}

	.error-time, .recovery-time, .prevention-time {
		font-size: 12px;
		color: #6b7280;
	}

	.error-message {
		color: #374151;
		margin-bottom: 5px;
	}

	.error-code {
		font-size: 12px;
		color: #6b7280;
		font-family: monospace;
	}

	.pattern-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 15px;
		margin-bottom: 15px;
	}

	.pattern-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}

	.pattern-header h4 {
		margin: 0;
		color: #1f2937;
	}

	.pattern-count {
		background: #dbeafe;
		color: #1d4ed8;
		padding: 2px 8px;
		border-radius: 12px;
		font-size: 12px;
		font-weight: 500;
	}

	.pattern-timeline {
		display: flex;
		gap: 20px;
		margin-bottom: 10px;
		font-size: 12px;
		color: #6b7280;
	}

	.common-messages h5 {
		margin: 10px 0 5px 0;
		color: #374151;
		font-size: 14px;
	}

	.common-messages ul {
		margin: 0;
		padding-left: 20px;
	}

	.common-messages li {
		color: #6b7280;
		font-size: 13px;
		margin-bottom: 3px;
	}

	.recovery-status.success {
		color: #059669;
	}

	.recovery-status.failure {
		color: #dc2626;
	}

	.recovery-details {
		font-size: 12px;
		color: #6b7280;
		font-family: monospace;
	}

	.prevention-type {
		font-weight: 600;
		color: #059669;
	}

	.prevention-action {
		color: #374151;
	}
</style>