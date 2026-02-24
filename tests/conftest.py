import os

# Ensure Qt can initialize in headless test environments.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
