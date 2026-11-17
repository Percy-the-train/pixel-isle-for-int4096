import os
import tempfile

# Keep tests away from the real ./data folder.
os.environ.setdefault("NCB_DATA_DIR", tempfile.mkdtemp(prefix="ncb_test_"))