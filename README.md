# vrc-patpatpat

<p align="center">
    <a href="//github.com/lebaston100/vrc-patpatpat/commits/refactor/" alt="Commits"><img alt="GitHub commit activity (branch)" src="https://img.shields.io/github/commit-activity/m/lebaston100/vrc-patpatpat/refactor"></a>
    <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/lebaston100/vrc-patpatpat/build.yml?branch=refactor">
    <a href="//github.com/lebaston100/vrc-patpatpat/actions/workflows/test.yaml" alt="test"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/lebaston100/vrc-patpatpat/test.yaml?branch=refactor&label=test"></a>
    <a href="//github.com/lebaston100/vrc-patpatpat?tab=GPL-3.0-1-ov-file#readme" alt="licence"><img alt="GitHub License" src="https://img.shields.io/github/license/lebaston100/vrc-patpatpat"></a>
    <a href="#" alt="stars"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/lebaston100/vrc-patpatpat"></a>
</p>

An open hardware and software project which tries to implement spatial haptic head pat (but also more generic) feedback to the player in VRchat.

## This project is actively work in progress

### Development TODO list

Server:

- [x] Main UI
- [x] Configuration windows
- [x] 3D visualizer
- [x] Log viewer
- [x] Config file
- [x] VRC comms
- [x] Hardware discovery
- [x] Hardware comms
- [x] MLAT solver
- [x] Linear solver
- [x] Slipserial support (base is there, but no priority)
- [ ] Fix bugs and improve code

Hardware:

- [x] Discovery logic
- [x] OTA support

Misc:

- [x] Simple osc recorder and player (for dev) (server/tools/oscRecReplayer.py)
- [x] Design dev pcb (v1 dev board manufactured and built, v2 dev board design done)
- [ ] Rewrite readme
- [ ] Add CI pytest job for server (more tests need to be written)
- [ ] Add CI build job for server (needs improvement)

# Software

![Screenshot of the main ui as of 09.03.2024](https://raw.githubusercontent.com/lebaston100/vrc-patpatpat/refactor/assets/main-ui-1.jpg)

### Basic Concepts/Terminology

Hardware Device: A HardwareDevice represents a physical hardware (ESP) device that receives realtime haptic data from the server.

Contact Group: A ContactGroup holds everything required to drive that hardware. This includes knowing the proporties of the VRChat contact receivers, motors and the solver.

Motor: A Motor is part of a contact group and represents a Motor that is beeing driven by the data produced by the Solver. Each motor has an address configuration that links it to the correct channel on a Hardware Device.

Solver: A Solver is what takes the input from the contact receiver(s) and transforms it into speed for all configured Motors.

### Solvers

There are currently 2 Solvers implemented:

#### MLat

This solver uses a localization technique called [Multilateration](https://en.wikipedia.org/wiki/Pseudo-range_multilateration) to calculate a 3d position of a contact sender (eg a users hand) using the distance of (at least) 3 known points on the avatar. This enables us to have real positional feedback without adding tons of contact receivers and synced parameters to the avatar. For example for perfect tracking on a head you can simply get away with 4 contact receives while having (theoreticaly) unlimited amount of physical feedback points(motors) distibuted inside the usable tracked zone. This idea of mine (initial implementation [here](https://github.com/lebaston100/vrc-patpatpat/commit/aa33e5e41202b058c82532f4fd79569b7d9bcd51)) was the main reason to fork patstrap and as far as i'm aware, this is the first project using this technique.

#### Single n:n

This solver simply takes the min/max/mean value of all configured contact receivers (1-n) and drives all configured motors with the same computed speed. Very usefull for single contact receiver -> motor setups.

### Firewall

Your windows firewall might block incoming and/or outgoing udp connection to the hardware. If that happens you can run server/firewall.bat (as admin!) to automatically create firewall exceptions for the required ports.

# Hardware

The hardware component of the project is defined very losely by design. You are free to follow what i built, or design your entire hardware from scratch. The only requirement in that the hardware can send and receive OSC over UDP or Serial.

### Development/My hardware

For development (and also future use) i have created a full pcb design that uses:
- a Wemos S2 Mini
- a ULN2003 driver board for up to 7 pwm channels
- a single 18650 cell holder
- a TP4046 charging module for the 18650 cell
- coin cell style [vibration motors](https://www.aliexpress.com/item/4000245243914.html) as haptic devices

## Firmware

Current firmware implementation has been developed for and tested on a Wemos D1 Mini (ESP8266) and Wemos S2 Mini(ESP32-S2). Though i don't see why any other ESP based microcontroller (except maybe the newer RISC-V ones?) should work too.

#### Wifi

To configure the wifi credentials, inside the firmware dictory rename wifi.ini.template to wifi.ini and change the values inside the file to your wifi network. You need to flash the firmware (again) if you changed them.

# Setup (todo)

This is currently just a rough overview to be re-written in more detail.

## Hardware
- Build hardware
- Mount to headset

## Firmware
- Set wifi credentials
- Set pwm output pins
- Flash firmware

## Software
- Add contact receivers to avatar in unity
- Configure contact group in software

## Readme notes (for me)

Other stuff/notes to add to the readme:

- Revise head mounting options for motors (idea-prototype beeing worked on)
- Update unity guide for positioning and coordinates
- Add wiring for battery voltage measurement
- Don't forget pcb BOM and pcb specific software stuff


## Tech stack

- Language: Python 3.12
- GUI framework: QT6 via PyQt6
- Hardware communication: OSC over UDP
- Embedded firmware: Arduino-flavoured c++ (using PIO)

## Credits

This project initially started as a fork of [https://github.com/danielfvm/Patstrap](https://github.com/danielfvm/Patstrap) but now has been rewritten from ground up.

This project uses a few smaller parts(to be specific some of the circuit schematics) from the [SlimeVR](https://www.crowdsupply.com/slimevr/slimevr-full-body-tracker) Project which is an open hardware, full body tracking solution and a great project to checkout. (I use it myself!)

It also makes use of the following python libraries:
- [PyQt6](https://pypi.org/project/PyQt6/)
- [python-osc](https://pypi.org/project/python-osc/)
- [numpy](https://pypi.org/project/numpy/)
- [scipy](https://pypi.org/project/scipy/)
- [multilateration](https://github.com/valentinbarral/Multilateration)
- [PyInstaller](https://pypi.org/project/pyinstaller/)
- [pytest](https://pypi.org/project/pytest/)