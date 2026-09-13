[app]
title = Altron
package.name = altron
package.domain = com.abbas.altron

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,html,css,js
source.exclude_dirs = tests,bin,.buildozer,.git,claude_exports,knowledge,__pycache__
source.exclude_patterns = *.pdf,*.zip,*.tar.gz,backup_*,Jarvis_code.txt

version = 1.0.0

# Keep this list small: every extra package makes the build slower and riskier.
requirements = python3,kivy==2.3.0,flask,werkzeug,jinja2,itsdangerous,click,markupsafe,requests,certifi,android,pyjnius

orientation = portrait
fullscreen = 0

# Permissions Altron needs: mic (voice), network (local server + web), storage
android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = 1
android.accept_sdk_license = True

# Author shown in the build metadata
author = Abbas

[buildozer]
log_level = 2
warn_on_root = 1
