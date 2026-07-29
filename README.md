[![Français](https://img.shields.io/badge/Langue-Fran%C3%A7ais-blue)](README.fr.md) [![English](https://img.shields.io/badge/Language-English-red)](#)

# Hydrao Custom for Home Assistant 🚿
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Adrien40/ha-hydrao-custom)](https://github.com/Adrien40/ha-hydrao-custom/releases)

If this project is useful to you, you can support its development 🙏

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="160"></a>

---

## ⚡ Summary
- 🔌 100 % local operation via Bluetooth (BLE)
- 🏠 Compatible with Home Assistant (No cloud)
- 🚿 Detailed tracking of each shower : Volume, duration, cold water lost
- 🔄⭐ Comfort Mode Sync : Automatic reset of the device's counter as soon as the water reaches the defined Minimum Comfort Temperature
- 🎨 Set the 4 liter thresholds and choose their color via a built-in direct picker
- 🌡️ Minimum Comfort Temperature adjustable in Home Assistant (never sent to the Hydrao device)
- 🔘 "Shower Finished" button to manually end a shower or via an automation (E.g. : Hey Google, Shower Finished FirstName) — <sub>an `input_boolean` may be needed to link it to Google Assistant</sub>
- ⚙️ Installation via HACS in 2 minutes

---

## 📸 Examples in Home Assistant

### 📊 Visualization

<p align="center">
  <img src="docs/screenshots/dashboard_overview.png" width="600">
</p>

<p align="center">
  <em>📊 Overview of shower data in Home Assistant</em>
</p>

---

### 🔍 Technical Details

<p align="center">
  <img src="docs/screenshots/entities_overview.png" width="600">
</p>

<p align="center">
  <em>🔍 Entities exposed by the integration & ⚙️ Advanced Configuration options</em>
</p>

> *(Screenshots to be added in `docs/screenshots/` — see note at the end of the file.)*

---

A **100 % local integration for Home Assistant** that communicates directly over Bluetooth Low Energy (BLE) with your Hydrao shower device, to track your shower water consumption, shower after shower, with no dependency on the Cloud. 🛡️

> ⚠️ **Warning** : This integration directly queries the Hydrao device over Bluetooth while the water is running.

### 💡 Why this integration ?
This integration directly leverages your Hydrao's BLE protocol for complete home automation tracking, with no compromises :

* **🔒 100 % local :** No internet connection required, data flows only from the shower to Home Assistant.
* **🚿 Precise per-shower tracking :** Volume, duration, and above all the amount of cold water lost before the water reaches the right temperature.
* **🔄 Comfort Mode Sync :** Restarts the counter on the device as soon as the Minimum Comfort Temperature is reached, so that the liter thresholds and colors only reflect water that was actually comfortable and therefore used.
* **🛡️ Longevity :** No dependency on any server or third-party app.

---

### ✅ Compatibility / Requirements
* 🏷️ **Supported models** : Hydrao devices broadcasting over Bluetooth (BLE) under an automatically detected name (`HYDRAO*`).
* 🏅 **Tested on** : Validated on the **Hydrao Aloé (HYDRA_SHOWER)**, Hardware version 9.
* 🛠️ **Required hardware** : Internal Bluetooth adapter, USB Bluetooth dongle, or an **ESPHome Bluetooth Proxy** (Recommended for range, [easy setup here](https://esphome.github.io/bluetooth-proxies/)).
* 💧 **Waking the device** : The Hydrao only communicates over Bluetooth while the water is running, so make sure the water is flowing for the integration to read or write settings (thresholds, colors, lathering time).
* 📶 **Bluetooth signal** : A dedicated RSSI sensor lets you monitor signal quality live.

---

### ✨ Key Features
* 🔄⭐ **Comfort Mode Sync** (Switch) : Automatic reset of the device's counter as soon as the water reaches the defined Minimum Comfort Temperature — the flagship feature of this integration.
* 🏠 **100 % Local (BLE)** : No dependency on the Cloud.
* 💧 **Detailed volumes** : Total cumulative volume, current shower volume, comfort volume, lost volume (cold water) — both per session and cumulative total.
* ⏱️ **Detailed durations** : Duration of the current shower and time spent in the comfort zone.
* 🎨 **Thresholds & Colors** : Set the 4 liter thresholds and choose their color via a built-in direct picker, read and updated live on the device.
* 🌡️ **Minimum Comfort Temperature** : Adjustable in Home Assistant via a Number entity, with a validated range (0 - 50 °C) — this setting stays in Home Assistant and is never sent to the Hydrao device.
* 🧴 **Maximum Lathering Time** : Duration before the counters reset, adjustable (10 to 600 seconds).
* 🔘 **"Shower Finished" button** : Manually ends the current shower count without waiting for the water to be turned off. <sub>Tip: an `input_boolean` may be needed to link this button to Google Assistant.</sub>
* 🔵 **Detailed Bluetooth state** : Water Off, Connecting, Connected, Error, Sending Configuration, Configuration Applied, Failed, or Rebooting Device (with **automatic retry on the next shower** in case of a write failure).
* 📋 **Pending Configuration** : Shows at a glance whether any settings (thresholds, colors, lathering time) have not been sent to the device yet.
* 📶 **Live Bluetooth signal** via passive listening, without polling the device or draining its battery.
* 🔧 **Diagnostics** : Firmware, Hardware, and Unique Identifier of the device exposed as diagnostic sensors.
* ⚙️ **100 % UI configuration** : Automatic Bluetooth discovery or manual addition by MAC address, everything is set up from the Home Assistant interface.
* 🔄 **Factory reset** available directly from the options.

---

### 🚀 Installation

#### Via HACS (Recommended)
Since this repository is not (yet) in the official default list, you need to add it as a custom repository.

1. Open **HACS** in your Home Assistant.
2. Click the 3 dots in the top right corner and select **Custom repositories**.
3. In **Repository**, paste the URL : `https://github.com/Adrien40/ha-hydrao-custom`
4. In **Type**, choose **Integration**, then click **Add**.
5. Once added, a window will appear : Click **Download** (Select the latest version).
6. **Fully restart Home Assistant**.
7. Go to **Settings** > **Devices & Services** > **Add Integration** and search for "Hydrao Custom".

#### Manual
Copy the `custom_components/hydrao_custom` folder into the `custom_components` folder of your Home Assistant configuration, then restart.

---

### 📊 Available Sensors and Controls
| Entity | Unit / Type | Description |
| :--- | :--- | :--- |
| 🌡️ **Temperature** | °C | Water temperature measured live. |
| 💧 **Total Cumulative Volume** | L | Total volume accumulated since installation. |
| 💨 **Flow Rate** | L/min | Instantaneous water flow rate. |
| ❄️ **Lost Volume (Cold Water)** | L | Volume lost before reaching the comfort temperature, for the current shower. |
| ❄️ **Total Cumulative Lost Volume** | L | Historical cumulative volume of cold water lost. |
| 💧 **Comfort Volume** | L | Volume used once the comfort temperature is reached. |
| 🚿 **Shower Volume** | L | Raw volume of the current shower. |
| ⏱️ **Shower Duration** | min | Raw duration of the current shower. |
| ⏱️ **Comfort Duration** | min | Time spent in the comfort zone. |
| 🟢🔵🩷🔴 **Threshold 1 to 4** | L | The 4 liter tiers configured on the device, with their color as an attribute. |
| 🔵 **Bluetooth State** | Status | Water Off / Connecting / Connected / Error / Sending Configuration / Configuration Applied / Failed / Rebooting Device. |
| 📋 **Pending Configuration** | Status | Setting(s) still waiting to be sent to the device (None, Lathering, Thresholds, Colors, or combinations). |
| 📶 **Bluetooth Signal** | dBm | Bluetooth signal strength received in real time. |
| 🔧 **Firmware / Hardware Version / Unique Identifier** | Diagnostic | Technical information about the device. |
| 🌡️ **Minimum Comfort Temperature** | Number (°C) | Adjustable comfort threshold (0 - 50 °C). |
| 🔄 **Comfort Mode Sync** | Switch | Enables automatic reset as soon as comfort is reached. |
| 🔘 **Shower Finished** | Button | Manually ends the current shower count. |

---

## 🚀 Configuration
1. Go to **Settings** > **Devices & Services**.
2. The integration automatically detects your Hydrao if the water is running and the device is in range (Or add it manually by MAC address).
3. Click **Add Integration** and search for **Hydrao Custom**.
4. Adjust the Minimum Comfort Temperature at this step if needed.

### ⚙️ Options
Once the device has been added, click **Configure** ⚙️ to :
* Adjust the Minimum Comfort Temperature, the Maximum Lathering Time, and the Comfort Mode Sync.
* Modify the 4 liter thresholds and their colors (Only once a first connection has been established — run the water to wake up the device).
* Reset to factory settings with one click.

> ⚠️ **The water must be running** when the form is submitted for the new thresholds to be sent to the device. If not, the status will show **"🚰 Water Off"** and the setting will remain visible in the **Pending Configuration** sensor until the next shower — and if the write still fails once the water is running, the integration will automatically retry on the following shower.

---

### 🐛 Troubleshooting

<details>
<summary>⚠️ See common issues</summary>

* **"Water Off" permanently** : Normal, the Hydrao only communicates over Bluetooth while the water is running.
* **"Connection Error"** : Unlike "Water Off", this status means the device was actually detected in range, but the connection or read still failed (weak or unstable signal, or a drop-out mid-shower). Move your antenna closer or [install an ESPHome Bluetooth Proxy](https://esphome.github.io/bluetooth-proxies/) near the shower.
* **"Configuration Failed"** : Writing the new settings to the device failed after several attempts. No need to worry : The change is not lost (visible in **Pending Configuration**), it will automatically be retried on the next shower.
* **Thresholds/Colors greyed out in options** : They can only be read/modified after a successful first connection — run the water once before adjusting them.

</details>

---

### 🤝 Contributions & Support
For any bug or feature request, please open an [Issue](https://github.com/Adrien40/ha-hydrao-custom/issues) on this repository.

### ⚠️ Disclaimer
This integration is an independent project. It has no connection whatsoever with the Hydrao company. Use of this software is at your own risk.

### ⚖️ License
Project licensed under **GPLv3**. Independent of the Hydrao company. Use at your own risk.

---

**Developed with ❤️ by @Adrien40**

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="180"></a>

<!-- Keywords: Home Assistant custom integration, BLE sensor, water saving, shower monitoring, local control -->
