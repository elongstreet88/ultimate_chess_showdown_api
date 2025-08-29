from pathlib import Path
import sys
import subprocess #nosec
from typing import Set, get_type_hints
from pydantic import SecretStr, BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.config.settings import AppSettings, app_settings
from tools.logs.logs import get_logger

logger = get_logger(__name__)

def extract_secret_values_from_settings(settings: AppSettings) -> Set[str]:
    secrets = set()

    def collect_secrets(obj, prefix=""):
        if isinstance(obj, SecretStr):
            secrets.add(obj.get_secret_value())
            return

        if isinstance(obj, BaseModel):
            values = obj.dict()
        elif hasattr(obj, "__dict__"):
            values = vars(obj)
        else:
            return

        for key, value in values.items():
            collect_secrets(value, f"{prefix}.{key}" if prefix else key)

    for name in get_type_hints(settings.__class__):
        if name.startswith("_"):
            continue
        value = getattr(settings, name)
        collect_secrets(value, prefix=name)

    return secrets

def scan_git_history_for_secrets(secrets: Set[str]) -> int:
    found = False
    print("🔍 Scanning Git history for secrets...")
    for secret in secrets:
        if not secret:
            continue
        try:
            cmd = f'git --no-pager grep -F -e "{secret}" $(git rev-list --all)'
            result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) #nosec
            if result.stdout.strip():
                print("🛑 Potential secret found in git history!")
                for line in result.stdout.strip().splitlines():
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        commit, file_path, _ = parts
                        print(f"Commit:[{commit}]  File:[{file_path}]  Secret:[{secret[:3]}{'*'*(len(secret)-3)}]")
                    else:
                        print(f"  {line}")
                found = True
        except Exception as e:
            print(f"Error scanning secret: {e}")
    return 1 if found else 0

def main():
    secrets = extract_secret_values_from_settings(app_settings)
    print(f"✅ Collected {len(secrets)} unique SecretStr values.")
    code = scan_git_history_for_secrets(secrets)
    if code:
        print("❌ One or more secrets were found in the git history. Failing build.")
    sys.exit(code)

if __name__ == "__main__":
    main()
