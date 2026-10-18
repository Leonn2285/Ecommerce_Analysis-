#!/usr/bin/env python3
"""Collect a small, balanced sample from public marketplace search pages.

This script reads public HTML pages only. It does not log in, call marketplace
internal APIs, or attempt to bypass access controls. Run only with permission
from the relevant marketplace. If a marketplace blocks access, stop and obtain
guidance rather than trying to evade the block.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


CATEGORIES = [
    ("beauty", "Làm đẹp", "kem chống nắng"),
    ("home_living", "Nhà cửa & đời sống", "kệ để đồ"),
    ("womens_fashion", "Thời trang nữ", "áo thun nữ"),
    ("electronics", "Điện tử", "tai nghe bluetooth"),
    ("food_beverage", "Thực phẩm & đồ uống", "cà phê hòa tan"),
    ("health", "Sức khỏe", "vitamin C"),
    ("kids_fashion", "Thời trang trẻ em", "áo thun trẻ em"),
    ("stationery", "Văn phòng phẩm", "sổ tay"),
    ("home_appliances", "Điện gia dụng", "nồi chiên không dầu"),
]

SEARCH_URLS = {
    "shopee": "https://shopee.vn/search?keyword={query}",
    "tiki": "https://tiki.vn/search?q={query}",
    "lazada": "https://www.lazada.vn/catalog/?q={query}",
}

FIELDS = [
    "platform", "category", "search_keyword", "product_id", "product_name",
    "brand", "price", "original_price", "discount_percent", "currency",
    "rating", "review_count", "sold_count", "seller_name", "seller_location",
    "seller_rating", "availability", "product_url", "crawl_time_utc",
]

PRODUCT_PATTERNS = {
    "shopee": re.compile(r"/(?:[^/?#]+-)?i\.(\d+)\.(\d+)(?:[/?#]|$)|/product/(\d+)/(\d+)", re.I),
    "tiki": re.compile(r"(?:-p|/p)(\d+)\.html", re.I),
    "lazada": re.compile(r"-i(\d+)(?:-s\d+)?\.html", re.I),
}

PRICE_RE = re.compile(r"(?:₫|đ|VND)\s*([\d.,]+)|([\d.,]+)\s*(?:₫|đ|VND)", re.I)


def product_id(platform: str, url: str) -> str:
    match = PRODUCT_PATTERNS[platform].search(urlparse(url).path)
    if not match:
        return ""
    return "_".join(part for part in match.groups() if part)


def search_page(platform: str, keyword: str) -> str:
    return SEARCH_URLS[platform].format(query=quote(keyword))


def parse_price(text: str) -> str:
    match = PRICE_RE.search(text.replace("\xa0", " "))
    if not match:
        return ""
    raw = next(value for value in match.groups() if value)
    digits = re.sub(r"\D", "", raw)
    return digits


def card_text(anchor) -> str:
    node = anchor
    best = anchor.get_text(" ", strip=True)
    # Marketplace cards vary; use a nearby ancestor with a compact amount of text.
    for _ in range(5):
        if node.parent is None:
            break
        node = node.parent
        text = node.get_text(" ", strip=True)
        if 15 <= len(text) <= 1200:
            best = text
        if len(text) > 1200:
            break
    return re.sub(r"\s+", " ", best)


def product_links(platform: str, html: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: dict[str, dict[str, str]] = {}
    for anchor in soup.select("a[href]"):
        href = urljoin(base_url, anchor.get("href", "")).split("?", 1)[0]
        pid = product_id(platform, href)
        if not pid:
            continue
        text = card_text(anchor)
        title = anchor.get("title", "").strip() or anchor.get_text(" ", strip=True)
        title = re.sub(r"\s+", " ", title)
        if len(title) < 4:
            title = text[:200]
        row = {
            "product_id": pid,
            "product_name": title[:300],
            "price": parse_price(text),
            "product_url": href,
        }
        existing = rows.get(pid)
        if not existing or len(row["product_name"]) > len(existing["product_name"]):
            rows[pid] = row
    return list(rows.values())


def meta_content(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            value = node.get("content", "").strip()
            if value:
                return value
    return ""


def jsonld_objects(soup: BeautifulSoup):
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        queue = data if isinstance(data, list) else [data]
        while queue:
            item = queue.pop(0)
            if isinstance(item, dict):
                yield item
                for key in ("@graph", "mainEntity", "itemListElement"):
                    child = item.get(key)
                    if isinstance(child, list):
                        queue.extend(child)
                    elif isinstance(child, dict):
                        queue.append(child)


def parse_detail(platform: str, html: str, row: dict[str, str]) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    row["product_name"] = meta_content(soup, [
        'meta[property="og:title"]', 'meta[name="twitter:title"]'
    ]) or row.get("product_name", "")
    row["price"] = meta_content(soup, [
        'meta[property="product:price:amount"]', 'meta[property="og:price:amount"]'
    ]) or row.get("price", "")
    row["currency"] = meta_content(soup, [
        'meta[property="product:price:currency"]', 'meta[property="og:price:currency"]'
    ]) or ("VND" if row.get("price") else "")

    for item in jsonld_objects(soup):
        item_type = item.get("@type", "")
        if isinstance(item_type, list):
            item_type = " ".join(item_type)
        if "Product" not in item_type:
            continue
        row["product_name"] = item.get("name") or row.get("product_name", "")
        brand = item.get("brand", "")
        row["brand"] = brand.get("name", "") if isinstance(brand, dict) else str(brand)
        offers = item.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            row["price"] = str(offers.get("price") or row.get("price", ""))
            row["currency"] = offers.get("priceCurrency") or row.get("currency", "VND")
            row["availability"] = str(offers.get("availability", "")).rsplit("/", 1)[-1]
        rating = item.get("aggregateRating", {})
        if isinstance(rating, dict):
            row["rating"] = str(rating.get("ratingValue", ""))
            row["review_count"] = str(rating.get("reviewCount") or rating.get("ratingCount") or "")
        break

    # Use rendered/visible text as a fallback for a rating summary; never collect review text.
    visible = soup.get_text(" ", strip=True)
    if not row.get("rating"):
        match = re.search(r"(?<!\d)([0-5](?:[.,]\d)?)\s*(?:/\s*5|\bđiểm\b)", visible, re.I)
        if match:
            row["rating"] = match.group(1).replace(",", ".")
    if not row.get("review_count"):
        match = re.search(r"([\d.,]+)\s*(?:đánh giá|nhận xét)", visible, re.I)
        if match:
            row["review_count"] = re.sub(r"\D", "", match.group(1))
    row["discount_percent"] = ""
    row["sold_count"] = ""
    row["seller_name"] = ""
    row["seller_location"] = ""
    row["seller_rating"] = ""
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-platform", type=int, default=200)
    parser.add_argument("--delay", type=float, default=2.5)
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--details", action="store_true", help="Open public product pages for detail fields")
    parser.add_argument("--replace", action="store_true", help="Replace the existing CSV instead of merging by platform/product ID")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; AcademicResearch/1.0; contact: course-project)",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
    })
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    quota, remainder = divmod(args.per_platform, len(CATEGORIES))
    all_rows: list[dict[str, str]] = []

    for platform in SEARCH_URLS:
        collected: list[dict[str, str]] = []
        print(f"[{platform}] bắt đầu; mục tiêu {args.per_platform} sản phẩm")
        for index, (slug, label, keyword) in enumerate(CATEGORIES):
            target = quota + (1 if index < remainder else 0)
            url = search_page(platform, keyword)
            print(f"  [{slug}] {keyword}: {target}")
            try:
                response = session.get(url, timeout=25)
            except requests.RequestException as exc:
                print(f"  Dừng tại {platform}/{slug}: lỗi kết nối {exc}")
                break
            if response.status_code in (403, 429) or "captcha" in response.url.lower():
                print(f"  Dừng tại {platform}/{slug}: HTTP {response.status_code}; không thử vượt chặn")
                break
            if response.status_code != 200:
                print(f"  Bỏ qua {platform}/{slug}: HTTP {response.status_code}")
                continue
            matches = product_links(platform, response.text, response.url)
            if not matches:
                print(f"  Không nhận diện được thẻ sản phẩm trên trang tìm kiếm; dừng sàn này để rà selector.")
                break
            for item in matches[:target]:
                item.update({
                    "platform": platform,
                    "category": label,
                    "search_keyword": keyword,
                    "crawl_time_utc": now,
                    "currency": "VND" if item.get("price") else "",
                    "brand": "", "original_price": "", "discount_percent": "",
                    "rating": "", "review_count": "", "sold_count": "",
                    "seller_name": "", "seller_location": "", "seller_rating": "",
                    "availability": "",
                })
                collected.append(item)
            time.sleep(args.delay)

        if args.details:
            for row in collected:
                try:
                    response = session.get(row["product_url"], timeout=25)
                except requests.RequestException as exc:
                    print(f"  Lỗi chi tiết sản phẩm: {exc}")
                    break
                if response.status_code in (403, 429) or "captcha" in response.url.lower():
                    print(f"  Dừng lấy chi tiết {platform}: HTTP {response.status_code}; không thử vượt chặn")
                    break
                if response.status_code == 200:
                    parse_detail(platform, response.text, row)
                time.sleep(args.delay)

        # Preserve observed count, even if a platform exposes fewer items than requested.
        deduped = {f"{r['platform']}:{r['product_id']}": r for r in collected if r.get("product_id")}
        platform_rows = list(deduped.values())[:args.per_platform]
        all_rows.extend(platform_rows)
        print(f"[{platform}] thu được {len(platform_rows)}/{args.per_platform}")

    out = args.output / "marketplace_products.csv"
    if out.exists() and not args.replace:
        with out.open(encoding="utf-8-sig", newline="") as file:
            existing = list(csv.DictReader(file))
        merged: dict[str, dict[str, str]] = {}
        for row in existing + all_rows:
            key = f"{row.get('platform', '')}:{row.get('product_id', '')}"
            if key == ":":
                continue
            merged.setdefault(key, {field: "" for field in FIELDS})
            for field in FIELDS:
                if row.get(field):
                    merged[key][field] = row[field]
        all_rows = list(merged.values())
    with out.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    mode = "thay thế" if args.replace else "gộp theo platform/product_id"
    print(f"Đã lưu {len(all_rows)} dòng ({mode}): {out}")


if __name__ == "__main__":
    main()
