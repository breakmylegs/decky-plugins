import json
import os

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_manifest_matches_folder_and_has_no_root_flag():
    with open(os.path.join(PLUGIN, "plugin.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest["name"] == os.path.basename(PLUGIN)
    assert manifest["api_version"] == 1
    assert "root" not in manifest["flags"] and "_root" not in manifest["flags"]
    with open(os.path.join(PLUGIN, "package.json"), encoding="utf-8") as handle:
        assert json.load(handle)["type"] == "module"
