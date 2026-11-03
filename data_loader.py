"""
Module responsible for loading and preparing the Empório da Música data.
Loads CSVs into DataFrames and extracts the store policies text (PDF).
"""

import os
import pandas as pd
from pypdf import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_csv(filename: str) -> pd.DataFrame:
    """Load a CSV file from the data/ directory."""
    filepath = os.path.join(DATA_DIR, filename)
    return pd.read_csv(filepath)


def load_all_data() -> dict[str, pd.DataFrame]:
    """Load all CSVs and return a dictionary of DataFrames."""
    data = {
        "products": load_csv("products.csv"),
        "categories": load_csv("categories.csv"),
        "customers": load_csv("customers.csv"),
        "orders": load_csv("orders.csv"),
        "order_items": load_csv("order_items.csv"),
        "promotions": load_csv("promotions.csv"),
    }

    # Enrich products with the category name
    data["products"] = data["products"].merge(
        data["categories"][["category_id", "name"]],
        on="category_id",
        how="left",
        suffixes=("", "_category"),
    )

    # Enrich orders with the customer name
    data["orders"] = data["orders"].merge(
        data["customers"][["customer_id", "name", "phone", "email"]],
        on="customer_id",
        how="left",
    )

    # Enrich order_items with the product name and price
    data["order_items"] = data["order_items"].merge(
        data["products"][["product_id", "name", "price_brl"]],
        on="product_id",
        how="left",
    )

    return data


def load_store_policies() -> str:
    """Extract the full text from the store policies PDF."""
    pdf_path = os.path.join(DATA_DIR, "politicas_da_loja.pdf")
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)
