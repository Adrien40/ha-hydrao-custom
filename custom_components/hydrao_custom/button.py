# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HydraoConfigEntry
from .coordinator import HydraoDataUpdateCoordinator
from .entity import HydraoEntity

# Writes are queued locally and sent on the next BLE connection.
PARALLEL_UPDATES = 1

BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="end_shower",
        translation_key="end_shower",
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


class HydraoButton(HydraoEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: HydraoDataUpdateCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        self.coordinator.force_end_shower()
