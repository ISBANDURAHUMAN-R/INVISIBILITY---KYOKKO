# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

import os
spec_dir = os.path.dirname(os.path.abspath(SPEC)) if 'SPEC' in locals() else os.path.dirname(os.path.abspath(__file__))

datas = [(os.path.join(spec_dir, 'ui', 'themes', 'style.qss'), 'ui/themes'), (os.path.join(spec_dir, 'assets'), 'assets')]
binaries = []
hiddenimports = ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'cv2', 'sqlite3', 'numpy']
datas += collect_data_files('mediapipe')
binaries += collect_dynamic_libs('mediapipe')
hiddenimports += collect_submodules('mediapipe')
tmp_ret = collect_all('pyvirtualcam')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    [os.path.join(spec_dir, 'main.py')],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KYOKKO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KYOKKO',
)
