#!/usr/bin/env python3
"""
Production server runner for Nazmito Healthcare XML API.

This script provides different ways to run the FastAPI server for different environments.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import XMLProcessor
sys.path.append(str(Path(__file__).parent.parent))


def run_development():
    """Run development server with auto-reload."""
    import uvicorn

    print("🚀 Starting Nazmito Healthcare XML API - Development Mode")
    print("📖 API Documentation: http://localhost:8000/api/docs")
    print("🔄 Auto-reload enabled")
    print("-" * 60)

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        reload_dirs=["api", "pipelines"],
    )


def run_production(host="0.0.0.0", port=8000, workers=1):
    """Run production server with gunicorn."""
    try:
        import uvicorn

        print("🏭 Starting Nazmito Healthcare XML API - Production Mode")
        print(f"🌐 Server: http://{host}:{port}")
        print(f"👷 Workers: {workers}")
        print(f"📖 API Documentation: http://{host}:{port}/api/docs")
        print("-" * 60)

        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info",
            access_log=True,
        )
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn[standard]")
        sys.exit(1)


def run_docker():
    """Run server optimized for Docker container."""
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    print("🐳 Starting Nazmito Healthcare XML API - Docker Mode")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"👷 Workers: {workers}")
    print("-" * 60)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
    )


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Nazmito Healthcare XML API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_server.py                     # Development mode (default)
  python run_server.py --mode production   # Production mode
  python run_server.py --mode docker       # Docker mode
  python run_server.py --mode production --host 127.0.0.1 --port 8080 --workers 4
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["development", "production", "docker"],
        default="development",
        help="Server mode (default: development)",
    )

    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (production mode only, default: 1)",
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    os.makedirs("api/logs", exist_ok=True)

    try:
        if args.mode == "development":
            run_development()
        elif args.mode == "production":
            run_production(args.host, args.port, args.workers)
        elif args.mode == "docker":
            run_docker()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
