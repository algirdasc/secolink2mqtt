# Your support
<a href="https://www.buymeacoffee.com/Ua0JwY9" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Intro
This is standalone Secolink2MQTT app for management of your Secolink alarm system. It is primarily used with Home-Assistant home automation system, but since it uses MQTT, it can be used with other home automation systems. 

# Home Assistant configuration example
```yaml
- platform: mqtt
  name: home
  availability_topic: secolink/<account_number>/availability
  command_topic: secolink/<account_number>/set
  command_template: '{{code}}{{action}}'
  state_topic: secolink/<account_number>/state
  payload_arm_away: A
  payload_arm_home: AS
  payload_arm_night: AN
  payload_disarm: D
  code: REMOTE_CODE
```