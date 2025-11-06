# ST7735S Robot Face Display - Viam Module

Viam Vision Service module voor het ST7735S (W180-1281260-RGB-8-V1.0) display om robot gezichtjes te tonen.

## Features

- **6 verschillende gezichtsuitdrukkingen**: happy, sad, surprised, sleepy, angry, neutral
- **Do Command API**: Bestuur het gezicht via Viam commands
- **Real-time updates**: Verander expressies direct vanaf je website/app
- **SPI communicatie**: Gebruikt hardware SPI voor snelle updates

## Hardware Setup

### Benodigdheden
- Raspberry Pi 4B
- ST7735S Display (W180-1281260-RGB-8-V1.0)
- Jumper wires

### Pin Verbindingen

**ST7735S → Raspberry Pi:**
```
VCC   → Pin 1  (3.3V) ⚠️ NIET 5V!
GND   → Pin 6  (GND)
SCL   → Pin 23 (GPIO 11 / SPI0 SCLK)
SDA   → Pin 19 (GPIO 10 / SPI0 MOSI)
RES   → Pin 22 (GPIO 24) - Reset
DS    → Pin 18 (GPIO 25) - Data/Command (DC)
CS    → Pin 24 (GPIO 8  / CE0) - Chip Select
BLK   → Pin 1  (3.3V) - Backlight
```

**Pin Assignment:**
- **VCC**: 3.3V power (⚠️ **NOT** 5V - will damage display!)
- **GND**: Ground
- **SCL**: SPI Clock (fixed to GPIO 11)
- **SDA**: SPI MOSI (fixed to GPIO 10)
- **RES**: Reset pin (configurable, default GPIO 24)
- **DS**: Data/Command pin (configurable, default GPIO 25)
- **CS**: Chip Select (configurable, default GPIO 8)
- **BLK**: Backlight power (3.3V)

### SPI Inschakelen

```bash
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

Verifieer SPI:
```bash
ls /dev/spi*
# Output: /dev/spidev0.0  /dev/spidev0.1
```

## Installatie

### Via Viam Registry

Voeg toe aan je robot config (`app.viam.com`):

```json
{
  "modules": [
    {
      "type": "registry",
      "name": "wootter_st7735s",
      "module_id": "wootter:st7735s",
      "version": "1.0.0"
    }
  ],
  "services": [
    {
      "name": "st7735s_display",
      "namespace": "rdk",
      "type": "vision",
      "model": "wootter:vision:st7735s",
      "attributes": {
        "cs_pin": 8,
        "dc_pin": 25,
        "reset_pin": 24,
        "rotation": 90
      }
    }
  ]
}
```

### Configuratie Opties

| Attribuut | Type | Default | Beschrijving |
|-----------|------|---------|--------------|
| `cs_pin` | int | 8 | GPIO pin voor Chip Select (CS) |
| `dc_pin` | int | 25 | GPIO pin voor Data/Command (DS) |
| `reset_pin` | int | 24 | GPIO pin voor Reset (RES) |
| `rotation` | int | 90 | Scherm rotatie (0, 90, 180, 270) |
| `width` | int | 128 | Display breedte in pixels |
| `height` | int | 160 | Display hoogte in pixels |

## Gebruik

### Via Viam SDK (Python)

```python
from viam.robot.client import RobotClient

async def main():
    robot = await RobotClient.at_address('YOUR_ROBOT_ADDRESS').connect()
    
    # Get the display service
    display = robot.get_service("st7735s_display")
    
    # Set expression
    await display.do_command({
        "command": "set_face",
        "expression": "happy"
    })
    
    # Get current expression
    result = await display.do_command({"command": "get_face"})
    print(result)  # {"current_face": "happy"}
    
    # Clear display
    await display.do_command({"command": "clear"})
    
    await robot.close()
```

### Beschikbare Expressies

- `"happy"` - Blije robot met smile 😊
- `"sad"` - Verdrietige robot met frons 😢
- `"surprised"` - Verraste robot met grote ogen 😲
- `"sleepy"` - Slaperige robot met Z's 😴
- `"angry"` - Boze robot met rode ogen 😠
- `"neutral"` - Neutrale robot expressie 😐

### Do Command API

#### Set Face
```python
await display.do_command({
    "command": "set_face",
    "expression": "happy"  # of: sad, surprised, sleepy, angry, neutral
})
# Returns: {"success": true, "expression": "happy"}
```

#### Get Current Face
```python
await display.do_command({
    "command": "get_face"
})
# Returns: {"current_face": "happy"}
```

#### Clear Display
```python
await display.do_command({
    "command": "clear"
})
# Returns: {"success": true}
```

#### Custom Text (experimental)
```python
await display.do_command({
    "command": "custom_text",
    "text": "Hello!",
    "x": 10,
    "y": 50
})
# Returns: {"success": true, "text": "Hello!"}
```

## Automatisch Gezicht Updaten

Combineer met je sensors om automatisch te reageren:

```python
from viam.robot.client import RobotClient
import asyncio

async def auto_face():
    robot = await RobotClient.at_address('localhost:8080').connect()
    
    display = robot.get_service("st7735s_display")
    motion = robot.get_component("motion_sensor")
    light = robot.get_component("light_sensor")
    
    while True:
        motion_data = await motion.get_readings()
        light_data = await light.get_readings()
        
        # Reageer op omgeving
        if motion_data["motion_detected"]:
            await display.do_command({"command": "set_face", "expression": "surprised"})
        elif light_data["lux"] < 10:
            await display.do_command({"command": "set_face", "expression": "sleepy"})
        else:
            await display.do_command({"command": "set_face", "expression": "happy"})
        
        await asyncio.sleep(1)

asyncio.run(auto_face())
```

## Troubleshooting

### Display blijft zwart
- Check of SPI enabled is: `ls /dev/spi*`
- Controleer pin verbindingen (vooral CS, DC, RST)
- Controleer 3.3V power (NIET 5V!)
- Check backlight (BLK) verbinding

### Permission errors
```bash
# Add user to SPI group
sudo usermod -a -G spi $USER
sudo reboot
```

### Module errors in logs
```bash
# Clear module cache
rm -rf ~/.viam/packages/data/module/*

# Restart Viam
sudo systemctl restart viam-server
```

## Development

### Lokaal testen
```bash
cd ST7735S
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m src
```

### Deploy nieuwe versie
```bash
git add .
git commit -m "Update robot face module"
git push
git tag v1.0.1
git push origin v1.0.1
```

## License

MIT License - zie LICENSE file

## Auteur

Wootter - Voor school AI assistant project
