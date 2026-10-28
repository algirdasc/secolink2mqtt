# Your support
This open-source project is developed in my free time. 
Your donation would help me dedicate more time and resources to improve project, add new features, fix bugs, 
as well as improve motivation and helps me understand, that this project is useful not only for me, but for more users.

<a href="https://www.buymeacoffee.com/Ua0JwY9" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Install (Docker)
Every push to `main` bumps the patch version (git tag `vX.Y.Z`) and publishes the image to
GitHub Container Registry: `ghcr.io/algirdasc/secolink2mqtt:<version>` and `:latest`.
(It is on ghcr.io, not Docker Hub. If the package is private, make it public in the package settings or `docker login ghcr.io`.)

1. Edit `config.ini` (see below).
2. `mkdir -p log && docker compose up -d`
3. Point your Secolink panel's monitoring/IP receiver to `<host>:8130`.

To build locally instead, replace `image:` in `docker-compose.yml` with `build: .`.

# Configuration (`config.ini`)
| Section | Key | Description |
|---|---|---|
| secolink | bind, port | listen address, default `0.0.0.0:8130` |
| secolink | encryption_key | panel encryption key |
| secolink | acc_number | panel account number, also used in MQTT topics |
| logging | filename, level | log file (default `log/event.log`) and level |
| mqtt | host, port, username, password, keepalive | broker settings (port 1883, keepalive 60 by default) |

# MQTT topics
All under `secolink/<account_number>/`: `availability`, `state`, `attributes`, and `set` (commands in).
The app reconnects to the broker automatically and re-publishes availability, attributes and last state after every reconnect.

# Intro
This is standalone Secolink2MQTT app for management of your Secolink alarm system. 
It is primarily used with Home-Assistant home automation system, but since it uses MQTT, it can be used with other home automation systems. 

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