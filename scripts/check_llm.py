import sys, importlib, traceback
print('PYTHON', sys.executable)

def try_import(name):
    try:
        m = importlib.import_module(name)
        print('OK', name, getattr(m, '__file__', None))
        return m
    except Exception as e:
        print('ERR', name, e)
        traceback.print_exc()
        return None

# módulos
m1 = try_import('langchain_google_genai')
if m1 is not None:
    print('Has ChatGoogleGenerativeAI?', hasattr(m1, 'ChatGoogleGenerativeAI'))

m2 = try_import('langchain_core.messages')

# revisar clase por separado
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print('Import ChatGoogleGenerativeAI OK')
except Exception as e:
    print('ERR importing ChatGoogleGenerativeAI:', e)
    traceback.print_exc()

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    print('Import messages OK')
except Exception as e:
    print('ERR importing messages:', e)
    traceback.print_exc()
