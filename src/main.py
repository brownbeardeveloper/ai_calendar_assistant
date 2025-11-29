import sys
from bootstrap.container import create_app


def main() -> None:
    """Application entrypoint."""    
    try:
        app = create_app()
        app.run()
        
    except KeyboardInterrupt:
        app.logger.info("Interrupted by user. Exiting.")
        sys.exit(0)
        
    except Exception:
        app.logger.exception("Unhandled application error.")
        sys.exit(1)


if __name__ == "__main__":
    main()