import requests
import re
import gspread
import os
import json

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials

# =====================
# Google Sheet Auth（GitHub Actions / 本地通用）
# =====================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_json,
    scope
)

client = gspread.authorize(creds)

sheet = client.open("Amazon Price Monitor").sheet1

print("Sheet connected:", sheet.title)


# =====================
# 时间（中国时间 UTC+8）
# =====================
def get_beijing_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


# =====================
# 主函数
# =====================
def get_product_info(asin, marketplace):

    url = f"https://www.amazon.{marketplace}/dp/{asin}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    page_text = soup.get_text(" ", strip=True)

    # =====================
    # Title
    # =====================
    title = ""
    title_element = soup.find(id="productTitle")
    if title_element:
        title = title_element.get_text(strip=True)

    # =====================
    # Price
    # =====================
    price = ""

    whole = soup.select_one(".a-price-whole")
    fraction = soup.select_one(".a-price-fraction")

    if whole and fraction:
        price = whole.get_text(strip=True).replace(",", "") + "." + fraction.get_text(strip=True)

    # =====================
    # Coupon（增强版）
    # =====================
    coupon = "No Coupon"

    coupon_element = soup.select_one(
        "[data-csa-c-type='coupon'], #couponBadge, .couponBadge, .promoPriceBlockMessage"
    )

    if coupon_element:
        coupon = coupon_element.get_text(" ", strip=True)

    # 兜底 regex（Amazon经常埋在文本里）
    if "coupon" not in coupon.lower():
        coupon_match = re.search(
            r'(AED|SAR|USD|EUR|GBP)\s*[\d,\.]+\s*coupon',
            page_text,
            re.IGNORECASE
        )
        if coupon_match:
            coupon = coupon_match.group(0)

    # =====================
    # Rating
    # =====================
    rating = ""
    rating_match = re.search(
        r'(\d\.\d)\s*out of 5 stars',
        page_text,
        re.IGNORECASE
    )
    if rating_match:
        rating = rating_match.group(1)

    # =====================
    # Review Count
    # =====================
    review_count = ""
    review_match = re.search(
        r'([\d,]+)\s*ratings',
        page_text,
        re.IGNORECASE
    )
    if review_match:
        review_count = review_match.group(1)

    # =====================
    # Deal
    # =====================
    deal = "No"

    deal_keywords = [
        "Limited time deal",
        "Lightning Deal",
        "Deal of the Day",
        "Prime Day Deal",
        "Best Deal"
    ]

    for keyword in deal_keywords:
        if keyword.lower() in page_text.lower():
            deal = keyword
            break

    # =====================
    # Availability
    # =====================
    availability = ""

    availability_element = soup.select_one("#availability")
    if availability_element:
        availability = availability_element.get_text(strip=True)

    # =====================
    # Return
    # =====================
    return {
        "date": get_beijing_time(),
        "marketplace": marketplace.upper(),
        "asin": asin,
        "title": title,
        "price": price,
        "coupon": coupon,
        "rating": rating,
        "review_count": review_count,
        "deal": deal,
        "availability": availability
    }


# =====================
# Test
# =====================
print(get_product_info("B0GR9WJLZ8", "ae"))


# =====================
# Products
# =====================
products = [
    {"marketplace": "ae", "asin": "B0GR9WJLZ8"},
    {"marketplace": "sa", "asin": "B0GR9WJLZ8"}
]


# =====================
# Write to Sheet
# =====================
for product in products:

    try:
        data = get_product_info(product["asin"], product["marketplace"])

        sheet.append_row([
            data["date"],
            data["marketplace"],
            data["asin"],
            data["title"],
            data["price"],
            data["coupon"],
            data["rating"],
            data["review_count"],
            data["deal"],
            data["availability"]
        ])

        print(f"成功：{product['marketplace'].upper()} - {product['asin']}")

    except Exception as e:
        print(f"失败：{product['marketplace'].upper()} - {product['asin']}")
        print(e)