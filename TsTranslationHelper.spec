# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[('styles.qss', '.'), ('example_en.ts', '.'), ('example_en_zh.ts', '.')],
    hiddenimports=['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'argostranslate', 'argostranslate.package', 'argostranslate.translate', 'pandas', 'lxml.etree', 'lxml._elementpath', 'pathlib', 'logging', 'sys', 'os', 'typing'],
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
    a.binaries,
    a.datas,
    [],
    name='TsTranslationHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
