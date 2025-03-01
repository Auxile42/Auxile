import gradio as gr
import requests
import json
import re
from datetime import datetime

# Configuration
MISTRAL_API_KEY = '1EDOYnjtjH8FYdgHhKaM7TgjnkxbiASW'
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
    
    return f"""Tu es un assistant virtuel expert pour un restaurant français, mais tu peux aussi répondre à toutes sortes de questions générales. Voici tes capacités et directives :

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

4. CONNAISSANCES GÉNÉRALES
- Tu peux répondre à des questions sur n'importe quel sujet
- Tu as accès à des connaissances générales sur le monde
- Tu peux aider avec des informations sur divers domaines comme la science, l'histoire, la culture, etc.
- Tu peux donner des conseils sur divers sujets

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
                <button onclick='addToOrder({item["id"]})' style='background-color: #1a73e8; color: white; border: none; border-radius: 4px; padding: 5px 10px; margin-top: 5px; cursor: pointer;'>Ajouter</button>
            </div>
            """
    
    menu_html += "</div>"
    return menu_html

def format_order():
    if not current_order:
        return "<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;'><p style='color: #5f6368;'>Votre panier est vide</p></div>"
    
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
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span><strong>{quantity}x</strong> {item['name']}</span>
                    <div style='font-size: 12px; color: #5f6368;'>{item['price']}€ par unité</div>
                </div>
                <div style='display: flex; align-items: center;'>
                    <span style='font-weight: bold; margin-right: 10px;'>{subtotal:.2f}€</span>
                    <button onclick='removeFromOrder({item["id"]})' style='background-color: transparent; border: none; color: #d93025; cursor: pointer;'>🗑️</button>
                </div>
            </div>
        </div>
        """
    
    order_html += f"""
    <div style='margin-top: 15px; display: flex; justify-content: space-between;'>
        <strong style='font-size: 18px;'>Total:</strong>
        <strong style='font-size: 18px; color: #1a73e8;'>{total:.2f}€</strong>
    </div>
    
    <div style='margin-top: 20px;'>
        <button onclick='confirmOrder()' style='background-color: #34a853; color: white; border: none; border-radius: 4px; padding: 10px; width: 100%; font-weight: bold; cursor: pointer;'>✅ Confirmer la commande</button>
        <button onclick='clearOrder()' style='background-color: #f8f9fa; color: #d93025; border: 1px solid #d93025; border-radius: 4px; padding: 8px; width: 100%; margin-top: 10px; font-weight: bold; cursor: pointer;'>🗑️ Vider le panier</button>
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
            quantities = re.findall(r'(\d+)\s*' + item['name'], message, re.IGNORECASE)
            quantity = int(quantities[0]) if quantities else 1
            
            # Vérifier si l'item existe déjà dans le panier
            existing_item = next((order for order in current_order if order['item']['id'] == item['id']), None)
            
            if existing_item:
                existing_item['quantity'] += quantity
            else:
                # Ajouter au panier
                current_order.append({
                    'item': item,
                    'quantity': quantity
                })

def add_to_order(item_id):
    global current_order
    
    # Trouver l'item dans le menu
    item = next((item for item in MENU_ITEMS if item['id'] == item_id), None)
    if not item:
        return "Item non trouvé"
    
    # Vérifier si l'item existe déjà dans le panier
    existing_item = next((order for order in current_order if order['item']['id'] == item_id), None)
    
    if existing_item:
        existing_item['quantity'] += 1
    else:
        # Ajouter au panier
        current_order.append({
            'item': item,
            'quantity': 1
        })
    
    return format_order()

def remove_from_order(item_id):
    global current_order
    
    # Filtrer le panier pour retirer l'item
    current_order = [order for order in current_order if order['item']['id'] != item_id]
    
    return format_order()

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
                'max_tokens': 800
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
            
            return bot_message
        else:
            error_message = "Désolé, je rencontre des difficultés techniques. Pouvez-vous réessayer plus tard ?"
            return error_message
            
    except Exception as e:
        print(f"Erreur: {str(e)}")
        error_message = "Désolé, je rencontre des difficultés techniques. Pouvez-vous réessayer plus tard ?"
        return error_message

def confirm_order():
    global current_order
    
    if not current_order:
        return "Votre panier est vide. Veuillez ajouter des articles avant de confirmer."
    
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
    
    return order_summary

def clear_order():
    global current_order
    current_order.clear()
    return "Panier vidé avec succès."

# Fonctions JavaScript pour les interactions
js = """
function addToOrder(itemId) {
    gradioApp().querySelector('#add_to_order_btn').click();
    document.getElementById('item_id_input').value = itemId;
}

function removeFromOrder(itemId) {
    gradioApp().querySelector('#remove_from_order_btn').click();
    document.getElementById('item_id_input').value = itemId;
}

function confirmOrder() {
    gradioApp().querySelector('#confirm_order_btn').click();
}

function clearOrder() {
    gradioApp().querySelector('#clear_order_btn').click();
}
"""

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
    .gradio-container {
        max-width: 1200px !important;
    }
""", js=js) as demo:
    gr.HTML("""
    <div class="header">
        <h1>🍽️ Assistant Restaurant</h1>
        <p>Je peux vous aider avec le menu, prendre votre commande ou répondre à vos questions.</p>
    </div>
    """)
    
    # Input caché pour l'ID de l'item
    item_id_input = gr.Number(value=0, visible=False, elem_id="item_id_input")
    
    with gr.Row():
        with gr.Column(scale=2):
            menu_html = gr.HTML(format_menu())
            
            # Boutons cachés pour les actions JavaScript
            with gr.Row(visible=False):
                add_to_order_btn = gr.Button("Ajouter au panier", elem_id="add_to_order_btn")
                remove_from_order_btn = gr.Button("Retirer du panier", elem_id="remove_from_order_btn")
                confirm_order_btn = gr.Button("Confirmer", elem_id="confirm_order_btn")
                clear_order_btn = gr.Button("Vider", elem_id="clear_order_btn")
        
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
                avatar_images=(None, "https://img.icons8.com/color/96/000000/chef-hat.png"),
                height=500
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Tapez votre message ici...",
                    container=False,
                    scale=7
                )
                submit = gr.Button("Envoyer", variant="primary", scale=1)
        
        with gr.Column(scale=2):
            order_html = gr.HTML(format_order())
    
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
    
    # Événements pour les boutons cachés
    add_to_order_btn.click(
        lambda x: add_to_order(int(x)), 
        [item_id_input], 
        [order_html]
    )
    
    remove_from_order_btn.click(
        lambda x: remove_from_order(int(x)), 
        [item_id_input], 
        [order_html]
    )
    
    confirm_order_btn.click(
        confirm_order, 
        None, 
        [chatbot]
    ).then(
        format_order, 
        None, 
        [order_html]
    )
    
    clear_order_btn.click(
        clear_order, 
        None, 
        [chatbot]
    ).then(
        format_order, 
        None, 
        [order_html]
    )
    
    # Message de bienvenue
    demo.load(
        lambda: [[None, "Bonjour ! Je suis votre assistant virtuel. Je peux vous aider avec le menu, prendre votre commande ou répondre à vos questions sur notre restaurant ou n'importe quel autre sujet. Comment puis-je vous aider aujourd'hui ?"]],
        None,
        [chatbot]
    )

# Lancer l'application
if __name__ == "__main__":
    demo.launch(share=True)