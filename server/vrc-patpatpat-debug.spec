# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/*', './resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [('v', None, 'OPTION')],
    name='vrc-patpatpat',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

import shutil
import os
import logging
logging.info("Copying files and folders into build directory")
isCI = bool(os.getenv("CI"))
serverpath = "server/" if isCI else ""
rootpath = "" if isCI else "../"
shutil.copyfile(f"{serverpath}patpatpat.cfg", f"{DISTPATH}/patpatpat.cfg")
shutil.copyfile(f"{rootpath}README.md", f"{DISTPATH}/README.md")
shutil.copyfile(f"{rootpath}LICENSE", f"{DISTPATH}/LICENSE")
shutil.copytree(f"{rootpath}firmware", f"{DISTPATH}/firmware")
shutil.copytree(f"{rootpath}pcb", f"{DISTPATH}/pcb")
logging.info("Successfully copied all files and folders into build directory")