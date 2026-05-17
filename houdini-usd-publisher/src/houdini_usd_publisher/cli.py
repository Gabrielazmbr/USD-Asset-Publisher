
import argparse
import sys
import tempfile
from pathlib import Path

from houdini_usd_publisher.core.config import ConfigError, PublishConfig
from houdini_usd_publisher.core.publisher import Publisher

DEFAULT_CONFIG = Path(__file__).parent.parent.parent / "config" / "publish_config.json"

"""
CLI entry point for the USD Asset Publisher.

Usage:
    hython -m houdini_usd_publisher.cli --asset AssetName --version v001

For development and testing without Houdini:
    uv run publish --asset AssetName --version v001 --dry-run
"""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="publish",
        description="Validate and publish a USD asset from a Houdini LOP network.",
    )
    parser.add_argument(
        "--asset",
        required=True,
        help="Asset name e.g. 'AssetName'",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version string e.g. 'v001'",
    )
    parser.add_argument(
        "--lop",
        default="/stage/finalize",
        help="Houdini path to the LOP node (default: /stage/finalize)",
    )
    parser.add_argument(
        "--publish-root",
        default=str(Path.cwd() / "assets"),
        help="Root directory for published assets (default: ./assets/)",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to publish_config.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validation only — does not package or write to publish root",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically fix correctable validation errors before publishing",
    )
    return parser.parse_args()


def main() -> int:
    # Parse arguments
    args = parse_args()

    # Load config
    try:
        config = PublishConfig(args.config)
    except ConfigError as e:
        print(f"ERROR config: {e}", file=sys.stderr)
        # Exit code 1
        return 1

    # Create publisher
    publisher = Publisher(config, publish_root=args.publish_root)

    if args.dry_run:
        print(f"Dry run — validating only, nothing will be published")

    # Working directory for temporary files
    with tempfile.TemporaryDirectory() as tmp:
        # Run publish
        result = publisher.publish(
            lop_node_path=args.lop,
            asset_name=args.asset,
            version=args.version,
            tmp_dir=tmp,
            dry_run=args.dry_run,
            auto_fix=args.auto_fix,
        )

    if args.dry_run:
        print("Dry run — validating only, nothing will be published")
    # Summary Print
    print(result.summary())
    # Exit code
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
