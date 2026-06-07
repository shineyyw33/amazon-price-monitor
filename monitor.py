import requests
import re
import gspread

from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

import os

import json

from oauth2client.service_account import ServiceAccountCredentials

creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(

    creds_json,

    scope

)

client = gspread.authorize(creds)

sheet = client.open(
    "Amazon Price Monitor"
).sheet1
#test
print(sheet.title)
def get_product_info(asin, marketplace):
    
    url = f"https://www.amazon.{marketplace}/dp/{asin}"

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36",
        "Accept-Language":
        "en-US,en;q=0.9"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_text = soup.get_text(
        " ",
        strip=True
    )

    # Title

    title = ""

    title_element = soup.find(
        id="productTitle"
    )

    if title_element:
        title = title_element.get_text(
            strip=True
        )

    # Price

    price = ""

    whole = soup.select_one(
        ".a-price-whole"
    )

    fraction = soup.select_one(
        ".a-price-fraction"
    )

    if whole and fraction:

        price = (
            whole.get_text(strip=True)
            .replace(",", "")
            + "."
            + fraction.get_text(strip=True)
        )

# =====================

# Coupon（稳定版）

# =====================

coupon = "No Coupon"

coupon_element = soup.select_one(

    "[data-csa-c-type='coupon'], #couponBadge, .couponBadge, .promoPriceBlockMessage"

)

if coupon_element:

    coupon_text = coupon_element.get_text(" ", strip=True)

    coupon = coupon_text

    if coupon == "No Coupon":
        import re

    coupon_match = re.search(
        r'(AED|SAR|USD|EUR|GBP)\s*[\d,\.]+\s*coupon',
        soup.get_text(" ", strip=True),
        re.IGNORECASE
    )

    if coupon_match:
        coupon = coupon_match.group(0)

    # Rating

    rating = ""

    rating_match = re.search(
        r'(\d\.\d)\s*out of 5 stars',
        page_text,
        re.IGNORECASE
    )

    if rating_match:

        rating = rating_match.group(1)

    # Review Count

    review_count = ""

    review_match = re.search(
        r'([\d,]+)\s*ratings',
        page_text,
        re.IGNORECASE
    )

    if review_match:

        review_count = review_match.group(1)

    # Deal

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

    # Availability

    availability = ""

    availability_element = soup.select_one(
        "#availability"
    )

    if availability_element:

        availability = (
            availability_element.get_text(
                strip=True
            )
        )

    return {

        "date":
        (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),

        "marketplace":
        marketplace.upper(),

        "asin":
        asin,

        "title":
        title,

        "price":
        price,

        "coupon":
        coupon,

        "rating":
        rating,

        "review_count":
        review_count,

        "deal":
        deal,

        "availability":
        availability
    }
data = get_product_info(
    "B0GR9WJLZ8",
    "ae"
)

print(data)
products = [

    {
        "marketplace": "ae",
        "asin": "B0GR9WJLZ8"
    },

    {
        "marketplace": "sa",
        "asin": "B0GR9WJLZ8"
    }

]

for product in products:

    try:

        data = get_product_info(
            product["asin"],
            product["marketplace"]
        )

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

        print(
            f"成功：{product['marketplace'].upper()} - {product['asin']}"
        )

    except Exception as e:

        print(
            f"失败：{product['marketplace'].upper()} - {product['asin']}"
        )

        print(e)