from ipaddress import ip_network
from pywizlight.discovery import find_wizlights, DiscoveredBulb

async def async_discover_devices(
    hass: HomeAssistant, 
    timeout: int,
) -> list[DiscoveredBulb]:
    """Discover WiZ devices on the current subnet(s) + 192.168.1.0/24."""

    # 1. Discover on HA's directly connected broadcast addresses
    broadcast_addrs = await network.async_get_ipv4_broadcast_addresses(hass)
    targets = [str(address) for address in broadcast_addrs]

    # 2. Add unicast targets for 192.168.1.0/24 (skip .0 and .255)
    extra_subnet = ip_network("192.168.1.0/24")
    targets.extend(str(ip) for ip in extra_subnet.hosts())

    combined_discoveries: dict[str, DiscoveredBulb] = {}

    # 3. Run discovery in parallel
    for idx, discovered in enumerate(
        await asyncio.gather(
            *[find_wizlights(timeout, address) for address in targets],
            return_exceptions=True,
        )
    ):
        if isinstance(discovered, Exception):
            _LOGGER.debug("Scanning %s failed with error: %s", targets[idx], discovered)
            continue
        if isinstance(discovered, BaseException):
            raise discovered from None
        for device in discovered:
            assert isinstance(device, DiscoveredBulb)
            combined_discoveries[device.ip_address] = device

    return list(combined_discoveries.values())
