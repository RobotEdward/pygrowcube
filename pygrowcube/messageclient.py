import asyncio
import logging
from .timeouthelper import TimeoutHelper
from .message import Message
from .message import MessageType
from time import perf_counter

logger = logging.getLogger(__name__)
TIMEOUT = 5


class MessageClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            logger.debug("Connecting to: %s %s ", self.host, self.port)
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.exception(
                f"Connection timed out connecting to: {self.host} {self.port}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"Connection error: {e}. Connecting to: {self.host} {self.port}"
            )
            raise

    async def close(self):
        if self.writer:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), timeout=TIMEOUT)

    async def send_message(
        self, message: Message, timeout: TimeoutHelper = TimeoutHelper(TIMEOUT)
    ):
        if not self.writer:
            raise ValueError(
                "Socket connection is not established. Call connect() first."
            )
        try:
            message_string = message.get_message()
            logger.info(
                f"SENDING {message.readable_message_type}: {message.message_content}. {message_string}"
            )
            self.writer.write(message_string.encode())
            await asyncio.wait_for(self.writer.drain(), timeout=timeout.remaining)
        except asyncio.TimeoutError:
            logger.exception("Network operation timed out.")
            raise
        except Exception as e:
            logger.exception(f"Error sending message: {e}")
            raise

    async def read_until_delimiter(
        self, timeout: TimeoutHelper = TimeoutHelper(TIMEOUT), delimiter=b"#"
    ) -> str:
        """Read a field from growcube until we get to a delimiter character.
        We have to do this a character at a time to strip the zeros sent in between messages.
        """
        data = b""
        try:
            while True:
                if timeout.timed_out:
                    logger.warn(
                        "Timed out waiting for data. Timeout=%s, elapsed=%s. Received: %s",
                        timeout.timeout,
                        timeout.elapsed,
                        data.decode(),
                    )
                    raise asyncio.TimeoutError()
                chunk = await asyncio.wait_for(
                    self.reader.read(1), timeout=timeout.remaining
                )
                if chunk == delimiter:
                    break
                if chunk != (b"\x00"):
                    data += chunk
                if len(data) == 6:
                    # GrowCube sends ele5XX responses without a trailing #
                    s = data[:4].decode()
                    if s == "ele5":
                        break
        except asyncio.TimeoutError:
            logger.warn(
                "Timed out waiting for data. Timeout=%s, elapsed=%s. Received: %s",
                timeout.timeout,
                timeout.elapsed,
                data.decode(),
            )
            raise
        except Exception as e:
            logger.exception(f"Error reading data {e}")
            raise
        return data.decode()

    async def receive_message(
        self, timeout: TimeoutHelper = TimeoutHelper(TIMEOUT)
    ) -> Message:
        if not self.reader:
            raise ValueError(
                "Socket connection is not established. Call connect() first."
            )
        try:
            # Receive message type and content length values
            message_type_string = await self.read_until_delimiter(timeout)
            if not message_type_string.startswith("ele"):
                raise ValueError(
                    f"Did not recognise a GrowCube message type - does not begin with 'ele': {message_type}"
                )
            if message_type_string[3] == "a":
                message_type = int(message_type_string[4:])
            else:
                message_type = int(message_type_string[3:])
            message = Message(message_type=message_type)
            if not message.content_expected_for_message_type:
                return message

            length = await self.read_until_delimiter(timeout)
            if not length.isdigit():
                raise ValueError(
                    f"Did not receive an integer content length as expected: {length}"
                )

            # Receive the message content based on the content length
            message_content_response = (await asyncio.wait_for(
                self.reader.read(int(length) + 1), timeout=timeout.remaining
            )).decode()
            message_content = message_content_response[:-1]
            end = message_content_response[-1]
            if not end == "#":
                logger.warn(
                    "Unexpected content at end of message. Expecting #, got " + end
                )
            message.content_length = length
            message.message_content = message_content
            logger.info(f"RECEIVED {message.readable_message_type}: {message_content}")
            return message
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None


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
