# HA UniFi AP Control

A Home Assistant custom integration for controlling UniFi Access Points.

> ⚠️ **WARNING: AI Slop Coded**
>
> This integration was AI slop coded. While it has been tested, **do not use this in mission-critical situations**. Use at your own risk. The code may contain bugs, security issues, or unexpected behavior.

## Features

- **Power Control**: Adjust WiFi transmit power (low/medium/high/auto) for each radio band (2.4GHz, 5GHz, 6GHz)
- **LED Control**: Turn AP LEDs on/off
- **Auto Discovery**: Automatically discovers all APs on your UniFi controller
- **Real-time State**: Entities reflect the actual state from the controller

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select **Custom repositories**
4. Add `https://github.com/hairyfred/ha_unifi_ap_control` as an **Integration**
5. Click **Add**
6. Search for **"HA UniFi AP Control"** and install it
7. Restart Home Assistant

### Manual Installation

1. Copy the `ha_unifi_ap_control` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/ha_unifi_ap_control/
   ```

2. Restart Home Assistant

3. Go to **Settings → Devices & Services → Add Integration**

4. Search for **"HA UniFi AP Control"**

5. Enter your UniFi Controller details:
   - Controller URL (e.g., `https://192.168.1.1:8443`)
   - Username
   - Password
   - Site (usually `default`)

## Entities Created

For each Access Point, the integration creates:

| Entity Type | Example | Description |
|-------------|---------|-------------|
| Select | `select.<ap_name>_2_4ghz_power` | Control 2.4GHz radio power |
| Select | `select.<ap_name>_5ghz_power` | Control 5GHz radio power |
| Select | `select.<ap_name>_6ghz_power` | Control 6GHz radio power (if supported) |
| Switch | `switch.<ap_name>_led` | Turn AP LED on/off |

*Replace `<ap_name>` with your actual AP name (e.g., `select.living_room_2_4ghz_power`)*

## Example Automations

### Night Mode - Low Power & LEDs Off

```yaml
alias: UniFi APs - Night Mode
description: Set APs to low power and turn off LEDs at midnight
mode: single
triggers:
  - trigger: time
    at: "00:00:00"
conditions: []
actions:
  - action: select.select_option
    target:
      entity_id:
        - select.<your_ap_name>_2_4ghz_power  # Replace with your AP names
        - select.<your_ap_name>_5ghz_power
    data:
      option: low
  - action: switch.turn_off
    target:
      entity_id:
        - switch.<your_ap_name>_led  # Replace with your AP names
```

### Day Mode - High Power & LEDs On

```yaml
alias: UniFi APs - Day Mode
description: Set APs to high power and turn on LEDs at 6am
mode: single
triggers:
  - trigger: time
    at: "06:00:00"
conditions: []
actions:
  - action: select.select_option
    target:
      entity_id:
        - select.<your_ap_name>_2_4ghz_power  # Replace with your AP names
        - select.<your_ap_name>_5ghz_power
    data:
      option: high
  - action: switch.turn_on
    target:
      entity_id:
        - switch.<your_ap_name>_led  # Replace with your AP names
```

## Compatibility

- UniFi Controller (self-hosted)
- UniFi Cloud Key
- UniFi Dream Machine / Dream Machine Pro
- UniFi Dream Router

## Requirements

- Home Assistant 2023.1 or newer
- UniFi Controller with API access
- A local user account on the UniFi Controller (Ubiquiti cloud accounts are not supported as 2FA is not implemented). For security reasons, give this account minimal permissions

## License

This is free and unencumbered software released into the public domain. See [LICENSE](LICENSE) for details.
