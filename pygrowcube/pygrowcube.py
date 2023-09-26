"""Main module."""
from .message import Message
from .message import MessageType
from .messageclient import MessageClient
from .timeouthelper import TimeoutHelper
import logging

PORT = 8800
STATUS_TIMEOUT = (
    15  # wait max 15 seconds - sensors send a refresh every 10s when connected
)

logger = logging.getLogger(__name__)


class Status:
    def __init__(
        self,
        temperature=0,
        humidity=0,
        moistures=[0, 0, 0, 0],
        sensor_warnings=[0, 0, 0, 0],
        outlet_locks=[0, 0, 0, 0],
        version="",
        id="",
        host="",
        has_water=True,
        connect_only=False,
    ):
        self.temperature = temperature
        self.humidity = humidity
        self.moistures = moistures
        self.sensor_warnings = sensor_warnings
        self.outlet_locks = outlet_locks
        self.version = version
        self.refreshed_sensors = [False, False, False, False]
        self.id = id
        self.host = host
        self.connect_only = connect_only
        self.has_water = has_water

    def __str__(self) -> str:
        s = f"GrowCube {self.id} ({self.host}). Software version: {self.version}\n"
        if not self.connect_only:
            s += f"Temperature: {self.temperature}, Humidity: {self.humidity}\n"
            if not self.has_water:
                s += "Warning: Not enough water. Refill and press the unlock button on GrowCube device.\n"
            for i in range(4):
                s += f" - Sensor {i}: "
                if self.sensor_warnings[i]:
                    s += f"DISCONNECTED "
                else:
                    if self.outlet_locks[i]:
                        s += "OUTLET LOCKED "
                    if not self.refreshed_sensors[i]:
                        s += "NO READING "
                    else:
                        s += f"{self.moistures[i]}"
                s += "\n"
            if not self.is_refresh_complete:
                s += f"Warning: GrowCube did not send latest status for all sensors before we stopped waiting\n"
        return s.rstrip()

    @property
    def is_refresh_complete(self):
        return all(self.refreshed_sensors)

    def handle_sensor_disconnected(self, message: Message):
        if not message.message_content.isdigit():
            raise ValueError(
                f"{message.readable_message_type}: Expecting message content to be a channel number. Message:"
                + message.get_message()
            )
        channel = int(message.message_content)
        if not channel < 4:
            raise ValueError(
                f"{message.readable_message_type}: Expecting channel number to be less than 4. Message:"
                + message.get_message()
            )
        self.sensor_warnings[channel] = True

    def handle_outlet_locked(self, message: Message):
        if not message.message_content.isdigit():
            raise ValueError(
                f"{message.readable_message_type}: Expecting message content to be a channel number. Message:"
                + message.get_message()
            )
        channel = int(message.message_content)
        if not channel < 4:
            raise ValueError(
                f"{message.readable_message_type}: Expecting channel number to be less than 4. Message:"
                + message.get_message()
            )
        self.outlet_locks[channel] = True

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
        self.refreshed_sensors = [False, False, False, False]
        self.moistures = [0, 0, 0, 0]
        if not (
            (message.message_content == "0@0") or (message.message_content == "1@1")
        ):
            raise ValueError(
                f"{message.readable_message_type}: Received content other than 0@0 or 1@1. Message: {message.get_message()}"
            )
        if message.message_content == "1@1":
            self.has_water = False

    def handle_growcube_version(self, message: Message):
        version, id = message.message_content.split("@")
        self.version = version
        self.id = id

    def handle_OK(self, message: Message):
        if message.message_content != "1":
            logger.warn(
                f"{message.readable_message_type} received with unexpected content: {message.message_content}"
            )
        return

    def default_handler(self, message: Message):
        logger.warn(
            f"{message.readable_message_type} default handler called. Full message: {message.get_message()}"
        )
        return

    status_handlers = {
        MessageType.VERSION: handle_growcube_version,
        MessageType.START_READINGS: handle_start_reading,
        MessageType.SENSOR_READING: handle_sensor_reading,
        MessageType.SENSOR_DISCONNECTED: handle_sensor_disconnected,
        MessageType.OUTLET_LOCKED: handle_outlet_locked,
        MessageType.OK: handle_OK,
    }

    def handle_message(self, message: Message):
        logger.debug(
            f"RECEIVED {message.readable_message_type}: {message.get_message()}"
        )
        if message.message_type in self.status_handlers:
            handler = self.status_handlers.get(message.message_type)
            handler(self, message)
        else:
            self.default_handler(message)


async def get_status(
    growcube_address: str,
    timeout_in_seconds: float = STATUS_TIMEOUT,
    wait_for_sensor_readings: bool = True,
) -> Status:
    logger.info(
        f"Getting status of GrowCube at {growcube_address}:{PORT}. Timeout {timeout_in_seconds}. Wait for readings: {wait_for_sensor_readings}."
    )
    client = MessageClient(growcube_address, PORT)
    status = Status(host=growcube_address, connect_only=not wait_for_sensor_readings)
    timeout = TimeoutHelper(timeout_in_seconds)
    try:
        await client.connect()
        request = Message(
            message_type=MessageType.REQUEST_HELLO,
            message_content=Message.format_datetime_for_growcube(),
        )
        await client.send_message(request, timeout)
        response = await client.receive_message(timeout)
        if response.message_type != MessageType.VERSION:
            logger.error(
                f"Did not receive version number as expected. Response: {str(response)}"
            )
        else:
            status.handle_message(response)
            if wait_for_sensor_readings:
                request = Message(
                    message_type=MessageType.REQUEST_READINGS, message_content="2"
                )
                await client.send_message(request, timeout)
                while not status.is_refresh_complete:
                    response = await client.receive_message(timeout)
                    if isinstance(response, Message):
                        status.handle_message(response)
                    else:
                        logger.warn(
                            f"Response is not a recognisable message: {str(response)}"
                        )
                    if timeout.timed_out:
                        logger.warn(
                            "Did not get a complete refresh of all sensors within time out"
                        )
                        break
                    else:
                        logger.debug(
                            f"Looping. Elapsed:{timeout.elapsed}, Timeout: {timeout_in_seconds}"
                        )
            return status
    finally:
        await client.close()
