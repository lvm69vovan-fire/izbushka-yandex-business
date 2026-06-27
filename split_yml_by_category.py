# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, parse, indent

SOURCE_FILE = Path("izbushka-yandex-in-stock.xml")
OUTPUT_DIR = Path("yml_by_category")


def safe_filename(name: str) -> str:
    value = name.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.I)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "category"


def write_category_file(category_id: str, category_name: str, offers: list[Element]) -> Path:
    root = Element("yml_catalog")
    shop = SubElement(root, "shop")

    categories = SubElement(shop, "categories")
    category = SubElement(categories, "category", {"id": category_id})
    category.text = category_name

    offers_node = SubElement(shop, "offers")
    for offer in offers:
        offers_node.append(offer)

    indent(root, space="    ")
    output_file = OUTPUT_DIR / f"{safe_filename(category_name)}.xml"
    ElementTree(root).write(output_file, encoding="utf-8", xml_declaration=True)
    return output_file


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Не найден файл: {SOURCE_FILE.resolve()}")

    tree = parse(SOURCE_FILE)
    root = tree.getroot()

    categories = {
        node.attrib["id"]: (node.text or "").strip()
        for node in root.findall("./shop/categories/category")
    }

    grouped: dict[str, list[Element]] = {}
    for offer in root.findall("./shop/offers/offer"):
        category_id = (offer.findtext("categoryId") or "").strip()
        if not category_id:
            continue
        grouped.setdefault(category_id, []).append(offer)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    created = []
    for category_id, category_name in sorted(categories.items(), key=lambda x: x[1].lower()):
        offers = grouped.get(category_id, [])
        if not offers:
            continue
        created.append(
            (category_name, len(offers), write_category_file(category_id, category_name, offers))
        )

    summary = OUTPUT_DIR / "_summary.txt"
    with summary.open("w", encoding="utf-8-sig") as f:
        f.write(f"Всего отдельных файлов: {len(created)}\n")
        f.write(f"Всего товаров: {sum(count for _, count, _ in created)}\n\n")
        for name, count, path in created:
            f.write(f"{name}: {count} товаров — {path.name}\n")

    archive = Path("izbushka-yml-by-category.zip")
    if archive.exists():
        archive.unlink()

    import zipfile
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for file in sorted(OUTPUT_DIR.iterdir()):
            z.write(file, arcname=file.name)

    print()
    print(f"Создано отдельных YML-файлов: {len(created)}")
    print(f"Папка: {OUTPUT_DIR.resolve()}")
    print(f"Архив: {archive.resolve()}")


if __name__ == "__main__":
    main()
