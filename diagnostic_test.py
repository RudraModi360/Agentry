
import sys
import os

print('='*60)
print('  AGENTRY FULL SYSTEM DIAGNOSTIC (FROM FILE)')
print('='*60)

# 1. Config
print('\n[1] Configuration...')
try:
    from agentry.config.settings import settings
    print(f'    Mode: {settings.MODE}')
    print(f'    Ollama URL: {settings.OLLAMA_URL}')
    print('    ✅ Config System: OK')
except Exception as e:
    print(f'    ❌ Config Error: {e}')

# 2. Framework Core
print('\n[2] Framework Core...')
try:
    from agentry import Agent
    from agentry.simplemem import AgentrySimpleMem
    print('    ✅ Agent Import: OK')
    print('    ✅ SimpleMem Import: OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'    ❌ Framework Error: {e}')

# 3. Backend Services
print('\n[3] Backend Services...')
try:
    from backend.services import get_chat_storage, is_simplemem_enabled
    print(f'    SimpleMem Enabled: {is_simplemem_enabled()}')
    print('    ✅ Services Import: OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'    ❌ Backend Error: {e}')

# 4. TUI Entry Point
print('\n[4] TUI Check...')
try:
    from agentry.cli import main as cli_main
    print('    ✅ TUI Entry Point: OK')
except Exception as e:
    print(f'    ❌ TUI Error: {e}')

# 5. GUI Entry Point
print('\n[5] GUI Check...')
try:
    from agentry.gui import main as gui_main
    print('    ✅ GUI Entry Point: OK')
except Exception as e:
    print(f'    ❌ GUI Error: {e}')

print('\n' + '='*60)
print('  DIAGNOSTIC COMPLETE')
print('='*60)
