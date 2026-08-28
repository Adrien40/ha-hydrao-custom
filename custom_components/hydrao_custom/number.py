# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import HydraoConfigEntry
from .coordinator import HydraoDataUpdateCoordinator
from .entity_helpers import apply_and_persist

COMFORT_TEMP_DESC = NumberEntityDescription(
    key="comfort_temperature",
    translation_key="comfort_temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    entity_category=EntityCategory.CONFIG,
    mode=NumberMode.BOX,
    native_min_value=0.0,
    native_max_value=50.0,
    native_step=0.5,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydraoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            HydraoComfortTempNumber(coordinator, entry),
        ]
    )


class HydraoNumberEntity(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
        entry: HydraoConfigEntry,
        description: NumberEntityDescription,
        default_value: float,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_native_value = default_value

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._apply_value(self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        apply_and_persist(
            self,
            self.hass,
            self._entry,
            self._option_key,
            value,
            self._apply_value,
            self._to_option_value,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        current = self._current_coordinator_value()
        if current != self._attr_native_value:
            self._attr_native_value = current
        super()._handle_coordinator_update()

    def _current_coordinator_value(self) -> float:
        raise NotImplementedError

    def _apply_value(self, value: float) -> None:
        raise NotImplementedError

    @property
    def _option_key(self) -> str:
        raise NotImplementedError

    def _to_option_value(self, value: float) -> float:
        """Convert to the unit stored in options (override if it differs
        from the entity's native unit, e.g. seconds vs minutes)."""
        return value


class HydraoComfortTempNumber(HydraoNumberEntity):
    def __init__(
        self, coordinator: HydraoDataUpdateCoordinator, entry: HydraoConfigEntry
    ) -> None:
        default = coordinator.min_temp_threshold
        super().__init__(coordinator, entry, COMFORT_TEMP_DESC, default)

    @property
    def _option_key(self) -> str:
        return "min_temp_threshold"

    def _current_coordinator_value(self) -> float:
        return self.coordinator.min_temp_threshold

    def _apply_value(self, value: float) -> None:
        self.coordinator.min_temp_threshold = float(value)
