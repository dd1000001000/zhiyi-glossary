"""Builds the language packs and glossary.json (maintainers; run tools/check.py first).

  python tools/build.py [--min-app 1.1.0]

packs/<pack>.gloss            the current pack (the installer takes zh-en and en-zh from here)
packs/<pack>.v<version>.gloss the same file under its release name
packs/glossary.json           the list the settings program downloads (sign it, then upload
                              glossary.json, glossary.json.sig and the changed .v<N>.gloss files
                              to the "glossary" release of dd1000001000/zhiyi_ime)

versions.json keeps each pack's version and the hash of its contents: a pack whose contents
changed gets the next version; the others keep theirs.
"""
import argparse
import datetime
import hashlib
import json

from glossary_format import PACKS, ROOT, merged_entries, pack_bytes, pack_parts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-app", default="1.1.0",
                        help="the oldest Zhiyi IME version that reads the packs")
    args = parser.parse_args()
    versions_path = ROOT / "versions.json"
    versions = json.loads(versions_path.read_text(encoding="utf-8")) if versions_path.exists() else {}
    out = ROOT / "packs"
    out.mkdir(exist_ok=True)
    built = int(datetime.date.today().strftime("%Y%m%d"))
    manifest = {"packs": []}
    for pack in PACKS:
        source, target = pack_parts(pack)
        merged = merged_entries(pack)
        sources = b"".join(path.read_bytes() for folder in ("base", "corrections")
                           for path in [ROOT / folder / f"{pack}.tsv"] if path.exists())
        known = versions.get(pack, {})
        # The version only moves when the translations change.
        _, content_hash, _ = pack_bytes(pack, merged, 0, built, hashlib.sha256(sources).digest())
        version = known.get("version", 0)
        if content_hash != known.get("content"):
            version += 1
        data, content_hash, count = pack_bytes(pack, merged, version, built,
                                               hashlib.sha256(sources).digest())
        versions[pack] = {"version": version, "content": content_hash, "entries": count}
        (out / f"{pack}.gloss").write_bytes(data)
        (out / f"{pack}.v{version}.gloss").write_bytes(data)
        manifest["packs"].append({
            "id": pack, "source": source, "target": target, "version": version,
            "format": 1, "min_app": args.min_app, "file": f"{pack}.v{version}.gloss",
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "entries": count})
        print(f"{pack}: v{version}, {count} words, {len(data) / 1024:.0f} KB"
              + ("  (changed)" if version != known.get("version") else ""))
    (out / "glossary.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    versions_path.write_text(json.dumps(versions, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
