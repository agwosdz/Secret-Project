/**
 * Error Analytics and Tracking System
 * Collects and analyzes error patterns to identify common user pain points
 */

export interface ErrorEvent {
    id: string;
    timestamp: number;
    type: 'error' | 'recovery' | 'prevention';
    category: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    errorCode?: string;
    message: string;
    technicalMessage?: string;
    userAction?: string;
    context: {
        page: string;
        userAgent: string;
        fileType?: string;
        fileSize?: number;
        uploadAttempt?: number;
        sessionId: string;
        userId?: string;
    };
    resolution?: {
        method: 'auto' | 'user' | 'retry' | 'abandon';
        timeToResolve?: number;
        successful: boolean;
        retryCount?: number;
    };
    metadata?: Record<string, any>;
}

export interface ErrorPattern {
    category: string;
    frequency: number;
    avgTimeToResolve: number;
    successRate: number;
    commonCauses: string[];
    suggestedImprovements: string[];
}

export interface AnalyticsReport {
    timeRange: {
        start: number;
        end: number;
    };
    totalErrors: number;
    errorsByCategory: Record<string, number>;
    errorsBySeverity: Record<string, number>;
    topErrorPatterns: ErrorPattern[];
    userJourneyInsights: {
        dropOffPoints: string[];
        recoveryPaths: string[];
        preventionEffectiveness: number;
    };
    recommendations: string[];
}

class ErrorAnalytics {
    private events: ErrorEvent[] = [];
    private sessionId: string;
    private maxEvents = 1000; // Limit stored events to prevent memory issues
    private storageKey = 'piano-led-error-analytics';

    constructor() {
        this.sessionId = this.generateSessionId();
        this.loadStoredEvents();
    }

    /**
     * Track an error event
     */
    trackError(error: {
        category: string;
        severity: 'low' | 'medium' | 'high' | 'critical';
        errorCode?: string;
        message: string;
        technicalMessage?: string;
        userAction?: string;
        context?: Partial<ErrorEvent['context']>;
        metadata?: Record<string, any>;
    }): string {
        const eventId = this.generateEventId();
        
        const errorEvent: ErrorEvent = {
            id: eventId,
            timestamp: Date.now(),
            type: 'error',
            category: error.category,
            severity: error.severity,
            errorCode: error.errorCode,
            message: error.message,
            technicalMessage: error.technicalMessage,
            userAction: error.userAction,
            context: {
                page: window.location.pathname,
                userAgent: navigator.userAgent,
                sessionId: this.sessionId,
                ...error.context
            },
            metadata: error.metadata
        };

        this.addEvent(errorEvent);
        return eventId;
    }

    /**
     * Track error recovery
     */
    trackRecovery(errorId: string, recovery: {
        method: 'auto' | 'user' | 'retry' | 'abandon';
        successful: boolean;
        retryCount?: number;
    }): void {
        const errorEvent = this.events.find(e => e.id === errorId);
        if (errorEvent) {
            errorEvent.resolution = {
                ...recovery,
                timeToResolve: Date.now() - errorEvent.timestamp
            };
            this.persistEvents();
        }

        // Track as separate recovery event
        const recoveryEvent: ErrorEvent = {
            id: this.generateEventId(),
            timestamp: Date.now(),
            type: 'recovery',
            category: errorEvent?.category || 'unknown',
            severity: 'low',
            message: `Recovery attempt: ${recovery.method}`,
            context: {
                page: window.location.pathname,
                userAgent: navigator.userAgent,
                sessionId: this.sessionId
            },
            resolution: recovery,
            metadata: { originalErrorId: errorId }
        };

        this.addEvent(recoveryEvent);
    }

    /**
     * Track error prevention (validation preview, etc.)
     */
    trackPrevention(prevention: {
        category: string;
        message: string;
        preventedIssues: string[];
        userAction: 'fixed' | 'ignored' | 'cancelled';
        context?: Partial<ErrorEvent['context']>;
    }): void {
        const preventionEvent: ErrorEvent = {
            id: this.generateEventId(),
            timestamp: Date.now(),
            type: 'prevention',
            category: prevention.category,
            severity: 'low',
            message: prevention.message,
            userAction: prevention.userAction,
            context: {
                page: window.location.pathname,
                userAgent: navigator.userAgent,
                sessionId: this.sessionId,
                ...prevention.context
            },
            metadata: {
                preventedIssues: prevention.preventedIssues,
                preventionEffective: prevention.userAction === 'fixed'
            }
        };

        this.addEvent(preventionEvent);
    }

    /**
     * Generate analytics report
     */
    generateReport(timeRange?: { start: number; end: number }): AnalyticsReport {
        const now = Date.now();
        const defaultTimeRange = {
            start: now - (7 * 24 * 60 * 60 * 1000), // Last 7 days
            end: now
        };

        const range = timeRange || defaultTimeRange;
        const filteredEvents = this.events.filter(
            e => e.timestamp >= range.start && e.timestamp <= range.end
        );

        const errorEvents = filteredEvents.filter(e => e.type === 'error');
        const recoveryEvents = filteredEvents.filter(e => e.type === 'recovery');
        const preventionEvents = filteredEvents.filter(e => e.type === 'prevention');

        // Analyze error patterns
        const errorsByCategory = this.groupBy(errorEvents, 'category');
        const errorsBySeverity = this.groupBy(errorEvents, 'severity');
        const topErrorPatterns = this.analyzeErrorPatterns(errorEvents, recoveryEvents);

        // Analyze user journey
        const userJourneyInsights = this.analyzeUserJourney(filteredEvents);

        // Generate recommendations
        const recommendations = this.generateRecommendations(
            topErrorPatterns,
            userJourneyInsights,
            preventionEvents
        );

        return {
            timeRange: range,
            totalErrors: errorEvents.length,
            errorsByCategory,
            errorsBySeverity,
            topErrorPatterns,
            userJourneyInsights,
            recommendations
        };
    }

    /**
     * Get error trends over time
     */
    getErrorTrends(days: number = 7): Array<{ date: string; count: number; category: string }> {
        const now = Date.now();
        const startTime = now - (days * 24 * 60 * 60 * 1000);
        
        const errorEvents = this.events.filter(
            e => e.type === 'error' && e.timestamp >= startTime
        );

        const trends: Array<{ date: string; count: number; category: string }> = [];
        const dailyData: Record<string, Record<string, number>> = {};

        errorEvents.forEach(event => {
            const date = new Date(event.timestamp).toISOString().split('T')[0];
            if (!dailyData[date]) {
                dailyData[date] = {};
            }
            if (!dailyData[date][event.category]) {
                dailyData[date][event.category] = 0;
            }
            dailyData[date][event.category]++;
        });

        Object.entries(dailyData).forEach(([date, categories]) => {
            Object.entries(categories).forEach(([category, count]) => {
                trends.push({ date, category, count });
            });
        });

        return trends.sort((a, b) => a.date.localeCompare(b.date));
    }

    /**
     * Clear old events to prevent memory issues
     */
    cleanup(): void {
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
        this.events = this.events.filter(e => e.timestamp > thirtyDaysAgo);
        
        if (this.events.length > this.maxEvents) {
            this.events = this.events.slice(-this.maxEvents);
        }
        
        this.persistEvents();
    }

    private addEvent(event: ErrorEvent): void {
        this.events.push(event);
        
        // Cleanup if we have too many events
        if (this.events.length > this.maxEvents) {
            this.events = this.events.slice(-this.maxEvents);
        }
        
        this.persistEvents();
    }

    private analyzeErrorPatterns(errorEvents: ErrorEvent[], recoveryEvents: ErrorEvent[]): ErrorPattern[] {
        const patterns: Record<string, ErrorPattern> = {};

        errorEvents.forEach(error => {
            if (!patterns[error.category]) {
                patterns[error.category] = {
                    category: error.category,
                    frequency: 0,
                    avgTimeToResolve: 0,
                    successRate: 0,
                    commonCauses: [],
                    suggestedImprovements: []
                };
            }

            patterns[error.category].frequency++;

            // Calculate resolution metrics
            if (error.resolution) {
                patterns[error.category].avgTimeToResolve += error.resolution.timeToResolve || 0;
                if (error.resolution.successful) {
                    patterns[error.category].successRate++;
                }
            }
        });

        // Finalize calculations
        Object.values(patterns).forEach(pattern => {
            if (pattern.frequency > 0) {
                pattern.avgTimeToResolve = pattern.avgTimeToResolve / pattern.frequency;
                pattern.successRate = pattern.successRate / pattern.frequency;
            }
            
            // Add common causes and suggestions based on category
            this.addPatternInsights(pattern);
        });

        return Object.values(patterns).sort((a, b) => b.frequency - a.frequency);
    }

    private analyzeUserJourney(events: ErrorEvent[]): AnalyticsReport['userJourneyInsights'] {
        const dropOffPoints: string[] = [];
        const recoveryPaths: string[] = [];
        let preventionEffectiveness = 0;

        const abandonedErrors = events.filter(
            e => e.type === 'error' && e.resolution?.method === 'abandon'
        );
        
        const recoveredErrors = events.filter(
            e => e.type === 'error' && e.resolution?.successful
        );

        const preventionEvents = events.filter(e => e.type === 'prevention');
        const effectivePreventions = preventionEvents.filter(
            e => e.metadata?.preventionEffective
        );

        // Identify drop-off points
        abandonedErrors.forEach(error => {
            dropOffPoints.push(`${error.category} on ${error.context.page}`);
        });

        // Identify successful recovery paths
        recoveredErrors.forEach(error => {
            if (error.resolution?.method) {
                recoveryPaths.push(`${error.category} → ${error.resolution.method}`);
            }
        });

        // Calculate prevention effectiveness
        if (preventionEvents.length > 0) {
            preventionEffectiveness = effectivePreventions.length / preventionEvents.length;
        }

        return {
            dropOffPoints: [...new Set(dropOffPoints)],
            recoveryPaths: [...new Set(recoveryPaths)],
            preventionEffectiveness
        };
    }

    private generateRecommendations(
        patterns: ErrorPattern[],
        journey: AnalyticsReport['userJourneyInsights'],
        preventionEvents: ErrorEvent[]
    ): string[] {
        const recommendations: string[] = [];

        // Recommendations based on error patterns
        patterns.slice(0, 3).forEach(pattern => {
            if (pattern.successRate < 0.7) {
                recommendations.push(
                    `Improve error recovery for ${pattern.category} (current success rate: ${Math.round(pattern.successRate * 100)}%)`
                );
            }
            
            if (pattern.avgTimeToResolve > 30000) { // 30 seconds
                recommendations.push(
                    `Streamline resolution process for ${pattern.category} errors (avg resolution time: ${Math.round(pattern.avgTimeToResolve / 1000)}s)`
                );
            }
        });

        // Recommendations based on user journey
        if (journey.preventionEffectiveness < 0.8) {
            recommendations.push(
                `Enhance validation preview effectiveness (current: ${Math.round(journey.preventionEffectiveness * 100)}%)`
            );
        }

        if (journey.dropOffPoints.length > 0) {
            recommendations.push(
                `Address high drop-off points: ${journey.dropOffPoints.slice(0, 2).join(', ')}`
            );
        }

        return recommendations;
    }

    private addPatternInsights(pattern: ErrorPattern): void {
        switch (pattern.category) {
            case 'file_validation':
                pattern.commonCauses = ['Invalid file type', 'File too large', 'Corrupted file'];
                pattern.suggestedImprovements = ['Better file type detection', 'Clearer size limits', 'File repair suggestions'];
                break;
            case 'upload':
                pattern.commonCauses = ['Network timeout', 'Server error', 'File processing failure'];
                pattern.suggestedImprovements = ['Retry mechanism', 'Progress indication', 'Offline support'];
                break;
            case 'network':
                pattern.commonCauses = ['Connection lost', 'Slow network', 'Server unavailable'];
                pattern.suggestedImprovements = ['Offline mode', 'Better error messages', 'Automatic retry'];
                break;
            default:
                pattern.commonCauses = ['Unknown cause'];
                pattern.suggestedImprovements = ['Investigate further'];
        }
    }

    private groupBy<T>(array: T[], key: keyof T): Record<string, number> {
        return array.reduce((groups, item) => {
            const value = String(item[key]);
            groups[value] = (groups[value] || 0) + 1;
            return groups;
        }, {} as Record<string, number>);
    }

    private generateSessionId(): string {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private generateEventId(): string {
        return `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private loadStoredEvents(): void {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                this.events = JSON.parse(stored);
            }
        } catch (error) {
            console.warn('Failed to load stored analytics events:', error);
            this.events = [];
        }
    }

    private persistEvents(): void {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.events));
        } catch (error) {
            console.warn('Failed to persist analytics events:', error);
        }
    }
}

// Export singleton instance
export const errorAnalytics = new ErrorAnalytics();

// Auto-cleanup every hour
if (typeof window !== 'undefined') {
    setInterval(() => {
        errorAnalytics.cleanup();
    }, 60 * 60 * 1000);
}