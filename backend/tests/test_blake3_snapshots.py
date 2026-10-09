import tempfile
from pathlib import Path
from app.ledger.fs_snapshotter import FSSnapshotter
from app.ledger.blake3_hasher import hash_str

def test_fs_snapshot_and_restore():
    with tempfile.TemporaryDirectory() as storage_dir:
        snapshotter = FSSnapshotter(storage_dir)

        with tempfile.TemporaryDirectory() as src_dir:
            src = Path(src_dir)
            (src / "app.py").write_text("print('hello world')")
            (src / "nested").mkdir()
            (src / "nested" / "config.json").write_text('{"env": "test"}')

            root_hash, manifest = snapshotter.take_snapshot(src)
            assert root_hash is not None
            assert len(manifest) == 2
            assert "app.py" in manifest
            assert "nested/config.json" in manifest

            # Verify blobs stored
            for rel_path, digest in manifest.items():
                blob = snapshotter.get_blob(digest)
                assert blob is not None

            # Test Restore
            with tempfile.TemporaryDirectory() as restore_dir:
                restored = snapshotter.restore_snapshot(root_hash, restore_dir)
                assert restored is True
                assert (Path(restore_dir) / "app.py").read_text() == "print('hello world')"
                assert (Path(restore_dir) / "nested" / "config.json").read_text() == '{"env": "test"}'

def test_snapshot_diffing():
    with tempfile.TemporaryDirectory() as storage_dir:
        snapshotter = FSSnapshotter(storage_dir)

        with tempfile.TemporaryDirectory() as work_dir:
            w = Path(work_dir)
            f1 = w / "file1.txt"
            f2 = w / "file2.txt"
            f1.write_text("version 1")
            f2.write_text("initial")

            hash1, _ = snapshotter.take_snapshot(w)

            # Modify file1, delete file2, add file3
            f1.write_text("version 2")
            f2.unlink()
            (w / "file3.txt").write_text("new file")

            hash2, _ = snapshotter.take_snapshot(w)

            diff = snapshotter.diff_snapshots(hash1, hash2)
            assert diff["modified"] == ["file1.txt"]
            assert diff["deleted"] == ["file2.txt"]
            assert diff["added"] == ["file3.txt"]
