from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    example_path = project_root / ".env.example"
    local_path = project_root / ".env.local"

    if not example_path.exists():
        raise FileNotFoundError(f".env.example was not found at {example_path}")

    if local_path.exists():
        print(".env.local already exists. Skipping file creation.")
    else:
        local_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env.local from .env.example")

    print()
    print("Next steps:")
    print("1) Open .env.local and set OPENWEATHER_API_KEY to your real key.")
    print("2) Run: docker compose up --build")


if __name__ == "__main__":
    main()
