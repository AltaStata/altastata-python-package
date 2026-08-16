import os
from pathlib import Path

from altastata import AltaStataFunctions

home = Path.home()
account = home / ".altastata" / "accounts" / "amazon.rsa.alice222"
desktop = home / "Desktop"
sample_ini = desktop / "desktop.ini"
sample_reg = desktop / "sample.reg"

altastata_functions = AltaStataFunctions.from_account_dir(str(account))
altastata_functions.set_password(os.environ.get("ALTASTATA_PASSWORD", ""))

# Store
result = altastata_functions.store(
    [str(sample_ini), str(sample_reg)],
    str(desktop),
    "StoreTest",
    True,
)

# Get the first CloudFileOperationStatus object
print("store: " + str(result[0].getOperationStateValue()) + " " + result[0].getCloudFileCreateTime())

file_create_time_id = int(result[0].getCloudFileCreateTime())

users = ["bob123", "catrina777"]
result = altastata_functions.share_files("StoreTest/desktop.ini", True, None, None, users)
print("share_files:" + str(result[0].getOperationStateValue()))

# Retrieve file
result = altastata_functions.retrieve_files(
    str(desktop / "tmp"),
    "StoreTest/desktop.ini",
    True,
    file_create_time_id,
    False,
    True,
)
print("retrieve_files:" + str(result[0].getOperationStateValue()))

# Show list
iterator = altastata_functions.list_cloud_files_versions("StoreTest", True, None, None)

for java_array in iterator:
    python_list = [str(element) for element in java_array]
    print(python_list)

# Read File as a buffer
buffer = altastata_functions.get_buffer("StoreTest/desktop.ini", file_create_time_id, 0, 4, 30)
print(buffer)

# Read File as a stream (chunk iterator — no full in-memory buffer)
print("Input Stream: ")
for chunk in altastata_functions.get_input_stream(
    "StoreTest/desktop.ini",
    snapshot_time=file_create_time_id,
    start_position=0,
    parallel_chunks=4,
):
    print(chunk.decode("utf-8"), end="")

result = altastata_functions.get_file_attribute("StoreTest/desktop.ini", file_create_time_id, "readers")
print(f"readers: {result}")

result = altastata_functions.get_file_attribute("StoreTest/desktop.ini", file_create_time_id, "size")
print(f"size: {result}")


# Delete Files
result = altastata_functions.delete_files("StoreTest", True, None, None)
# Get the first CloudFileOperationStatus object
print("delete_files: " + str(result[0].getOperationStateValue()))

altastata_functions.shutdown()
