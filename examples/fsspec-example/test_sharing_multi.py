import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altastata.fsspec import AltaStataFileSystem
from altastata.altastata_functions import AltaStataFunctions

def main():
    account_dir = os.path.expanduser('~/.altastata/accounts/amazon.rsa.bob123')
    props_path = os.path.join(account_dir, "altastata-myorgrsa444-bob123.user.properties")
    key_path = os.path.join(account_dir, "private.key")
    
    with open(props_path, "r") as f:
        props = f.read()
    with open(key_path, "r") as f:
        key = f.read()
        
    alt = AltaStataFunctions.from_credentials(props, key, password="123")
    alt.set_password(os.environ.get("ALTASTATA_PASSWORD", ""))
    
    fs = AltaStataFileSystem(alt, "bob123")
    
    # 1. Check list_users (should return the 5 other users)
    users = fs.list_users()
    print(f"Other users ({len(users)}): {users}")
    
    # Create two test files under a common prefix
    prefix = "Public/MultiShareTest/"
    f1 = prefix + "doc1.txt"
    f2 = prefix + "doc2.txt"
    alt.create_file(f1, b"doc1")
    alt.create_file(f2, b"doc2")
    
    try:
        # Share BOTH files with TWO users by sharing the prefix
        print("\nSharing prefix 'Public/MultiShareTest/' with ['alice222', 'serge678']...")
        # Since these aren't fully initialized locally, this might throw if it tries to actually do the crypto.
        # But let's see if the Python interface accepts lists as expected.
        try:
            fs.share(prefix, ["alice222", "serge678"])
            print("Share call succeeded.")
        except Exception as e:
            print(f"Share call failed (expected if users lack keys): {e}")
            
    finally:
        alt.delete_files(prefix, True, None, None)
        print("Cleaned up.")

if __name__ == "__main__":
    main()
