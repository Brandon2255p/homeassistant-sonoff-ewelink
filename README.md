# eWeLink Sonoff for Home Assistant Integration
Home Assistant Integration for Sonoff eWeLink smart devices. Using the stock firmware, works alongside the eWeLink mobile app!

This was inspired by [HASS-sonoff-ewelink](https://github.com/peterbuga/HASS-sonoff-ewelink)


***
### DISCLAIMER: This is a very new library so use at your own risk!
***

***
### WARNING: completely deactivate the `sonoff` integration from Home Assistant while doing a firmware update, due to auto-relogin function you might be kicked out of the app before the process is completed. I would not be held liable for any problems occuring if not following this steps!
***

## Installation
And copy the *.py files in `custom_components` folder using the same structure like defined here:
```
 custom_components
    └── sonoff
        └── __init__.py
        └── switch.py
        └── sensor.py
```

1. Open the integrations page in Home Assistant e.g.: http://homeassitant.local/config/integrations
2. Click `Add Integration`
3. Choose for `eWeLink Sonoff`
4. Enter your eWeLink login credentials

## Credits 
- [@peterbuga](https://github.com/peterbuga) for providing a good base to work with
- [@skydiver](https://github.com/skydiver) for the super useful eWeLink API in javascript [@skydiver](https://github.com/skydiver/ewelink-api)  
