# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HydraoConfigEntry
from .coordinator import HydraoDataUpdateCoordinator
from .entity import HydraoEntity
from .entity_helpers import apply_and_persist

# Writes are queued locally and sent on the next BLE connection.
PARALLEL_UPDATES = 1

AUTO_SYNC_DESC = SwitchEntityDescription(
    key="auto_sync_at_comfort",
    translation_key="auto_sync_at_comfort",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydraoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([HydraoAutoSyncSwitch(coordinator, entry)])


class HydraoAutoSyncSwitch(HydraoEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
        entry: HydraoConfigEntry,
    ) -> None:
        super().__init__(coordinator, AUTO_SYNC_DESC.key)
        self._entry = entry
        self.entity_description = AUTO_SYNC_DESC
        self._attr_is_on = coordinator.auto_sync_at_comfort

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._apply_value(bool(self._attr_is_on))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_state(False)

    async def _async_set_state(self, value: bool) -> None:
        self._attr_is_on = value
        apply_and_persist(
            self,
            self.hass,
            self._entry,
            "auto_sync_at_comfort",
            value,
            self._apply_value,
        )

    def _apply_value(self, value: bool) -> None:
        self.coordinator.auto_sync_at_comfort = value

    @callback
    def _handle_coordinator_update(self) -> None:
        current = self.coordinator.auto_sync_at_comfort
        if current != self._attr_is_on:
            self._attr_is_on = current
        super()._handle_coordinator_update()
