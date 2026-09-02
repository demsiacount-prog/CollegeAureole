# -*- mode: python ; coding: utf-8 -*-
# Spécification PyInstaller pour l'exécutable serveur College Aureole.
#
#   pyinstaller college-aureole-backend.spec
#
# Mode onedir (COLLECT) : démarrage plus rapide et moins de faux positifs
# antivirus que le mode onefile. Le dossier `dist/college-aureole-serveur/`
# produit est repris tel quel par l'installeur NSIS (desktop/serveur/).
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("alembic.ini", "."),
    ("alembic", "alembic"),
] + collect_data_files("alembic")

hiddenimports = [
    # passlib charge ses handlers dynamiquement par nom (get_crypt_handler) :
    # "argon2" est donc invisible de l'analyse statique. On l'ajoute
    # explicitement → PyInstaller analyse argon2, suit son import de
    # _argon2_cffi_bindings (collecte le .pyd/.dll natif) et active le hook
    # argon2 (ajoute _cffi_backend).
    "passlib.handlers.argon2",
    "argon2",
    "argon2._password_hasher",
    "_argon2_cffi_bindings",
    # uvicorn choisit ses composants dynamiquement → invisibles de l'analyse statique
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "anyio._backends._asyncio",
]

a = Analysis(
    ["serveur.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "faker"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="college-aureole-serveur",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="college-aureole-serveur",
)
