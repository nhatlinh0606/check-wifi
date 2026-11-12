import json
import pytest
from unittest.mock import patch, MagicMock
from modules.network_discovery import NetworkDiscovery, NetworkInterfaceInfo


def test_network_interface_info_to_dict():
    info = NetworkInterfaceInfo(
        name="eth0",
        ip="192.168.1.50",
        netmask="255.255.255.0",
        cidr="192.168.1.50/24",
        network="192.168.1.0/24",
        mac="00:11:22:33:44:55",
        is_up=True,
        is_default=True,
        gateway="192.168.1.1"
    )
    d = info.to_dict()
    assert d["name"] == "eth0"
    assert d["ip"] == "192.168.1.50"
    assert d["gateway"] == "192.168.1.1"
    assert d["is_default"] is True


def test_get_default_gateway_from_ip_command():
    mock_json = json.dumps([
        {"dst": "default", "gateway": "192.168.0.1", "dev": "enp3s0"}
    ])
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_json)
        nd = NetworkDiscovery()
        gw = nd.get_default_gateway()
        assert gw is not None
        assert gw["gateway"] == "192.168.0.1"
        assert gw["dev"] == "enp3s0"


def test_get_arp_table_from_ip_neigh():
    mock_json = json.dumps([
        {"dst": "192.168.0.1", "lladdr": "50:d4:f7:11:22:33", "dev": "enp3s0", "state": ["REACHABLE"]},
        {"dst": "192.168.0.5", "lladdr": "aa:bb:cc:dd:ee:ff", "dev": "enp3s0", "state": ["FAILED"]}
    ])
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_json)
        nd = NetworkDiscovery()
        arp = nd.get_arp_table()
        assert len(arp) == 1
        assert arp[0]["ip"] == "192.168.0.1"
        assert arp[0]["mac"] == "50:d4:f7:11:22:33"


def test_resolve_hostname_timeout():
    with patch("socket.gethostbyaddr", side_effect=Exception("Host not found")):
        name = NetworkDiscovery.resolve_hostname("192.0.2.1", timeout=0.1)
        assert name is None
