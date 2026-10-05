# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Base entity shared by every Hydrao platform."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import HydraoDataUpdateCoordinator


class HydraoEntity(CoordinatorEntity[HydraoDataUpdateCoordinator]):
    """Common behaviour of all Hydrao entities: translated names, a unique id
    built from the device's Bluetooth address, and the shared device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HydraoDataUpdateCoordinator, key: str) -> None:
        """Set up the entity.

        `key` is the entity's own identifier; combined with the Bluetooth
        address it forms the unique id, which must never change once released.
        """
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Attach the entity to the Hydrao device."""
        return self.coordinator.device_info
