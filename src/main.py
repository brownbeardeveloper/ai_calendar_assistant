import sys, traceback
from bootstrap.container import create_app
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    """Application entrypoint."""    
    app = None
    try:
        app = create_app()
        app.run()
        
    except KeyboardInterrupt:
        if app:
            app.logger.info("Interrupted by user. Exiting.")
        sys.exit(0)
        
    except Exception:
        if app:
            app.logger.exception("Unhandled application error.")
        else:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()