## Sumsg Smart

[中文说明](readme_zh.md)

### Introduction

This custom integration enables SUMSG platform smart devices to connect to the Home Assistant platform.

### Supported Devices

| Model          | Product Name          |
|----------------|-----------------------|
| pcSw1          | WiFi Boot Card Gen 1  |
| pcS3           | WiFi Boot Card Gen 2  |
| powerSwitch1   | Smart Switch Gen 1    |
| pcHealth1      | PC Hardware Monitor   |

### Installation

Extract the library files into the `custom_components` directory of Home Assistant.  
If the `custom_components` directory doesn't exist, create it first.  
The directory structure should look like this:

```
-config
–-custom_components
—--sumsg_smart
```

### Configuration

1. Restart Home Assistant.
2. Search for `Sumsg Smart` in the integrations list.
3. Enter your [SUMSG platform account and password](https://app.sumsg.com).
