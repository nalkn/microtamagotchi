### MicroBit_Backend
MicroBit_Backend class is the base of MicroTamagotchi_Tool. It can connect, interact with micropython (on micro:bit) filsystem. This class depends of (modified) pyboard.py tool.
#### Example :
```python
# imports
from backend import MicroBit_Backend

# init backend and connect
backend = MicroBit_Backend(loglevel="debug")
backend.send_cmd("connect")

# exec cmds
platform = backend.send_cmd("platform")
version = backend.send_cmd("version")
print(platform, version, "connected")

# exit
backend.send_cmd("restart")
backend.exit()
```