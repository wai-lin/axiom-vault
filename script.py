from pathlib import Path

#!/usr/bin/env python3


def main():
    workspace = Path.cwd()
    for pem_file in workspace.rglob("*.pem"):
        # Skip files inside any .venv directory
        if ".venv" in pem_file.parts:
            continue

        try:
            pem_file.unlink()
            print(f"Deleted: {pem_file}")
        except Exception as e:
            print(f"Error deleting {pem_file}: {e}")


if __name__ == "__main__":
    main()
