#!/usr/bin/env python3
"""Check which packages are installed and working"""

import sys

print("Checking installed packages...\n")

packages = {
    'streamlit': 'streamlit',
    'pandas': 'pandas',
    'whisper': 'whisper',
    'rapidfuzz': 'rapidfuzz',
    'openpyxl': 'openpyxl',
    'plotly': 'plotly',
    'soundfile': 'soundfile',
}

# Check audiorecorder with multiple import methods
audiorecorder_works = False
try:
    from audiorecorder import audiorecorder
    print("✓ audiorecorder (via streamlit_audiorecorder)")
    audiorecorder_works = True
except:
    try:
        from audiorecorder import audiorecorder
        print("✓ audiorecorder (via audiorecorder)")
        audiorecorder_works = True
    except:
        print("✗ audiorecorder - INSTALL: pip install streamlit-audiorecorder")

# Check other packages
for name, module in packages.items():
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} - INSTALL: pip install {name if name != 'whisper' else 'openai-whisper'}")

print("\n" + "="*50)
if audiorecorder_works:
    print("All required packages installed! ✓")
    print("Run: streamlit run app.py")
else:
    print("Missing packages detected!")
    print("Run: pip install streamlit-audiorecorder openai-whisper")
print("="*50)
