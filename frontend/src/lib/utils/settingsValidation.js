/**
 * Settings Validation Utilities
 * Provides real-time validation feedback for settings forms
 */

import { validateSetting, validateCategory, validateAllSettings } from '../schemas/settingsSchema.js';
import { writable, derived } from 'svelte/store';

// Validation state store
export const validationState = writable({});

// Validation results store
export const validationResults = writable({});

// Loading states for individual fields
export const fieldValidationLoading = writable({});

/**
 * Create a validation store for a specific settings category
 */
export function createCategoryValidation(category) {
    const categoryValidation = writable({
        isValid: true,
        errors: {},
        warnings: {},
        loading: false
    });

    return {
        subscribe: categoryValidation.subscribe,
        
        /**
         * Validate a single field in real-time
         */
        validateField: async (key, value, showLoading = true) => {
            if (showLoading) {
                fieldValidationLoading.update(state => ({
                    ...state,
                    [`${category}.${key}`]: true
                }));
            }

            // Simulate async validation delay for better UX
            await new Promise(resolve => setTimeout(resolve, 300));

            const result = validateSetting(category, key, value);
            
            categoryValidation.update(state => {
                const newErrors = { ...state.errors };
                const newWarnings = { ...state.warnings };
                
                if (result.valid) {
                    delete newErrors[key];
                    // Check for warnings (optional validation)
                    const warning = getFieldWarning(category, key, value);
                    if (warning) {
                        newWarnings[key] = warning;
                    } else {
                        delete newWarnings[key];
                    }
                } else {
                    newErrors[key] = result.error;
                    delete newWarnings[key];
                }

                const isValid = Object.keys(newErrors).length === 0;
                
                return {
                    ...state,
                    isValid,
                    errors: newErrors,
                    warnings: newWarnings
                };
            });

            if (showLoading) {
                fieldValidationLoading.update(state => ({
                    ...state,
                    [`${category}.${key}`]: false
                }));
            }

            return result;
        },

        /**
         * Validate entire category
         */
        validateCategory: async (data) => {
            categoryValidation.update(state => ({ ...state, loading: true }));

            const result = validateCategory(category, data);
            
            categoryValidation.update(state => ({
                ...state,
                loading: false,
                isValid: result.valid,
                errors: result.valid ? {} : { _category: result.error },
                warnings: {}
            }));

            return result;
        },

        /**
         * Clear validation state
         */
        clear: () => {
            categoryValidation.set({
                isValid: true,
                errors: {},
                warnings: {},
                loading: false
            });
        }
    };
}

/**
 * Get validation state for a specific field
 */
export function getFieldValidationState(category, key, errors, warnings, loading) {
    const fieldKey = `${category}.${key}`;
    const hasError = errors && errors[key];
    const hasWarning = warnings && warnings[key];
    const isLoading = loading && loading[fieldKey];

    if (isLoading) return 'validating';
    if (hasError) return 'invalid';
    if (hasWarning) return 'warning';
    if (!hasError && !hasWarning && (errors || warnings)) return 'valid';
    return 'none';
}

/**
 * Get user-friendly error message
 */
export function getFieldErrorMessage(category, key, error) {
    if (!error) return '';

    // Convert technical validation errors to user-friendly messages
    const friendlyMessages = {
        'must be a boolean': 'Please select a valid option',
        'must be a number': 'Please enter a valid number',
        'must be a string': 'Please enter valid text',
        'is required': 'This field is required',
        'must be >= ': 'Value is too low. Minimum: ',
        'must be <= ': 'Value is too high. Maximum: ',
        'must be one of:': 'Please select from the available options: '
    };

    let friendlyError = error;
    for (const [technical, friendly] of Object.entries(friendlyMessages)) {
        if (error.includes(technical)) {
            friendlyError = error.replace(technical, friendly);
            break;
        }
    }

    return friendlyError;
}

/**
 * Get field warnings for optional validation
 */
function getFieldWarning(category, key, value) {
    // Define warnings for specific fields
    const warnings = {
        led: {
            count: (val) => {
                if (val > 500) return 'High LED count may impact performance';
                if (val < 10) return 'Very low LED count may not be visible';
                return null;
            },
            brightness: (val) => {
                if (val > 80) return 'High brightness may cause overheating';
                return null;
            }
        },
        gpio: {
            pins: (val) => {
                if (Array.isArray(val) && val.length > 20) {
                    return 'Many GPIO pins configured - ensure no conflicts';
                }
                return null;
            }
        },
        audio: {
            buffer_size: (val) => {
                if (val < 128) return 'Low buffer size may cause audio dropouts';
                if (val > 512) return 'High buffer size increases latency';
                return null;
            }
        }
    };

    const categoryWarnings = warnings[category];
    if (categoryWarnings && categoryWarnings[key]) {
        return categoryWarnings[key](value);
    }

    return null;
}

/**
 * Debounced validation function
 */
export function createDebouncedValidator(validationFn, delay = 500) {
    let timeoutId;
    
    return (...args) => {
        clearTimeout(timeoutId);
        return new Promise((resolve) => {
            timeoutId = setTimeout(async () => {
                const result = await validationFn(...args);
                resolve(result);
            }, delay);
        });
    };
}

/**
 * Batch validation for multiple fields
 */
export async function validateFields(category, fields) {
    const results = {};
    const promises = Object.entries(fields).map(async ([key, value]) => {
        const result = validateSetting(category, key, value);
        results[key] = result;
        return result;
    });

    await Promise.all(promises);
    return results;
}

/**
 * Get validation summary for UI display
 */
export function getValidationSummary(validationResults) {
    const errors = [];
    const warnings = [];
    let totalFields = 0;
    let validFields = 0;

    for (const [category, categoryResults] of Object.entries(validationResults)) {
        if (categoryResults.errors) {
            for (const [field, error] of Object.entries(categoryResults.errors)) {
                errors.push(`${category}.${field}: ${error}`);
            }
        }
        
        if (categoryResults.warnings) {
            for (const [field, warning] of Object.entries(categoryResults.warnings)) {
                warnings.push(`${category}.${field}: ${warning}`);
            }
        }

        // Count fields for progress indication
        if (categoryResults.fieldCount) {
            totalFields += categoryResults.fieldCount;
            validFields += categoryResults.validFieldCount || 0;
        }
    }

    return {
        isValid: errors.length === 0,
        errorCount: errors.length,
        warningCount: warnings.length,
        errors,
        warnings,
        progress: totalFields > 0 ? (validFields / totalFields) * 100 : 100
    };
}

/**
 * Export validation utilities for components
 */
export const validationUtils = {
    createCategoryValidation,
    getFieldValidationState,
    getFieldErrorMessage,
    createDebouncedValidator,
    validateFields,
    getValidationSummary
};