/**
 * Upload service for handling MIDI file uploads
 */

export interface UploadResponse {
	success: boolean;
	filename?: string;
	filesize?: number;
	path?: string;
	error?: string;
	message?: string;
}

export interface UploadProgress {
	loaded: number;
	total: number;
	percentage: number;
}

export class UploadError extends Error {
	constructor(
		message: string,
		public status?: number
	) {
		super(message);
		this.name = 'UploadError';
	}
}

/**
 * Validates a file before upload with detailed error messages
 */
export function validateMidiFile(file: File): { valid: boolean; message: string } {
	const allowedExtensions = ['.mid', '.midi'];
	const maxSize = 1024 * 1024; // 1MB
	const minSize = 100; // 100 bytes minimum

	// Check if file exists
	if (!file) {
		return { valid: false, message: 'No file selected. Please choose a MIDI file to upload.' };
	}

	// Check file extension
	const fileName = file.name.toLowerCase();
	const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));

	if (!hasValidExtension) {
		const fileExtension = fileName.includes('.') ? fileName.split('.').pop() : 'unknown';
		return {
			valid: false,
			message: `Invalid file type "${fileExtension}". Please select a MIDI file with .mid or .midi extension.`
		};
	}

	// Check file size
	if (file.size > maxSize) {
		const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
		const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0);
		return {
			valid: false,
			message: `File size (${fileSizeMB}MB) exceeds the maximum limit of ${maxSizeMB}MB. Please choose a smaller MIDI file.`
		};
	}

	if (file.size < minSize) {
		return {
			valid: false,
			message: `File appears to be empty (${file.size} bytes). Please select a valid MIDI file with musical content.`
		};
	}

	// Additional validation for common non-MIDI files that might have .mid extension
	if (file.type && !file.type.includes('midi') && !file.type.includes('audio')) {
		return {
			valid: false,
			message: `File type "${file.type}" is not supported. Please select a genuine MIDI file.`
		};
	}

	return { valid: true, message: 'File validation successful.' };
}

/**
 * Uploads a MIDI file to the server
 */
export async function uploadMidiFile(
	file: File,
	onProgress?: (progress: UploadProgress) => void
): Promise<UploadResponse> {
	// Validate file before upload
	const validation = validateMidiFile(file);
	if (!validation.valid) {
		throw new UploadError(validation.message);
	}

	// Create form data
	const formData = new FormData();
	formData.append('file', file);

	try {
		// Create XMLHttpRequest for progress tracking
		const xhr = new XMLHttpRequest();

		// Set up progress tracking
		if (onProgress) {
			xhr.upload.addEventListener('progress', (event) => {
				if (event.lengthComputable) {
					const progress: UploadProgress = {
						loaded: event.loaded,
						total: event.total,
						percentage: Math.round((event.loaded / event.total) * 100)
					};
					onProgress(progress);
				}
			});
		}

		// Create promise for XMLHttpRequest
		const uploadPromise = new Promise<UploadResponse>((resolve, reject) => {
			xhr.onload = () => {
				try {
					const response = JSON.parse(xhr.responseText);

					if (xhr.status >= 200 && xhr.status < 300) {
						resolve({
							success: true,
							...response
						});
					} else {
						reject(
							new UploadError(
								response.error || `Upload failed with status ${xhr.status}`,
								xhr.status,
								response
							)
						);
					}
				} catch (parseError) {
					reject(
						new UploadError(
							'Invalid response from server',
							xhr.status
						)
					);
				}
			};

			xhr.onerror = () => {
				reject(new UploadError('Network error occurred during upload'));
			};

			xhr.ontimeout = () => {
				reject(new UploadError('Upload timed out'));
			};

			xhr.onabort = () => {
				reject(new UploadError('Upload was cancelled'));
			};
		});

		// Configure and send request
		xhr.open('POST', '/api/upload-midi');
		xhr.timeout = 30000; // 30 second timeout
		xhr.send(formData);

		return await uploadPromise;
	} catch (error) {
		if (error instanceof UploadError) {
			throw error;
		}
		throw new UploadError(
			error instanceof Error ? error.message : 'Unknown upload error'
		);
	}
}

/**
 * Alternative upload function using fetch API (simpler, but no progress tracking)
 */
export async function uploadMidiFileSimple(file: File): Promise<UploadResponse> {
	// Validate file before upload
	const validation = validateMidiFile(file);
	if (!validation.valid) {
		throw new UploadError(validation.message);
	}

	// Create form data
	const formData = new FormData();
	formData.append('file', file);

	try {
		const response = await fetch('/api/upload-midi', {
			method: 'POST',
			body: formData
		});

		const result = await response.json();

		if (response.ok) {
			return {
				success: true,
				...result
			};
		} else {
			throw new UploadError(
				result.error || `Upload failed with status ${response.status}`,
				response.status,
				result
			);
		}
	} catch (error) {
		if (error instanceof UploadError) {
			throw error;
		}

		if (error instanceof TypeError && error.message.includes('fetch')) {
			throw new UploadError('Network error occurred during upload');
		}

		throw new UploadError(
			error instanceof Error ? error.message : 'Unknown upload error'
		);
	}
}

/**
 * Formats file size for display
 */
export function formatFileSize(bytes: number): string {
	if (bytes === 0) return '0 Bytes';

	const k = 1024;
	const sizes = ['Bytes', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));

	return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}