# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from typing import Any, ClassVar

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_last_service_info,
    async_register_callback,
)
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    StateType,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BT_STATUS_CONNECTING,
    BT_STATUS_ERROR,
    BT_STATUS_REBOOTING,
    BT_STATUS_SUCCESS,
    BT_STATUS_SYNC_APPLIED,
    BT_STATUS_SYNC_FAILED,
    BT_STATUS_WAITING,
    BT_STATUS_WRITING_SYNC,
    HydraoConfigEntry,
)
from .coordinator import HydraoDataUpdateCoordinator

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="total_volume",
        translation_key="total_volume",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="flow_rate",
        translation_key="flow_rate",
        icon="mdi:water-pump",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="wasted_volume",
        translation_key="wasted_volume",
        icon="mdi:water-minus",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="wasted_volume_total",
        translation_key="wasted_volume_total",
        icon="mdi:water-minus",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="shower_volume_comfort",
        translation_key="shower_volume_comfort",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="shower_volume_comfort_total",
        translation_key="shower_volume_comfort_total",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="shower_volume_raw",
        translation_key="shower_volume_raw",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="shower_duration",
        translation_key="shower_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="shower_duration_comfort",
        translation_key="shower_duration_comfort",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="threshold_1",
        translation_key="threshold_1",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:water-opacity",
    ),
    SensorEntityDescription(
        key="threshold_2",
        translation_key="threshold_2",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:water-opacity",
    ),
    SensorEntityDescription(
        key="threshold_3",
        translation_key="threshold_3",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:water-opacity",
    ),
    SensorEntityDescription(
        key="threshold_4",
        translation_key="threshold_4",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:water-opacity",
    ),
]

SOAPING_DURATION_DESC = SensorEntityDescription(
    key="soaping_duration",
    translation_key="soaping_duration",
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement=UnitOfTime.SECONDS,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydraoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    sensors = [HydraoSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS]
    sensors.append(HydraoBluetoothStatusSensor(coordinator))
    sensors.append(HydraoRealTimeRSSISensor(coordinator))
    sensors.append(HydraoSoapingDurationSensor(coordinator))
    sensors.append(HydraoPendingConfigSensor(coordinator))

    async_add_entities(sensors)


class HydraoSensor(CoordinatorEntity, RestoreSensor):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._restored_value = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        if (
            not self.coordinator.is_new_entry
            and (last_sensor_data := await self.async_get_last_sensor_data())
            is not None
            and self.entity_description.key != "flow_rate"
        ):
            self._restored_value = last_sensor_data.native_value

            if (
                self.entity_description.key == "wasted_volume_total"
                and self._restored_value is not None
            ):
                try:
                    self.coordinator.restore_wasted_volume_total(
                        float(self._restored_value)
                    )
                except (ValueError, TypeError):
                    pass
            elif (
                self.entity_description.key == "shower_volume_comfort_total"
                and self._restored_value is not None
            ):
                try:
                    self.coordinator.restore_shower_volume_comfort_total(
                        float(self._restored_value)
                    )
                except (ValueError, TypeError):
                    pass

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    _RAW_KEYS: ClassVar[set[str]] = {"shower_volume_raw", "shower_duration"}
    _NUMERIC_KEYS = frozenset(
        {
            "total_volume",
            "shower_volume_comfort",
            "shower_volume_comfort_total",
            "wasted_volume",
            "wasted_volume_total",
            "shower_volume_raw",
            "temperature",
            "shower_duration",
            "shower_duration_comfort",
            "flow_rate",
        }
    )

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data or {}
        key = self.entity_description.key

        if key.startswith("threshold_"):
            idx = int(key.split("_")[1]) - 1
            if "thresholds" in self.coordinator.static_data:
                try:
                    return float(self.coordinator.static_data["thresholds"][idx])
                except (IndexError, ValueError, TypeError):
                    pass
            if self._restored_value is not None:
                try:
                    return float(self._restored_value)
                except (ValueError, TypeError):
                    pass
            return self._restored_value

        if key in self._RAW_KEYS:
            val = data.get("raw", {}).get(key)
        else:
            val = data.get(key)

        if val is None:
            if key == "flow_rate":
                return 0.0
            if self._restored_value is not None:
                try:
                    if key in self._NUMERIC_KEYS:
                        return float(self._restored_value)
                except (ValueError, TypeError):
                    pass
                return self._restored_value
            return None

        if key in self._NUMERIC_KEYS:
            return float(val)

        return val

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {}

        if self.entity_description.key.startswith("threshold_"):
            idx = int(self.entity_description.key.split("_")[1]) - 1
            colors = self.coordinator.static_data.get("colors")
            if colors is not None:
                try:
                    r, g, b = (int(c) for c in colors[idx])
                    attrs["color_rgb"] = f"{r}, {g}, {b}"
                    attrs["color_hex"] = f"#{r:02X}{g:02X}{b:02X}"
                except (IndexError, ValueError, TypeError):
                    return attrs

        return attrs


class HydraoBluetoothStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_translation_key = "bluetooth_status"
    _attr_options: ClassVar[list[str]] = [
        BT_STATUS_WAITING,
        BT_STATUS_CONNECTING,
        BT_STATUS_SUCCESS,
        BT_STATUS_ERROR,
        BT_STATUS_WRITING_SYNC,
        BT_STATUS_SYNC_APPLIED,
        BT_STATUS_SYNC_FAILED,
        BT_STATUS_REBOOTING,
    ]

    def __init__(self, coordinator: HydraoDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_bluetooth_status"

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    def native_value(self) -> StateType:
        if not self.coordinator.data:
            return BT_STATUS_WAITING
        return self.coordinator.data.get("bluetooth_status", BT_STATUS_WAITING)

    @property
    def icon(self) -> str:
        icons = {
            BT_STATUS_WAITING: "mdi:bluetooth-off",
            BT_STATUS_CONNECTING: "mdi:bluetooth-connect",
            BT_STATUS_SUCCESS: "mdi:bluetooth",
            BT_STATUS_ERROR: "mdi:bluetooth-off",
            BT_STATUS_WRITING_SYNC: "mdi:cog-sync",
            BT_STATUS_SYNC_APPLIED: "mdi:check-circle",
            BT_STATUS_SYNC_FAILED: "mdi:alert-circle",
            BT_STATUS_REBOOTING: "mdi:restart",
        }
        return icons.get(str(self.native_value), "mdi:bluetooth-alert")


# Developer's choice: This sensor inherits from CoordinatorEntity to ensure its state
# explicitly syncs with the main coordinator's update cycles and base availability logic,
# despite maintaining its own passive BLE listener for real-time RSSI updates.
class HydraoRealTimeRSSISensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "rssi"
    _attr_should_poll = False

    def __init__(self, coordinator: HydraoDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_rssi"
        self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        if self._attr_native_value is None:
            return False

        status = (
            self.coordinator.data.get("bluetooth_status")
            if self.coordinator.data
            else None
        )
        # Only "available" while genuinely connected to the device
        # (mid-shower, or writing/rebooting as part of that same
        # connection) — not while merely searching (waiting), attempting
        # a connection, or in error, where a passively-scanned value
        # could still be sitting around from an earlier session and
        # falsely suggest the device is currently reachable.
        return status in (
            BT_STATUS_SUCCESS,
            BT_STATUS_WRITING_SYNC,
            BT_STATUS_SYNC_APPLIED,
            BT_STATUS_SYNC_FAILED,
            BT_STATUS_REBOOTING,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        last_info = async_last_service_info(
            self.hass, self.coordinator.address, connectable=False
        )
        if last_info and hasattr(last_info, "rssi"):
            self._attr_native_value = last_info.rssi

        self.async_write_ha_state()

        @callback
        def _async_on_bluetooth_change(
            info: BluetoothServiceInfoBleak, change: BluetoothChange
        ) -> None:
            self._attr_native_value = info.rssi
            self.async_write_ha_state()

        self.async_on_remove(
            async_register_callback(
                self.hass,
                _async_on_bluetooth_change,
                BluetoothCallbackMatcher(address=self.coordinator.address),
                BluetoothScanningMode.PASSIVE,
            )
        )


class HydraoSoapingDurationSensor(CoordinatorEntity, RestoreSensor):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = SOAPING_DURATION_DESC
        self._attr_unique_id = f"{coordinator.address}_{SOAPING_DURATION_DESC.key}"
        self._restored_value = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.coordinator.is_new_entry:
            last_sensor_data = await self.async_get_last_sensor_data()
            if last_sensor_data is not None:
                self._restored_value = last_sensor_data.native_value

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    def native_value(self) -> StateType:
        val = self.coordinator.static_data.get("soaping_duration")
        if val is not None:
            return val

        if self._restored_value is not None:
            try:
                return int(self._restored_value)
            except (ValueError, TypeError):
                pass

        return None


class HydraoPendingConfigSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_translation_key = "pending_config"
    _attr_icon = "mdi:file-sync-outline"
    _attr_options: ClassVar[list[str]] = [
        "none",
        "soaping",
        "thresholds",
        "colors",
        "soaping_thresholds",
        "soaping_colors",
        "thresholds_colors",
        "soaping_thresholds_colors",
    ]

    def __init__(self, coordinator: HydraoDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_pending_config"

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    def native_value(self) -> StateType:
        parts = []
        if self.coordinator.pending_soaping_duration is not None:
            parts.append("soaping")
        if self.coordinator.pending_thresholds is not None:
            parts.append("thresholds")
        if self.coordinator.pending_colors is not None:
            parts.append("colors")
        return "_".join(parts) if parts else "none"
