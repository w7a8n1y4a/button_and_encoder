import machine

from pepeunit_micropython_client.client import PepeunitClient


# ---- Hardware pins ----
pin_button = None
pin_encoder_clk = None
pin_encoder_dt = None


# ---- Encoder state ----
_enc_last_clk = 1
_enc_last_event_ms = 0


# ---- Button debounce + click state ----
_btn_stable = 1
_btn_raw_last = 1
_btn_raw_change_ms = 0

_btn_press_start_ms = None
_btn_long_fired = False

_btn_click_count = 0
_btn_one_deadline_ms = None
_btn_double_deadline_ms = None


def _maybe_publish_rotation(client: PepeunitClient, direction: str):
    # direction: "Right" / "Left"
    client.publish_to_topics('encoder_rotation/pepeunit', direction)

    if direction == 'Right':
        msg = client.settings.RIGHT_ROTATE_MESSAGE
        if msg is not None:
            client.publish_to_topics('encoder_right_rotate_messages/pepeunit', str(msg))
    else:
        msg = client.settings.LEFT_ROTATE_MESSAGE
        if msg is not None:
            client.publish_to_topics('encoder_left_rotate_messages/pepeunit', str(msg))


def _maybe_publish_button_click(client: PepeunitClient, kind: str):
    # kind: "One" / "Double" / "Triple" / "Long"
    client.publish_to_topics('button_click/pepeunit', kind)

    if kind == 'One':
        msg = client.settings.ONE_CLICK_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_one_click_messages/pepeunit', str(msg))
    elif kind == 'Double':
        msg = client.settings.DOUBLE_CLICK_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_double_click_messages/pepeunit', str(msg))
    elif kind == 'Triple':
        msg = client.settings.TRIPLE_CLICK_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_triple_click_messages/pepeunit', str(msg))
    elif kind == 'Long':
        msg = client.settings.LONG_PRESS_MESSAGE
        if msg is not None:
            client.publish_to_topics('button_long_press_messages/pepeunit', str(msg))


def init_pins(client: PepeunitClient):
    global pin_button, pin_encoder_clk, pin_encoder_dt
    global _enc_last_clk

    pin_button = machine.Pin(int(client.settings.PIN_BUTTON), machine.Pin.IN, machine.Pin.PULL_UP)

    # Encoder pins are optional via feature flag
    if bool(client.settings.FF_ENCODER_ENABLE):
        pin_encoder_clk = machine.Pin(int(client.settings.PIN_ENCODER_CLK), machine.Pin.IN, machine.Pin.PULL_UP)
        pin_encoder_dt = machine.Pin(int(client.settings.PIN_ENCODER_DT), machine.Pin.IN, machine.Pin.PULL_UP)
        _enc_last_clk = pin_encoder_clk.value()


def _handle_encoder(client: PepeunitClient, now_ms: int):
    global _enc_last_clk, _enc_last_event_ms

    if not bool(client.settings.FF_ENCODER_ENABLE):
        return

    if pin_encoder_clk is None or pin_encoder_dt is None:
        return

    clk = pin_encoder_clk.value()
    if clk == _enc_last_clk:
        return

    _enc_last_clk = clk

    # Use rising edge of CLK
    if clk != 1:
        return

    if (now_ms - _enc_last_event_ms) < int(client.settings.ENCODER_DEBOUNCE_TIME):
        return

    dt = pin_encoder_dt.value()

    # Typical KY-040: on CLK rising, DT==0 -> clockwise.
    direction = 'Right' if dt == 0 else 'Left'
    _maybe_publish_rotation(client, direction)
    _enc_last_event_ms = now_ms


def _commit_short_click(client: PepeunitClient, count: int):
    if count <= 0:
        return
    if count == 1:
        _maybe_publish_button_click(client, 'One')
    elif count == 2:
        _maybe_publish_button_click(client, 'Double')
    else:
        _maybe_publish_button_click(client, 'Triple')


def _handle_button(client: PepeunitClient, now_ms: int):
    global _btn_stable, _btn_raw_last, _btn_raw_change_ms
    global _btn_press_start_ms, _btn_long_fired
    global _btn_click_count, _btn_one_deadline_ms, _btn_double_deadline_ms

    raw = pin_button.value()

    # Debounce: track raw changes then accept when stable for BUTTON_DEBOUNCE_TIME
    if raw != _btn_raw_last:
        _btn_raw_last = raw
        _btn_raw_change_ms = now_ms

    if raw != _btn_stable:
        if (now_ms - _btn_raw_change_ms) >= int(client.settings.BUTTON_DEBOUNCE_TIME):
            _btn_stable = raw

            # stable edge committed
            if _btn_stable == 0:
                # pressed
                _btn_press_start_ms = now_ms
                _btn_long_fired = False
            else:
                # released
                if _btn_long_fired:
                    # long already published while holding
                    _btn_press_start_ms = None
                    _btn_long_fired = False
                    return

                if _btn_press_start_ms is None:
                    return

                press_dur = now_ms - _btn_press_start_ms
                _btn_press_start_ms = None

                if press_dur >= int(client.settings.BUTTON_LONG_PRESS_TIME):
                    _btn_click_count = 0
                    _btn_one_deadline_ms = None
                    _btn_double_deadline_ms = None
                    _maybe_publish_button_click(client, 'Long')
                    return

                # short click
                _btn_click_count += 1
                if _btn_click_count == 1:
                    _btn_one_deadline_ms = now_ms + int(client.settings.BUTTON_DOUBLE_CLICK_TIME)
                elif _btn_click_count == 2:
                    _btn_one_deadline_ms = None
                    _btn_double_deadline_ms = now_ms + int(client.settings.BUTTON_TRIPLE_CLICK_TIME)
                else:
                    # 3rd (or more): commit immediately as Triple
                    _commit_short_click(client, _btn_click_count)
                    _btn_click_count = 0
                    _btn_one_deadline_ms = None
                    _btn_double_deadline_ms = None

    # Long press detection while holding (more responsive than waiting for release)
    if _btn_stable == 0 and (not _btn_long_fired) and _btn_press_start_ms is not None:
        if (now_ms - _btn_press_start_ms) >= int(client.settings.BUTTON_LONG_PRESS_TIME):
            _btn_long_fired = True
            _btn_click_count = 0
            _btn_one_deadline_ms = None
            _btn_double_deadline_ms = None
            _maybe_publish_button_click(client, 'Long')

    # Resolve pending single/double when their windows expire
    if _btn_one_deadline_ms is not None and now_ms >= _btn_one_deadline_ms:
        _commit_short_click(client, 1)
        _btn_click_count = 0
        _btn_one_deadline_ms = None
        _btn_double_deadline_ms = None

    if _btn_double_deadline_ms is not None and now_ms >= _btn_double_deadline_ms:
        _commit_short_click(client, 2)
        _btn_click_count = 0
        _btn_one_deadline_ms = None
        _btn_double_deadline_ms = None


def output_handler(client: PepeunitClient):
    now_ms = client.time_manager.get_epoch_ms()
    _handle_encoder(client, now_ms)
    _handle_button(client, now_ms)


def input_handler(client: PepeunitClient, msg):
    return


def main(client: PepeunitClient):
    client.set_mqtt_input_handler(input_handler)
    client.mqtt_client.connect()
    client.subscribe_all_schema_topics()
    client.set_output_handler(output_handler)
    init_pins(client)

    client.run_main_cycle()


if __name__ == '__main__':
    try:
        main(client)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        client.logger.critical(f"Error with reset: {str(e)}", file_only=True)
        client.restart_device()
