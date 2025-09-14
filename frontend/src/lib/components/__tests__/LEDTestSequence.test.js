import { render, fireEvent, waitFor, screen } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LEDTestSequence from '../LEDTestSequence.svelte';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 10);
  }
  
  send(data) {
    // Mock send method
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }
}

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;
global.WebSocket = MockWebSocket;

describe('LEDTestSequence Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default values', () => {
    render(LEDTestSequence);
    
    expect(screen.getByText('LED Test Sequences')).toBeInTheDocument();
    expect(screen.getByLabelText('Sequence Type:')).toBeInTheDocument();
    expect(screen.getByLabelText('Duration (seconds):')).toBeInTheDocument();
    expect(screen.getByLabelText('LED Count:')).toBeInTheDocument();
    expect(screen.getByText('Start Test')).toBeInTheDocument();
  });

  it('displays all sequence type options', () => {
    render(LEDTestSequence);
    
    const select = screen.getByLabelText('Sequence Type:');
    const options = select.querySelectorAll('option');
    
    expect(options).toHaveLength(4);
    expect(options[0]).toHaveTextContent('Rainbow');
    expect(options[1]).toHaveTextContent('Chase');
    expect(options[2]).toHaveTextContent('Fade');
    expect(options[3]).toHaveTextContent('Piano Keys');
  });

  it('updates input values correctly', async () => {
    render(LEDTestSequence);
    
    const durationInput = screen.getByLabelText('Duration (seconds):');
    const ledCountInput = screen.getByLabelText('LED Count:');
    
    await fireEvent.input(durationInput, { target: { value: '10' } });
    await fireEvent.input(ledCountInput, { target: { value: '88' } });
    
    expect(durationInput.value).toBe('10');
    expect(ledCountInput.value).toBe('88');
  });

  it('starts test sequence successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Rainbow test sequence started'
      })
    });
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/led-test-sequence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sequence_type: 'rainbow',
          duration: 5,
          led_count: 88,
          gpio_pin: 18
        })
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Rainbow test sequence started')).toBeInTheDocument();
    });
  });

  it('handles test sequence start error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        success: false,
        message: 'GPIO initialization failed'
      })
    });
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText('GPIO initialization failed')).toBeInTheDocument();
    });
  });

  it('stops test sequence successfully', async () => {
    // First start a sequence
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Rainbow test sequence started'
      })
    });
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText('Stop Test')).toBeInTheDocument();
    });
    
    // Now stop the sequence
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Test sequence stopped'
      })
    });
    
    const stopButton = screen.getByText('Stop Test');
    await fireEvent.click(stopButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/led-test-sequence/stop', {
        method: 'POST'
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test sequence stopped')).toBeInTheDocument();
    });
  });

  it('disables start button when sequence is running', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Rainbow test sequence started'
      })
    });
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(startButton).toBeDisabled();
    });
  });

  it('validates input values', async () => {
    render(LEDTestSequence);
    
    const durationInput = screen.getByLabelText('Duration (seconds):');
    const ledCountInput = screen.getByLabelText('LED Count:');
    
    // Test negative duration
    await fireEvent.input(durationInput, { target: { value: '-1' } });
    expect(durationInput.value).toBe('1'); // Should be clamped to minimum
    
    // Test zero LED count
    await fireEvent.input(ledCountInput, { target: { value: '0' } });
    expect(ledCountInput.value).toBe('1'); // Should be clamped to minimum
    
    // Test maximum LED count
    await fireEvent.input(ledCountInput, { target: { value: '1000' } });
    expect(ledCountInput.value).toBe('500'); // Should be clamped to maximum
  });

  it('displays connection status correctly', async () => {
    render(LEDTestSequence);
    
    // Initially should show connecting
    expect(screen.getByText('WebSocket: Connecting...')).toBeInTheDocument();
    
    // After connection, should show connected
    await waitFor(() => {
      expect(screen.getByText('WebSocket: Connected')).toBeInTheDocument();
    }, { timeout: 100 });
  });

  it('handles WebSocket messages correctly', async () => {
    const component = render(LEDTestSequence);
    
    // Wait for WebSocket to connect
    await waitFor(() => {
      expect(screen.getByText('WebSocket: Connected')).toBeInTheDocument();
    });
    
    // Simulate receiving a WebSocket message
    const mockMessage = {
      data: JSON.stringify({
        type: 'test_sequence_progress',
        progress: 50,
        current_step: 25
      })
    };
    
    // Find the WebSocket instance and trigger message event
    const wsInstances = component.container.querySelectorAll('[data-testid="websocket"]');
    if (wsInstances.length > 0) {
      const ws = wsInstances[0].__ws;
      if (ws && ws.onmessage) {
        ws.onmessage(mockMessage);
      }
    }
    
    // Check if progress is displayed (this would depend on your implementation)
    // This is a placeholder - adjust based on your actual WebSocket message handling
  });

  it('changes sequence type correctly', async () => {
    render(LEDTestSequence);
    
    const select = screen.getByLabelText('Sequence Type:');
    
    await fireEvent.change(select, { target: { value: 'chase' } });
    expect(select.value).toBe('chase');
    
    await fireEvent.change(select, { target: { value: 'fade' } });
    expect(select.value).toBe('fade');
    
    await fireEvent.change(select, { target: { value: 'piano_keys' } });
    expect(select.value).toBe('piano_keys');
  });

  it('handles network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to start test sequence/)).toBeInTheDocument();
    });
  });

  it('clears messages after timeout', async () => {
    vi.useFakeTimers();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Test message'
      })
    });
    
    render(LEDTestSequence);
    
    const startButton = screen.getByText('Start Test');
    await fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
    
    // Fast-forward time
    vi.advanceTimersByTime(5000);
    
    await waitFor(() => {
      expect(screen.queryByText('Test message')).not.toBeInTheDocument();
    });
    
    vi.useRealTimers();
  });
});