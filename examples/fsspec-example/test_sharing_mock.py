import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altastata.fsspec import AltaStataFileSystem

class MockAltaStataFunctions:
    def __init__(self):
        self.grpc_client = self
        self._attrs = {"Public/test.txt": {"readers": "bob123"}}
        self._size = "100"
        
    def list_users(self):
        return [
            {"user_name": "bob123", "initialized": True},
            {"user_name": "alice222", "initialized": True},
            {"user_name": "uninit_user", "initialized": False}
        ]
        
    def share_files(self, path, subdirs, start, end, users):
        self._attrs[path]["readers"] = " ".join(["bob123"] + users)
        return [{"status": "OK"}]
        
    def revoke_reader_access(self, path, subdirs, start, end, users):
        self._attrs[path]["readers"] = "bob123"
        return [{"status": "OK"}]
        
    def get_file_attribute(self, path, time, attr):
        if attr == "size": return self._size
        if attr == "readers": return self._attrs.get(path, {}).get("readers", "")
        return ""

def main():
    fs = AltaStataFileSystem(MockAltaStataFunctions(), "bob123")
    users = fs.list_users()
    print(f"Users (excluding self): {users}")
    assert users == ["alice222", "uninit_user"]
    print("✅ OK")

if __name__ == "__main__":
    main()
