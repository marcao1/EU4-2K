# Millennium Dawn: EU4 (foundation)

Standalone Europa Universalis IV 1.37.5 mod with a 1 January 2000 start and a
technical end date of 31 December 9999.

The generated world uses the vanilla EU4 province map. Modern country borders
are assigned from the public-domain Natural Earth Admin 0 dataset, with explicit
historical overrides for the 2000 world. Extended Timeline is not a dependency
and none of its files are used by the generator.

## Generate

```powershell
python tools/generate_mod.py `
  --game "F:\Steam\steamapps\common\Europa Universalis IV"
```

The generator downloads Natural Earth and REST Countries flag assets into
`.cache/`, then writes the complete mod to `MillenniumDawnEU4/`.

## Validate

```powershell
python tools/validate_mod.py --mod MillenniumDawnEU4
```

The generated `source_data/countries.csv` and `source_data/provinces.csv` are the
canonical audit tables for country tags and province ownership.

## Install

```powershell
.\tools\install_mod.ps1
```

The currently installed copy is enabled in the local `dlc_load.json` playset.
