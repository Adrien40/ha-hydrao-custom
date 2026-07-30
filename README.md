[![English](https://img.shields.io/badge/Language-English-red)](#) [![Français](https://img.shields.io/badge/Langue-Fran%C3%A7ais-blue)](README.fr.md)

# Hydrao Custom for Home Assistant 🚿
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Adrien40/ha-hydrao-custom)](https://github.com/Adrien40/ha-hydrao-custom/releases)

A **100% local integration for Home Assistant** that communicates directly via Bluetooth Low Energy (BLE) with your Hydrao shower device, to track your water consumption shower after shower, without any Cloud dependency. 🛡️

> ℹ️ **Good to know**: This integration directly queries the Hydrao device via Bluetooth while the water is running — this is necessary to read data and send settings live to the device.

If you find this project helpful, you can support its development 🙏

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="160"></a>

---

## ⚡ At a Glance
- 🔌 100% local operation via Bluetooth (BLE)
- 🏠 Home Assistant compatible (No Cloud)
- 🚿 Detailed tracking for each shower: Volume, duration, wasted cold water volume
- 🔄⭐ Comfort Mode Sync: Automatic reset of the device's counter as soon as the water reaches the defined Minimum Comfort Temperature
- 🎨 Configuration of the 4 liter thresholds and their colors via an integrated selector
- 🌡️ Minimum Comfort Temperature adjustable in Home Assistant (not sent to the Hydrao device)
- 🔘 "Shower Ended" button to manually close a shower or via automation (e.g., Hey Google, Shower Ended "Name") — <sub>an `input_boolean` may be required to link it to Google Assistant</sub>
- ⚙️ 2-minute installation via HACS

---

## 📸 Examples in Home Assistant

### 📊 Visualization

<p align="center">
  <img src="docs/screenshots/dashboard_overview.png" width="600">
</p>

<p align="center">
  <em>📊 Overview of shower data in Home Assistant</em>
</p>

### 🔍 Technical Details

<p align="center">
  <img src="docs/screenshots/entities_overview.png" width="600">
</p>

<p align="center">
  <em>🔍 Entities exposed by the integration & ⚙️ Advanced Configuration options</em>
</p>

---

### 💡 Why this integration?
This integration directly leverages your Hydrao's BLE protocol for comprehensive smart home tracking, without compromise:

* **🔒 100% local:** No internet connection required, data flows only from the shower to Home Assistant.
* **🚿 Precise tracking per shower:** Volume, duration, and most importantly, the cold water volume wasted before reaching the right temperature.
* **🔄 Comfort Mode Sync:** Restarts the device's counter as soon as the Minimum Comfort Temperature is reached, so the liter and color thresholds only reflect water that is actually comfortable and used.
* **🛡️ Future-proof:** No dependency on a third-party server or app.

---

### ✅ Compatibility / Prerequisites
* 🏷️ **Supported Models**: Hydrao devices broadcasting via Bluetooth (BLE) under an automatically detected name (`HYDRAO*`).
* 🏅 **Tested on**: Validated on the **Hydrao Aloé (HYDRA_SHOWER)**, Hardware version 9.
* 🛠️ **Required Hardware**: Internal Bluetooth adapter, Bluetooth USB dongle, or **ESPHome Bluetooth Proxy** (Recommended for range, [easy installation here](https://esphome.github.io/bluetooth-proxies/)).
* 💧 **Device Wake-up**: Hydrao only communicates via Bluetooth when water is flowing. Remember to run the water so the integration can read or write settings (thresholds, colors, soaping time).
* 📶 **Bluetooth Signal**: A dedicated RSSI sensor monitors signal quality in real time.

---

### ✨ Key Features
* 🔄⭐ **Comfort Mode Sync** (Switch): Automatic reset of the device's counter as soon as the water reaches the defined Minimum Comfort Temperature — the flagship feature of this integration.
* 🏠 **100% Local (BLE)**: Zero Cloud dependency.
* 💧 **Detailed Volumes**: Total cumulative volume, current shower volume, comfort volume, wasted volume (cold water) — available as session totals and lifetime totals.
* ⏱️ **Detailed Durations**: Current shower duration and time spent in the comfort zone.
* 🎨 **Thresholds & Colors**: Configure the 4 liter thresholds and their colors via an integrated selector, read and modified live on the device.
* 🌡️ **Minimum Comfort Temperature**: Adjustable in Home Assistant via a Number entity with validated range (0 - 50 °C) — this setting stays in Home Assistant and is never sent to the Hydrao device.
* 🧴 **Maximum Soaping Time**: Adjustable duration before the counters reset (10 to 600 seconds).
* 🔘 **"Shower Ended" Button**: Manually ends the current counting without waiting for the water to stop. <sub>Tip: an `input_boolean` may be required to link this button to Google Assistant.</sub>
* 🔵 **Detailed Bluetooth Status**: Water Off, Connecting, Connected, Error, Sending Configuration, Configuration Applied, Failed, or Restarting Device.
* 📋 **Pending Configuration**: Indicates at a glance if settings (thresholds, colors, soaping time) are queued to be sent to the device.
* 📶 **Live Bluetooth Signal** via passive scanning, without draining the device's battery.
* 🔧 **Diagnostic**: Firmware, Hardware, and Unique ID exposed as diagnostic sensors.
* ⚙️ **100% UI Configuration**: Automatic Bluetooth discovery or manual addition via MAC address; everything is managed from the Home Assistant interface.
* 🔄 **Reset to factory defaults** available directly from the options.

---

### 🚀 Installation

#### Via HACS (Recommended)
Since this repository is not (yet) in the default official list, you need to add it as a custom repository.

1. Open **HACS** in your Home Assistant.
2. Click on the 3 dots in the top right corner and select **Custom repositories**.
3. In **Repository**, paste the URL: `https://github.com/Adrien40/ha-hydrao-custom`
4. In **Type**, choose **Integration** and click **Add**.
5. Once added, a window appears: Click **Download** (Select the latest version).
6. **Completely restart Home Assistant**.
7. Go to **Settings** > **Devices & Services** > **Add integration** and search for "Hydrao Custom".

#### Manual
Copy the `custom_components/hydrao_custom` folder into your Home Assistant's `custom_components` folder, then restart.

---

### 📊 Available Sensors and Controls
| Entity | Unit / Type | Description |
| :--- | :--- | :--- |
| 🔘 **Shower Ended** | Button | Manually ends the current shower counting. |
| ⏱️ **Shower Duration** | min | Raw duration of the current shower. |
| ⏱️ **Comfort Shower Duration** | min | Time spent in the comfort zone. |
| 🌡️ **Temperature** | °C | Live water temperature. |
| 🚿 **Shower Volume** | L | Raw volume of the current shower. |
| 💧 **Comfort Shower Volume** | L | Volume used once the comfort temperature is reached, for the current shower. |
| 💧 **Total Cumulative Comfort Shower Volume** | L | Historical cumulative volume used in the comfort zone. |
| 💧 **Total Cumulative Shower Volume** | L | Total cumulative volume since installation. |
| ❄️ **Wasted Volume (Cold Water)** | L | Volume wasted before reaching the comfort temperature, for the current shower. |
| ❄️ **Total Cumulative Wasted Volume** | L | Historical cumulative wasted cold water volume. |
| 🔄 **Comfort Mode Sync** | Switch | Enables automatic reset as soon as the comfort temperature is reached. |
| 🌡️ **Minimum Comfort Temperature** | Number (°C) | Adjustable comfort threshold (0 - 50 °C). |
| 📋 **Pending Configuration** | Status | Setting(s) waiting to be sent to the device (None, Soaping Time, Thresholds, Colors, or combinations). |
| 💨 **Flow Rate** | L/min | Instantaneous water flow rate. |
| 🧴 **Maximum Soaping Time** | s | Currently configured maximum soaping time, read from the device. |
| 🔵 **Bluetooth Status** | Status | Water Off / Connecting / Connected / Error / Sending Configuration / Configuration Applied / Failed / Restarting Device. |
| 🟢🔵🩷🔴 **Threshold 1 to 4** | L | The 4 liter thresholds configured on the device, with their color as an attribute. |
| 📶 **Bluetooth Signal** | dBm | Real-time received Bluetooth signal strength. |
| 🔧 **Firmware / Hardware Version / Unique ID** | Diagnostic | Technical device information. |

---

## 🚀 Configuration
1. Go to **Settings** > **Devices & Services**.
2. **If the water is running and the Hydrao device is in range**, Home Assistant will detect it automatically: open the discovery notification and follow the wizard. **Otherwise**, click **Add integration**, search for **Hydrao Custom**, and manually enter the device's MAC address.
3. In both cases, you can set the Minimum Comfort Temperature during this step.

### ⚙️ Options
Once the device is added, click **Configure** ⚙️ to:
* Adjust the Minimum Comfort Temperature, Maximum Soaping Time, and Comfort Mode Sync.
* Modify the 4 liter thresholds and their colors (Only after a first successful connection — run the water to wake up the device).
* Reset to factory defaults in one click.

> ⚠️ **The water must be running** when submitting the form for the new thresholds to be sent to the device. If it's not, the state will show **"🚰 Water Off"** and the setting will remain visible in the **Pending Configuration** sensor until the next shower — and if the transfer fails even with the water running, the integration will automatically retry on the following shower.

---

### 🐛 Troubleshooting

<details>
<summary>⚠️ See common issues</summary>

* **Constantly showing "Water Off"**: Normal, the Hydrao only communicates via Bluetooth when water is flowing.
* **"Connection Error"**: Unlike "Water Off", this status means the device was detected in range, but the connection or reading still failed (signal too weak or unstable, or water turned off mid-shower). Move your antenna closer or [install an ESPHome Bluetooth Proxy](https://esphome.github.io/bluetooth-proxies/) near the shower.
* **"Configuration Failed"**: Writing the new settings to the device failed after several attempts. Don't worry: The change is not lost (visible in **Pending Configuration**), it will automatically be retried during the next shower.
* **Thresholds/Colors grayed out in options**: They can only be read/modified after a first successful connection — run the water once before adjusting them.

</details>

---

### 🤝 Contributions & Support
For any bug reports or feature requests, please open an [Issue](https://github.com/Adrien40/ha-hydrao-custom/issues) on this repository.

### ⚖️ License & Disclaimer
Project licensed under **GPLv3**. This is an independent project with no affiliation to the Hydrao company. The use of this software is at your own risk.

---

**Developed with ❤️ by @Adrien40**

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="180"></a>

<!-- Keywords: Home Assistant custom integration, BLE sensor, water saving, shower monitoring, local control -->
