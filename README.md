# RuCaptcha Home Assistant Integration

This custom integration allows you to monitor your RuCaptcha balance in Home Assistant.

## Installation

1. Copy the `custom_components/rucaptcha` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "RuCaptcha"
5. Enter your RuCaptcha API key

## Configuration

The integration requires:
- Your RuCaptcha API key (obtain from your RuCaptcha account dashboard)
- Update interval in minutes (1-1440 minutes, default: 1 minute)
- Currency display label (RUB, EUR, USD, default: RUB - note: API returns balance in default currency, this only changes the display label)

## Features

- Monitors your RuCaptcha balance
- Configurable update interval (1-1440 minutes)
- Configurable currency display label (RUB, EUR, USD)
- Shows as unavailable if API calls fail

## Sensor

The integration creates a sensor called `sensor.rucaptcha_balance` that shows your current balance.

## Usage in Automations

You can use the sensor in automations to get notified when your balance is low:

```yaml
automation:
  - alias: "Low RuCaptcha Balance Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.rucaptcha_balance
      below: 10
    action:
      service: notify.notify
      data:
        message: "RuCaptcha balance is low: {{ states('sensor.rucaptcha_balance') }} {{ state_attr('sensor.rucaptcha_balance', 'unit_of_measurement') }}"
```

## Troubleshooting

If the sensor shows as unavailable:
1. Check your API key is correct
2. Ensure you have internet connectivity
3. Check the Home Assistant logs for error messages
4. Verify your RuCaptcha account is active