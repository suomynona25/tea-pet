import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.google_tool import google_tool

res = google_tool.invoke('best milkshakes in SG')
print(res)
print(type(res))
