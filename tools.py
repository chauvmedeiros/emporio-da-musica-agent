"""
Ferramentas (tools) do agente de atendimento do Empório da Música.
Cada ferramenta encapsula uma consulta específica aos dados da loja.
"""

import json
import pandas as pd
from langchain_core.tools import tool
from data_loader import load_all_data, load_store_policies

# Carregar dados uma vez na inicialização
DATA = load_all_data()
STORE_POLICIES = load_store_policies()


@tool
def search_products(query: str) -> str:
    """Busca produtos no catálogo da loja por nome, categoria ou descrição.
    Use esta ferramenta quando o cliente perguntar sobre produtos disponíveis,
    preços, especificações ou quiser recomendações de instrumentos.
    O parâmetro query pode ser o nome do produto, categoria (ex: 'violão', 'guitarra',
    'ukulele', 'teclado', 'bateria', 'baixo') ou característica (ex: 'nylon', 'elétrico').
    """
    df = DATA["products"]
    query_lower = query.lower()

    # Buscar em nome, descrição e categoria
    mask = (
        df["name"].str.lower().str.contains(query_lower, na=False)
        | df["description"].str.lower().str.contains(query_lower, na=False)
        | df["name_category"].str.lower().str.contains(query_lower, na=False)
    )

    results = df[mask & (df["status"] != "discontinued")]

    if results.empty:
        return f"Nenhum produto encontrado para '{query}'. Tente buscar por categoria (violão, guitarra, baixo, bateria, teclado, ukulele) ou por características específicas."

    # Limitar a 10 resultados mais relevantes
    results = results.head(10)

    output = []
    for _, row in results.iterrows():
        stock_info = f"Em estoque: {row['stock_quantity']} unidades" if row["stock_quantity"] > 0 else "❌ FORA DE ESTOQUE"
        status_info = f" ({row['status']})" if row["status"] != "active" else ""

        # Verificar promoção ativa
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
    """Busca um produto específico pelo ID.
    Use quando o cliente já sabe o ID do produto ou quando precisa de detalhes
    de um produto específico.
    """
    df = DATA["products"]
    product = df[df["product_id"] == product_id]

    if product.empty:
        return f"Produto com ID {product_id} não encontrado."

    row = product.iloc[0]
    stock_info = f"Em estoque: {row['stock_quantity']} unidades" if row["stock_quantity"] > 0 else "❌ FORA DE ESTOQUE"

    # Verificar promoção ativa
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
    """Lista todas as promoções ativas no momento.
    Use quando o cliente perguntar sobre promoções, ofertas, descontos
    ou quiser saber o que está em oferta.
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
    """Rastreia um pedido pelo ID do pedido, código de rastreio, nome ou e-mail do cliente.
    Use quando o cliente perguntar sobre o status do pedido, entrega,
    rastreamento ou quiser saber onde está sua encomenda.
    """
    df = DATA["orders"]
    identifier_lower = identifier.lower().strip()

    # Tentar buscar por order_id
    try:
        order_id = int(identifier_lower)
        results = df[df["order_id"] == order_id]
    except ValueError:
        # Buscar por tracking code, nome ou email
        results = df[
            df["tracking_code"].str.lower().str.contains(identifier_lower, na=False)
            | df["name"].str.lower().str.contains(identifier_lower, na=False)
            | df["email"].str.lower().str.contains(identifier_lower, na=False)
        ]

    if results.empty:
        return (
            f"Não encontrei nenhum pedido com '{identifier}'. "
            f"Por favor, verifique o número do pedido, código de rastreio, "
            f"nome completo ou e-mail cadastrado."
        )

    output = []
    for _, order in results.iterrows():
        # Buscar itens do pedido
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
    """Busca informações de um cliente pelo nome, e-mail ou telefone.
    Use quando precisar identificar um cliente ou verificar seus dados cadastrais.
    """
    df = DATA["customers"]
    identifier_lower = identifier.lower().strip()

    results = df[
        df["name"].str.lower().str.contains(identifier_lower, na=False)
        | df["email"].str.lower().str.contains(identifier_lower, na=False)
        | df["phone"].str.contains(identifier, na=False)
    ]

    if results.empty:
        return f"Cliente não encontrado com '{identifier}'. Verifique o nome completo, e-mail ou telefone."

    output = []
    for _, customer in results.iterrows():
        # Buscar pedidos do cliente
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
    """Consulta as políticas da loja para responder dúvidas sobre trocas, devoluções,
    frete, formas de pagamento, horário de funcionamento, garantia, LGPD etc.
    Use quando o cliente perguntar sobre regras da loja, prazos, condições de compra
    ou qualquer política comercial.
    O parâmetro question deve ser a pergunta ou tema específico.
    """
    return (
        f"Pergunta do cliente: {question}\n\n"
        f"=== POLÍTICAS DA LOJA (documento completo) ===\n\n"
        f"{STORE_POLICIES}\n\n"
        f"=== FIM DAS POLÍTICAS ===\n\n"
        f"Responda a pergunta do cliente com base nas políticas acima. "
        f"Seja preciso e cite as regras específicas."
    )


# Lista de todas as ferramentas para o agente
ALL_TOOLS = [
    search_products,
    check_product_by_id,
    check_active_promotions,
    track_order,
    lookup_customer,
    consult_store_policies,
]
