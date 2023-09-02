"""Main module."""
from .message import Message
from .message import MessageType
from .messageclient import MessageClient
from time import perf_counter
import logging

PORT = 8800
STATUS_TIMEOUT = 15 # wait max 15 seconds - sensors send a refresh every 10s when connected

logger = logging.getLogger(__name__)


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
        s = f"GrowCube version: {self.version}\nTemperature: {self.temperature}, Humidity: {self.humidity}\n"
        for i in range(4):
            s += f" - Sensor {i}: "
            if self.sensor_warnings[i]:
                s += f"DISCONNECTED\n"
            else: 
                if not self.refreshed_sensors[i]:
                    s += "NO READING\n"
                else:
                    s += f"{self.moistures[i]}\n"
        if not self.is_refresh_complete:
            s += f"Warning: GrowCube did not send latest status for all sensors before we stopped waiting\n"
        return s.rstrip()
        
    @property
    def is_refresh_complete(self):
        return all(self.refreshed_sensors)

    def handle_sensor_disconnected(self, message: Message):
        if not message.message_content.isdigit():
            raise ValueError(f"{message.readable_message_type}: Expecting message content to be a channel number. Message:" + message.get_message())
        channel = int(message.message_content)
        if not channel < 4:
            raise ValueError(f"{message.readable_message_type}: Expecting channel number to be less than 4. Message:" + message.get_message())        
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
        logger.debug(f"Received reading for sensor {channel}: {reading}.")

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
        logger.warn(f"{message.readable_message_type} default handler called. Full message: {message.get_message()}")
        return

    status_handlers = {
        MessageType.VERSION: handle_growcube_version,
        MessageType.START_READINGS: handle_start_reading,
        MessageType.SENSOR_READING: handle_sensor_reading,
        MessageType.SENSOR_DISCONNECTED: handle_sensor_disconnected,
    }

    def handle_message(self, message: Message):
        logger.debug(f"RECEIVED {message.readable_message_type}: {message.get_message()}")
        handler = self.status_handlers.get(message.message_type, self.default_handler)
        handler(self, message)


def get_status(growcube_address:str, timeout_in_seconds:float = STATUS_TIMEOUT) -> Status:
    logger.info(f"Getting status of GrowCube at {growcube_address}:{PORT}")
    client = MessageClient(growcube_address,PORT)
    status = Status()
    start = perf_counter()
    try:
        client.connect()
        request = Message(
            message_type=44, message_content=Message.format_datetime_for_growcube()
        )
        client.send_message(request)
        while not status.is_refresh_complete:
            response = client.receive_message(start,timeout_in_seconds)
            if isinstance(response,Message):
                status.handle_message(response)
            else:
                logger.warn(f"Response is not a recognisable message: {str(response)}")
            if (perf_counter() - start) > timeout_in_seconds:
                logger.warn("Did not get a complete refresh of all sensors within time out")
                break
        return status
    finally:
        client.close()
