from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


def _rel(p: Path, base: Path) -> str:
    """Csak relatív útvonal kerül kiírásra (megosztható kód)."""
    try:
        return str(Path(p).resolve().relative_to(Path(base).resolve()))
    except ValueError:
        return Path(p).name


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def _is_valid(dest: Path, meta_path: Path, min_bytes: int, expected_sha256: str | None) -> bool:
    if not dest.exists() or dest.stat().st_size < min_bytes:
        return False
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("size") != dest.stat().st_size:  # félbemaradt / módosult fájl
            return False
    if expected_sha256 and _sha256(dest) != expected_sha256:
        return False
    return True


def ensure_file(
    dest,
    url: str | None = None,
    *,
    base,
    min_bytes: int = 1,
    expected_sha256: str | None = None,
    search_root=None,
    manual_hint: str = "",
    retries: int = 3,
    timeout: int = 120,
) -> Path:
    """
    Garantálja, hogy a fájl létezik; ha megvan és ép, nem tölt le semmit.

    Sorrend:
      1) dest létezik és ép (méret / meta / opcionális sha256) -> kihagyja
      2) search_root alatt máshol megvan ugyanazzal a névvel -> azt adja vissza
      3) letöltés .part fájlba, ellenőrzés, atomikus átnevezés, meta írása
      4) ha nincs url vagy a letöltés elbukik -> érthető hibaüzenet, hová kell kézzel tenni
    """
    dest, base = Path(dest), Path(base)
    meta_path = dest.with_name(dest.name + ".meta.json")

    if _is_valid(dest, meta_path, min_bytes, expected_sha256):
        print(f"[megvan] {_rel(dest, base)} -> kihagyva")
        return dest

    if search_root is not None:
        hits = [p for p in sorted(Path(search_root).rglob(dest.name))
                if p.resolve() != dest.resolve() and p.stat().st_size >= min_bytes]
        if hits:
            print(f"[máshol megvan] {_rel(hits[0], base)} -> nem töltöm le újra")
            return hits[0]

    hint = (f"\nKézi megoldás: másold a fájlt ide: {_rel(dest, base)}"
            f"\n{manual_hint}".rstrip())
    if url is None:
        raise FileNotFoundError(f"Nincs meg: {_rel(dest, base)}, és nincs megadva letöltési URL.{hint}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            part.unlink(missing_ok=True)
            print(f"[letöltés {attempt}/{retries}] {url}")
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                # Tömörített átvitelnél (gzip/deflate) a Content-Length a tömörített méret,
                # a lemezre viszont kicsomagolva írunk -> ilyenkor nem hasonlítjuk össze.
                expected = 0 if r.headers.get("Content-Encoding") else int(r.headers.get("Content-Length", 0))
                with open(part, "wb") as f:
                    for block in r.iter_content(1 << 20):
                        f.write(block)
            size = part.stat().st_size
            if size < min_bytes or (expected and size != expected):
                raise IOError(f"hibás méret: {size} bájt (várt: {expected or '?'}, min: {min_bytes})")
            os.replace(part, dest)
            meta_path.write_text(json.dumps({
                "url": url, "size": size, "sha256": _sha256(dest),
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }, indent=2))
            print(f"[kész] {_rel(dest, base)} ({size / 1e6:.2f} MB)")
            return dest
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"  hiba: {e}")
    part.unlink(missing_ok=True)
    raise RuntimeError(f"A letöltés {retries} próbálkozás után sem sikerült: {last_err}{hint}")