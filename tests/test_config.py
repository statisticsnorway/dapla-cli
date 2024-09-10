from configparser import ConfigParser

from dp import config


def test_set_creates_new_section_if_not_exists(mocker):
    configparser = ConfigParser()
    mocker.patch("dp.config._load_config", return_value=configparser)
    mocker.patch("dp.config._save_config")
    config.set("new_section", "key", "value", None)
    config._save_config.assert_called_once()


def test_set_updates_existing_section(mocker):
    configparser = ConfigParser()
    configparser["existing_section"] = {"key": "old_value"}
    mocker.patch("dp.config._load_config", return_value=configparser)
    mocker.patch("dp.config._save_config")
    config.set("existing_section", "key", "new_value", None)
    assert configparser["existing_section"]["key"] == "new_value"
    config._save_config.assert_called_once()


def test_get_returns_value_if_exists(mocker):
    configparser = ConfigParser()
    configparser["section"] = {"key": "value"}
    mocker.patch("dp.config._load_config", return_value=configparser)
    value = config.get("section", "key", None)
    assert value == "value"


def test_get_returns_none_if_not_exists(mocker):
    configparser = ConfigParser()
    mocker.patch("dp.config._load_config", return_value=configparser)
    value = config.get("section", "key", None)
    assert value is None


def test_remove_deletes_section_if_exists(mocker):
    configparser = ConfigParser()
    configparser["section"] = {"key": "value"}
    mocker.patch("dp.config._load_config", return_value=configparser)
    mocker.patch("dp.config._save_config")
    config.remove("section", None)
    assert "section" not in configparser
    config._save_config.assert_called_once()


def test_remove_does_nothing_if_section_not_exists(mocker):
    configparser = ConfigParser()
    mocker.patch("dp.config._load_config", return_value=configparser)
    mocker.patch("dp.config._save_config")
    config.remove("non_existent_section", None)
    config._save_config.assert_not_called()
