import socket
import select
import logging
from .message import Message
from .message import MessageType
from time import perf_counter

logger = logging.getLogger(__name__)

class MessageClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            logger.debug(f"Connecting to socket {self.host} {self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        except Exception as e:
            logger.error(f"Socket connection error: {e}")
            raise

    def send_message(self, message:Message):
        if not self.socket:
            raise ValueError(
                "Socket connection is not established. Call connect() first."
            )
        try:
            logger.info(f"SENDING {message.readable_message_type}: {message.message_content}")
            self.socket.sendall(message.get_message().encode())
        except Exception as e:
            logger.error(f"ERROR SENDING {message.readable_message_type}: {e}")

    def read_until_delimiter(self, start:float, timeout_in_seconds:float, delimiter=b"#"):
        data = b""
        while True:
            if (perf_counter()-start) > timeout_in_seconds:
                logger.warn(f"Timeout exceeded. Timeout={timeout_in_seconds}, start={start}, now={perf_counter()}")
                break
            chunk = self.socket.recv(1)
            if not chunk:
                break
            data += chunk
            if data.endswith(delimiter):
                break
        # Trim leading zero bytes
        while data.startswith(b"\x00"):
            data = data[1:]
        return data

    def receive_message(self, start:float=perf_counter(), timeout_in_seconds:float=15):
        if not self.socket:
            raise ValueError(
                "Socket connection is not established. Call connect() first."
            )

        try:
            ready = select.select([self.socket], [], [], timeout_in_seconds)
            if ready[0]:
                # Receive message type and content length values
                type_and_length = (
                    self.read_until_delimiter(start,timeout_in_seconds) + self.read_until_delimiter(start, timeout_in_seconds)
                )
                if not type_and_length:
                    return None

                data = type_and_length
                # Split the received data into message type and content length
                type_and_length = type_and_length.decode().strip("#").split("#")
                if len(type_and_length) != 2:
                    return "NOHEADER"

                message_type_string, content_length = type_and_length
                # if not message_type.startswith("elea") or not message_type[4:].isdigit() or not content_length.isdigit():
                #     return "WRONGFORMAT:"+ message_type + "::" + content_length

                if not message_type_string.startswith("elea"):
                    raise ValueError(f"Did not recognise a GrowCube message type - does not begin with 'elea': {type_and_length}")
                message_type = message_type_string[4:]
                if not message_type.isdigit():
                    raise ValueError(f"Could not parse message type as a number: {type_and_length}")
                if not content_length.isdigit():
                    raise ValueError(f"Could not parse content_length as a number: {type_and_length}")

                content_length = int(content_length)

                # Receive the message content based on the content length
                message_content = self.socket.recv(content_length).decode()
                end = self.socket.recv(1).decode()
                if not end == "#":
                    logger.warn("Unexpected content at end of message. Expecting #, got " + end)
                

                logger.debug(f"About to parse message: {message_type}#{content_length}#{message_content}")
                message = Message(message_type=int(message_type),message_content=message_content) 
                logger.info(f"RECEIVED {message.readable_message_type}: {message_content}")
                return message
            else:
                logger.info("Select not ready")
                return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None

    def close(self):
        if self.socket:
            self.socket.close()


# Example usage:
# if __name__ == "__main__":
#     host = "example.com"  # Replace with the actual remote host address
#     port = 12345  # Replace with the actual port number

#     client = MessageClient(host, port)

#     try:
#         client.connect()

#         # Receive and parse a message from the remote host
#         received_data = client.receive_message()
#         if received_data:
#             received_message = Message(received_data)
#             print("Received Message:")
#             print(received_message)
#     finally:
#         client.close()
