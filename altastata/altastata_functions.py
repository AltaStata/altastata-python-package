from .grpc_client import AltaStataGrpcClient, GrpcEndpoint
from .s3_bridge import S3BridgeMixin

from typing import List, Any, Optional, Callable

import threading
import queue
import warnings


def _warn_deprecated_factory_kwargs(kwargs: dict, *, stacklevel: int = 3) -> None:
    """Accept and warn on removed factory kwargs so old call sites keep working."""
    if "transport" in kwargs:
        warnings.warn(
            "transport= is ignored; AltaStataFunctions always uses gRPC. "
            "Remove the argument from your call site.",
            DeprecationWarning,
            stacklevel=stacklevel,
        )
        kwargs.pop("transport")
    if "grpc_setup_port" in kwargs:
        warnings.warn(
            "grpc_setup_port= is ignored (AuthService.LoginV2 uses grpc_endpoint). "
            "Remove the argument from your call site.",
            DeprecationWarning,
            stacklevel=stacklevel,
        )
        kwargs.pop("grpc_setup_port")
    if kwargs:
        raise TypeError(
            f"unexpected keyword argument(s): {', '.join(sorted(kwargs))}"
        )


class AltaStataEventListener:
    """
    Python implementation of the Java AltaStataEventListener interface.
    This class receives events from the Java side and forwards them to a Python callback.
    """

    def __init__(self, callback: Callable[[str, Any], None]):
        """
        Initialize the event listener with a Python callback function.

        Args:
            callback: A function that takes (event_name: str, data: Any) as parameters
        """
        self.callback = callback
        self._event_queue = queue.Queue()  # Queue for events
        self._processing = False
        self._lock = threading.Lock()  # Thread synchronization

    def notify(self, altastata_event):
        """
        Called by Java when an event occurs.
        This method is thread-safe to handle concurrent events.

        Args:
            altastata_event: Java AltaStataEvent object
        """
        # Serialize event processing to prevent race conditions
        with self._lock:
            try:
                event_name = altastata_event.getEventName()
                data = altastata_event.getData()

                # Convert data to Python-friendly format if possible
                if data is not None:
                    data = str(data)

                # Call the Python callback
                self.callback(event_name, data)
            except Exception as e:
                print(f"Error in event listener callback: {e}")

    class Java:
        implements = ["com.altastata.api.AltaStataEventListener"]


class AltaStataFunctions(S3BridgeMixin):
    def __init__(
        self,
        *,
        grpc_client: Optional[AltaStataGrpcClient] = None,
    ):
        """
        Base initialization. This should not be called directly.
        Use from_account_dir or from_credentials instead.
        """
        # Kept for callers that still branch on ``.transport`` (always gRPC).
        self.transport = "grpc"
        self.grpc_client = grpc_client
        self._event_listeners = []  # Track registered listeners

        # Material the S3 boto3 helper needs to drive the admin bootstrap
        # PUTs (setUserProperties / setPrivateKey / setPassword) without
        # asking the caller to repeat what they already gave us.
        # Populated by from_account_dir / from_credentials below.
        self._account_dir_path: Optional[str] = None
        self._user_properties: Optional[str] = None
        self._private_key_encrypted: Optional[str] = None
        self._cached_password: Optional[str] = None
        # Cache of bootstrapped S3 credentials keyed by endpoint URL. The
        # access/secret pair never changes for a given (endpoint, user) so a
        # second `s3_credentials()` / `boto3_s3()` call is a dict lookup.
        self._s3_credentials_cache: dict = {}

    @classmethod
    def from_account_dir(
        cls,
        account_dir_path,
        *,
        password: Optional[str] = None,
        user_name: Optional[str] = None,
        grpc_endpoint: Optional[GrpcEndpoint] = None,
        grpc_auto_start_server: bool = True,
        **deprecated,
    ):
        """
        Create an instance using account directory path.

        Args:
            account_dir_path (str): Path to the account directory
            password: Account password (empty string for HPCS/HSM).
            user_name: Optional override for the login user name.
            grpc_endpoint: Optional gRPC target (defaults to localhost:9877).
            grpc_auto_start_server: When True, start the bundled Java gateway
                if the gRPC port is not already listening.

        Returns:
            AltaStataFunctions: New instance initialized with account directory
        """
        _warn_deprecated_factory_kwargs(deprecated)
        endpoint = grpc_endpoint or GrpcEndpoint()
        client = AltaStataGrpcClient.from_account_dir(
            account_dir_path=account_dir_path,
            password=password,
            user_name=user_name,
            endpoint=endpoint,
            auto_start_server=grpc_auto_start_server,
        )
        instance = cls(grpc_client=client)
        instance._account_dir_path = account_dir_path
        instance._cached_password = password
        return instance

    @classmethod
    def from_credentials(
        cls,
        user_properties,
        private_key_encrypted,
        *,
        password: Optional[str] = None,
        user_name: Optional[str] = None,
        grpc_endpoint: Optional[GrpcEndpoint] = None,
        grpc_auto_start_server: bool = True,
        **deprecated,
    ):
        """
        Create an instance using user properties and a single RSA private key.

        Community shorthand for :meth:`from_upload` with
        ``{"private.key": private_key_encrypted}``. For Enterprise / eval
        kits use :meth:`from_upload` (include ``license.jwt`` + ``org-ca.pem``)
        or :meth:`from_account_dir`.
        """
        _warn_deprecated_factory_kwargs(deprecated)
        account_files = {}
        if private_key_encrypted:
            account_files["private.key"] = (
                private_key_encrypted.encode("utf-8")
                if isinstance(private_key_encrypted, str)
                else private_key_encrypted
            )
        return cls.from_upload(
            user_properties,
            account_files,
            password=password,
            user_name=user_name,
            grpc_endpoint=grpc_endpoint,
            grpc_auto_start_server=grpc_auto_start_server,
        )

    @classmethod
    def from_upload(
        cls,
        user_properties,
        account_files,
        *,
        password: Optional[str] = None,
        user_name: Optional[str] = None,
        grpc_endpoint: Optional[GrpcEndpoint] = None,
        grpc_auto_start_server: bool = True,
        **deprecated,
    ):
        """
        Create an instance via LoginV2 upload map (basename → content).

        Args:
            user_properties: Raw ``*user.properties`` text.
            account_files: Dict of basename → bytes/str (``private.key``,
                ``license.jwt``, ``org-ca.pem``, …).
        """
        _warn_deprecated_factory_kwargs(deprecated)
        endpoint = grpc_endpoint or GrpcEndpoint()
        client = AltaStataGrpcClient.from_upload(
            user_properties=user_properties,
            account_files=account_files or {},
            password=password,
            user_name=user_name,
            endpoint=endpoint,
            auto_start_server=grpc_auto_start_server,
        )
        instance = cls(grpc_client=client)
        instance._user_properties = user_properties
        instance._account_files = dict(account_files or {})
        pem = (account_files or {}).get("private.key")
        if isinstance(pem, bytes):
            instance._private_key_encrypted = pem.decode("utf-8", errors="replace")
        elif isinstance(pem, str):
            instance._private_key_encrypted = pem
        instance._cached_password = password
        return instance

    def convert_java_list_to_python(self, java_list):
        return list(java_list) if java_list is not None else []

    def set_password(self, account_password: str):
        # Remember the plaintext so s3_credentials() / boto3_s3() / install_aws_env()
        # can drive the S3 admin PUTs without forcing the caller to retype it.
        self._cached_password = account_password
        return self.grpc_client.set_password(account_password)

    def create_file(self, cloud_file_path, buffer=None):
        """
        Create a new file version on cloud and add the buffer (may be empty).
        This operation is fast but does not guarantee streaming order.

        Args:
            cloud_file_path (str): The file path on the cloud
            buffer (bytes, optional): Initial buffer to store in the file. Defaults to None (empty buffer).

        Returns:
            CloudFileOperationStatus: Status of the file creation operation
        """
        if buffer is None:
            buffer = bytes()
        return self.grpc_client.create_file(cloud_file_path, buffer)

    def append_buffer_to_file(self, cloud_file_path, buffer, snapshot_time=None):
        """
        Append the buffer as an output stream to the File version.

        Args:
            cloud_file_path (str): The file path on the cloud
            buffer (bytes): The buffer to append
            snapshot_time (Long, optional): File version creation time. Defaults to None (current time).

        Raises:
            IOException: If there is an error during the append operation
        """
        return self.grpc_client.append_buffer_to_file(
            cloud_file_path, buffer, snapshot_time=snapshot_time
        )

    def store(self, localFilesOrDirectories: List[str], localFSPrefix: str, cloudPathPrefix: str, waitUntilDone: bool):
        return self.grpc_client.store(
            localFilesOrDirectories, localFSPrefix, cloudPathPrefix, waitUntilDone
        )

    def retrieve_files(self, output_dir, cloud_path_prefix, including_subdirectories, snapshot_time, is_streaming, wait_until_done):
        return self.grpc_client.retrieve_files(
            output_dir,
            cloud_path_prefix,
            including_subdirectories,
            snapshot_time,
            is_streaming,
            wait_until_done,
        )

    def delete_files(self, cloud_path_prefix, including_subdirectories, time_interval_start, time_interval_end):
        return self.grpc_client.delete_files(
            cloud_path_prefix,
            including_subdirectories=including_subdirectories,
            time_interval_start=time_interval_start,
            time_interval_end=time_interval_end,
        )

    def share_files(self, cloud_path_prefix: str, including_subdirectories: bool, time_interval_start: str, time_interval_end: str, users: list) -> list:
        return self.grpc_client.share_files(
            cloud_path_prefix, including_subdirectories, time_interval_start, time_interval_end, users
        )

    def revoke_reader_access(self, cloud_path_prefix: str, including_subdirectories: bool, time_interval_start: str, time_interval_end: str, readers_to_revoke: list) -> list:
        """
        Revoke reader access for the given users from files that match the cloud path and time range.
        Callable by the data owner or the custodian. The file is kept; only the listed readers lose access.

        Args:
            cloud_path_prefix: Prefix that matches the cloud files (e.g. "MyDir/file.txt" or "MyDir/").
            including_subdirectories: If True, include files in subdirectories.
            time_interval_start: Filter file versions with creation time >= this value. Use None to ignore.
            time_interval_end: Filter file versions with creation time <= this value. Use None to ignore.
            readers_to_revoke: List of user names to revoke access from.

        Returns:
            List of CloudFileOperationStatus for each revoked file version.
        """
        return self.grpc_client.revoke_reader_access(
            cloud_path_prefix,
            including_subdirectories,
            time_interval_start,
            time_interval_end,
            readers_to_revoke,
        )

    def list_cloud_files_versions(self, cloudPathPrefix, includingSubdirectories, timeIntervalStart, timeIntervalEnd):
        return self.grpc_client.list_cloud_files_versions(
            cloudPathPrefix,
            including_subdirectories=includingSubdirectories,
            time_interval_start=timeIntervalStart,
            time_interval_end=timeIntervalEnd,
        )

    def get_buffer(self, cloudFilePath, snapshotTime, startPosition, howManyChunksInParallel, size, trust_cached_size=False):
        """Read file content from cloud storage as ``bytes``.

        Args:
            cloudFilePath: Cloud file path (may include ✹ version suffix).
            snapshotTime: Version timestamp, or None for latest.
            startPosition: Byte offset to start reading from.
            howManyChunksInParallel: Number of chunks to download concurrently.
            size: Expected file size in bytes.
            trust_cached_size: When True, declare this file's content immutable
                (write-once) so the per-open fresh cloud GET of the ``size``
                attribute is skipped and the cached value is trusted. Big win
                for read-many workloads (ML dataset epochs); leave False (the
                default) for mutable files.

        Returns:
            bytes: File content.

        Strategy:
            Uses gRPC unary for small payloads and gRPC stream assembly for
            large/unknown payloads (implemented in AltaStataGrpcClient).
        """
        return self.grpc_client.get_buffer(
            cloudFilePath,
            size=size,
            snapshot_time=0 if snapshotTime is None else snapshotTime,
            start_position=startPosition,
            parallel_chunks=howManyChunksInParallel,
            trust_cached_size=trust_cached_size,
        )

    def get_java_input_stream(self, cloud_file_path, snapshot_time, start_position, how_many_chunks_in_parallel):
        """Open a stream iterator for the given cloud file."""
        return self.grpc_client.get_java_input_stream(
            cloud_file_path, snapshot_time, start_position, how_many_chunks_in_parallel,
        )

    def get_file_attribute(self, cloud_file_path, snapshot_time, name):
        """
        Get file attribute from Altastata file system.
        """
        return self.grpc_client.get_file_attribute(cloud_file_path, snapshot_time, name)

    def copy_file(self, from_cloud_file_path: str, to_cloud_file_path: str):
        """
        Copy a file from one cloud path to another.

        Args:
            from_cloud_file_path (str): The source file path on the cloud
            to_cloud_file_path (str): The destination file path on the cloud

        Returns:
            CloudFileOperationStatus: Status of the copy operation
        """
        return self.grpc_client.copy_file(from_cloud_file_path, to_cloud_file_path)

    def add_event_listener(self, callback: Callable[[str, Any], None]) -> AltaStataEventListener:
        """
        Add an event listener to receive file share/delete/etc events.

        Args:
            callback: A function that takes (event_name: str, data: Any) as parameters.
                      Will be called when events occur (e.g., SHARE, DELETE)

        Returns:
            AltaStataEventListener: The listener object (keep reference to remove later)

        Example:
            def my_event_handler(event_name, data):
                print(f"Event: {event_name}, Data: {data}")
                if event_name == "SHARE":
                    # Handle file sharing event
                    pass
                elif event_name == "DELETE":
                    # Handle file deletion event
                    pass

            listener = altastata.add_event_listener(my_event_handler)
            # ... do work ...
            altastata.remove_event_listener(listener)
        """
        return self.grpc_client.add_event_listener(callback)

    def remove_event_listener(self, listener: AltaStataEventListener):
        """
        Remove a previously registered event listener.

        Args:
            listener: The listener object returned by add_event_listener()
        """
        return self.grpc_client.remove_event_listener(listener)

    def remove_all_event_listeners(self):
        """
        Remove all registered event listeners.
        """
        return self.grpc_client.remove_all_event_listeners()

    def shutdown(self):
        if self.grpc_client is not None:
            self.grpc_client.close()
