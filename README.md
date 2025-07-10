# RuCaptcha / 2Captcha Home Assistant Integration

This custom integration allows you to monitor your RuCaptcha or 2Captcha balance in Home Assistant. Both services are from the same company and use identical APIs.

## Installation

1. Copy the `custom_components/rucaptcha` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "RuCaptcha"
5. Select your service (RuCaptcha or 2Captcha)
6. Enter your API key

## Configuration

The integration requires:
- Service selection (RuCaptcha or 2Captcha)
- Your API key (obtain from your account dashboard)
- Update interval in minutes (1-1440 minutes, default: 1 minute)
- Currency display label (RUB, EUR, USD, default: RUB - note: API returns balance in default currency, this only changes the display label)

## Features

- Supports both RuCaptcha and 2Captcha services
- Monitors your account balance
- Configurable update interval (1-1440 minutes)
- Configurable currency display label (RUB, EUR, USD)
- Shows as unavailable if API calls fail
- Automatic retry with exponential backoff
- Dynamic icons based on balance level

## Sensor

The integration creates a sensor called `sensor.captcha_balance` that shows your current balance. The sensor name will reflect the selected service (RuCaptcha Balance or 2Captcha Balance).

## Usage in Automations

You can use the sensor in automations to get notified when your balance is low:

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

## Troubleshooting

If the sensor shows as unavailable:
1. Check your API key is correct for the selected service
2. Ensure you have internet connectivity
3. Check the Home Assistant logs for error messages
4. Verify your account is active and has sufficient funds