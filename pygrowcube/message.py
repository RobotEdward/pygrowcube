from datetime import datetime
from enum import IntEnum
import logging


class MessageType(IntEnum):
    # Client command messages:
    REQUEST_READINGS = (
        43  # TBC: Sent by the client close to start of session elea43#1#2#
    )
    REQUEST_HELLO = 44  # Sent with client datetime at start of session elea44#19#2023@09@05@11@53@30#
    REQUEST_DELETE = 45 # Delete the settings for a channel - always seems to be sent as a pair with 46 - elea45#1#0# 
    REQUEST_DELETE_CONFIRM = 46 # Second part of the delete request - don't know why but client alwasy sends this immediately after #45 
    REQUEST_WATER_CONTROL = 47  # Turn water on or off for a channel
    REQUEST_SENSOR_HISTORY = 48  # Request the moisture history for a channel
    REQUEST_CHANNEL_SETTINGS = 49  # Settings for a channel
    # Smart watering: channel@3@min%@max% elea49#9#2@3@10@50#
    # Smart watering outside of sunlight hours: elea49#9#2@2@10@50#
    # Regular watering: channel@1@how_often@how_long elea49#9#2@1@30s@6#

    # GrowCube response messages:
    OK = 20 # suspect this is OK - always comes back with a #1
    SENSOR_READING = 21  # Moisture reading for an individual sensor
    SENSOR_HISTORY_ENTRY = (
        22  # Moisture readings by hour for a specific channel and date
    )
    WATERING_HISTORY_ENTRY = (
        23  # Invdividual watering event date and time for a specific channel
    )
    VERSION = 24  # Sent on connection
    WATER_ON = 26  # Water turned on for a channel
    WATER_OFF = 27  # Water turned off for a channel
    SENSOR_DISCONNECTED = (
        30  # Sent on connection when a sensor is disconnected elea30#1#2#
    )
    START_READINGS = 33  # Always sent before sensor readings with content 0@0
    OUTLET_LOCKED = 34  # The outlet for the specified channel is locked elea34#1#1#
    UNKNOWN = 0


class Message:
    def __init__(
        self,
        message_string=None,
        message_type: MessageType = MessageType.UNKNOWN,
        message_content=None,
    ):
        self.message_type = None
        self.content_length = None
        self.message_content = None

        if message_string is not None:
            self.parse_message(message_string)
        elif message_type is not None and message_content is not None:
            self.message_type = message_type
            self.message_content = message_content
            self.content_length = len(message_content)

    @property
    def readable_message_type(self) -> str:
        if self.message_type in MessageType.__members__.values():
            return f"{self.message_type} {MessageType(self.message_type).name}"
        else:
            return f"{self.message_type} UNKNOWN"

    def parse_growcube_datetime(datetime_str):
        """
        Parse a datetime string in the format "YYYY@MM@DD@HH@mm@SS" into a datetime object.
        This is the format GrowCube uses to send datetimes
        Args:
            datetime_str (str): The datetime string to parse.
        Returns:
            datetime: A datetime object.
        """
        try:
            return datetime.strptime(datetime_str, "%Y@%m@%d@%H@%M@%S")
        except ValueError as e:
            raise ValueError("Invalid datetime string format") from e

    def format_datetime_for_growcube(dt=datetime.now()):
        """
        Format a datetime object as a string in the format "YYYY@MM@DD@HH@mm@SS".
        Args:
            dt (datetime): A datetime object to format.
        Returns:
            str: The formatted datetime string.
        """
        return dt.strftime("%Y@%m@%d@%H@%M@%S")

    def parse_message(self, message_string):
        # Split the message into sections using '#' as the delimiter
        sections = message_string.strip("#").split("#")

        if len(sections) != 3:
            raise ValueError(
                "Invalid message format. It should have exactly 3 sections."
                + message_string
            )

        # Extract and validate message type
        message_type = sections[0]
        if not message_type.startswith("elea") or not message_type[4:].isdigit():
            raise ValueError("Invalid message type format.")
        self.message_type = int(message_type[4:])

        # Extract and validate content length
        content_length = sections[1]
        if not content_length.isdigit():
            raise ValueError("Invalid content length format.")
        self.content_length = int(content_length)

        # Extract and validate message content
        message_content = sections[2]
        if len(message_content) != self.content_length:
            raise ValueError("Content length does not match actual content length.")
        self.message_content = message_content

    def get_fields(self):
        if not self.message_content:
            return []

        # Split the message content into fields using '@' as the delimiter
        fields = self.message_content.split("@")

        return fields

    def get_message(self):
        if (
            self.message_type is None
            or self.content_length is None
            or self.message_content is None
        ):
            raise ValueError("Message is not fully initialized.")

        # Create the resulting message string
        return f"{self.message_type}#{self.content_length}#{self.message_content}#"

    def __str__(self):
        return f"Message Type: {self.message_type}, Content Length: {self.content_length}, Content: {self.message_content}"


# # Example usage with alternative constructor:
# message = Message(message_type="elea01", message_content="John@Doe")

# print(message.message_type)  # Output: elea01
# print(message.content_length)  # Output: 8
# print(message.message_content)  # Output: John@Doe

# fields = message.get_fields()
# print(fields)  # Output: ['John', 'Doe']

# resulting_message = message.get_message()
# print(resulting_message)  # Output: elea01#8#John@Doe#
