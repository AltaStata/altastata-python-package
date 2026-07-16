"""Example AltaStata setup for TensorFlow demos.

Do not commit real credentials. Point this at a local account folder, or set:

  export ALTASTATA_ACCOUNT_DIR="$HOME/.altastata/accounts/<your-account>"
  export ALTASTATA_PASSWORD="..."   # RSA/PQC only; leave unset for HPCS/HSM
"""

import os
from pathlib import Path

from altastata.altastata_functions import AltaStataFunctions
from altastata.altastata_tensorflow_dataset import register_altastata_functions_for_tensorflow

ACCOUNT_DIR = Path(
    os.environ.get(
        "ALTASTATA_ACCOUNT_DIR",
        Path.home() / ".altastata" / "accounts" / "amazon.rsa.demo",
    )
)
PASSWORD = os.environ.get("ALTASTATA_PASSWORD", "")
REGISTRY_ID = os.environ.get("ALTASTATA_REGISTRY_ID", "demo_rsa")

if not ACCOUNT_DIR.is_dir():
    raise FileNotFoundError(
        f"Account directory not found: {ACCOUNT_DIR}\n"
        "Copy your AltaStata account folder there, or set ALTASTATA_ACCOUNT_DIR."
    )

altastata_functions = AltaStataFunctions.from_account_dir(
    str(ACCOUNT_DIR),
    password=PASSWORD or None,
)
register_altastata_functions_for_tensorflow(altastata_functions, REGISTRY_ID)
