import { errorAnalytics } from './errorAnalytics.js';
import type { AnalyticsReport } from './errorAnalytics.js';

/**
 * Analytics Reporter
 * Provides methods to generate and export analytics reports
 */
export class AnalyticsReporter {
	/**
	 * Generate comprehensive analytics report
	 */
	generateReport(): AnalyticsReport {
		return errorAnalytics.generateReport();
	}

	/**
	 * Export analytics data as JSON
	 */
	exportAsJSON(): string {
		const report = this.generateReport();
		return JSON.stringify(report, null, 2);
	}

	/**
	 * Export analytics data as CSV
	 */
	exportAsCSV(): string {
		const report = this.generateReport();
		const lines: string[] = [];

		// Error events CSV
		lines.push('Error Events');
		lines.push('Type,Severity,Message,Code,Timestamp,Context');
		
		report.errorEvents.forEach(event => {
			const contextStr = JSON.stringify(event.context).replace(/"/g, '""');
			lines.push(`"${event.type}","${event.severity}","${event.message}","${event.code || ''}","${event.timestamp.toISOString()}","${contextStr}"`);
		});

		lines.push('');
		lines.push('Recovery Events');
		lines.push('Error ID,Method,Attempt Number,Success,Timestamp');
		
		report.recoveryEvents.forEach(event => {
			lines.push(`"${event.errorId}","${event.method}","${event.attemptNumber}","${event.success}","${event.timestamp.toISOString()}"`);
		});

		lines.push('');
		lines.push('Prevention Events');
		lines.push('Type,Action,Timestamp,Context');
		
		report.preventionEvents.forEach(event => {
			const contextStr = JSON.stringify(event.context).replace(/"/g, '""');
			lines.push(`"${event.type}","${event.action}","${event.timestamp.toISOString()}","${contextStr}"`);
		});

		return lines.join('\n');
	}

	/**
	 * Get error patterns summary
	 */
	getErrorPatternsSummary(): string {
		const report = this.generateReport();
		const lines: string[] = [];

		lines.push('Error Patterns Summary');
		lines.push('===================');
		lines.push('');

		report.patterns.forEach(pattern => {
			lines.push(`Pattern: ${pattern.type}`);
			lines.push(`Count: ${pattern.count}`);
			lines.push(`First Seen: ${pattern.firstSeen.toLocaleString()}`);
			lines.push(`Last Seen: ${pattern.lastSeen.toLocaleString()}`);
			lines.push(`Common Messages:`);
			pattern.commonMessages.forEach(msg => lines.push(`  - ${msg}`));
			lines.push('');
		});

		return lines.join('\n');
	}

	/**
	 * Clear all analytics data
	 */
	clearData(): void {
		errorAnalytics.clearData();
	}

	/**
	 * Download report as file
	 */
	downloadReport(format: 'json' | 'csv' = 'json'): void {
		const data = format === 'json' ? this.exportAsJSON() : this.exportAsCSV();
		const blob = new Blob([data], { type: format === 'json' ? 'application/json' : 'text/csv' });
		const url = URL.createObjectURL(blob);
		
		const a = document.createElement('a');
		a.href = url;
		a.download = `error-analytics-${new Date().toISOString().split('T')[0]}.${format}`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
}

export const analyticsReporter = new AnalyticsReporter();