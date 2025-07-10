# RuCaptcha / 2Captcha Balance Sensor

Monitor your RuCaptcha or 2Captcha balance directly in Home Assistant. Both services are from the same company and use identical APIs.

## Features

- 🌐 Support for both RuCaptcha and 2Captcha services
- 🔄 Configurable update interval (1-1440 minutes, default: 1 minute)
- 💰 Configurable currency display label (RUB, EUR, USD)
- 📊 Integration with Home Assistant sensors
- 🔔 Use in automations for low balance alerts
- ⚙️ Easy configuration through Home Assistant UI
- 🔁 Automatic retry with exponential backoff
- 🎨 Dynamic icons based on balance level

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL and select "Integration" as category
5. Click "Add"
6. Search for "RuCaptcha" and install
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/captcha_balance` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click "Add Integration"
3. Search for "RuCaptcha"
4. Select your service (RuCaptcha or 2Captcha)
5. Enter your API key, update interval, and currency display label

## Usage

The integration creates a sensor `sensor.captcha_balance` that shows your current balance.

### Automation Example

```yaml
automation:
  - alias: "Low Balance Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.captcha_balance
      below: 10
    action:
      service: notify.notify
      data:
        message: "Captcha service balance is low: {{ states('sensor.captcha_balance') }} {{ state_attr('sensor.captcha_balance', 'unit_of_measurement') }}"
```

## Support

If you encounter any issues, please report them on the GitHub repository.