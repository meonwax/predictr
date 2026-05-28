#!/usr/bin/env python3
"""Fetch pinned vendor JS/CSS into ``app/static/vendor/``.

These third-party assets (Bootstrap, Bootstrap Icons, HTMX) are intentionally
*not* committed to git: they're bytes-for-bytes reproducible from the URLs +
SHA-256 hashes below, and committing them just bloats the repo and pollutes
diffs when we bump versions.

Usage::

    uv run python scripts/fetch_vendor_assets.py

Re-runs are idempotent: if a destination file already exists and its
SHA-256 matches, the file is left alone (no network call).

To bump a version:
    1. Update the relevant entry below (URL + filename).
    2. Run this script *without* updating the hash - it will fail loudly with
       the new digest.
    3. Copy the new digest into the entry and run again.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = PROJECT_ROOT / "app" / "static" / "vendor"


@dataclass(frozen=True, slots=True)
class VendorAsset:
    name: str
    url: str
    rel_path: str  # relative to VENDOR_ROOT
    sha256: str

    @property
    def dest(self) -> Path:
        return VENDOR_ROOT / self.rel_path


# Pinned vendor assets. Bump version by updating url + rel_path + sha256.
ASSETS: tuple[VendorAsset, ...] = (
    VendorAsset(
        name="Bootstrap CSS",
        url="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        rel_path="bootstrap-5.3.3/css/bootstrap.min.css",
        sha256="3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8",
    ),
    VendorAsset(
        name="Bootstrap JS bundle",
        url="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        rel_path="bootstrap-5.3.3/js/bootstrap.bundle.min.js",
        sha256="0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c",
    ),
    VendorAsset(
        name="Bootstrap Icons CSS",
        url="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
        rel_path="bootstrap-icons-1.11.3/bootstrap-icons.css",
        sha256="4ffa6bea4304d2eda418683f56261685ed47bf00995039f27e5ad62d53938d2d",
    ),
    VendorAsset(
        name="Bootstrap Icons woff",
        url="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff",
        rel_path="bootstrap-icons-1.11.3/fonts/bootstrap-icons.woff",
        sha256="bb1de989b83970f6f4e54de1cd974c5cba55b73582da5e1b225a6d0edf029483",
    ),
    VendorAsset(
        name="Bootstrap Icons woff2",
        url="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2",
        rel_path="bootstrap-icons-1.11.3/fonts/bootstrap-icons.woff2",
        sha256="476adf42b40325098fcfa8b36ab3e769186bb4f6ce6a249753e2e1a9c22bf99e",
    ),
    VendorAsset(
        name="HTMX",
        url="https://cdn.jsdelivr.net/npm/htmx.org@2.0.3/dist/htmx.min.js",
        rel_path="htmx-2.0.3/htmx.min.js",
        sha256="491955cd1810747d7d7b9ccb936400afb760e06d25d53e4572b64b6563b2784e",
    ),
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


#: Identifies this script to upstream CDNs and to Wikimedia.
#: Wikimedia's User-Agent policy requires a descriptive UA and a contact URL;
#: the default urllib UA gets a hard 403. See:
#: https://meta.wikimedia.org/wiki/User-Agent_policy
_USER_AGENT = "predictr-vendor-fetch/1.0 (+https://github.com/meonwax/predictr) python-urllib"


def _fetch(url: str, timeout: float = 30.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - hardcoded https URLs
        return response.read()


def _ensure(asset: VendorAsset, *, verbose: bool = True) -> str:
    """Make sure *asset* is on disk with the expected hash.

    Returns one of ``"cached"`` (already present, hash matched),
    ``"downloaded"`` (fetched fresh), or raises ``RuntimeError`` on a
    hash mismatch.
    """
    if asset.dest.is_file():
        digest = _sha256_file(asset.dest)
        if digest == asset.sha256:
            if verbose:
                print(f"  cached      {asset.rel_path}")
            return "cached"
        if verbose:
            print(
                f"  re-fetch    {asset.rel_path}  "
                f"(on-disk hash {digest[:12]}... != expected {asset.sha256[:12]}...)"
            )

    asset.dest.parent.mkdir(parents=True, exist_ok=True)
    data = _fetch(asset.url)
    digest = hashlib.sha256(data).hexdigest()
    if digest != asset.sha256:
        raise RuntimeError(
            f"SHA-256 mismatch for {asset.name} ({asset.url}):\n"
            f"  expected: {asset.sha256}\n"
            f"  received: {digest}\n"
            f"If this is intentional (version bump), update the entry in "
            f"{Path(__file__).name}."
        )
    asset.dest.write_bytes(data)
    if verbose:
        print(f"  downloaded  {asset.rel_path}  ({len(data)} bytes)")
    return "downloaded"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fetch_vendor_assets.py",
        description=__doc__.splitlines()[0] if __doc__ else None,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print errors.",
    )
    args = parser.parse_args(argv)
    verbose = not args.quiet

    if verbose:
        print(f"Fetching {len(ASSETS)} vendor asset(s) into {VENDOR_ROOT}")

    cached = downloaded = 0
    for asset in ASSETS:
        try:
            result = _ensure(asset, verbose=verbose)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(
                f"error: failed to fetch {asset.url}: {exc}",
                file=sys.stderr,
            )
            return 2
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        if result == "cached":
            cached += 1
        else:
            downloaded += 1

    if verbose:
        print(f"\nDone. {cached} cached, {downloaded} downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
