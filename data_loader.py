"""
Módulo responsável por carregar e preparar os dados do Empório da Música.
Carrega CSVs em DataFrames e extrai texto das políticas da loja (PDF).
"""

import os
import pandas as pd
from pypdf import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_csv(filename: str) -> pd.DataFrame:
    """Carrega um arquivo CSV do diretório data/."""
    filepath = os.path.join(DATA_DIR, filename)
    return pd.read_csv(filepath)


def load_all_data() -> dict[str, pd.DataFrame]:
    """Carrega todos os CSVs e retorna um dicionário de DataFrames."""
    data = {
        "products": load_csv("products.csv"),
        "categories": load_csv("categories.csv"),
        "customers": load_csv("customers.csv"),
        "orders": load_csv("orders.csv"),
        "order_items": load_csv("order_items.csv"),
        "promotions": load_csv("promotions.csv"),
    }

    # Enriquecer products com nome da categoria
    data["products"] = data["products"].merge(
        data["categories"][["category_id", "name"]],
        on="category_id",
        how="left",
        suffixes=("", "_category"),
    )

    # Enriquecer orders com nome do cliente
    data["orders"] = data["orders"].merge(
        data["customers"][["customer_id", "name", "phone", "email"]],
        on="customer_id",
        how="left",
    )

    # Enriquecer order_items com nome e preço do produto
    data["order_items"] = data["order_items"].merge(
        data["products"][["product_id", "name", "price_brl"]],
        on="product_id",
        how="left",
    )

    return data


def load_store_policies() -> str:
    """Extrai o texto completo do PDF de políticas da loja."""
    pdf_path = os.path.join(DATA_DIR, "politicas_da_loja.pdf")
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)
