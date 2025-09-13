import mido

print('Backend details:')
backend = mido.backend
print('Name:', backend.name)
print('API:', getattr(backend, 'api', 'Unknown'))
print('Available ports:')
try:
    print('Inputs:', backend.get_input_names())
    print('Outputs:', backend.get_output_names())
except Exception as e:
    print('Error:', e)

print('\nMido version:', mido.__version__)
print('Available backends:', mido.available_backends())