<script>
  import { onMount } from 'svelte';
  import { io } from 'socket.io-client';

  let socket;
  let isConnected = false;
  let isTestRunning = false;
  let currentSequence = null;
  let testDuration = 5;
  let selectedSequence = 'rainbow';
  let ledCount = 88;
  let testMessage = '';
  let testStatus = 'idle'; // idle, running, complete, error

  const sequenceTypes = [
    { value: 'rainbow', label: 'Rainbow Cycle', description: 'Smooth rainbow color transition' },
    { value: 'chase', label: 'Chase Light', description: 'Moving light pattern' },
    { value: 'fade', label: 'Fade In/Out', description: 'Breathing light effect' },
    { value: 'piano_keys', label: 'Piano Keys', description: 'White and black key pattern' }
  ];

  onMount(() => {
    // Connect to WebSocket
    socket = io('http://localhost:5001');
    
    socket.on('connect', () => {
      isConnected = true;
      console.log('Connected to LED test server');
    });
    
    socket.on('disconnect', () => {
      isConnected = false;
      console.log('Disconnected from LED test server');
    });
    
    socket.on('led_test_sequence_start', (data) => {
      isTestRunning = true;
      currentSequence = data;
      testStatus = 'running';
      testMessage = `Running ${data.type} sequence for ${data.duration}s`;
    });
    
    socket.on('led_test_sequence_complete', (data) => {
      isTestRunning = false;
      currentSequence = null;
      testStatus = 'complete';
      testMessage = `${data.type} sequence completed successfully`;
      setTimeout(() => {
        testStatus = 'idle';
        testMessage = '';
      }, 3000);
    });
    
    socket.on('led_test_sequence_stop', () => {
      isTestRunning = false;
      currentSequence = null;
      testStatus = 'idle';
      testMessage = 'Test sequence stopped';
    });
    
    socket.on('led_test_sequence_error', (data) => {
      isTestRunning = false;
      currentSequence = null;
      testStatus = 'error';
      testMessage = `Error: ${data.error}`;
    });
    
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  });

  async function startTestSequence() {
    try {
      const response = await fetch('/api/led-test-sequence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: selectedSequence,
          duration: testDuration,
          ledCount: ledCount
        })
      });
      
      const result = await response.json();
      
      if (!result.success) {
        testStatus = 'error';
        testMessage = result.message;
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `Failed to start test: ${error.message}`;
    }
  }

  async function stopTestSequence() {
    try {
      const response = await fetch('/api/led-test-sequence/stop', {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (!result.success) {
        testStatus = 'error';
        testMessage = result.message;
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `Failed to stop test: ${error.message}`;
    }
  }
</script>

<div class="led-test-container">
  <div class="header">
    <h3>LED Test Sequences</h3>
    <div class="connection-status" class:connected={isConnected}>
      <span class="status-dot"></span>
      {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  </div>

  <div class="test-controls">
    <div class="control-group">
      <label for="sequence-type">Sequence Type:</label>
      <select id="sequence-type" bind:value={selectedSequence} disabled={isTestRunning}>
        {#each sequenceTypes as sequence}
          <option value={sequence.value}>{sequence.label}</option>
        {/each}
      </select>
      <p class="sequence-description">
        {sequenceTypes.find(s => s.value === selectedSequence)?.description}
      </p>
    </div>

    <div class="control-group">
      <label for="duration">Duration (seconds):</label>
      <input 
        id="duration" 
        type="number" 
        bind:value={testDuration} 
        min="1" 
        max="60" 
        disabled={isTestRunning}
      />
    </div>

    <div class="control-group">
      <label for="led-count">LED Count:</label>
      <input 
        id="led-count" 
        type="number" 
        bind:value={ledCount} 
        min="1" 
        max="246" 
        disabled={isTestRunning}
      />
    </div>
  </div>

  <div class="test-actions">
    {#if !isTestRunning}
      <button 
        class="btn btn-primary" 
        on:click={startTestSequence}
        disabled={!isConnected}
      >
        Start Test
      </button>
    {:else}
      <button 
        class="btn btn-secondary" 
        on:click={stopTestSequence}
      >
        Stop Test
      </button>
    {/if}
  </div>

  {#if testMessage}
    <div class="test-status" class:running={testStatus === 'running'} class:complete={testStatus === 'complete'} class:error={testStatus === 'error'}>
      <div class="status-icon">
        {#if testStatus === 'running'}
          <div class="spinner"></div>
        {:else if testStatus === 'complete'}
          ✓
        {:else if testStatus === 'error'}
          ✗
        {/if}
      </div>
      <span>{testMessage}</span>
    </div>
  {/if}

  {#if currentSequence}
    <div class="current-test">
      <h4>Current Test</h4>
      <div class="test-info">
        <div class="info-item">
          <span class="label">Type:</span>
          <span class="value">{currentSequence.type}</span>
        </div>
        <div class="info-item">
          <span class="label">Duration:</span>
          <span class="value">{currentSequence.duration}s</span>
        </div>
        <div class="info-item">
          <span class="label">LED Count:</span>
          <span class="value">{currentSequence.ledCount}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .led-test-container {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e0e0e0;
  }

  .header h3 {
    margin: 0;
    color: #333;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #666;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #dc3545;
  }

  .connection-status.connected .status-dot {
    background: #28a745;
  }

  .test-controls {
    display: grid;
    gap: 15px;
    margin-bottom: 20px;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .control-group label {
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }

  .control-group select,
  .control-group input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  .control-group select:disabled,
  .control-group input:disabled {
    background: #f5f5f5;
    color: #999;
  }

  .sequence-description {
    font-size: 12px;
    color: #666;
    margin: 0;
    font-style: italic;
  }

  .test-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #007bff;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0056b3;
  }

  .btn-secondary {
    background: #6c757d;
    color: white;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #545b62;
  }

  .test-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 15px;
  }

  .test-status.running {
    background: #e3f2fd;
    color: #1976d2;
    border: 1px solid #bbdefb;
  }

  .test-status.complete {
    background: #e8f5e8;
    color: #2e7d32;
    border: 1px solid #c8e6c9;
  }

  .test-status.error {
    background: #ffebee;
    color: #c62828;
    border: 1px solid #ffcdd2;
  }

  .status-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #e3f2fd;
    border-top: 2px solid #1976d2;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .current-test {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 15px;
  }

  .current-test h4 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 16px;
  }

  .test-info {
    display: grid;
    gap: 8px;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .info-item .label {
    font-weight: 500;
    color: #666;
  }

  .info-item .value {
    color: #333;
    font-family: monospace;
  }

  @media (min-width: 768px) {
    .test-controls {
      grid-template-columns: 1fr 1fr;
    }

    .control-group:first-child {
      grid-column: 1 / -1;
    }
  }
</style>