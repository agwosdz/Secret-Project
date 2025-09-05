import type { ValidationResult } from './upload';

export interface ValidationRule {
	type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'email' | 'number' | 'range' | 'fileSize' | 'fileType' | 'custom';
	value?: any;
	message?: string;
	validator?: (value: any) => boolean;
}

export interface ValidationOptions {
	rules: ValidationRule[];
	field?: string;
	showSuggestions?: boolean;
}

// Common validation patterns
export const VALIDATION_PATTERNS = {
	email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
	phone: /^[\+]?[1-9][\d]{0,15}$/,
	url: /^https?:\/\/.+/,
	alphanumeric: /^[a-zA-Z0-9]+$/,
	alphabetic: /^[a-zA-Z]+$/,
	numeric: /^[0-9]+$/,
	noSpecialChars: /^[a-zA-Z0-9\s]+$/,
	filename: /^[a-zA-Z0-9._-]+$/
};

// Common validation messages
export const VALIDATION_MESSAGES = {
	required: 'This field is required',
	email: 'Please enter a valid email address',
	minLength: (min: number) => `Must be at least ${min} characters long`,
	maxLength: (max: number) => `Must be no more than ${max} characters long`,
	pattern: 'Please enter a valid format',
	number: 'Please enter a valid number',
	range: (min: number, max: number) => `Must be between ${min} and ${max}`,
	fileSize: (max: string) => `File size must be less than ${max}`,
	fileType: (types: string[]) => `File must be one of: ${types.join(', ')}`
};

/**
 * Validates a single value against a set of rules
 */
export function validateValue(value: any, options: ValidationOptions): ValidationResult {
	const { rules, field = 'Field', showSuggestions = true } = options;
	
	for (const rule of rules) {
		const result = validateRule(value, rule, field, showSuggestions);
		if (!result.valid) {
			return result;
		}
	}
	
	return { valid: true, message: '' };
}

/**
 * Validates a single rule against a value
 */
function validateRule(value: any, rule: ValidationRule, field: string, showSuggestions: boolean): ValidationResult {
	const { type, value: ruleValue, message, validator } = rule;
	
	switch (type) {
		case 'required':
			if (!value || (typeof value === 'string' && value.trim() === '')) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.required,
					suggestion: showSuggestions ? `${field} cannot be empty` : undefined
				};
			}
			break;
			
		case 'minLength':
			if (typeof value === 'string' && value.length < ruleValue) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.minLength(ruleValue),
					suggestion: showSuggestions ? `Current length: ${value.length}, required: ${ruleValue}` : undefined,
					details: {
						actualLength: value.length,
						requiredLength: ruleValue
					}
				};
			}
			break;
			
		case 'maxLength':
			if (typeof value === 'string' && value.length > ruleValue) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.maxLength(ruleValue),
					suggestion: showSuggestions ? `Current length: ${value.length}, maximum: ${ruleValue}` : undefined,
					details: {
						actualLength: value.length,
						maxLength: ruleValue
					}
				};
			}
			break;
			
		case 'pattern':
			if (typeof value === 'string' && !ruleValue.test(value)) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.pattern,
					suggestion: showSuggestions ? getPatternSuggestion(ruleValue) : undefined
				};
			}
			break;
			
		case 'email':
			if (typeof value === 'string' && !VALIDATION_PATTERNS.email.test(value)) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.email,
					suggestion: showSuggestions ? 'Example: user@example.com' : undefined
				};
			}
			break;
			
		case 'number':
			if (isNaN(Number(value))) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.number,
					suggestion: showSuggestions ? 'Enter numbers only (0-9)' : undefined
				};
			}
			break;
			
		case 'range':
			const numValue = Number(value);
			const [min, max] = ruleValue;
			if (numValue < min || numValue > max) {
				return {
					valid: false,
					message: message || VALIDATION_MESSAGES.range(min, max),
					suggestion: showSuggestions ? `Current value: ${numValue}` : undefined,
					details: {
						actualValue: numValue,
						minValue: min,
						maxValue: max
					}
				};
			}
			break;
			
		case 'fileSize':
			if (value instanceof File) {
				const maxBytes = parseFileSize(ruleValue);
				if (value.size > maxBytes) {
					return {
						valid: false,
						message: message || VALIDATION_MESSAGES.fileSize(ruleValue),
						suggestion: showSuggestions ? `Current size: ${formatFileSize(value.size)}` : undefined,
						details: {
							actualSize: formatFileSize(value.size),
							maxSize: ruleValue
						}
					};
				}
			}
			break;
			
		case 'fileType':
			if (value instanceof File) {
				const allowedTypes = Array.isArray(ruleValue) ? ruleValue : [ruleValue];
				const fileExt = value.name.split('.').pop()?.toLowerCase();
				if (!fileExt || !allowedTypes.includes(fileExt)) {
					return {
						valid: false,
						message: message || VALIDATION_MESSAGES.fileType(allowedTypes),
						suggestion: showSuggestions ? `Current type: .${fileExt || 'unknown'}` : undefined,
						details: {
							actualExtension: fileExt || 'unknown',
							allowedExtensions: allowedTypes
						}
					};
				}
			}
			break;
			
		case 'custom':
			if (validator && !validator(value)) {
				return {
					valid: false,
					message: message || 'Invalid value',
					suggestion: showSuggestions ? 'Please check your input' : undefined
				};
			}
			break;
	}
	
	return { valid: true, message: '' };
}

/**
 * Get suggestion text for common patterns
 */
function getPatternSuggestion(pattern: RegExp): string {
	const patternStr = pattern.toString();
	
	if (patternStr.includes('email')) return 'Example: user@example.com';
	if (patternStr.includes('phone')) return 'Example: +1234567890';
	if (patternStr.includes('url')) return 'Example: https://example.com';
	if (patternStr.includes('[a-zA-Z0-9]')) return 'Use only letters and numbers';
	if (patternStr.includes('[a-zA-Z]')) return 'Use only letters';
	if (patternStr.includes('[0-9]')) return 'Use only numbers';
	
	return 'Please check the format';
}

/**
 * Parse file size string to bytes
 */
function parseFileSize(sizeStr: string): number {
	const units = { B: 1, KB: 1024, MB: 1024 * 1024, GB: 1024 * 1024 * 1024 };
	const match = sizeStr.match(/^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)$/i);
	
	if (!match) return 0;
	
	const [, size, unit] = match;
	return parseFloat(size) * (units[unit.toUpperCase() as keyof typeof units] || 1);
}

/**
 * Format file size in bytes to human readable string
 */
function formatFileSize(bytes: number): string {
	if (bytes === 0) return '0 B';
	
	const units = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	
	return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

/**
 * Validate form data with multiple fields
 */
export function validateForm(data: Record<string, any>, schema: Record<string, ValidationOptions>): Record<string, ValidationResult> {
	const results: Record<string, ValidationResult> = {};
	
	for (const [field, options] of Object.entries(schema)) {
		const value = data[field];
		results[field] = validateValue(value, { ...options, field });
	}
	
	return results;
}

/**
 * Check if form validation results have any errors
 */
export function hasValidationErrors(results: Record<string, ValidationResult>): boolean {
	return Object.values(results).some(result => !result.valid);
}

/**
 * Get first validation error from results
 */
export function getFirstValidationError(results: Record<string, ValidationResult>): ValidationResult | null {
	return Object.values(results).find(result => !result.valid) || null;
}

/**
 * Common validation rule presets
 */
export const VALIDATION_PRESETS = {
	requiredText: (minLength = 1): ValidationRule[] => [
		{ type: 'required' },
		{ type: 'minLength', value: minLength }
	],
	
	email: (): ValidationRule[] => [
		{ type: 'required' },
		{ type: 'email' }
	],
	
	password: (minLength = 8): ValidationRule[] => [
		{ type: 'required' },
		{ type: 'minLength', value: minLength }
	],
	
	number: (min?: number, max?: number): ValidationRule[] => {
		const rules: ValidationRule[] = [
			{ type: 'required' },
			{ type: 'number' }
		];
		
		if (min !== undefined && max !== undefined) {
			rules.push({ type: 'range', value: [min, max] });
		}
		
		return rules;
	},
	
	file: (maxSize: string, allowedTypes: string[]): ValidationRule[] => [
		{ type: 'required' },
		{ type: 'fileSize', value: maxSize },
		{ type: 'fileType', value: allowedTypes }
	],
	
	filename: (): ValidationRule[] => [
		{ type: 'required' },
		{ type: 'pattern', value: VALIDATION_PATTERNS.filename, message: 'Filename can only contain letters, numbers, dots, hyphens, and underscores' }
	]
};