import { render, fireEvent, waitFor, screen } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ConfigurationManager from '../ConfigurationManager.svelte';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.confirm
const mockConfirm = vi.fn();
global.confirm = mockConfirm;

// Mock window.location.reload
const mockReload = vi.fn();
Object.defineProperty(window, 'location', {
  value: {
    reload: mockReload
  },
  writable: true
});

describe('ConfigurationManager Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockConfirm.mockClear();
    mockReload.mockClear();
    
    // Mock successful config history fetch by default
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        history: [
          {
            timestamp: '2024-01-01T12:00:00Z',
            action: 'Configuration saved',
            description: 'Updated LED count to 88'
          }
        ]
      })
    });
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with all main elements', async () => {
    render(ConfigurationManager);
    
    expect(screen.getByText('Configuration Management')).toBeInTheDocument();
    expect(screen.getByText('Validate Configuration')).toBeInTheDocument();
    expect(screen.getByText('Create Backup')).toBeInTheDocument();
    expect(screen.getByText('Restore from Backup')).toBeInTheDocument();
    expect(screen.getByText('Reset to Defaults')).toBeInTheDocument();
    expect(screen.getByText('Export Configuration')).toBeInTheDocument();
  });

  it('loads configuration history on mount', async () => {
    render(ConfigurationManager);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/history');
    });
  });

  it('validates configuration successfully', async () => {
    // Mock successful config fetch
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: { led_count: 88, gpio_pins: { data_pin: 18 } }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          validation: {
            is_valid: true,
            errors: [],
            warnings: []
          }
        })
      });
    
    render(ConfigurationManager);
    
    const validateButton = screen.getByText('Validate Configuration');
    await fireEvent.click(validateButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config');
      expect(mockFetch).toHaveBeenCalledWith('/api/config/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ led_count: 88, gpio_pins: { data_pin: 18 } })
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Configuration is valid!')).toBeInTheDocument();
    });
  });

  it('displays validation errors correctly', async () => {
    // Mock config fetch and validation with errors
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: { led_count: 0 } // Invalid config
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          validation: {
            is_valid: false,
            errors: ['LED count must be greater than 0', 'GPIO pin is required'],
            warnings: ['Consider using a higher LED count']
          }
        })
      });
    
    render(ConfigurationManager);
    
    const validateButton = screen.getByText('Validate Configuration');
    await fireEvent.click(validateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Configuration has 2 error(s)')).toBeInTheDocument();
      expect(screen.getByText('Validation Results')).toBeInTheDocument();
      expect(screen.getByText('Status: Invalid')).toBeInTheDocument();
      expect(screen.getByText('LED count must be greater than 0')).toBeInTheDocument();
      expect(screen.getByText('GPIO pin is required')).toBeInTheDocument();
      expect(screen.getByText('Consider using a higher LED count')).toBeInTheDocument();
    });
  });

  it('creates backup successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuration backed up successfully'
      })
    });
    
    render(ConfigurationManager);
    
    const backupButton = screen.getByText('Create Backup');
    await fireEvent.click(backupButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/backup', {
        method: 'POST'
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Configuration backed up successfully')).toBeInTheDocument();
    });
  });

  it('restores configuration with confirmation', async () => {
    mockConfirm.mockReturnValue(true);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuration restored successfully'
      })
    });
    
    render(ConfigurationManager);
    
    const restoreButton = screen.getByText('Restore from Backup');
    await fireEvent.click(restoreButton);
    
    expect(mockConfirm).toHaveBeenCalledWith(
      'Are you sure you want to restore from backup? This will overwrite your current configuration.'
    );
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/restore', {
        method: 'POST'
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Configuration restored successfully')).toBeInTheDocument();
    });
  });

  it('cancels restore when user declines confirmation', async () => {
    mockConfirm.mockReturnValue(false);
    
    render(ConfigurationManager);
    
    const restoreButton = screen.getByText('Restore from Backup');
    await fireEvent.click(restoreButton);
    
    expect(mockConfirm).toHaveBeenCalled();
    expect(mockFetch).not.toHaveBeenCalledWith('/api/config/restore', expect.any(Object));
  });

  it('resets configuration with confirmation', async () => {
    mockConfirm.mockReturnValue(true);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuration reset to defaults'
      })
    });
    
    render(ConfigurationManager);
    
    const resetButton = screen.getByText('Reset to Defaults');
    await fireEvent.click(resetButton);
    
    expect(mockConfirm).toHaveBeenCalledWith(
      'Are you sure you want to reset to default configuration? This cannot be undone.'
    );
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/reset', {
        method: 'POST'
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Configuration reset to defaults')).toBeInTheDocument();
    });
  });

  it('exports configuration with custom path', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuration exported to custom_config.json',
        export_path: 'custom_config.json'
      })
    });
    
    render(ConfigurationManager);
    
    const exportInput = screen.getByPlaceholderText('Optional: custom export path');
    const exportButton = screen.getByText('Export');
    
    await fireEvent.input(exportInput, { target: { value: 'custom_config.json' } });
    await fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: 'custom_config.json' })
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Configuration exported to custom_config.json')).toBeInTheDocument();
    });
    
    // Input should be cleared after successful export
    expect(exportInput.value).toBe('');
  });

  it('exports configuration with default path when no path provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuration exported to config_export_20240101_120000.json',
        export_path: 'config_export_20240101_120000.json'
      })
    });
    
    render(ConfigurationManager);
    
    const exportButton = screen.getByText('Export');
    await fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/config/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: undefined })
      });
    });
  });

  it('toggles configuration history display', async () => {
    render(ConfigurationManager);
    
    const toggleButton = screen.getByText('Show History');
    
    // Initially history should be hidden
    expect(screen.queryByText('Configuration saved')).not.toBeInTheDocument();
    
    // Show history
    await fireEvent.click(toggleButton);
    
    await waitFor(() => {
      expect(screen.getByText('Configuration saved')).toBeInTheDocument();
      expect(screen.getByText('Hide History')).toBeInTheDocument();
    });
    
    // Hide history again
    const hideButton = screen.getByText('Hide History');
    await fireEvent.click(hideButton);
    
    expect(screen.queryByText('Configuration saved')).not.toBeInTheDocument();
    expect(screen.getByText('Show History')).toBeInTheDocument();
  });

  it('displays no history message when history is empty', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        history: []
      })
    });
    
    render(ConfigurationManager);
    
    const toggleButton = screen.getByText('Show History');
    await fireEvent.click(toggleButton);
    
    await waitFor(() => {
      expect(screen.getByText('No configuration history available.')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        success: false,
        message: 'Backup failed: Disk full'
      })
    });
    
    render(ConfigurationManager);
    
    const backupButton = screen.getByText('Create Backup');
    await fireEvent.click(backupButton);
    
    await waitFor(() => {
      expect(screen.getByText('Backup failed: Disk full')).toBeInTheDocument();
    });
  });

  it('handles network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(ConfigurationManager);
    
    const backupButton = screen.getByText('Create Backup');
    await fireEvent.click(backupButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Backup failed: Network error/)).toBeInTheDocument();
    });
  });

  it('disables buttons while loading', async () => {
    // Mock a slow response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ success: true, message: 'Success' })
        }), 100)
      )
    );
    
    render(ConfigurationManager);
    
    const backupButton = screen.getByText('Create Backup');
    await fireEvent.click(backupButton);
    
    // Button should be disabled and show loading text
    expect(screen.getByText('Backing up...')).toBeInTheDocument();
    expect(screen.getByText('Backing up...')).toBeDisabled();
    
    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Create Backup')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('closes validation results when close button is clicked', async () => {
    // Mock validation with results
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: { led_count: 88 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          validation: {
            is_valid: true,
            errors: [],
            warnings: []
          }
        })
      });
    
    render(ConfigurationManager);
    
    const validateButton = screen.getByText('Validate Configuration');
    await fireEvent.click(validateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Validation Results')).toBeInTheDocument();
    });
    
    const closeButton = screen.getByText('Close');
    await fireEvent.click(closeButton);
    
    expect(screen.queryByText('Validation Results')).not.toBeInTheDocument();
  });

  it('formats timestamps correctly', async () => {
    const mockHistory = [
      {
        timestamp: '2024-01-01T12:30:45Z',
        action: 'Test action',
        description: 'Test description'
      }
    ];
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        history: mockHistory
      })
    });
    
    render(ConfigurationManager);
    
    const toggleButton = screen.getByText('Show History');
    await fireEvent.click(toggleButton);
    
    await waitFor(() => {
      // Check that timestamp is formatted (exact format depends on locale)
      const timestampElement = screen.getByText(/2024/);
      expect(timestampElement).toBeInTheDocument();
    });
  });
});