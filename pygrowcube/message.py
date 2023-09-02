class Message:
    def __init__(self, message_string=None, message_type=None, message_content=None):
        self.message_type = None
        self.content_length = None
        self.message_content = None

        if message_string is not None:
            self.parse_message(message_string)
        elif message_type is not None and message_content is not None:
            self.message_type = message_type
            self.message_content = message_content
            self.content_length = len(message_content)

    def parse_message(self, message_string):
        # Split the message into sections using '#' as the delimiter
        sections = message_string.strip("#").split("#")

        if len(sections) != 3:
            raise ValueError(
                "Invalid message format. It should have exactly 3 sections."
            )

        # Extract and validate message type
        message_type = sections[0]
        if not message_type.startswith("elea") or not message_type[4:].isdigit():
            raise ValueError("Invalid message type format.")
        self.message_type = message_type

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
