# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

mp_datas, mp_binaries, mp_hiddenimports = collect_all("mediapipe")

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[*mp_binaries],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('backend/perception/pose_landmarker_lite.task', 'backend/perception'),
        ('backend/perception/pose_landmarker_full.task', 'backend/perception'),
        ('backend/perception/pose_landmarker_heavy.task', 'backend/perception'),
        *mp_datas,
    ],
    hiddenimports=[*mp_hiddenimports],
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
    name='Human Controller',
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
    name='Human Controller',
)
