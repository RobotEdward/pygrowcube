import socket
import select

class MessageClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Connection error: {e}")
            raise

    def read_until_delimiter(self, delimiter=b'#'):
        data = b""
        while True:
            chunk = self.socket.recv(1)
            if not chunk:
                break
            data += chunk
            if data.endswith(delimiter):
                break
        # Trim leading zero bytes
        while data.startswith(b'\x00'):
            data = data[1:]
        return data

    def receive_message(self, timeout_in_seconds=1):
        if not self.socket:
            raise ValueError("Socket connection is not established. Call connect() first.")

        try:
            ready = select.select([self.socket], [], [], timeout_in_seconds)
            if ready[0]:
                # Receive message type and content length values
                type_and_length = self.read_until_delimiter() + self.read_until_delimiter();
                if not type_and_length:
                    return "NOCONTENT"

                data = type_and_length;
                # Split the received data into message type and content length
                type_and_length = type_and_length.decode().strip('#').split('#')
                if len(type_and_length) != 2:
                    return "NOHEADER"

                message_type, content_length = type_and_length
                # if not message_type.startswith("elea") or not message_type[4:].isdigit() or not content_length.isdigit():
                #     return "WRONGFORMAT:"+ message_type + "::" + content_length

                if not message_type.startswith("elea"):
                    return "NOELEA:"+ message_type + "::" + content_length + "::" + data.hex()
                if not message_type[4:].isdigit():
                    return "NOCOMMAND:"+ message_type + "::" + content_length
                if not content_length.isdigit():
                    return "NOCONTENTLENGTH:"+ message_type + "::" + content_length

                content_length = int(content_length)

                # Receive the message content based on the content length
                message_content = self.socket.recv(content_length).decode()
                end = self.socket.recv(1).decode()
                assert end == "#", "Unexpected content at end of message. Expecting #, got " + end

                return f"{message_type}#{content_length}#{message_content}"
            else:
                print("Select not ready")
                return ""
        except Exception as e:
            print(f"Error receiving message: {e}")
            return ""

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
