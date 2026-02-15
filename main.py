import machine
import uasyncio as asyncio

from pepeunit_micropython_client.client import PepeunitClient

from encoder import EncoderButton


client = globals().get("client")
_controller = None

ENCODER_POLL_MS = 1


async def _encoder_poll_task(client: PepeunitClient, controller: EncoderButton):
    while True:
        now_ms = client.time_manager.get_epoch_ms()
        controller.handle_encoder(now_ms)
        controller.handle_button(now_ms)
        await asyncio.sleep_ms(ENCODER_POLL_MS)


async def _maybe_publish_rotation(client: PepeunitClient, direction: str):
    await client.publish_to_topics('encoder_rotation/pepeunit', direction)

    print(direction)

    if direction == 'Right':
        msg = client.settings.RIGHT_ROTATE_MESSAGE
        if msg is not None:
            await client.publish_to_topics('encoder_right_rotate_message/pepeunit', str(msg))
    else:
        msg = client.settings.LEFT_ROTATE_MESSAGE
        if msg is not None:
            await client.publish_to_topics('encoder_left_rotate_message/pepeunit', str(msg))


async def _maybe_publish_button_click(client: PepeunitClient, kind: str):
    await client.publish_to_topics('button_click/pepeunit', kind)

    print(kind)

    if kind == 'One':
        msg = client.settings.ONE_CLICK_MESSAGE
        if msg is not None:
            await client.publish_to_topics('button_one_click_message/pepeunit', str(msg))
    elif kind == 'Double':
        msg = client.settings.DOUBLE_CLICK_MESSAGE
        if msg is not None:
            await client.publish_to_topics('button_double_click_message/pepeunit', str(msg))
    elif kind == 'Long':
        msg = client.settings.LONG_PRESS_MESSAGE
        if msg is not None:
            await client.publish_to_topics('button_long_press_message/pepeunit', str(msg))


def init_pins(client: PepeunitClient):
    pin_button = machine.Pin(int(client.settings.PIN_BUTTON), machine.Pin.IN, machine.Pin.PULL_UP)

    pin_encoder_clk = None
    pin_encoder_dt = None
    if bool(client.settings.FF_ENCODER_ENABLE):
        pin_encoder_clk = machine.Pin(int(client.settings.PIN_ENCODER_CLK), machine.Pin.IN, machine.Pin.PULL_UP)
        pin_encoder_dt = machine.Pin(int(client.settings.PIN_ENCODER_DT), machine.Pin.IN, machine.Pin.PULL_UP)

    return pin_button, pin_encoder_clk, pin_encoder_dt


async def output_handler(client: PepeunitClient):
    pass


async def input_handler(client: PepeunitClient, msg):
    return


async def main_async(client: PepeunitClient):
    global _controller
    await client.wifi_manager.ensure_connected()
    await client.time_manager.sync_epoch_ms_from_ntp()

    client.set_mqtt_input_handler(input_handler)
    await client.mqtt_client.connect()
    await client.mqtt_client.subscribe_all_schema_topics()
    client.set_output_handler(output_handler)
    pin_button, pin_encoder_clk, pin_encoder_dt = init_pins(client)

    def on_button(kind: str):
        asyncio.create_task(_maybe_publish_button_click(client, kind))
        return kind

    def on_rotate(direction: str):
        asyncio.create_task(_maybe_publish_rotation(client, direction))
        return direction

    _controller = EncoderButton(
        pin_button=pin_button,
        pin_encoder_clk=pin_encoder_clk,
        pin_encoder_dt=pin_encoder_dt,
        encoder_enabled=bool(client.settings.FF_ENCODER_ENABLE),
        button_debounce_ms=int(client.settings.BUTTON_DEBOUNCE_TIME),
        button_double_click_ms=int(client.settings.BUTTON_DOUBLE_CLICK_TIME),
        button_long_press_ms=int(client.settings.BUTTON_LONG_PRESS_TIME),
        encoder_debounce_ms=int(client.settings.ENCODER_DEBOUNCE_TIME),
        on_button=on_button,
        on_rotate=on_rotate,
    )

    asyncio.create_task(_encoder_poll_task(client, _controller))
    await client.run_main_cycle()


if __name__ == '__main__':
    try:
        asyncio.run(main_async(client))
    except KeyboardInterrupt:
        raise
    except Exception as e:
        client.logger.critical(f"Error with reset: {str(e)}", file_only=True)
        client.restart_device()
