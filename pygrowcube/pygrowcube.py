"""Main module."""
from .message import Message
from .messageclient import MessageClient
HOST="192.168.239.139"
PORT=8800

def GetStatus():
    client = MessageClient(HOST, PORT)
    
    try:
        client.connect()
        messages = []
        i = 0
        # Receive and parse a message from the remote host
        while True:
            print("read")
            message = client.receive_message()
            print(message)
            if not message:
                break
            messages.append(message)
        return " -- ".join(messages)
    finally:
        client.close()
