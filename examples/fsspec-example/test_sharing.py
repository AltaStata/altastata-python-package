import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altastata.altastata_functions import AltaStataFunctions
from altastata.fsspec import create_filesystem

def main():
    print("Testing fsspec sharing extensions...")
    
    account_dir = os.path.expanduser('~/.altastata/accounts/amazon.rsa.bob123')
    props_path = os.path.join(account_dir, "altastata-myorgrsa444-bob123.user.properties")
    key_path = os.path.join(account_dir, "private.key")
    
    with open(props_path, "r") as f:
        props = f.read()
    with open(key_path, "r") as f:
        key = f.read()
        
    print(f"Using credentials from: {account_dir}")
    alt = AltaStataFunctions.from_credentials(props, key, password="123")
    alt.set_password(os.environ.get("ALTASTATA_PASSWORD", ""))
    
    fs = create_filesystem(alt, "bob123")
    
    # Test list_users
    users = fs.list_users()
    print(f"\n1. list_users(): Found {len(users)} initialized users.")
    print(f"   First few: {users[:5]}")
    
    if len(users) < 2:
        print("Not enough users to test sharing. Need at least 1 other user.")
        return
        
    target_user = next((u for u in users if u != "bob123"), users[0])
    
    # Create test file
    test_file = f"Public/fsspec-share-test-{int(time.time())}.txt"
    alt.create_file(test_file, b"secret data")
    print(f"\nCreated file: {test_file}")
    
    try:
        # Check readers before share
        info = fs.info(test_file)
        print(f"2. Initial readers: '{info['readers']}'")
        
        # Test share
        print(f"\n3. Sharing with {target_user}...")
        res = fs.share(test_file, [target_user])
        print(f"   Share result: {res[0].getOperationStateValue() if res else 'Unknown'}")
        
        # Wait a moment for metadata update
        time.sleep(1)
        info = fs.info(test_file)
        print(f"4. Readers after share: '{info['readers']}'")
        assert target_user in info['readers']
        
        # Test revoke
        print(f"\n5. Revoking from {target_user}...")
        res = fs.revoke(test_file, [target_user])
        print(f"   Revoke result: {res[0].getOperationStateValue() if res else 'Unknown'}")
        
        time.sleep(1)
        info = fs.info(test_file)
        print(f"6. Readers after revoke: '{info['readers']}'")
        assert target_user not in info['readers']
        
        print("\n✅ All sharing tests passed!")
        
    finally:
        # Cleanup
        alt.delete_files(test_file, False, None, None)
        print(f"Deleted {test_file}")

if __name__ == "__main__":
    main()
