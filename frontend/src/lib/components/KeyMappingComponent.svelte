<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let settings = {};
	export let pianoSpecs = null;

	let draggedKey = null;
	let draggedLed = null;
	let mappingMode = settings.mapping_mode || 'auto';
	let keyOffset = settings.key_offset || 0;
	let ledsPerKey = settings.leds_per_key || 3;
	let mappingBaseOffset = settings.mapping_base_offset || 0;
	let showAdvanced = false;

	// Piano key data
	const keyTypes = {
		white: ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
		black: ['C#', 'D#', 'F#', 'G#', 'A#']
	};

	// Generate piano keys based on specs
	$: pianoKeys = generatePianoKeys();
	$: ledStrip = generateLEDStrip();
	$: keyMapping = settings.key_mapping || {};

	function generatePianoKeys() {
		if (!pianoSpecs) return [];
		
		const keys = [];
		const startOctave = Math.floor(pianoSpecs.midi_start / 12) - 1;
		const endOctave = Math.floor(pianoSpecs.midi_end / 12) - 1;
		
		for (let octave = startOctave; octave <= endOctave; octave++) {
			for (const note of keyTypes.white) {
				const midiNote = (octave + 1) * 12 + ['C', 'D', 'E', 'F', 'G', 'A', 'B'].indexOf(note);
				if (midiNote >= pianoSpecs.midi_start && midiNote <= pianoSpecs.midi_end) {
					keys.push({
						id: `key-${midiNote}`,
						midi: midiNote,
						note: `${note}${octave}`,
						type: 'white',
						ledIndices: keyMapping[midiNote] || []
					});
				}
			}
			
			for (const note of keyTypes.black) {
				const baseNote = note.replace('#', '');
				const midiNote = (octave + 1) * 12 + ['C', 'D', 'E', 'F', 'G', 'A', 'B'].indexOf(baseNote) + 1;
				if (midiNote >= pianoSpecs.midi_start && midiNote <= pianoSpecs.midi_end) {
					keys.push({
						id: `key-${midiNote}`,
						midi: midiNote,
						note: `${note}${octave}`,
						type: 'black',
						ledIndices: keyMapping[midiNote] || []
					});
				}
			}
		}
		
		return keys.sort((a, b) => a.midi - b.midi);
	}

	function generateLEDStrip() {
		const ledCount = settings.ledCount || 246;
		const leds = [];
		
		for (let i = 0; i < ledCount; i++) {
			leds.push({
				id: `led-${i}`,
				index: i,
				assignedKey: findKeyForLED(i),
				color: getLEDColor(i)
			});
		}
		
		return leds;
	}

	function findKeyForLED(ledIndex) {
		for (const [midi, ledIndices] of Object.entries(keyMapping)) {
			const indices = Array.isArray(ledIndices) ? ledIndices : [ledIndices];
			if (indices.includes(ledIndex)) {
				return parseInt(midi);
			}
		}
		return null;
	}

	function getLEDColor(ledIndex) {
		const assignedKey = findKeyForLED(ledIndex);
		if (assignedKey) {
			const key = pianoKeys.find(k => k.midi === assignedKey);
			return key?.type === 'black' ? '#2d3748' : '#f7fafc';
		}
		return '#e2e8f0';
	}

	function generateAutoMapping() {
		const newMapping = {};
		const whiteKeys = pianoKeys.filter(k => k.type === 'white');
		const ledCount = settings.ledCount || 246;
		
		if (mappingMode === 'auto') {
			// Auto linear mapping with multi-LED support
			whiteKeys.forEach((key, index) => {
				const baseIndex = mappingBaseOffset + (index * ledsPerKey);
				if (ledsPerKey > 1) {
					const ledIndices = [];
					for (let i = 0; i < ledsPerKey; i++) {
						const ledIndex = baseIndex + i;
						if (ledIndex < ledCount) {
							ledIndices.push(ledIndex);
						}
					}
					if (ledIndices.length > 0) {
						newMapping[key.midi] = ledIndices;
					}
				} else {
					if (baseIndex < ledCount) {
						newMapping[key.midi] = baseIndex;
					}
				}
			});
		} else if (mappingMode === 'proportional') {
			// Proportional mapping with multi-LED support
			const totalKeys = whiteKeys.length;
			const availableLeds = ledCount - mappingBaseOffset;
			const ledsPerKeyFloat = availableLeds / totalKeys;
			
			whiteKeys.forEach((key, index) => {
				const baseIndex = mappingBaseOffset + Math.floor(index * ledsPerKeyFloat);
				if (ledsPerKey > 1) {
					const ledIndices = [];
					for (let i = 0; i < ledsPerKey; i++) {
						const ledIndex = baseIndex + i;
						if (ledIndex < ledCount) {
							ledIndices.push(ledIndex);
						}
					}
					if (ledIndices.length > 0) {
						newMapping[key.midi] = ledIndices;
					}
				} else {
					if (baseIndex < ledCount) {
						newMapping[key.midi] = baseIndex;
					}
				}
			});
		}
		
		updateMapping(newMapping);
	}

	function clearMapping() {
		updateMapping({});
	}

	function updateMapping(newMapping) {
		const updatedSettings = {
			...settings,
			key_mapping: newMapping,
			mapping_mode: mappingMode,
			key_offset: keyOffset,
			leds_per_key: ledsPerKey,
			mapping_base_offset: mappingBaseOffset
		};
		
		dispatch('change', updatedSettings);
	}

	// Drag and drop handlers
	function handleKeyDragStart(event, key) {
		draggedKey = key;
		event.dataTransfer.effectAllowed = 'move';
		event.dataTransfer.setData('text/plain', key.id);
	}

	function handleLEDDragStart(event, led) {
		draggedLed = led;
		event.dataTransfer.effectAllowed = 'move';
		event.dataTransfer.setData('text/plain', led.id);
	}

	function handleKeyDrop(event, targetKey) {
		event.preventDefault();
		
		if (draggedLed) {
			// LED dropped on key
			const newMapping = { ...keyMapping };
			
			// Remove existing mapping for this LED
			for (const [midi, ledIndex] of Object.entries(newMapping)) {
				if (ledIndex === draggedLed.index) {
					delete newMapping[midi];
				}
			}
			
			// For multi-LED mapping, add to existing array or create new array
			if (ledsPerKey > 1) {
				if (!newMapping[targetKey.midi]) {
					newMapping[targetKey.midi] = [];
				}
				if (!Array.isArray(newMapping[targetKey.midi])) {
					newMapping[targetKey.midi] = [newMapping[targetKey.midi]];
				}
				if (!newMapping[targetKey.midi].includes(draggedLed.index)) {
					newMapping[targetKey.midi].push(draggedLed.index);
					// Limit to ledsPerKey
					if (newMapping[targetKey.midi].length > ledsPerKey) {
						newMapping[targetKey.midi] = newMapping[targetKey.midi].slice(-ledsPerKey);
					}
				}
			} else {
				// Single LED mapping
				newMapping[targetKey.midi] = draggedLed.index;
			}
			updateMapping(newMapping);
		}
		
		draggedKey = null;
		draggedLed = null;
	}

	function handleLEDDrop(event, targetLed) {
		event.preventDefault();
		
		if (draggedKey) {
			// Key dropped on LED
			const newMapping = { ...keyMapping };
			
			// Remove existing mapping for this key
			delete newMapping[draggedKey.midi];
			
			// Remove existing mapping for this LED
			for (const [midi, ledIndex] of Object.entries(newMapping)) {
				if (ledIndex === targetLed.index) {
					delete newMapping[midi];
				}
			}
			
			// Add new mapping
			newMapping[draggedKey.midi] = targetLed.index;
			updateMapping(newMapping);
		}
		
		draggedKey = null;
		draggedLed = null;
	}

	function handleDragOver(event) {
		event.preventDefault();
		event.dataTransfer.dropEffect = 'move';
	}

	function removeKeyMapping(key) {
		if (keyMapping[key.note]) {
			delete keyMapping[key.note];
			keyMapping = { ...keyMapping };
			updateMapping();
		}
	}
</script>

<div class="space-y-6">
	<div class="flex justify-between items-center">
		<h3 class="text-lg font-medium text-gray-900">Key to LED Mapping</h3>
		<button
			on:click={() => showAdvanced = !showAdvanced}
			class="text-sm text-blue-600 hover:text-blue-800"
		>
			{showAdvanced ? 'Hide' : 'Show'} Advanced Options
		</button>
	</div>

	{#if showAdvanced}
		<div class="bg-gray-50 p-4 rounded-lg space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				<div>
					<label for="mapping_mode" class="block text-sm font-medium text-gray-700 mb-2">
						Mapping Mode
					</label>
					<select
						id="mapping_mode"
						bind:value={mappingMode}
						on:change={() => updateMapping(keyMapping)}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					>
						<option value="auto">Auto Linear</option>
						<option value="manual">Manual</option>
						<option value="proportional">Proportional</option>
					</select>
				</div>

				<div>
					<label for="leds_per_key" class="block text-sm font-medium text-gray-700 mb-2">
						LEDs per Key
					</label>
					<input
						id="leds_per_key"
						type="number"
						min="1"
						max="10"
						bind:value={ledsPerKey}
						on:input={() => updateMapping(keyMapping)}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div>
					<label for="mapping_base_offset" class="block text-sm font-medium text-gray-700 mb-2">
						Base Offset
					</label>
					<input
						id="mapping_base_offset"
						type="number"
						min="0"
						max="100"
						bind:value={mappingBaseOffset}
						on:input={() => updateMapping(keyMapping)}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div>
					<label for="key_offset" class="block text-sm font-medium text-gray-700 mb-2">
						Key Offset
					</label>
					<input
						id="key_offset"
						type="number"
						min="-50"
						max="50"
						bind:value={keyOffset}
						on:input={() => updateMapping(keyMapping)}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div class="flex items-end space-x-2 md:col-span-2">
					<button
						on:click={generateAutoMapping}
						class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						Auto Map
					</button>
					<button
						on:click={clearMapping}
						class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
					>
						Clear
					</button>
				</div>
			</div>
		</div>
	{/if}

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Piano Keys -->
		<div class="space-y-4">
			<h4 class="text-md font-medium text-gray-900">Piano Keys</h4>
			<div class="bg-white border border-gray-300 rounded-lg p-4 max-h-96 overflow-y-auto">
				<div class="space-y-2">
					{#each pianoKeys as key (key.id)}
						<div
							class="flex items-center justify-between p-2 rounded border {key.type === 'black' ? 'bg-gray-800 text-white border-gray-700' : 'bg-white border-gray-300'} cursor-move hover:shadow-md transition-shadow"
							draggable="true"
							on:dragstart={(e) => handleKeyDragStart(e, key)}
							on:dragover={handleDragOver}
							on:drop={(e) => handleKeyDrop(e, key)}
						>
							<div class="flex items-center space-x-2">
								<span class="text-sm font-mono">{key.note}</span>
								<span class="text-xs text-gray-500">MIDI {key.midi}</span>
							</div>
							<div class="flex items-center space-x-2">
								{#if key.ledIndices && key.ledIndices.length > 0}
									{#if Array.isArray(key.ledIndices)}
										<div class="flex flex-wrap gap-1">
											{#each key.ledIndices as ledIndex}
												<span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">LED {ledIndex}</span>
											{/each}
										</div>
									{:else}
										<span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">LED {key.ledIndices}</span>
									{/if}
									<button
										on:click={() => removeKeyMapping(key)}
										class="text-red-600 hover:text-red-800 text-xs"
									>
										✕
									</button>
								{:else}
									<span class="text-xs text-gray-400">Unmapped</span>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- LED Strip -->
		<div class="space-y-4">
			<h4 class="text-md font-medium text-gray-900">LED Strip ({ledStrip.length} LEDs)</h4>
			<div class="bg-white border border-gray-300 rounded-lg p-4 max-h-96 overflow-y-auto">
				<div class="grid grid-cols-10 gap-1">
					{#each ledStrip as led (led.id)}
						<div
							class="w-6 h-6 rounded-full border-2 cursor-move flex items-center justify-center text-xs font-mono transition-all hover:scale-110"
							style="background-color: {led.color}; border-color: {led.assignedKey ? '#3b82f6' : '#d1d5db'}"
							title="LED {led.index}{led.assignedKey ? ` → Key ${led.assignedKey}` : ''}"
							draggable="true"
							on:dragstart={(e) => handleLEDDragStart(e, led)}
							on:dragover={handleDragOver}
							on:drop={(e) => handleLEDDrop(e, led)}
						>
							{#if led.assignedKey}
								<span class="text-white text-xs">•</span>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>

	<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
		<h5 class="text-sm font-medium text-blue-900 mb-2">How to Map Keys to LEDs</h5>
		<ul class="text-sm text-blue-800 space-y-1">
			<li>• Drag piano keys to LED positions or vice versa</li>
			<li>• Use "Auto Map" for automatic linear mapping</li>
			<li>• Adjust key offset to shift the mapping</li>
			<li>• Click ✕ to remove individual mappings</li>
			<li>• White keys are shown in white, black keys in dark gray</li>
		</ul>
	</div>

	<div class="text-sm text-gray-600">
		<strong>Mapping Statistics:</strong>
		{Object.keys(keyMapping).length} of {pianoKeys.length} keys mapped
		({Math.round((Object.keys(keyMapping).length / pianoKeys.length) * 100)}% complete)
	</div>
</div>

<style>
	.cursor-move {
		cursor: move;
	}
	
	.cursor-move:active {
		cursor: grabbing;
	}
</style>