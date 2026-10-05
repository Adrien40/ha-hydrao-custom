# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import HydraoConfigEntry
from .coordinator import HydraoDataUpdateCoordinator

BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="end_shower",
        translation_key="end_shower",
        icon="mdi:water-off",
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydraoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [HydraoButton(coordinator, desc) for desc in BUTTON_DESCRIPTIONS]
    )


class HydraoButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    async def async_press(self) -> None:
        self.coordinator.force_end_shower()
