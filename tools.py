"""
Tools for the Empório da Música customer service agent.
Each tool encapsulates a specific query over the store's data.
"""

import json
import unicodedata

import pandas as pd
from langchain_core.tools import tool
from data_loader import load_all_data, load_store_policies

# Load data once at startup
DATA = load_all_data()
STORE_POLICIES = load_store_policies()


def _normalize(text) -> str:
    """Normalize text for search: lowercase and accent-free.
    Lets customers find products even when typing without accents
    (e.g. 'violao' matches 'Violão'), as is common on WhatsApp.
    """
    normalized = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in normalized if not unicodedata.combining(c))


@tool
def search_products(query: str) -> str:
    """Search the store catalog for products by name, category, or description.
    Use this tool when the customer asks about available products, prices,
    specifications, or wants instrument recommendations.
    The query parameter can be the product name, a category (e.g. 'violão', 'guitarra',
    'ukulele', 'teclado', 'bateria', 'baixo') or a feature (e.g. 'nylon', 'elétrico').
    """
    df = DATA["products"]
    query_norm = _normalize(query)

    # Search in name, description, and category (ignoring accents and case)
    mask = (
        df["name"].map(_normalize).str.contains(query_norm, na=False, regex=False)
        | df["description"].map(_normalize).str.contains(query_norm, na=False, regex=False)
        | df["name_category"].map(_normalize).str.contains(query_norm, na=False, regex=False)
    )

    results = df[mask & (df["status"] != "discontinued")]

    if results.empty:
        return f"Nenhum produto encontrado para '{query}'. Tente buscar por categoria (violão, guitarra, baixo, bateria, teclado, ukulele) ou por características específicas."

    # Limit to the 10 most relevant results
    results = results.head(10)

    output = []
    for _, row in results.iterrows():
        stock_info = f"Em estoque: {row['stock_quantity']} unidades" if row["stock_quantity"] > 0 else "❌ FORA DE ESTOQUE"
        status_info = f" ({row['status']})" if row["status"] != "active" else ""

        # Check for an active promotion
        promo = DATA["promotions"][
            (DATA["promotions"]["product_id"] == row["product_id"])
            & (DATA["promotions"]["is_active"] == 1)
        ]
        promo_info = ""
        if not promo.empty:
            discount = promo.iloc[0]["discount_percent"]
            promo_desc = promo.iloc[0]["description"]
            price_with_discount = row["price_brl"] * (1 - discount / 100)
            promo_info = f"\n  🏷️ PROMOÇÃO: {promo_desc} - {discount}% OFF → R$ {price_with_discount:,.2f}"

        specs = ""
        if pd.notna(row.get("specs")):
            try:
                specs_dict = json.loads(row["specs"]) if isinstance(row["specs"], str) else row["specs"]
                specs = f"\n  Specs: {json.dumps(specs_dict, ensure_ascii=False)}"
            except (json.JSONDecodeError, TypeError):
                pass

        output.append(
            f"• {row['name']} (ID: {row['product_id']})\n"
            f"  Preço: R$ {row['price_brl']:,.2f}\n"
            f"  Categoria: {row['name_category']}\n"
            f"  {stock_info}{status_info}{promo_info}{specs}\n"
            f"  {row['description']}"
        )

    return f"Encontrei {len(results)} produto(s):\n\n" + "\n\n".join(output)


@tool
def check_product_by_id(product_id: int) -> str:
    """Look up a specific product by ID.
    Use when the customer already knows the product ID or needs details
    about a specific product.
    """
    df = DATA["products"]
    product = df[df["product_id"] == product_id]

    if product.empty:
        return f"Produto com ID {product_id} não encontrado."

    row = product.iloc[0]
    stock_info = f"Em estoque: {row['stock_quantity']} unidades" if row["stock_quantity"] > 0 else "❌ FORA DE ESTOQUE"

    # Check for an active promotion
    promo = DATA["promotions"][
        (DATA["promotions"]["product_id"] == product_id)
        & (DATA["promotions"]["is_active"] == 1)
    ]
    promo_info = ""
    if not promo.empty:
        discount = promo.iloc[0]["discount_percent"]
        promo_desc = promo.iloc[0]["description"]
        price_with_discount = row["price_brl"] * (1 - discount / 100)
        promo_info = f"\n🏷️ PROMOÇÃO: {promo_desc} - {discount}% OFF → R$ {price_with_discount:,.2f}"

    return (
        f"📦 {row['name']} (ID: {product_id})\n"
        f"Preço: R$ {row['price_brl']:,.2f}{promo_info}\n"
        f"Categoria: {row['name_category']}\n"
        f"Status: {row['status']}\n"
        f"{stock_info}\n"
        f"Descrição: {row['description']}\n"
        f"Specs: {row.get('specs', 'N/A')}"
    )


@tool
def check_active_promotions() -> str:
    """List all currently active promotions.
    Use when the customer asks about promotions, offers, discounts,
    or wants to know what is on sale.
    """
    promos = DATA["promotions"][DATA["promotions"]["is_active"] == 1]

    if promos.empty:
        return "No momento não temos promoções ativas."

    output = []
    for _, promo in promos.iterrows():
        product = DATA["products"][DATA["products"]["product_id"] == promo["product_id"]]
        if not product.empty:
            p = product.iloc[0]
            original_price = p["price_brl"]
            discounted_price = original_price * (1 - promo["discount_percent"] / 100)
            output.append(
                f"🏷️ {promo['description']} - {promo['discount_percent']}% OFF\n"
                f"  Produto: {p['name']}\n"
                f"  De R$ {original_price:,.2f} por R$ {discounted_price:,.2f}\n"
                f"  Economia: R$ {original_price - discounted_price:,.2f}"
            )

    return f"🔥 Promoções ativas ({len(output)}):\n\n" + "\n\n".join(output)


@tool
def track_order(identifier: str) -> str:
    """Track an order by order ID, tracking code, customer name, or e-mail.
    Use when the customer asks about order status, delivery, tracking,
    or wants to know where their package is.
    """
    df = DATA["orders"]
    identifier_lower = identifier.lower().strip()

    # Try to look up by order_id
    try:
        order_id = int(identifier_lower)
        results = df[df["order_id"] == order_id]
    except ValueError:
        # Search by tracking code, name, or email (ignoring accents and case)
        query_norm = _normalize(identifier_lower)
        results = df[
            df["tracking_code"].map(_normalize).str.contains(query_norm, na=False, regex=False)
            | df["name"].map(_normalize).str.contains(query_norm, na=False, regex=False)
            | df["email"].map(_normalize).str.contains(query_norm, na=False, regex=False)
        ]

    if results.empty:
        return (
            f"Não encontrei nenhum pedido com '{identifier}'. "
            f"Por favor, verifique o número do pedido, código de rastreio, "
            f"nome completo ou e-mail cadastrado."
        )

    output = []
    for _, order in results.iterrows():
        # Fetch the order items
        items = DATA["order_items"][DATA["order_items"]["order_id"] == order["order_id"]]
        items_str = ", ".join(
            f"{row['name']} (x{row['quantity']})" for _, row in items.iterrows()
        )

        status_map = {
            "pending": "⏳ Pendente",
            "confirmed": "✅ Confirmado",
            "shipped": "🚚 Enviado",
            "delivered": "📦 Entregue",
            "cancelled": "❌ Cancelado",
        }
        status = status_map.get(order["status"], order["status"])

        tracking = f"\nCódigo de rastreio: {order['tracking_code']}" if pd.notna(order.get("tracking_code")) and order["tracking_code"] else ""
        delivery = f"\nPrevisão de entrega: {order['estimated_delivery']}" if pd.notna(order.get("estimated_delivery")) and order["estimated_delivery"] else ""
        notes = f"\nObs: {order['notes']}" if pd.notna(order.get("notes")) and order["notes"] else ""

        output.append(
            f"📋 Pedido #{order['order_id']}\n"
            f"Cliente: {order['name']}\n"
            f"Data: {order['order_date']}\n"
            f"Status: {status}\n"
            f"Itens: {items_str}\n"
            f"Total: R$ {order['total_brl']:,.2f}\n"
            f"Pagamento: {order['payment_method']}"
            f"{tracking}{delivery}{notes}"
        )

    return "\n\n---\n\n".join(output)


@tool
def lookup_customer(identifier: str) -> str:
    """Look up a customer's information by name, e-mail, or phone.
    Use when you need to identify a customer or verify their records.
    """
    df = DATA["customers"]
    query_norm = _normalize(identifier.strip())

    results = df[
        df["name"].map(_normalize).str.contains(query_norm, na=False, regex=False)
        | df["email"].map(_normalize).str.contains(query_norm, na=False, regex=False)
        | df["phone"].str.contains(identifier.strip(), na=False, regex=False)
    ]

    if results.empty:
        return f"Cliente não encontrado com '{identifier}'. Verifique o nome completo, e-mail ou telefone."

    output = []
    for _, customer in results.iterrows():
        # Fetch the customer's orders
        orders = DATA["orders"][DATA["orders"]["customer_id"] == customer["customer_id"]]
        orders_info = f"{len(orders)} pedido(s)" if not orders.empty else "Nenhum pedido"

        output.append(
            f"👤 {customer['name']} (ID: {customer['customer_id']})\n"
            f"📞 {customer['phone']}\n"
            f"📧 {customer['email']}\n"
            f"📍 {customer['city']}\n"
            f"🛒 {orders_info}"
        )

    return "\n\n".join(output)


@tool
def consult_store_policies(question: str) -> str:
    """Consult the store policies to answer questions about exchanges, returns,
    shipping, payment methods, business hours, warranty, LGPD (data privacy), etc.
    Use when the customer asks about store rules, deadlines, purchase conditions,
    or any commercial policy.
    The question parameter should be the specific question or topic.
    """
    return (
        f"Pergunta do cliente: {question}\n\n"
        f"=== POLÍTICAS DA LOJA (documento completo) ===\n\n"
        f"{STORE_POLICIES}\n\n"
        f"=== FIM DAS POLÍTICAS ===\n\n"
        f"Responda a pergunta do cliente com base nas políticas acima. "
        f"Seja preciso e cite as regras específicas."
    )


# List of all tools available to the agent
ALL_TOOLS = [
    search_products,
    check_product_by_id,
    check_active_promotions,
    track_order,
    lookup_customer,
    consult_store_policies,
]
