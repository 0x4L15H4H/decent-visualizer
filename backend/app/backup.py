"""Create consistent SQLite snapshots and upload them with OCI instance principals."""

import argparse
import gzip
import os
import sqlite3
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import oci  # pyright: ignore[reportMissingTypeStubs]

from app.config import get_settings


def create_backup() -> str:
    bucket = os.environ["OCI_BACKUP_BUCKET"]
    namespace = os.environ["OCI_OBJECT_STORAGE_NAMESPACE"]
    region = os.environ["OCI_REGION"]
    source = sqlite3.connect(get_settings().database_path)
    with tempfile.TemporaryDirectory() as temporary_directory:
        snapshot = Path(temporary_directory) / "decent-visualizer.sqlite3"
        destination = sqlite3.connect(snapshot)
        with destination:
            source.backup(destination)
        destination.close()
        source.close()

        compressed = snapshot.with_suffix(".sqlite3.gz")
        with snapshot.open("rb") as input_file, gzip.open(compressed, "wb") as output_file:
            while chunk := input_file.read(1024 * 1024):
                output_file.write(chunk)

        name = f"sqlite/{datetime.now(UTC):%Y/%m/%d}/decent-visualizer-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.sqlite3.gz"
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client = oci.object_storage.ObjectStorageClient({"region": region}, signer=signer)
        with compressed.open("rb") as backup_file:
            client.put_object(namespace, bucket, name, backup_file)
    return name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Upload now and every 24 hours.")
    args = parser.parse_args()
    while True:
        print(f"Uploaded SQLite backup: {create_backup()}")
        if not args.loop:
            return
        time.sleep(24 * 60 * 60)


if __name__ == "__main__":
    main()
