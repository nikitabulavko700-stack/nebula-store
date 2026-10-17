#!/usr/bin/env python3
"""Добавляет .cxskin в каталог магазина Nebula.

Использование:
    python add_skin.py путь/к/скину.cxskin [--id my-skin] [--tags neon,anime]

Что делает: кладёт файл в skins/, достаёт из него превью в previews/,
считает SHA-256 и дописывает запись в index.json (если id уже есть — обновляет её).
"""
import argparse, hashlib, json, os, re, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.json")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--id")
    ap.add_argument("--tags", default="")
    a = ap.parse_args()

    with zipfile.ZipFile(a.file) as z:
        names = z.namelist()
        if "skin.json" not in names or "skin.png" not in names:
            sys.exit("Это не скин Nebula: нет skin.json / skin.png")
        meta = json.loads(z.read("skin.json").decode("utf-8-sig"))
        png = z.read("skin.png")

    slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    stem = os.path.splitext(os.path.basename(a.file))[0]
    base = a.id or slug(meta.get("Name", "")) or slug(stem) or "skin"  # кириллица в id не годится — берём имя файла
    sid = base[:64]
    os.makedirs(os.path.join(ROOT, "skins"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "previews"), exist_ok=True)
    dst = os.path.join(ROOT, "skins", sid + ".cxskin")
    shutil.copyfile(a.file, dst)
    with open(os.path.join(ROOT, "previews", sid + ".png"), "wb") as f:
        f.write(png)
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()

    item = {
        "id": sid,
        "name": meta.get("Name", sid),
        "author": meta.get("Author", ""),
        "effect": meta.get("Effect", "none"),
        "gif": bool(meta.get("Delays")),
        "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
        "preview": f"previews/{sid}.png",
        "file": f"skins/{sid}.cxskin",
        "sha256": sha,
    }
    data = json.load(open(INDEX, encoding="utf-8")) if os.path.exists(INDEX) else {"version": 1, "skins": []}
    data["skins"] = [s for s in data["skins"] if s.get("id") != sid] + [item]
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Готово: {sid} (всего скинов: {len(data['skins'])}). Теперь закоммить и запушь папку на GitHub.")

main()
