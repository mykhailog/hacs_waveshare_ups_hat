# INA219 UPS HAT Integration for Home Assistant

This integration allows you to monitor any INA219 based UPS hat (e.g. [Waveshare UPS Hat](https://www.waveshare.com/wiki/UPS_HAT) or its clones) status in your Home Assistant instance.

<table border="0">
<tr>
<td valign="top"><img alt="Waveshare UPS hat" src="https://user-images.githubusercontent.com/1454659/114266149-595d6280-99fd-11eb-9056-dd0fbe178ecc.png" width="300" height="auto"></td>
<td valign="top"><img alt="INA219 UPS hat" src="https://raw.githubusercontent.com/odya/hass-ina219-ups-hat/33137ea16042972f65d71bea2709fe8e60679914/docs/INA219_3S_UPS.jpg" width="300" height="auto"></td>
</tr>
</table>

## Installation
### HACS
If you use [HACS](https://hacs.xyz/) you can install and update this component.
1. Go into HACS -> CUSTOM REPOSITORIES and add url: https://github.com/odya/hass-ina219-ups-hat with type "integration"
2. Go to integration, search "ina219_ups_hat" and click *Install*.


### Manual
Download and unzip or clone this repository and copy `custom_components/ina219_ups_hat/` to your configuration directory of Home Assistant, e.g. `~/.homeassistant/custom_components/`.

In the end your file structure should look like that:
```
~/.homeassistant/custom_components/ina219_ups_hat/__init__.py
~/.homeassistant/custom_components/ina219_ups_hat/manifest.json
~/.homeassistant/custom_components/ina219_ups_hat/sensor.py
~/.homeassistant/custom_components/ina219_ups_hat/binary_sensor.py
~/.homeassistant/custom_components/ina219_ups_hat/const.py
~/.homeassistant/custom_components/ina219_ups_hat/ina219.py
~/.homeassistant/custom_components/ina219_ups_hat/ina219_wrapper.py
```

## Configuration
### Sensor
Create a new sensor entry in your `configuration.yaml` 

```yaml
sensor:
  - platform: ina219_ups_hat
    name: Hassio UPS          # Optional
    unique_id: hassio_ups     # Optional
    scan_interval: 60         # Optional
    batteries_count: 3        # Optional
    max_soc: 91               # Optional
    battery_capacity: 9000    # Optional
    sma_samples: 5            # Optional
```
Following data can be read:
 - SoC (State of Charge)
 - Voltage
 - Current
 - Power
 - Charging Status
 - Online Status
 - Remaining Capacity
 - Remaining Time

If you consistently experience capacity below 100% when the device is fully charged, you can adjust it using the `max_soc` property.

```yaml
sensor:
  - platform: ina219_ups_hat
    max_soc: 91                      
```

#### SMA Filtering
By default, the SMA5 filter is applied to the measurements from INA219. That's necessary to filter out noise from the switching power supply and provide smoother readings. You can control the window size with the `sma_samples` property.

```yaml
sensor:
  - platform: ina219_ups_hat
    max_soc: 91
    sma_samples: 10                    
```

*Tip:* Doubled window size is used for calculation of SoC, Remaining Battery Capacity and Remaining Time

#### Batteries Count
The original Waveshare UPS Hat has 2 batteries in series (8.4V), but some versions of the UPS Hats may have 3 batteries (12.6V). If you have more than 2 batteries in series, use the `batteries_count` parameter.

### Example automations
Copy contents of [examples/automations.yaml](/examples/automations.yaml) to your `automations.yaml`. Customize.

## Directions for installing smbus support on Raspberry Pi

### HassOS

To enable i2c in Home Assistant OS System follow this [instruction](https://www.home-assistant.io/common-tasks/os/#enable-i2c) or
use this [addon](https://community.home-assistant.io/t/add-on-hassos-i2c-configurator/264167)

### Home Asisstant Core

Enable I2c interface with the Raspberry Pi configuration utility:

```bash
# pi user environment: Enable i2c interface
$ sudo raspi-config
```

Select `Interfacing options->I2C` choose `<Yes>` and hit `Enter`, then go to `Finish` and you'll be prompted to reboot.

Install dependencies for use the `smbus-cffi` module and enable your `homeassistant` user to join the _i2c_ group:

```bash
# pi user environment: Install i2c dependencies and utilities
$ sudo apt-get install build-essential libi2c-dev i2c-tools python-dev libffi-dev

# pi user environment: Add homeassistant user to the i2c group
$ sudo addgroup homeassistant i2c

# pi user environment: Reboot Raspberry Pi to apply changes
$ sudo reboot
```

#### Check the i2c address of the sensor

After installing `i2c-tools`, a new utility is available to scan the addresses of the connected sensors:

```bash
/usr/sbin/i2cdetect -y 1
```

It will output a table like this:

```text
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- 23 -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- UU -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- 77
```

## Thanks
Most of the code was written by [@mykhailog](https://github.com/mykhailog), the author of the original [integration](https://github.com/mykhailog/hacs_waveshare_ups_hat). Unfortunately, his repository seems to be inactive, so I decided to fork it.

## Notes
- Original [waveshare_ups_hat](https://github.com/mykhailog/hacs_waveshare_ups_hat) integration by [@mykhailog](https://github.com/mykhailog) (seems to be dead)
- Cheap [INA219 UPS Hat](https://www.aliexpress.com/item/1005005071564178.html) module from AliExpress

## License
MIT 2023
