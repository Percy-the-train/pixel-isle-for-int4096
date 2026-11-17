"""Build a portable single-file executable:  python build_exe.py
Output: dist/NewsCrawlerBuddy(.exe).  Data is stored in ./data next to the exe."""
import os

import PyInstaller.__main__

sep = os.pathsep
PyInstaller.__main__.run([
    "run.py",
    "--name", "NewsCrawlerBuddy",
    "--onefile",
    "--noconfirm",
    "--add-data", f"app/static{sep}app/static",
    "--collect-submodules", "uvicorn",
    "--collect-all", "trafilatura",
    "--collect-all", "htmldate",
    "--collect-all", "courlan",
    "--collect-all", "justext",
    "--collect-data", "langdetect",
    "--collect-all", "feedparser",
])