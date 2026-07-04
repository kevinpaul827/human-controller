import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = ROOT / "frontend" / "dist"
APP_FRONTEND_DIR = (
    ROOT
    / "dist"
    / "Human Controller.app"
    / "Contents"
    / "Resources"
    / "frontend"
    / "dist"
)


def main() -> int:
    if sys.platform != "darwin":
        print("This sync helper is only intended for macOS.")
        return 1

    if not FRONTEND_DIST_DIR.exists():
        print("Frontend build is missing. Run `npm run build --prefix frontend` first.")
        return 1

    if not APP_FRONTEND_DIR.parent.parent.exists():
        print("macOS app bundle is missing. Run `make macos-app` first.")
        return 1

    if APP_FRONTEND_DIR.exists():
        shutil.rmtree(APP_FRONTEND_DIR)

    shutil.copytree(FRONTEND_DIST_DIR, APP_FRONTEND_DIR)
    print(f"Synced frontend build into: {APP_FRONTEND_DIR}")
    print('Reopen the app with: open "dist/Human Controller.app"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
