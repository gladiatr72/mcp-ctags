#!/usr/bin/env python3
"""MCP Ctags Server Entry Point

Standalone entry point for the MCP ctags server.
"""

import sys
import argparse
from pathlib import Path

from .ctags_server import mcp


def main():
    """Main entry point for the MCP ctags server."""
    parser = argparse.ArgumentParser(
        description="MCP server for ctags-based code navigation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ctags-mcp                    # Run MCP server with stdio transport
  ctags-mcp --help            # Show this help message

For Claude Desktop integration, add this to claude_desktop_config.json:
{
  "mcpServers": {
    "ctags": {
      "command": "ctags-mcp"
    }
  }
}
        """,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )

    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path.cwd(),
        help="Working directory to search for tags file (default: current directory)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="ctags-mcp 0.1.0",
    )

    args = parser.parse_args()

    # Change to working directory if specified
    if args.working_dir != Path.cwd():
        try:
            args.working_dir.resolve(strict=True)
        except (OSError, FileNotFoundError):
            print(
                f"Error: Working directory does not exist: {args.working_dir}",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        # Run the MCP server
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nMCP server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
