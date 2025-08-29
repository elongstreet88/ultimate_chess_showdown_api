import subprocess
import sys
from typing import Dict
from pydantic import SecretStr

def run_command(
    cmd: str,
    check: bool = False,
    capture_output: bool = False,
    text: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=text
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Command failed: {e}")
            sys.exit(1)
        raise e

def fetch_all_secrets() -> Dict[str, SecretStr]:
    # RUN#
    # infisical init 
    cmd: str = f"infisical secrets --path='/ucs' --plain"
    result: subprocess.CompletedProcess[str] = run_command(cmd, capture_output=True)

    if result.returncode != 0:
        print("❌ Failed to fetch secrets.")
        sys.exit(1)

    secrets_dict: Dict[str, SecretStr] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if "=" in line:
            key, value = line.split("=", 1)
            secrets_dict[key.strip()] = SecretStr(value.strip())

    if not secrets_dict:
        print("❌ No secrets retrieved.")
        sys.exit(1)

    return secrets_dict

if __name__ == "__main__":
    secrets: Dict[str, SecretStr] = fetch_all_secrets()
    for key, value in secrets.items():
        print(f"{key} = {value}")
