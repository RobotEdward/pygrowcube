# Python dev notes

Scratchpad of stuff while understanding this setup

## CookieCutter docs
https://github.com/audreyfeldroy/cookiecutter-pypackage/blob/master/docs/tutorial.rst

## invoking the CLI
[Ref](https://github.com/audreyfeldroy/cookiecutter-pypackage/blob/master/docs/console_script_setup.rst)
```bash
source .venv/bin/activate
pip install -e ~/src/pygrowcube
pygrowcube
```
Changes made to code then apply immediately.

## Importing classes
Message class is defined in message.py (in the same folder as the rest of the pygrowcube files):
```python
class Message:
    def __init__(self, message_string=None, message_type=None, message_content=None):
        self.message_type = None
        self.content_length = None
        self.message_content = None

# etc...
```
To reference it from the cli.py I needed to add
```python
from .message import Message
```
Simpler variants didn't seem to work for me. [Ref](https://stackoverflow.com/questions/4142151/how-to-import-the-class-within-the-same-directory-or-sub-directory)

## Socket handling
[Waiting for data and timeouts](https://stackoverflow.com/a/2721734)

```python
import select

mysocket.setblocking(0)

ready = select.select([mysocket], [], [], timeout_in_seconds)
if ready[0]:
    data = mysocket.recv(4096)
```