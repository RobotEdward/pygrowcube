"""Main module."""
from .message import Message
from .message import MessageType
from .messageclient import MessageClient

HOST = "192.168.239.139"
PORT = 8800


class Status:
    def __init__(
        self,
        temperature=0,
        humidity=0,
        moistures=[0, 0, 0, 0],
        sensors_warnings=[0, 0, 0, 0],
        version="",
    ):
        self.temperature = temperature
        self.humidity = humidity
        self.moistures = moistures
        self.sensor_warnings = sensors_warnings
        self.version = version
        self.refreshed_sensors = [False, False, False, False]

    def __str__(self) -> str:
        s = f"GrowCube Version: {self.version}, Refresh Complete: {self.is_refresh_complete()}, Temperature: {self.temperature}, Humidity: {self.humidity}\n"
        for i in range(4):
            s += f" - Sensor {i} - Refreshed: {self.refreshed_sensors[i]}, Reading: {self.moistures[i]}, Disconnection Warning: {self.sensor_warnings[i]}\n"
        return s
        

    def is_refresh_complete(self):
        return all(self.refreshed_sensors)

    def handle_sensor_disconnected(self, message: Message):
        assert message.message_content.isdigit(), (
            "Expecting message content to be a number: " + message.get_message()
        )
        channel = int(message.message_content)
        assert channel < 4, (
            "Channel number out of range: " + message.get_message()
        )
        self.sensor_warnings[channel] = True

    def handle_sensor_reading(self, message: Message):
        fields = message.get_fields()
        assert len(fields) == 4, (
            "Expecting message content to have 4 fields: " + message.get_message()
        )
        assert all(field.isdigit() for field in fields), (
            "Expecting message content fields to be all digits" + message.get_message()
        )
        channel, reading, humidity, temperature = fields
        channel = int(channel)
        assert channel < 4, "Channel number out of range: " + message.get_message()
        self.humidity = int(humidity)
        self.temperature = int(temperature)
        self.moistures[channel] = int(reading)
        self.refreshed_sensors[channel] = True
        self.refreshed = all(self.refreshed_sensors)

    def handle_start_reading(self, message: Message):
        assert message.message_content == "0@0", (
            "Received message content other than 0@0 for start readings message: "
            + message.message_content
        )
        self.refreshed_sensors = [False, False, False, False]
        self.moistures = [0, 0, 0, 0]

    def handle_growcube_version(self, message: Message):
        self.version = message.message_content

    def default_handler(self, message: Message):
        print(f"DEBUG: default handler called for messagetype: {message.message_type}. Full message: {message.get_message()}")
        return

    status_handlers = {
        MessageType.VERSION: handle_growcube_version,
        MessageType.START_READINGS: handle_start_reading,
        MessageType.SENSOR_READING: handle_sensor_reading,
        MessageType.SENSOR_DISCONNECTED: handle_sensor_disconnected,
    }

    def handle_message(self, message: Message):
        
        handler = self.status_handlers.get(message.message_type, self.default_handler)
        handler(self, message)


def get_status():
    client = MessageClient(HOST, PORT)
    status = Status()

    try:
        client.connect()
        messages = []
        request = Message(
            message_type=44, message_content=Message.format_datetime_for_growcube()
        )
        messages.append("SEND:" + request.get_message())
        client.send_message(request.get_message())
        i = 0
        while not status.is_refresh_complete():
            response = client.receive_message()
            message = Message(message_string=response)
            status.handle_message(message)
            print(f"{i} {str(status)}")
            i += 1
        # i = 0
        # while i < 7:
        #     response = client.receive_message()
        #     if not response:
        #         break
        #     message = Message(message_string=response)

        #     print(response)
        #     messages.append(response)
        #     i += 1
        return str(status)
    finally:
        client.close()
