import re

INTENTS = {
    "greeting": (["hi", "hello", "hey", "vanakkam", "good morning", "good evening"], "Hi! 👋 Welcome to ShopBot. Ask me about products, delivery, returns, payment or orders."),
    "delivery": (["delivery", "shipping", "deliver", "when will", "track order", "tracking"], "Standard delivery usually takes 3–7 business days in this demo. Sign in and open My Orders to check your order status."),
    "return": (["return", "refund", "replace", "replacement", "damaged"], "For this demo, contact support within 7 days of delivery with your order number and the issue. A real store should connect this flow to its return policy."),
    "payment": (["payment", "pay", "cash on delivery", "cod", "upi", "card"], "Checkout currently supports Cash on Delivery and UPI/Card as demo choices. No real payment is processed by this project."),
    "products": (["product", "available", "catalog", "show items", "what do you sell"], "ShopBot has demo products across Mobiles, Laptops, Audio, Smart Watches, Accessories and Home. Use the category filters or search bar to explore."),
    "price": (["price", "cost", "cheap", "budget", "discount", "offer"], "You can compare prices and discounts on each product card. Try searching for a category or product name to narrow the list."),
    "account": (["login", "sign in", "register", "account", "password"], "Use Sign in to access orders and checkout. New here? Choose Create account. Passwords are stored as secure hashes in this demo."),
    "thanks": (["thank", "thanks", "nandri"], "You're welcome! 😊 Anything else I can help with?")
}

def chatbot_response(message):
    text = re.sub(r"\s+", " ", message.lower()).strip()
    for _intent, (keywords, response) in INTENTS.items():
        if any(keyword in text for keyword in keywords):
            return response
    return ("I can help with products, delivery, returns, payment, accounts and orders. "
            "Try asking: “How long does delivery take?” or “What payment methods are available?”")
