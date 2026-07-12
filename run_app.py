import sys

from app.main import main as app_main
from backend.dev_server import main as backend_main


BACKEND_HELPER_FLAG = "--backend-helper"


def main():
    if BACKEND_HELPER_FLAG in sys.argv[1:]:
        backend_main()
        return

    app_main()


if __name__ == "__main__":
    main()
