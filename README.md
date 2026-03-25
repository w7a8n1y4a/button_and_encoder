# Button and Encoder

Parameter | Implementation
-- | --
Description | Обрабатывает нажатия кнопки (одиночный клик, двойной клик, долгое нажатие) и вращение энкодера. Публикует события в топик `encoder_action/pepeunit` и опциональные сообщения в `*_message/pepeunit`
Lang | `Micropython`
Hardware | `esp8266`, `esp32`, `esp32c3`, `esp32s3`, `KY-040`, `button`
Firmware | [RELEASE-1.1.1](https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_micropython_client/-/releases/1.1.1)
Stack | `pepeunit_micropython_client`
Version | 1.1.1
License | AGPL v3 License
Authors | Ivan Serebrennikov <admin@silberworks.com>

## Schema

<div align="center"><img align="center" src="https://minio.pepemoss.com/public-data/schema/button_encoder.png"></div>

## Physical IO

Key | Description
-- | --
`client.settings.PIN_BUTTON` | Вывод кнопки
`client.settings.PIN_ENCODER_CLK` | Вывод `CLK` энкодера (работет только при `FF_ENCODER_ENABLE` = `true`)
`client.settings.PIN_ENCODER_DT` | Вывод `DT` энкодера (работет только при `FF_ENCODER_ENABLE` = `true`)

## Env variable assignment

Variable | Description
-- | --
`FF_ENCODER_ENABLE` | Включить энкодер: `true` или `false`
`PIN_BUTTON` | Номер пина кнопки
`PIN_ENCODER_CLK` | Номер пина `CLK` энкодера
`PIN_ENCODER_DT` | Номер пина `DT` энкодера
`ONE_CLICK_MESSAGE` | Сообщение при одиночном клике (или `null` — не публиковать)
`DOUBLE_CLICK_MESSAGE` | Сообщение при двойном клике (или `null` — не публиковать)
`LONG_PRESS_MESSAGE` | Сообщение при долгом нажатии (или `null` — не публиковать)
`RIGHT_ROTATE_MESSAGE` | Сообщение при повороте вправо (или `null` — не публиковать)
`LEFT_ROTATE_MESSAGE` | Сообщение при повороте влево (или `null` — не публиковать)
`BUTTON_DEBOUNCE_TIME` | Время антидребезга кнопки в миллисекундах
`BUTTON_DOUBLE_CLICK_TIME` | Окно для двойного клика в миллисекундах
`BUTTON_LONG_PRESS_TIME` | Время долгого нажатия в миллисекундах
`PUC_WIFI_SSID` | Имя сети `WiFi`
`PUC_WIFI_PASS` | Пароль от сети `WiFi`

## Assignment of Device Topics

Topic | Description
-- | --
`encoder_action/pepeunit` | Действие энкодера: `One`, `Double`, `Long` (кнопка) или `Right`, `Left` (вращение)
`button_one_click_message/pepeunit` | Публикует `ONE_CLICK_MESSAGE` при одиночном клике (если задано)
`button_double_click_message/pepeunit` | Публикует `DOUBLE_CLICK_MESSAGE` при двойном клике (если задано)
`button_long_press_message/pepeunit` | Публикует `LONG_PRESS_MESSAGE` при долгом нажатии (если задано)
`encoder_right_rotate_message/pepeunit` | Публикует `RIGHT_ROTATE_MESSAGE` при повороте вправо (если задано)
`encoder_left_rotate_message/pepeunit` | Публикует `LEFT_ROTATE_MESSAGE` при повороте влево (если задано)

## Work algorithm

1. Подключение к `WiFi`
2. Подключение к `MQTT` Брокеру
3. Синхронизация времени по `NTP`
4. Инициализация пина кнопки и пинов энкодера (если `FF_ENCODER_ENABLE` = `true`)
5. Запуск цикла опроса кнопки и энкодера каждую миллисекунду
6. При нажатии кнопки или вращении энкодера: публикация действия в `encoder_action/pepeunit` (`One`, `Double`, `Long`, `Right`, `Left`)
7. При наличии `*_CLICK_MESSAGE` / `*_ROTATE_MESSAGE` — дополнительная публикация в соответствующий топик `*_message/pepeunit`

## Installation

1. Установите образ `Micropython` указанный в `firmware` на `esp8266`, как это сделано в [руководстве](https://micropython.org/download/ESP8266_GENERIC/)
2. Создайте `Unit` в `Pepeunit`
3. Установите переменные окружения в `Pepeunit`
4. Скачайте архив c программой из `Pepeunit`
5. Распакуйте архив в директорию
6. Загрузите файлы из директории на физическое устройство, например командой: `ampy -p /dev/ttyUSB0 -b 115200 put ./ .`
7. Запустить устройство нажатием кнопки `reset`
