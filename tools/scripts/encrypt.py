import sys
import uuid
import base64
import os
from pathlib import Path
from cryptography.fernet import Fernet
from pydantic import SecretStr
sys.path.append(str(Path(__file__).resolve().parents[2]))
from tools.scripts.infisical import fetch_all_secrets

ENCRYPTION_PREFIX = "ENC__"
ENCRYPTION_KEY_ENV_VAR = "ENV_ENCRYPTION_KEY"

def get_env_encryption_key() -> bytes:
    """Generate a machine-specific key based on ENV_ENCRYPTION_KEY or MAC address."""
    try:
        # Try to parse the env var as an integer (e.g., output of uuid.getnode())
        key = int(os.environ.get(ENCRYPTION_KEY_ENV_VAR, "0"))
    except (TypeError, ValueError):
        # Fallback to actual machine MAC address
        key = uuid.getnode()

    # Convert to 6-byte representation
    mac_bytes = key.to_bytes(6, 'big', signed=False)

    # Pad to 32 bytes for Fernet
    padded = mac_bytes.ljust(32, b'\0')

    # Base64 encode as Fernet key
    key = base64.urlsafe_b64encode(padded)
    return key

def encrypt_secret(secret: SecretStr, fernet: Fernet) -> str:
    """Encrypt a SecretStr using Fernet and add prefix."""
    plaintext = secret.get_secret_value().encode()
    encrypted = fernet.encrypt(plaintext).decode()
    return ENCRYPTION_PREFIX + encrypted

def decrypt_secret(encrypted_value: str, fernet: Fernet) -> SecretStr:
    """Decrypt an encrypted secret."""
    if not encrypted_value.startswith(ENCRYPTION_PREFIX):
        raise ValueError("Value is not encrypted.")
    encrypted_body = encrypted_value[len(ENCRYPTION_PREFIX):]
    plaintext = fernet.decrypt(encrypted_body.encode()).decode()
    return SecretStr(plaintext)

def encrypt_secrets_to_file(secrets: dict[str, SecretStr], output_path: str = ".env"):
    """Encrypt secrets and write them to a file."""
    key = get_env_encryption_key()
    fernet = Fernet(key)

    lines = []
    for name, secret in secrets.items():
        encrypted_value = encrypt_secret(secret, fernet)
        lines.append(f"{name}={encrypted_value}")

    Path(output_path).write_text("\n".join(lines))

def decrypt_environment_vars_in_place() -> None:
    """Decrypt encrypted environment variables directly in os.environ."""
    key = get_env_encryption_key()
    fernet = Fernet(key)

    for name, value in os.environ.items():
        if value.startswith(ENCRYPTION_PREFIX):
            try:
                decrypted_secret = decrypt_secret(value, fernet)
                os.environ[name] = decrypted_secret.get_secret_value()
            except Exception as e:
                print(f"❌ Failed to decrypt {name}: {e}")
                sys.exit(1)

if __name__ == "__main__":
    # Example usage
    secrets = fetch_all_secrets()
    encrypt_secrets_to_file(secrets, ".env")