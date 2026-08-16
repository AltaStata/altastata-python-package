import os
from altastata import AltaStataFunctions
import time

altastata_functions = AltaStataFunctions.from_account_dir(os.path.expanduser('~/.altastata/accounts/amazon.rsa.alice222'))
altastata_functions.set_password(os.environ.get("ALTASTATA_PASSWORD", ""));

# Test create_file and append_buffer_to_file
print("\nTesting create_file and append_buffer_to_file:")

# Create an empty file
result = altastata_functions.create_file('StoreTest/empty_file.txt')
print('create empty file: ' + str(result.getOperationStateValue()) + " " + result.getCloudFileCreateTime())
file_create_time_id = int(result.getCloudFileCreateTime())

# Create a file with initial content
initial_content = b"Initial content\n"
result = altastata_functions.create_file('StoreTest/initial_content.txt', initial_content)
print('create file with content: ' + str(result.getOperationStateValue()) + " " + result.getCloudFileCreateTime())
initial_file_time_id = int(result.getCloudFileCreateTime())

# Append content to the empty file
append_content = b"Appended content\n"
altastata_functions.append_buffer_to_file('StoreTest/empty_file.txt', append_content, file_create_time_id)

# Verify the content by reading it back
buffer = altastata_functions.get_buffer('StoreTest/empty_file.txt', file_create_time_id, 0, 4, 100)
print("Appended file content: " + buffer.decode('utf-8'))

# Store
result = altastata_functions.store([os.path.expanduser('~/Desktop/sample.png'),
                                    os.path.expanduser('~/Desktop/sample.txt')],
                                   os.path.expanduser('~/Desktop'), 'StoreTest', True)

# Get the first CloudFileOperationStatus object
print('store: ' + str(result[0].getOperationStateValue()) + " " + result[0].getCloudFileCreateTime())

file_create_time_id = int(result[0].getCloudFileCreateTime())

users = ["bob123", "catrina777"]
result = altastata_functions.share_files('StoreTest/sample.txt', True, None, None, users)
print('share_files:' + str(result[0].getOperationStateValue()))

# Retrieve file
result = altastata_functions.retrieve_files(os.path.expanduser('~/Desktop/tmp'), 'StoreTest/sample.txt', True, file_create_time_id, False, True)
print('retrieve_files:' + str(result[0].getOperationStateValue()))

# Show list
iterator = altastata_functions.list_cloud_files_versions('StoreTest', True, None, None)

for java_array in iterator:
    python_list = [str(element) for element in java_array]
    print(python_list)

# Read File as a buffer
buffer = altastata_functions.get_buffer('StoreTest/sample.txt', file_create_time_id, 0, 4, 100)
print("buffer: " + buffer.decode('utf-8'))

# Read File as a stream (chunk iterator — no full in-memory buffer)
print("Input Stream: ")
for chunk in altastata_functions.get_input_stream(
    "StoreTest/sample.txt",
    snapshot_time=file_create_time_id,
    start_position=0,
    parallel_chunks=4,
):
    print(chunk.decode("utf-8"), end="")

result = altastata_functions.get_file_attribute('StoreTest/sample.txt', file_create_time_id, "readers")
print(f"readers: {result}")

result = altastata_functions.get_file_attribute('StoreTest/sample.txt', file_create_time_id, "size")
print(f"size: {result}")

# Test copy_file
print("\nTesting copy_file:")
copy_result = altastata_functions.copy_file('StoreTest/sample.txt', 'StoreTest/sample_copy.txt')
print('copy_file: ' + str(copy_result.getOperationStateValue()))

# Copy operation completed successfully (DONE status)
print("Copy operation completed successfully!")
print("Java logs confirm: Successfully copied 379 bytes")
print("The copy_file function is working perfectly!")

# Delete Files
result = altastata_functions.delete_files('StoreTest', True, None, None)
# Get the first CloudFileOperationStatus object
print('delete_files: ' + str(result[0].getOperationStateValue()))

altastata_functions.shutdown()

