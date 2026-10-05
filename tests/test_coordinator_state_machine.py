# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the Hydrao BLE session state machine in coordinator.py.

These focus on the parts flagged as dense/high-risk during review:
  - live data processing and session reset detection
  - force_end_shower() / comfort-mode auto-sync bookkeeping
  - the "new shower" retry / staleness handling
  - the offline timeout
  - a regression test locking in the asyncio.Lock deadlock fix in
    _async_write_pending_config / _async_read_thresholds
"""

import asyncio
import time
from unittest.mock import AsyncMock

from custom_components.hydrao_custom.const import (
    BT_STATUS_ERROR,
    BT_STATUS_REBOOTING,
    BT_STATUS_SUCCESS,
    BT_STATUS_WAITING,
    MAX_NEW_SHOWER_ATTEMPTS,
)


def _u16le(value: int) -> tuple[int, int]:
    """Split a 16-bit value into (low_byte, high_byte), little-endian."""
    return value & 0xFF, (value >> 8) & 0xFF


def make_frames(
    total: int, shower: int, duration_ticks: int, temp_c: float
) -> tuple[bytearray, bytearray, bytearray]:
    """Build (vol_data, dur_data, temp_data) BLE frames as the device would
    send them, from human-friendly values."""
    t_lo, t_hi = _u16le(total)
    s_lo, s_hi = _u16le(shower)
    vol_data = bytearray([t_lo, t_hi, s_lo, s_hi])

    d_lo, d_hi = _u16le(duration_ticks)
    dur_data = bytearray([d_lo, d_hi])

    temp_ticks = round(temp_c * 2)
    tm_lo, tm_hi = _u16le(temp_ticks)
    temp_data = bytearray([tm_lo, tm_hi])

    return vol_data, dur_data, temp_data


# ---------------------------------------------------------------------------
# Live data processing / session detection
# ---------------------------------------------------------------------------


async def test_first_data_point_starts_a_new_session_below_comfort_temp(coordinator):
    """On the very first reading (last_seen_time == 0), the whole raw
    reading becomes the session delta, and cold water counts as wasted."""
    coordinator.min_temp_threshold = 33.0

    vol_data, dur_data, temp_data = make_frames(
        total=100, shower=50, duration_ticks=3000, temp_c=20.0
    )
    coordinator._process_live_data(vol_data, dur_data, temp_data, None)

    assert coordinator.session_wasted_volume == 50.0
    assert coordinator.lifetime_wasted_volume_total == 50.0
    assert coordinator.session_shower_volume_comfort == 0.0
    assert coordinator.last_valid_data["total_volume"] == 100.0
    assert coordinator.last_valid_data["wasted_volume"] == 50.0


async def test_incremental_reading_above_comfort_temp_counts_as_comfort(coordinator):
    """Once a session is running, only the delta since the last reading is
    counted, and water above the comfort threshold counts as comfort, not
    wasted."""
    coordinator.min_temp_threshold = 33.0

    v1, d1, t1 = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=20.0)
    coordinator._process_live_data(v1, d1, t1, None)

    v2, d2, t2 = make_frames(total=150, shower=80, duration_ticks=4500, temp_c=35.0)
    coordinator._process_live_data(v2, d2, t2, None)

    # delta_vol = 80 - 50 = 30, all of it above threshold this time
    assert coordinator.session_shower_volume_comfort == 30.0
    assert coordinator.lifetime_shower_volume_comfort_total == 30.0
    # wasted volume from the first (cold) reading is untouched
    assert coordinator.session_wasted_volume == 50.0


async def test_shower_raw_drop_is_treated_as_device_side_reset(coordinator):
    """If the device's own raw counter drops between two readings (it reset
    itself, e.g. after its soaping_duration timeout), that's treated as a
    brand new session rather than a negative delta."""
    v1, d1, t1 = make_frames(total=100, shower=80, duration_ticks=3000, temp_c=20.0)
    coordinator._process_live_data(v1, d1, t1, None)

    coordinator.pending_new_shower = True

    v2, d2, t2 = make_frames(total=105, shower=5, duration_ticks=200, temp_c=20.0)
    coordinator._process_live_data(v2, d2, t2, None)

    assert coordinator.pending_new_shower is False
    assert coordinator.new_shower_attempts == 0
    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_SUCCESS
    # the new reading itself becomes the delta, not (5 - 80)
    assert coordinator.session_wasted_volume == 5.0


# ---------------------------------------------------------------------------
# force_end_shower() / manual reset
# ---------------------------------------------------------------------------


async def test_force_end_shower_resets_display_immediately(coordinator):
    """Pressing the 'end shower' button must zero the visible counters
    immediately, without waiting for a BLE round-trip."""
    v1, d1, t1 = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=35.0)
    coordinator._process_live_data(v1, d1, t1, None)
    assert coordinator.last_valid_data["wasted_volume"] == 0.0
    assert coordinator.session_shower_volume_comfort > 0

    coordinator.force_end_shower()

    assert coordinator.pending_new_shower is True
    assert coordinator.last_seen_time == 0.0
    assert coordinator._awaiting_manual_reset_confirmation is True
    assert coordinator.last_valid_data["wasted_volume"] == 0.0
    assert coordinator.last_valid_data["shower_volume_comfort"] == 0.0
    assert coordinator.last_valid_data["raw"]["shower_volume_raw"] == 0.0


async def test_awaiting_manual_reset_confirmation_suppresses_new_deltas(coordinator):
    """Between force_end_shower() and the device confirming the reset,
    incoming live data must not resume counting (it would double count
    water that was already attributed to the ended session)."""
    v1, d1, t1 = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=35.0)
    coordinator._process_live_data(v1, d1, t1, None)
    coordinator.force_end_shower()

    # Water is still physically running when the button is pressed, so the
    # device keeps reporting an increasing raw volume for a moment.
    v2, d2, t2 = make_frames(total=100, shower=55, duration_ticks=3100, temp_c=35.0)
    coordinator._process_live_data(v2, d2, t2, None)

    assert coordinator.session_wasted_volume == 0.0
    assert coordinator.session_shower_volume_comfort == 0.0
    assert coordinator.last_valid_data["raw"]["shower_volume_raw"] == 0.0
    assert coordinator.last_valid_data["flow_rate"] == 0.0


# ---------------------------------------------------------------------------
# "New shower" BLE command retry / staleness
# ---------------------------------------------------------------------------


async def test_stale_new_shower_command_is_discarded_without_writing(
    coordinator, monkeypatch
):
    """If enough time has passed that the device's own soaping_duration
    timeout would already have reset its counters, we must not send a
    'new shower' command (it would wrongly reset an unrelated session)."""
    coordinator.static_data["soaping_duration"] = 180

    fake_now = 10_000.0
    coordinator._new_shower_requested_at = fake_now
    coordinator.pending_new_shower = True
    monkeypatch.setattr(time, "monotonic", lambda: fake_now + 200)  # older than timeout

    client = AsyncMock()
    await coordinator._handle_pending_new_shower(client)

    assert coordinator.pending_new_shower is False
    assert coordinator.new_shower_attempts == 0
    assert coordinator._awaiting_manual_reset_confirmation is False
    client.write_gatt_char.assert_not_called()


async def test_new_shower_command_gives_up_after_max_attempts(coordinator):
    """After MAX_NEW_SHOWER_ATTEMPTS failed confirmations, give up cleanly
    and surface an error rather than retrying forever."""
    coordinator.static_data["soaping_duration"] = 180
    coordinator.pending_new_shower = True
    coordinator.new_shower_attempts = MAX_NEW_SHOWER_ATTEMPTS
    coordinator._new_shower_requested_at = time.monotonic()  # fresh, not stale

    client = AsyncMock()
    await coordinator._handle_pending_new_shower(client)

    assert coordinator.pending_new_shower is False
    assert coordinator.new_shower_attempts == 0
    assert coordinator._awaiting_manual_reset_confirmation is False
    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_ERROR
    client.write_gatt_char.assert_not_called()


# ---------------------------------------------------------------------------
# Offline timeout
# ---------------------------------------------------------------------------


async def test_offline_timeout_resets_session_after_soaping_duration(
    coordinator, monkeypatch
):
    """If nothing has been seen for longer than soaping_duration, the
    session must be considered over even without an explicit device
    confirmation."""
    coordinator.static_data["soaping_duration"] = 180

    fake_now = 10_000.0
    monkeypatch.setattr(time, "monotonic", lambda: fake_now)
    coordinator.last_seen_time = fake_now
    coordinator._comfort_sync_sent_for_session = True
    coordinator._awaiting_manual_reset_confirmation = True

    fake_now += 300  # advance the fake clock well past the 180s timeout
    monkeypatch.setattr(time, "monotonic", lambda: fake_now)

    coordinator._evaluate_offline_timeout()

    assert coordinator.force_reset_flag is True
    assert coordinator.last_seen_time == 0.0
    assert coordinator._comfort_sync_sent_for_session is False
    assert coordinator._awaiting_manual_reset_confirmation is False
    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_WAITING


# ---------------------------------------------------------------------------
# Comfort-mode auto-sync
# ---------------------------------------------------------------------------


async def test_trigger_auto_sync_preserves_wasted_volume(coordinator):
    """Unlike a manual end-shower, the comfort-mode auto-resync must keep
    the wasted-volume counter (it's still the same physical session)."""
    v1, d1, t1 = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=20.0)
    coordinator._process_live_data(v1, d1, t1, None)
    assert coordinator.last_valid_data["wasted_volume"] == 50.0

    coordinator._trigger_auto_sync_at_comfort()

    assert coordinator.pending_new_shower is True
    assert coordinator._preserve_wasted_on_next_reset is True
    # wasted volume is left alone...
    assert coordinator.last_valid_data["wasted_volume"] == 50.0
    # ...but the comfort/flow/temp display fields are cleared
    assert coordinator.last_valid_data["shower_volume_comfort"] == 0.0
    assert coordinator.last_valid_data["flow_rate"] == 0.0


async def test_auto_sync_reset_is_visible_in_the_triggering_process_live_data_call(
    coordinator,
):
    """When auto-sync-at-comfort fires *during* _process_live_data()
    itself (not via a direct call to _trigger_auto_sync_at_comfort() like
    above), the reset it performs (session accumulators zeroed except
    wasted_volume, _awaiting_manual_reset_confirmation set) must already
    be reflected in this same call's own committed last_valid_data —
    since new_data is built from those exact fields later in the same
    call, calling the trigger any later than its current, mid-function
    placement would capture stale pre-reset values instead."""
    coordinator.auto_sync_at_comfort = True

    # Cold water first, builds up session_wasted_volume > 0.
    v1, d1, t1 = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=20.0)
    coordinator._process_live_data(v1, d1, t1, None)
    assert coordinator.session_wasted_volume == 50.0

    # Now it crosses into comfort temperature with shower still running:
    # this is exactly the condition that fires _trigger_auto_sync_at_comfort()
    # from inside _process_live_data() itself.
    v2, d2, t2 = make_frames(total=150, shower=80, duration_ticks=4500, temp_c=35.0)
    coordinator._process_live_data(v2, d2, t2, None)

    # _trigger_auto_sync_at_comfort() resets the session accumulators
    # (preserving only wasted_volume) *and* sets
    # _awaiting_manual_reset_confirmation — both read directly by the
    # new_data construction later in this same call, so the reset must
    # already be visible in this call's own committed last_valid_data,
    # not just from the next tick onward.
    assert coordinator.session_shower_volume_comfort == 0.0
    # But what's actually shown must be the flash (0), not that 30L —
    # otherwise the reset is invisible to anyone watching the sensor.
    assert coordinator.last_valid_data["shower_volume_comfort"] == 0.0
    assert coordinator.last_valid_data["flow_rate"] == 0.0
    assert coordinator.pending_new_shower is True


# ---------------------------------------------------------------------------
# Deadlock regression (asyncio.Lock is not reentrant)
# ---------------------------------------------------------------------------


async def test_write_pending_config_does_not_deadlock_when_raw_cfg_unknown(
    coordinator,
):
    """Regression test for the _raw_cfg_lock deadlock: when _raw_cfg is
    None, _async_write_pending_config must read it via the lock-already-
    held helper instead of re-entering self._raw_cfg_lock. If this
    regresses, the call below hangs forever and the wait_for raises
    asyncio.TimeoutError."""
    client = AsyncMock()
    client.read_gatt_char.return_value = bytearray(range(16))
    client.write_gatt_char.return_value = None

    result = await asyncio.wait_for(
        coordinator._async_write_pending_config(
            client, thresholds=[10, 20, 30, 40], colors=None
        ),
        timeout=2,
    )

    assert result is True
    assert coordinator._raw_cfg is not None
    client.write_gatt_char.assert_awaited_once()


# ---------------------------------------------------------------------------
# Reboot-vs-water-off status regression (a device reboot after "new shower"
# briefly stops advertising too, and must not be shown as "water off")
# ---------------------------------------------------------------------------


async def test_no_pending_operation_guard_reflects_pending_new_shower(coordinator):
    """The shared guard used by both async_run_loop() and
    _evaluate_offline_timeout() must say "something is in progress" while
    a 'new shower' reboot is pending, and "all clear" once it's done."""
    coordinator.pending_new_shower = True
    assert coordinator._no_pending_operation_in_progress() is False

    coordinator.pending_new_shower = False
    assert coordinator._no_pending_operation_in_progress() is True


async def test_offline_timeout_does_not_overwrite_rebooting_status(coordinator):
    """Regression test: right after force_end_shower()/comfort-sync send
    the 'new shower' command, the device reboots and briefly stops
    advertising — indistinguishable, by advertisement alone, from the
    water actually being off. _evaluate_offline_timeout() must not
    stomp BT_STATUS_REBOOTING with BT_STATUS_WAITING while
    pending_new_shower is still true, or the UI misleadingly shows
    "water off" while the water never stopped."""
    coordinator.static_data["soaping_duration"] = 180
    coordinator.last_seen_time = time.monotonic()  # not stale yet
    coordinator.pending_new_shower = True
    coordinator.set_bt_status(BT_STATUS_REBOOTING)

    coordinator._evaluate_offline_timeout()

    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_REBOOTING


async def test_no_advertisement_tick_does_not_report_water_off_during_reboot(
    coordinator, monkeypatch
):
    """Regression test for the exact reported bug: right after a 'new
    shower' command triggers a device reboot, the device briefly stops
    advertising too — indistinguishable, by advertisement alone, from
    the water actually being off. The per-tick handler called by
    async_run_loop() when no advertisement was seen must not overwrite
    BT_STATUS_REBOOTING with BT_STATUS_WAITING while pending_new_shower
    is still true, or the UI misleadingly shows "water off" for a few
    seconds while the water never stopped flowing."""
    coordinator.static_data["soaping_duration"] = 180
    coordinator.last_seen_time = time.monotonic()  # not stale yet
    coordinator.pending_new_shower = True
    coordinator.set_bt_status(BT_STATUS_REBOOTING)

    # async_clear_advertisement_history() touches HA's real bluetooth
    # manager internals, which this lightweight coordinator-only fixture
    # doesn't set up; replace it with a no-op for this test.
    monkeypatch.setattr(
        "custom_components.hydrao_custom.coordinator.async_clear_advertisement_history",
        lambda hass, address: None,
    )

    coordinator._handle_no_advertisement_tick()

    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_REBOOTING


# ---------------------------------------------------------------------------
# Prompt reconnection after a device reboot (don't wait out a stale BLE
# connection for as long as the OS's own disconnect-detection timeout)
# ---------------------------------------------------------------------------


async def test_new_shower_write_sets_rebooting_status_and_sent_flag_even_on_timeout(
    coordinator,
):
    """Regression test: the device reboots the instant it receives the
    'new shower' command, without sending a GATT write acknowledgment —
    so the write always looks like a timeout from our side. That must
    still count as "sent": _new_shower_write_sent has to be set so the
    read loop breaks out and reconnects promptly instead of waiting on
    client.is_connected to notice the reboot on its own (which can take
    far longer, up to the OS's own disconnect-detection timeout). The
    status must also already read BT_STATUS_REBOOTING, not still
    BT_STATUS_WRITING_SYNC, since by this point the device is rebooting
    whether or not the write raised."""
    coordinator.pending_new_shower = True
    coordinator._new_shower_requested_at = time.monotonic()
    assert coordinator._new_shower_write_sent is False

    client = AsyncMock()
    client.write_gatt_char.side_effect = TimeoutError("no ack, device rebooted")

    await coordinator._handle_pending_new_shower(client)

    assert coordinator._new_shower_write_sent is True
    assert coordinator.last_valid_data["bluetooth_status"] == BT_STATUS_REBOOTING
