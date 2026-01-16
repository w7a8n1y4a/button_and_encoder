import machine

from pepeunit_micropython_client.client import PepeunitClient

from encoder import EncoderButton


client = globals().get("client")
_controller = None


def _maybe_publish_rotation(client: PepeunitClient, direction: str):
    client.publish_to_topics('encoder_rotation/pepeunit', direction)

    print(direction)

    if direction == 'Right':
        msg = client.settings.RIGHT_ROTATE_MESSAGE
        if msg is not None:
            client.publish_to_topics('encoder_right_rotate_messages/pepeunit', str(msg))
    else:
        msg = client.settings.LEFT_ROTATE_MESSAGE
        if msg is not None:
            client.publish_to_topics('encoder_left_rotate_messages/pepeunit', str(msg))


def _maybe_publish_button_click(client: PepeunitClient, kind: str):
    client.publish_to_topics('button_click/pepeunit', kind)

    print(kind)

    if kind == 'One':
        msg = client.settings.ONE_CLICK_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_one_click_messages/pepeunit', str(msg))
    elif kind == 'Double':
        msg = client.settings.DOUBLE_CLICK_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_double_click_messages/pepeunit', str(msg))
    elif kind == 'Long':
        msg = client.settings.LONG_PRESS_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_long_press_messages/pepeunit', str(msg))


def init_pins(client: PepeunitClient):
    pin_button = machine.Pin(int(client.settings.PIN_BUTTON), machine.Pin.IN, machine.Pin.PULL_UP)

    pin_encoder_clk = None
    pin_encoder_dt = None
    if bool(client.settings.FF_ENCODER_ENABLE):
        pin_encoder_clk = machine.Pin(int(client.settings.PIN_ENCODER_CLK), machine.Pin.IN, machine.Pin.PULL_UP)
        pin_encoder_dt = machine.Pin(int(client.settings.PIN_ENCODER_DT), machine.Pin.IN, machine.Pin.PULL_UP)

    return pin_button, pin_encoder_clk, pin_encoder_dt


def output_handler(client: PepeunitClient):
    now_ms = client.time_manager.get_epoch_ms()
    if _controller is None:
        return
    _controller.handle_encoder(now_ms)
    _controller.handle_button(now_ms)


def input_handler(client: PepeunitClient, msg):
    return


def main(client: PepeunitClient):
    global _controller
    client.set_mqtt_input_handler(input_handler)
    client.mqtt_client.connect()
    client.subscribe_all_schema_topics()
    client.set_output_handler(output_handler)
    pin_button, pin_encoder_clk, pin_encoder_dt = init_pins(client)

    def on_button(kind: str):
        _maybe_publish_button_click(client, kind)
        return kind

    def on_rotate(direction: str):
        _maybe_publish_rotation(client, direction)
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

    client.run_main_cycle()


if __name__ == '__main__':
    try:
        main(client)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        client.logger.critical(f"Error with reset: {str(e)}", file_only=True)
        client.restart_device()
