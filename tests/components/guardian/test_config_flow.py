"""Define tests for the Elexa Guardian config flow."""
from unittest.mock import patch

from aioguardian.errors import GuardianError

from homeassistant import data_entry_flow
from homeassistant.components import dhcp, zeroconf
from homeassistant.components.guardian import CONF_UID, DOMAIN
from homeassistant.components.guardian.config_flow import (
    async_get_pin_from_discovery_hostname,
    async_get_pin_from_uid,
)
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT


async def test_duplicate_error(hass, config, config_entry, setup_guardian):
    """Test that errors are shown when duplicate entries are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_connect_error(hass, config):
    """Test that the config entry errors out if the device cannot connect."""
    with patch(
        "aioguardian.client.Client.connect",
        side_effect=GuardianError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}


async def test_get_pin_from_discovery_hostname():
    """Test getting a device PIN from the zeroconf-discovered hostname."""
    pin = async_get_pin_from_discovery_hostname("GVC1-3456.local.")
    assert pin == "3456"


async def test_get_pin_from_uid():
    """Test getting a device PIN from its UID."""
    pin = async_get_pin_from_uid("ABCDEF123456")
    assert pin == "3456"


async def test_step_user(hass, config, setup_guardian):
    """Test the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "ABCDEF123456"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
        CONF_UID: "ABCDEF123456",
    }


async def test_step_zeroconf(hass, setup_guardian):
    """Test the zeroconf step."""
    zeroconf_data = zeroconf.ZeroconfServiceInfo(
        host="192.168.1.100",
        port=7777,
        hostname="GVC1-ABCD.local.",
        type="_api._udp.local.",
        name="Guardian Valve Controller API._api._udp.local.",
        properties={"_raw": {}},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "ABCDEF123456"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
        CONF_UID: "ABCDEF123456",
    }


async def test_step_zeroconf_already_in_progress(hass):
    """Test the zeroconf step aborting because it's already in progress."""
    zeroconf_data = zeroconf.ZeroconfServiceInfo(
        host="192.168.1.100",
        port=7777,
        hostname="GVC1-ABCD.local.",
        type="_api._udp.local.",
        name="Guardian Valve Controller API._api._udp.local.",
        properties={"_raw": {}},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"


async def test_step_dhcp(hass, setup_guardian):
    """Test the dhcp step."""
    dhcp_data = dhcp.DhcpServiceInfo(
        ip="192.168.1.100",
        hostname="GVC1-ABCD.local.",
        macaddress="aa:bb:cc:dd:ee:ff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "ABCDEF123456"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
        CONF_UID: "ABCDEF123456",
    }


async def test_step_dhcp_already_in_progress(hass):
    """Test the zeroconf step aborting because it's already in progress."""
    dhcp_data = dhcp.DhcpServiceInfo(
        ip="192.168.1.100",
        hostname="GVC1-ABCD.local.",
        macaddress="aa:bb:cc:dd:ee:ff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"
