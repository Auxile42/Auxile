import gradio as gr
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Accéder à la variable d'environnement
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "1EDOYnjtjH8FYdgHhKaM7TgjnkxbiASW")

# Vérifiez que la clé API est chargée
if not MISTRAL_API_KEY:
    raise ValueError("La clé API Mistral n'est pas définie dans le fichier .env")

API_URL = 'https://api.mistral.ai/v1/chat/completions'

# Menu du restaurant
MENU_ITEMS = [
    {
        "id": 1,
        "name": "Burger Classic",
        "price": 12.99,
        "description": "Bœuf, salade, tomate, oignon, fromage",
        "category": "Burgers",
        "allergenes": ["gluten", "lactose"],
        "preparation": "Viande 100% bœuf français, cuite à point, avec fromage fondu et légumes frais"
    },
    {
        "id": 2,
        "name": "Pizza Margherita",
        "price": 14.99,
        "description": "Sauce tomate, mozzarella, basilic",
        "category": "Pizzas",
        "allergenes": ["gluten", "lactose"],
        "preparation": "Pâte fraîche maison, sauce tomate italienne, mozzarella di bufala, basilic frais"
    },
    {
        "id": 3,
        "name": "Salade César",
        "price": 10.99,
        "description": "Laitue romaine, parmesan, croûtons, sauce césar",
        "category": "Salades",
        "allergenes": ["gluten", "œuf", "lactose"],
        "preparation": "Salade romaine fraîche, sauce césar maison, croûtons à l'ail, copeaux de parmesan"
    },
    {
        "id": 4,
        "name": "Pâtes Carbonara",
        "price": 13.99,
        "description": "Spaghetti, œuf, parmesan, lardons",
        "category": "Pâtes",
        "allergenes": ["gluten", "œuf", "lactose"],
        "preparation": "Pâtes fraîches, sauce crémeuse aux œufs, lardons fumés, parmesan râpé"
    }
]

def get_system_prompt():
    menu_details = []
    for item in MENU_ITEMS:
        details = (
            f"- {item['name']} ({item['price']}€)\n"
            f"  Description: {item['description']}\n"
            f"  Préparation: {item['preparation']}\n"
            f"  Allergènes: {', '.join(item['allergenes'])}"
        )
        menu_details.append(details)

    menu_str = "\n\n".join(menu_details)

    return f"""Tu es un assistant virtuel expert pour un restaurant français. Voici tes capacités et directives :

1. EXPERTISE CULINAIRE
- Connaissance approfondie de chaque plat, sa préparation et ses ingrédients
- Capacité à expliquer les techniques de cuisine utilisées
- Information sur les allergènes et régimes spéciaux
- Suggestions personnalisées basées sur les préférences client

2. GESTION DES COMMANDES
- Prise de commande précise et détaillée
- Vérification systématique des préférences de cuisson
- Gestion des modifications et personnalisations
- Calcul automatique du total
- Confirmation claire de la commande

3. INFORMATIONS PRATIQUES
- Horaires : 11h00-23h00, 7j/7
- Réservations : groupes de 2 à 12 personnes
- Temps de préparation moyen par plat
- Options de paiement : CB, espèces, tickets restaurant
- Parking gratuit disponible

MENU DÉTAILLÉ :
{menu_str}

PROTOCOLE DE COMMANDE :
1. Écouter attentivement la demande du client
2. Poser des questions de clarification si nécessaire
3. Confirmer les détails de chaque plat
4. Vérifier les allergies ou restrictions alimentaires
5. Annoncer le total
6. Proposer des accompagnements ou desserts
7. Confirmer la commande complète"""

# Initialisation de l'historique de conversation
conversation_history = [
    {"role": "system", "content": get_system_prompt()}
]

# Panier
current_order = []

def format_menu():
    menu_html = "<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
    menu_html += "<h2 style='color: #1a73e8; font-size: 24px; margin-bottom: 20px;'>🍽️ Notre Menu</h2>"

    # Grouper par catégorie
    categories = {}
    for item in MENU_ITEMS:
        if item['category'] not in categories:
            categories[item['category']] = []
        categories[item['category']].append(item)

    # Afficher par catégorie
    for category, items in categories.items():
        menu_html += f"<h3 style='color: #202124; font-size: 18px; margin-top: 15px;'>📋 {category}</h3>"

        for item in items:
            menu_html += f"""
            <div style='background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong style='font-size: 16px;'>{item['name']}</strong>
                    <span style='color: #1a73e8; font-weight: bold;'>{item['price']}€</span>
                </div>
                <p style='margin: 5px 0; color: #5f6368;'>{item['description']}</p>
                <p style='margin: 5px 0; font-size: 12px; color: #d93025;'>⚠️ Allergènes : {', '.join(item['allergenes'])}</p>
            </div>
            """

    menu_html += "</div>"
    return menu_html

def format_order():
    if not current_order:
        return "<p style='color: #5f6368; text-align: center;'>Votre panier est vide</p>"

    order_html = "<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
    order_html += "<h2 style='color: #1a73e8; font-size: 20px; margin-bottom: 15px;'>🛒 Votre Commande</h2>"

    total = 0
    for order in current_order:
        item = order['item']
        quantity = order['quantity']
        subtotal = item['price'] * quantity
        total += subtotal

        order_html += f"""
        <div style='padding: 10px 0; border-bottom: 1px solid #e0e0e0;'>
            <div style='display: flex; justify-content: space-between;'>
                <span><strong>{quantity}x</strong> {item['name']}</span>
                <span>{subtotal:.2f}€</span>
            </div>
        </div>
        """

    order_html += f"""
    <div style='margin-top: 15px; display: flex; justify-content: space-between;'>
        <strong style='font-size: 18px;'>Total:</strong>
        <strong style='font-size: 18px; color: #1a73e8;'>{total:.2f}€</strong>
    </div>
    """

    order_html += "</div>"
    return order_html

def analyze_response(message):
    global current_order

    # Recherche des plats mentionnés dans la réponse
    for item in MENU_ITEMS:
        if item['name'].lower() in message.lower():
            # Recherche de quantités
            import re
            quantities = re.findall(r'(\d+)\s*' + item['name'], message, re.IGNORECASE)
            quantity = int(quantities[0]) if quantities else 1

            # Ajouter au panier
            current_order.append({
                'item': item,
                'quantity': quantity
            })

def chat(message, history):
    global conversation_history

    try:
        # Ajouter le message utilisateur à l'historique
        conversation_history.append({
            "role": "user",
            "content": message
        })

        # Limiter l'historique à 10 messages
        if len(conversation_history) > 10:
            conversation_history = [
                conversation_history[0],  # Garder le prompt système
                *conversation_history[-9:]  # Garder les 9 derniers messages
            ]

        # Appel à l'API Mistral
        response = requests.post(
            API_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MISTRAL_API_KEY}'
            },
            json={
                'model': 'mistral-tiny',
                'messages': conversation_history,
                'temperature': 0.7,
                'max_tokens': 400
            }
        )

        if response.status_code == 200:
            bot_message = response.json()['choices'][0]['message']['content']

            # Ajouter la réponse à l'historique
            conversation_history.append({
                "role": "assistant",
                "content": bot_message
            })

            # Analyser la réponse pour détecter les commandes
            analyze_response(bot_message)

            # Retourner le message sous forme de tuple
            return [(message, bot_message)]
        else:
            error_message = "Désolé, je rencontre des difficultés techniques. Pouvez-vous réessayer plus tard ?"
            return [(message, error_message)]

    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion: {str(e)}")
        error_message = "Désolé, je rencontre des difficultés techniques. Pouvez-vous réessayer plus tard ?"
        return [(message, error_message)]

def confirm_order():
    global current_order

    if not current_order:
        return [(None, "Votre panier est vide. Veuillez ajouter des articles avant de confirmer.")]

    total = sum(order['item']['price'] * order['quantity'] for order in current_order)

    order_summary = "✅ Commande confirmée !\n\n"
    order_summary += "Récapitulatif :\n"
    for order in current_order:
        item = order['item']
        quantity = order['quantity']
        order_summary += f"- {quantity}x {item['name']} ({item['price']}€)\n"

    order_summary += f"\nTotal : {total:.2f}€"
    order_summary += "\n\nMerci pour votre commande ! Elle sera prête dans environ 20 minutes."

    # Vider le panier
    current_order.clear()

    return [(None, order_summary)]

def clear_order():
    global current_order
    current_order.clear()
    return [(None, "Panier vidé avec succès.")]

# Interface Gradio
with gr.Blocks(css="""
    .container {
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }
    .header {
        text-align: center;
        margin-bottom: 20px;
    }
    .header h1 {
        color: #1a73e8;
    }
""") as demo:
    gr.HTML("""
    <div class="header">
        <h1>🍽️ Assistant Restaurant</h1>
        <p>Je peux vous aider avec le menu, prendre votre commande ou répondre à vos questions.</p>
    </div>
    """)

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            menu_html = gr.HTML(format_menu())

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
                avatar_images=(None, "https://img.icons8.com/color/96/000000/chef-hat.png"),
                height=500
            )
            msg = gr.Textbox(
                placeholder="Tapez votre message ici...",
                container=False,
                scale=7
            )
            with gr.Row():
                submit = gr.Button("Envoyer", variant="primary", scale=1)

        with gr.Column(scale=2):
            order_html = gr.HTML(format_order())
            with gr.Row():
                confirm_btn = gr.Button("✅ Confirmer la commande", variant="primary")
                clear_btn = gr.Button("🗑️ Vider le panier", variant="secondary")

    # Événements
    submit.click(chat, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    ).then(
        format_order, None, [order_html]
    )

    msg.submit(chat, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    ).then(
        format_order, None, [order_html]
    )

    confirm_btn.click(confirm_order, None, [chatbot]).then(
        format_order, None, [order_html]
    )

    clear_btn.click(clear_order, None, [chatbot]).then(
        format_order, None, [order_html]
    )

    # Message de bienvenue
    demo.load(
        lambda: [(None, "Bonjour ! Je suis votre assistant virtuel. Je peux vous aider avec le menu, prendre votre commande ou répondre à vos questions. Comment puis-je vous aider aujourd'hui ?")],
        None,
        [chatbot]
    )

# Lancer l'application
if __name__ == "__main__":
    demo.launch(share=True)
