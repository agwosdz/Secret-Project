<script>
  import { onMount } from 'svelte';
  import { io } from 'socket.io-client';

  let socket;
  let isConnected = false;
  let isTestRunning = false;
  let currentSequence = null;
  let testDuration = 5;
  let selectedSequence = 'rainbow';
  let ledCount = 246;
  let testMessage = '';
  let testStatus = 'idle'; // idle, running, complete, error
  let testProgress = 0;
  let currentTestId = null;
  let systemCapabilities = null;
  let individualTestLed = 0;
  let individualTestColor = '#ffffff';
  let individualTestBrightness = 1.0;
  let customPattern = [];
  let showAdvancedOptions = false;
  let testSpeed = 1.0;
  let gpioPin = 18;

  const sequenceTypes = [
    { value: 'rainbow', label: 'Rainbow Cycle', description: 'Smooth rainbow color transition across all LEDs' },
    { value: 'chase', label: 'Chase Light', description: 'Moving light pattern with trailing fade' },
    { value: 'fade', label: 'Fade In/Out', description: 'Breathing light effect with color transitions' },
    { value: 'piano_keys', label: 'Piano Keys', description: 'White and black key pattern simulation' },
    { value: 'custom', label: 'Custom Pattern', description: 'User-defined LED pattern sequence' }
  ];

  // Tab switching functionality
  function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
      content.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
      button.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
      selectedTab.style.display = 'block';
    }
    
    // Add active class to clicked button
    const clickedButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (clickedButton) {
      clickedButton.classList.add('active');
    }
  }

  onMount(async () => {
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
    
    // Enhanced WebSocket event handlers for new hardware test API
    socket.on('led_sequence_start', (data) => {
      isTestRunning = true;
      currentSequence = data;
      currentTestId = data.test_id;
      testStatus = 'running';
      testProgress = 0;
      testMessage = `Running ${data.sequence_type} sequence for ${data.duration}s`;
    });
    
    socket.on('led_sequence_progress', (data) => {
      if (data.test_id === currentTestId) {
        testProgress = data.progress || 0;
        if (data.current_step !== undefined) {
          testMessage = `Running ${currentSequence?.sequence_type} - Step ${data.current_step}`;
        }
      }
    });
    
    socket.on('led_sequence_complete', (data) => {
      if (data.test_id === currentTestId) {
        isTestRunning = false;
        currentSequence = null;
        currentTestId = null;
        testStatus = 'complete';
        testProgress = 100;
        testMessage = `${data.sequence_type} sequence completed successfully`;
        setTimeout(() => {
          testStatus = 'idle';
          testMessage = '';
          testProgress = 0;
        }, 3000);
      }
    });
    
    socket.on('led_sequence_stop', (data) => {
      if (data.test_id === currentTestId) {
        isTestRunning = false;
        currentSequence = null;
        currentTestId = null;
        testStatus = 'idle';
        testProgress = 0;
        testMessage = 'Test sequence stopped';
      }
    });
    
    socket.on('led_sequence_error', (data) => {
      if (data.test_id === currentTestId) {
        isTestRunning = false;
        currentSequence = null;
        currentTestId = null;
        testStatus = 'error';
        testProgress = 0;
        testMessage = `Error: ${data.error}`;
      }
    });

    socket.on('led_test_update', (data) => {
      if (data.type === 'individual') {
        testMessage = `LED ${data.led_index} ${data.status === 'active' ? 'ON' : 'OFF'}`;
      }
    });

    // Set up tab click handlers
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const tabName = e.target.getAttribute('data-tab');
        switchTab(tabName);
      });
    });
    
    // Show first tab by default
    switchTab('sequence');

    // Load system capabilities
    await loadSystemCapabilities();
    
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  });

  async function loadSystemCapabilities() {
    try {
      const response = await fetch('/api/hardware-test/system/capabilities');
      const result = await response.json();
      
      if (result.success) {
        systemCapabilities = result.capabilities;
      }
    } catch (error) {
      console.error('Failed to load system capabilities:', error);
    }
  }

  async function startTestSequence() {
    try {
      const requestBody = {
        sequence_type: selectedSequence,
        duration: testDuration,
        led_count: ledCount,
        gpio_pin: gpioPin,
        speed: testSpeed,
        brightness: individualTestBrightness
      };

      if (selectedSequence === 'custom' && customPattern.length > 0) {
        requestBody.pattern = customPattern;
      }

      const response = await fetch('/api/hardware-test/led/sequence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      const result = await response.json();
      
      if (!result.success) {
        testStatus = 'error';
        testMessage = result.error || 'Failed to start test';
      } else {
        currentTestId = result.test_id;
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `Failed to start test: ${error.message}`;
    }
  }

  async function stopTestSequence() {
    if (!currentTestId) return;
    
    try {
      const response = await fetch(`/api/hardware-test/led/sequence/${currentTestId}/stop`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (!result.success) {
        testStatus = 'error';
        testMessage = result.error || 'Failed to stop test';
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `Failed to stop test: ${error.message}`;
    }
  }

  async function testIndividualLED() {
    try {
      const color = hexToRgb(individualTestColor);
      
      const response = await fetch('/api/hardware-test/led/individual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          led_index: individualTestLed,
          color: color,
          brightness: individualTestBrightness,
          duration: 2.0,
          gpio_pin: gpioPin,
          led_count: ledCount
        })
      });
      
      const result = await response.json();
      
      if (!result.success) {
        testStatus = 'error';
        testMessage = result.error || 'Failed to test individual LED';
      } else {
        testMessage = `Testing LED ${individualTestLed}`;
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `Failed to test LED: ${error.message}`;
    }
  }

  async function validateGPIO() {
    try {
      const response = await fetch('/api/hardware-test/gpio/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          pins: [gpioPin],
          mode: 'output'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        const pinResult = result.results[gpioPin];
        if (pinResult.status === 'ok') {
          testMessage = `GPIO pin ${gpioPin} validated successfully`;
          testStatus = 'complete';
        } else {
          testMessage = `GPIO pin ${gpioPin} error: ${pinResult.error}`;
          testStatus = 'error';
        }
      } else {
        testMessage = result.error || 'GPIO validation failed';
        testStatus = 'error';
      }
    } catch (error) {
      testStatus = 'error';
      testMessage = `GPIO validation failed: ${error.message}`;
    }
  }

  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
    ] : [255, 255, 255];
  }

  function addCustomPatternStep() {
    customPattern = [...customPattern, {
      leds: [0],
      color: [255, 255, 255],
      duration: 1.0,
      brightness: 1.0
    }];
  }

  function removeCustomPatternStep(index) {
    customPattern = customPattern.filter((_, i) => i !== index);
  }
</script>

<div class="led-test-container">
  <div class="header">
    <h3>Hardware Test Suite</h3>
    <div class="connection-status" class:connected={isConnected}>
      <span class="status-dot"></span>
      {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  </div>

  <!-- System Capabilities -->
  {#if systemCapabilities}
    <div class="capabilities-panel">
      <h4>System Status</h4>
      <div class="capabilities-grid">
        <div class="capability-item" class:available={systemCapabilities.led_controller}>
          <span class="capability-icon">{systemCapabilities.led_controller ? '✓' : '✗'}</span>
          <span>LED Controller</span>
        </div>
        <div class="capability-item" class:available={systemCapabilities.gpio}>
          <span class="capability-icon">{systemCapabilities.gpio ? '✓' : '✗'}</span>
          <span>GPIO Access</span>
        </div>
        <div class="capability-item">
          <span class="capability-icon">🖥️</span>
          <span>Platform: {systemCapabilities.platform}</span>
        </div>
      </div>
    </div>
  {/if}

  <!-- Test Tabs -->
  <div class="test-tabs">
    <button class="tab-button active" data-tab="sequence">LED Sequences</button>
    <button class="tab-button" data-tab="individual">Individual LEDs</button>
    <button class="tab-button" data-tab="gpio">GPIO Test</button>
  </div>

  <!-- LED Sequence Testing -->
  <div class="tab-content" id="sequence-tab">
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

      <div class="control-row">
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

      <!-- Advanced Options -->
      <div class="advanced-toggle">
        <button 
          class="toggle-button" 
          on:click={() => showAdvancedOptions = !showAdvancedOptions}
        >
          {showAdvancedOptions ? '▼' : '▶'} Advanced Options
        </button>
      </div>

      {#if showAdvancedOptions}
        <div class="advanced-options">
          <div class="control-row">
            <div class="control-group">
              <label for="gpio-pin">GPIO Pin:</label>
              <input 
                id="gpio-pin" 
                type="number" 
                bind:value={gpioPin} 
                min="1" 
                max="40" 
                disabled={isTestRunning}
              />
            </div>

            <div class="control-group">
              <label for="test-speed">Speed:</label>
              <input 
                id="test-speed" 
                type="range" 
                bind:value={testSpeed} 
                min="0.1" 
                max="3.0" 
                step="0.1" 
                disabled={isTestRunning}
              />
              <span class="range-value">{testSpeed}x</span>
            </div>

            <div class="control-group">
              <label for="brightness">Brightness:</label>
              <input 
                id="brightness" 
                type="range" 
                bind:value={individualTestBrightness} 
                min="0.1" 
                max="1.0" 
                step="0.1" 
                disabled={isTestRunning}
              />
              <span class="range-value">{Math.round(individualTestBrightness * 100)}%</span>
            </div>
          </div>
        </div>
      {/if}

      <!-- Custom Pattern Editor -->
      {#if selectedSequence === 'custom'}
        <div class="custom-pattern-editor">
          <h4>Custom Pattern Steps</h4>
          {#each customPattern as step, index}
            <div class="pattern-step">
              <div class="step-header">
                <span>Step {index + 1}</span>
                <button class="remove-step" on:click={() => removeCustomPatternStep(index)}>×</button>
              </div>
              <div class="step-controls">
                <input type="text" placeholder="LED indices (e.g., 0,1,2)" bind:value={step.leds} />
                <input type="color" bind:value={step.color} />
                <input type="number" placeholder="Duration" bind:value={step.duration} min="0.1" step="0.1" />
              </div>
            </div>
          {/each}
          <button class="add-step" on:click={addCustomPatternStep}>+ Add Step</button>
        </div>
      {/if}
    </div>

    <div class="test-actions">
      {#if !isTestRunning}
        <button 
          class="btn btn-primary" 
          on:click={startTestSequence}
          disabled={!isConnected || (systemCapabilities && !systemCapabilities.led_controller)}
        >
          Start Sequence Test
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

    <!-- Progress Bar -->
    {#if isTestRunning && testProgress > 0}
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: {testProgress}%"></div>
        </div>
        <span class="progress-text">{Math.round(testProgress)}%</span>
      </div>
    {/if}
  </div>

  <!-- Individual LED Testing -->
  <div class="tab-content" id="individual-tab" style="display: none;">
    <div class="test-controls">
      <div class="control-row">
        <div class="control-group">
          <label for="individual-led">LED Index:</label>
          <input 
            id="individual-led" 
            type="number" 
            bind:value={individualTestLed} 
            min="0" 
            max={ledCount - 1}
          />
        </div>

        <div class="control-group">
          <label for="individual-color">Color:</label>
          <input 
            id="individual-color" 
            type="color" 
            bind:value={individualTestColor}
          />
        </div>

        <div class="control-group">
          <label for="individual-brightness">Brightness:</label>
          <input 
            id="individual-brightness" 
            type="range" 
            bind:value={individualTestBrightness} 
            min="0.1" 
            max="1.0" 
            step="0.1"
          />
          <span class="range-value">{Math.round(individualTestBrightness * 100)}%</span>
        </div>
      </div>
    </div>

    <div class="test-actions">
      <button 
        class="btn btn-primary" 
        on:click={testIndividualLED}
        disabled={!isConnected || (systemCapabilities && !systemCapabilities.led_controller)}
      >
        Test LED {individualTestLed}
      </button>
    </div>
  </div>

  <!-- GPIO Testing -->
  <div class="tab-content" id="gpio-tab" style="display: none;">
    <div class="test-controls">
      <div class="control-group">
        <label for="gpio-test-pin">GPIO Pin to Test:</label>
        <input 
          id="gpio-test-pin" 
          type="number" 
          bind:value={gpioPin} 
          min="1" 
          max="40"
        />
        <p class="help-text">Test GPIO pin availability and functionality</p>
      </div>
    </div>

    <div class="test-actions">
      <button 
        class="btn btn-primary" 
        on:click={validateGPIO}
        disabled={!isConnected || (systemCapabilities && !systemCapabilities.gpio)}
      >
        Validate GPIO Pin {gpioPin}
      </button>
    </div>
  </div>

  <!-- Test Status -->
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

  <!-- Current Test Info -->
  {#if currentSequence}
    <div class="current-test">
      <h4>Current Test</h4>
      <div class="test-info">
        <div class="info-item">
          <span class="label">Type:</span>
          <span class="value">{currentSequence.sequence_type}</span>
        </div>
        <div class="info-item">
          <span class="label">Duration:</span>
          <span class="value">{currentSequence.duration}s</span>
        </div>
        <div class="info-item">
          <span class="label">LED Count:</span>
          <span class="value">{currentSequence.led_count}</span>
        </div>
        <div class="info-item">
          <span class="label">Test ID:</span>
          <span class="value">{currentTestId}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .led-test-container {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 1px solid var(--border-color);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .header h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: 1.25rem;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    background: var(--bg-tertiary);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .connection-status.connected {
    background: var(--success-bg);
    color: var(--success-text);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--error-color);
  }

  .connection-status.connected .status-dot {
    background: var(--success-color);
  }

  /* System Capabilities Panel */
  .capabilities-panel {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--border-color);
  }

  .capabilities-panel h4 {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .capabilities-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
  }

  .capability-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-radius: 4px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
  }

  .capability-item.available {
    background: var(--success-bg);
    border-color: var(--success-color);
  }

  .capability-icon {
    font-weight: bold;
    font-size: 0.875rem;
  }

  /* Tab Navigation */
  .test-tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1.5rem;
  }

  .tab-button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
    font-weight: 500;
  }

  .tab-button:hover {
    color: var(--text-primary);
    background: var(--bg-tertiary);
  }

  .tab-button.active {
    color: var(--accent-color);
    border-bottom-color: var(--accent-color);
  }

  .tab-content {
    display: block;
  }

  .test-controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .control-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .control-group label {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .control-group select,
  .control-group input {
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .control-group select:focus,
  .control-group input:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px var(--accent-color-alpha);
  }

  .control-group select:disabled,
  .control-group input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .sequence-description {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin: 0;
    font-style: italic;
  }

  .help-text {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin: 0;
  }

  /* Advanced Options */
  .advanced-toggle {
    margin: 1rem 0;
  }

  .toggle-button {
    background: none;
    border: none;
    color: var(--accent-color);
    cursor: pointer;
    font-weight: 500;
    padding: 0.5rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .toggle-button:hover {
    text-decoration: underline;
  }

  .advanced-options {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 1rem;
    margin-top: 0.5rem;
  }

  .range-value {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-weight: 500;
  }

  /* Custom Pattern Editor */
  .custom-pattern-editor {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 1rem;
    margin-top: 1rem;
  }

  .custom-pattern-editor h4 {
    margin: 0 0 1rem 0;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .pattern-step {
    background: var(--bg-primary);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border-color);
  }

  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .step-header span {
    font-weight: 500;
    color: var(--text-primary);
  }

  .remove-step {
    background: var(--error-color);
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
  }

  .step-controls {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 0.75rem;
  }

  .add-step {
    background: var(--accent-color);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s ease;
  }

  .add-step:hover {
    background: var(--accent-color-hover);
  }

  /* Progress Bar */
  .progress-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-color);
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
    min-width: 40px;
  }

  .test-actions {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background: var(--accent-color);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--accent-color-hover);
    transform: translateY(-1px);
  }

  .btn-secondary {
    background: var(--error-color);
    color: white;
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--error-color-hover);
    transform: translateY(-1px);
  }

  .test-status {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    font-weight: 500;
  }

  .test-status.running {
    background: var(--warning-bg);
    color: var(--warning-text);
    border: 1px solid var(--warning-color);
  }

  .test-status.complete {
    background: var(--success-bg);
    color: var(--success-text);
    border: 1px solid var(--success-color);
  }

  .test-status.error {
    background: var(--error-bg);
    color: var(--error-text);
    border: 1px solid var(--error-color);
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
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .current-test {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 1rem;
    border: 1px solid var(--border-color);
  }

  .current-test h4 {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .test-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .info-item .label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .info-item .value {
    font-size: 0.875rem;
    color: var(--text-primary);
    font-weight: 600;
  }

  @media (max-width: 768px) {
    .led-test-container {
      padding: 1rem;
      margin: 0.5rem 0;
    }

    .header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .test-tabs {
      flex-direction: column;
    }

    .tab-button {
      text-align: left;
      border-bottom: none;
      border-left: 2px solid transparent;
    }

    .tab-button.active {
      border-left-color: var(--accent-color);
      border-bottom-color: transparent;
    }

    .control-row {
      grid-template-columns: 1fr;
    }

    .step-controls {
      grid-template-columns: 1fr;
    }

    .test-actions {
      flex-direction: column;
    }

    .btn {
      width: 100%;
    }

    .test-info {
      grid-template-columns: 1fr;
    }

    .capabilities-grid {
      grid-template-columns: 1fr;
    }

    .progress-container {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>