# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],          # 前端模板已内嵌，无需额外数据文件
    hiddenimports=[
        'flask',
        'flask_cors',
        'pandas',
        'requests',
        'dotenv',
        'zoneinfo',
        'api_client',
        'config'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XAU_Showtime',           # 生成的可执行文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                      # 使用 UPX 压缩（需安装 upx）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                  # 显示控制台窗口（便于查看日志和错误）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)