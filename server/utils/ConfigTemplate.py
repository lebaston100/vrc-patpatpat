"""This holds a clean version of the config for use when creating new
entries or whenever needed
"""

# TODO:
# We need more specific templates for all the different solver types.
# Those could be used in the ui


class ConfigTemplate:
    TEMPLATE = {
        "configVersion": 1,
        "program": {
            "vrcOscSendPort": 9001,
            "vrcOscReceivePort": 9000,
            "vrcOscReceiveAddress": "127.0.0.1",
            "mainTps": 40,
            "logLevel": "DEBUG"
        },
        "esps": {
            "esp0": {
                "id": 0,
                "name": "HardwareDevice 1",
                "connectionType": "OSC",
                "lastIp": "127.0.0.1",
                "wifiMac": "FF:FF:FF:AA:AA:AA",
                "serialPort": "",
                "numMotors": 0
            }
        },
        "groups": {
            "group0": {
                "id": 0,
                "name": "Group 1",
                "motors": [
                    {
                        "name": "Motor 1",
                        "espAddr": [
                            0,
                            1
                        ],
                        "minPwm": 70,
                        "maxPwm": 255,
                        "xyz": [
                            1.0,
                            2.0,
                            3.0
                        ],
                        "r": 1.0
                    }
                ],
                "avatarPoints": [
                    {
                        "name": "Point 1",
                        "receiverId": "contact_1",
                        "xyz": [
                            1.0,
                            2.0,
                            3.0
                        ],
                        "r": 1.0
                    }
                ],
                "solver": {
                    "solverType": "MLat",
                    "strength": 100,
                    "MLat_enableHalfSphereCheck": True,
                    "contactOnly": False
                }
            }
        }
    }
