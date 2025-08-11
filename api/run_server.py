#!/usr/bin/env python3
"""
Production server runner for Nazmito Healthcare XML API.

This script provides different ways to run the FastAPI server for different environments.
"""

import os
import sys
import argparse

from preauth_system.utils import get_config


def _get_server_cfg():
    cfg = get_config()
    server = cfg.get("server", {}) if isinstance(cfg, dict) else {}
    return {
        "host": server.get("host"),
        "port": server.get("port"),
        "workers": server.get("workers"),
    }


def run_development():
    """Run development server with auto-reload."""
    import uvicorn

    server_cfg = _get_server_cfg()
    host = server_cfg.get("host") or "127.0.0.1"
    port = int(server_cfg.get("port") or 8000)

    print("🚀 Starting Nazmito Healthcare XML API - Development Mode")
    print(f"📖 API Documentation: http://{host}:{port}/api/docs")
    print("🔄 Auto-reload enabled")
    print("-" * 60)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        access_log=True,
        reload_dirs=["api", "preauth_system"],
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

    server_cfg = _get_server_cfg()
    host = server_cfg.get("host") or os.getenv("HOST", "0.0.0.0")
    port = int(server_cfg.get("port") or os.getenv("PORT", "8000"))
    workers = int(server_cfg.get("workers") or os.getenv("WORKERS", "1"))

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

    if args.mode == "development":
        run_development()
    elif args.mode == "production":
        run_production(host=args.host, port=args.port, workers=args.workers)
    elif args.mode == "docker":
        run_docker()


if __name__ == "__main__":
    main()
