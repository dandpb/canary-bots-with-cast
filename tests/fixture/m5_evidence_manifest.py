"""Publish a final external manifest only after artifact producers/logs are closed."""

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

from canary_brain.persistence_witness import exclusive, sync_directory


def finalize_manifest(paths, destination):
    destination = Path(destination)
    identities = set()
    for stream in (sys.stdout, sys.stderr):
        try:
            item = os.fstat(stream.fileno())
            identities.add((item.st_dev, item.st_ino))
        except (AttributeError, OSError, ValueError):
            pass
    artifacts = {}
    for path in map(Path, paths):
        if path == destination or path.is_symlink():
            raise ValueError("manifest cannot hash itself or symlink inputs")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or (before.st_dev, before.st_ino) in identities
            ):
                raise ValueError(
                    "artifact is an open collector stdout/stderr or nonregular file"
                )
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("artifact changed while hashing")
        artifacts[str(path)] = {"size": after.st_size, "sha256": digest}
    partial = destination.with_name(destination.name + ".partial")
    body = (
        json.dumps(
            {"version": 1, "artifact_sha256": artifacts}, sort_keys=True, indent=2
        )
        + "\n"
    ).encode()
    exclusive(partial, body)
    os.link(partial, destination, follow_symlinks=False)
    partial.unlink()
    sync_directory(destination.parent)
    # Return to the EXTERNAL coordinator; never append a summary to hashed inputs.
    return hashlib.sha256(body).hexdigest()
