from flask import Flask, request, jsonify, session
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import random
import json
from groq import Groq

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session storage

client = Groq(api_key="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")

mysticSeerPrompt = """"You are "The Mystic Seer," a tarot reader who communicates in a deeply mystical and poetic way. Your role is to offer cryptic and symbolic insights that invite deep reflection. You speak in metaphors, riddles, and spiritual imagery, often drawing upon the wisdom of the cosmos and the mysteries of the unknown. When providing advice, maintain an enigmatic tone that leaves room for interpretation, allowing the user to reflect on their own journey.
Tone Style: Enigmatic, mystical, and poetic
Language Style: Flowing, rich in metaphors and symbolic imagery
Personality: Mysterious, wise, spiritually attuned
Manner of Delivery: Provide cryptic and reflective advice, encouraging the user to explore hidden meanings and spiritual depth.''',
"""
theFortuneTellerPrompt = '''You are "The Fortune Teller," a tarot reader who brings fun and excitement to every reading. You offer quick, entertaining, and witty insights, often with a playful twist. Your style is conversational and lighthearted, but you still provide meaningful guidance. Users come to you for fast-paced, engaging, and fortune-cookie-like predictions.
Tone Style: Playful, witty, and upbeat
Language Style: Conversational, humorous, and entertaining
Personality: Lively, energetic, and charming
Manner of Delivery: Deliver fast, playful readings that are fun yet insightful, making predictions in a witty and charming manner.'''

theModernLifeCoachPrompt = ''' You are "The Modern Life Coach," a tarot reader focused on practical, motivational, and actionable advice. Your tone is direct, encouraging, and goal-oriented, with a focus on personal growth and self-improvement. You provide clear, logical insights and inspire the user to take positive steps forward in their life. Your advice blends tarot wisdom with modern-day life coaching techniques.
Tone Style: Motivational, practical, and uplifting
Language Style: Direct, pragmatic, and empowering
Personality: Supportive, logical, and goal-focused
Manner of Delivery: Offer straightforward, actionable guidance that helps the user achieve their goals and unlock their potential.'''

# Initialize the model for sentence embedding
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(
    "dunzhang/stella_en_400M_v5",
    trust_remote_code=True,
    device="cpu",
    config_kwargs={"use_memory_efficient_attention": False, "unpad_inputs": False}
)

# Set up environment variables for Qdrant
from qdrant_client import QdrantClient
os.environ['QDRANT_HOST'] = 'https://0bebad36-b802-4577-a9be-17cf23e99183.europe-west3-0.gcp.cloud.qdrant.io:6333'
os.environ['QDRANT_API_KEY'] = 'Mr2uiA_jevWxIszHKy9Pf9EElthS32DUAzJGj5-WGxm1ZrR6nAttVg'

qdrant_client_instance = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY")
)
collection_name = "tarotBookletPreprocessedcopystella1"

CARD_FOLDER_PATH = r"E:\ALESA AI\TarrotCardReading-Pradeep\FLASKAPP\CardspngRENAMED - Copy"

# Helper function to initialize MongoDB collection
def get_mongo_collection(db_name, collection_name, mongo_uri='mongodb://localhost:27017'):
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        return db[collection_name]
    except PyMongoError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def chat_with_groq(system_prompt):
    if "messages" not in globals():
        globals()["messages"] = [{"role": "system", "content": system_prompt}]

    # Display previous chat messages
    for message in globals()["messages"]:
        if message["role"] != "system":
            print(f"{message['role']}: {message['content']}")

    # Handle user input
    while True:
        user_input = input("User: ")
        if user_input.strip().lower() == 'exit':
            break

        globals()["messages"].append({"role": "user", "content": user_input})

        # Send the conversation to the Groq API for completion
        response = client.chat.completions.create(
            messages=globals()["messages"],
            model="llama3-70b-8192"
        )

        # Extract and display AI's response
        ai_response = response.choices[0].message.content
        globals()["messages"].append({"role": "assistant", "content": ai_response})
        print(f"Assistant: {ai_response}")

# Function to shuffle tarot cards
def shuffle_tarot_cards(folder_path):
    try:
        cards = [
            {"path": os.path.join(folder_path, filename), 
             "name": os.path.splitext(filename)[0].replace("_", " ")}
            for filename in os.listdir(folder_path) if filename.endswith(('.png', '.jpg'))
        ]
        if len(cards) != 78:
            raise ValueError("The folder must contain exactly 78 tarot card images.")
        
        upright_count = int(len(cards) * 0.67)
        reversed_count = len(cards) - upright_count
        
        upright_cards = random.sample(cards, upright_count)
        remaining_cards = [card for card in cards if card not in upright_cards]
        reversed_cards = random.sample(remaining_cards, reversed_count)
        
        shuffled_cards = (
            [{"card": card, "orientation": "Upright"} for card in upright_cards] +
            [{"card": card, "orientation": "Reversed"} for card in reversed_cards]
        )
        random.shuffle(shuffled_cards)
        
        for idx, card in enumerate(shuffled_cards):
            card["index"] = idx + 1
        
        return shuffled_cards
    except Exception as e:
        print(f"Error in shuffling cards: {e}")
        raise

# Helper function to query Qdrant and retrieve card details
def get_card_from_qdrant(card_name):
    query_vector = model.encode(card_name)
    search_result = qdrant_client_instance.search(
        collection_name=collection_name,
        query_vector=query_vector.tolist(),
        limit=1
    )

    if search_result:
        card_data = search_result[0].payload
        return card_data
    else:
        return {"error": f"Details for '{card_name}' not found in Qdrant."}

# Route to handle tarot options
@app.route('/select-tarot-options', methods=['POST'])
def select_tarot_options():
    try:
        data = request.get_json()
        category = data.get("category")
        spread = data.get("spread")
        variation = data.get("variation")
        selection_method = data.get("selection_method", "random")
        tarot_reader = data.get("tarot_reader", "The Mystic Seer")
        selected_indices = data.get("selected_indices", [])

        if tarot_reader == "The Mystic Seer":
            reader_prompt = mysticSeerPrompt
        elif tarot_reader == "The Fortune Teller":
            reader_prompt = theFortuneTellerPrompt
        elif tarot_reader == "The Modern Life Coach":
            reader_prompt = theModernLifeCoachPrompt
        else:
            return jsonify({"error": "Invalid tarot reader selected."}), 400

        # MongoDB and shuffling logic
        Spreadcollection = get_mongo_collection("TarrorCardscheetsheetDB", "spreadS")
        Cardcollection = get_mongo_collection("TarrorCardscheetsheetDB", "cheetsheetDB")
        if Spreadcollection is None or Cardcollection is None:
            return jsonify({"error": "Failed to connect to MongoDB collections."}), 500

        spread_data = Spreadcollection.find_one({"category": category, "spread_name": spread})
        if not spread_data:
            return jsonify({"error": f"Spread '{spread}' not found in category '{category}'."}), 404

        shuffled_cards = shuffle_tarot_cards(CARD_FOLDER_PATH)
        number_of_cards = spread_data['number_of_cards']

        if selection_method == "manual":
            if not selected_indices:
                return jsonify({"error": "No indices selected for manual selection."}), 400
            
            # Validate the number of indices matches the spread
            if len(selected_indices) != number_of_cards:
                return jsonify({"error": f"Incorrect number of indices selected. Expected {number_of_cards}, got {len(selected_indices)}."}), 400
            
            # Validate that all indices are within the range of shuffled cards
            if any(idx < 1 or idx > len(shuffled_cards) for idx in selected_indices):
                return jsonify({"error": "One or more indices are out of range."}), 400
            
            selected_cards = [shuffled_cards[idx - 1] for idx in selected_indices]
        else:
            selected_cards = random.sample(shuffled_cards, number_of_cards)

        # Retrieve card details from MongoDB and Qdrant
        detailed_cards = []
        for card in selected_cards:
            card_name = card["card"]["name"]
            card_details = Cardcollection.find_one({"card_name": {"$regex": card_name, "$options": "i"}})
            card_qdrant_data = get_card_from_qdrant(card_name)

            if card_details:
                # Organize MongoDB and Qdrant data together for each card
                card_data = {
                    "card_name": card_name,
                    "arcana": card_details.get("arcana"),
                    "upright_meaning": card_details.get("upright_meaning"),
                    "reversed_meaning": card_details.get("reversed_meaning"),
                    "advice_position": card_details.get("advice_position"),
                    "love_position": card_details.get("love_position"),
                    "career_position": card_details.get("career_position"),
                    "yesorno_cardreading": card_details.get("yesorno_cardreading"),
                    "orientation": card["orientation"],
                    "index": card["index"],
                    "pictorial_essence": {
                        "qdrant_details": card_qdrant_data
                    }
                }
                detailed_cards.append(card_data)

        # Store the response data in session or return it to another endpoint
        session['tarot_reading'] = {
            "category": category,
            "spread": spread,
            "variation": variation,
            "tarot_reader": tarot_reader,
            "tarot_reader_prompt": reader_prompt,
            "shuffled_cards": detailed_cards
        }

        return jsonify({"message": "Tarot options successfully selected.", "tarot_reading": session['tarot_reading']}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/process-tarot-reading', methods=['POST'])
def process_tarot_reading():

    try:
        # Fetch the stored tarot reading data from session
        tarot_reading = session.get('tarot_reading')

        if not tarot_reading:
            return jsonify({"error": "No tarot reading data found. Please select tarot options first."}), 400

        # Retrieve tarot reader prompt
        tarot_reader_prompt = tarot_reading.get("tarot_reader_prompt")

        # Extract detailed cards from the stored tarot reading
        selected_cards = tarot_reading.get("shuffled_cards", [])
        
        # Generate detailed descriptions for each card
        card_descriptions = "\n".join(
            f"""{card['index']}. {card['card_name']} ({card['orientation']}):
            Arcana: {card.get('arcana', 'N/A')}
            Meaning: {card.get('upright_meaning') if card['orientation'] == 'Upright' else card.get('reversed_meaning', 'N/A')}
            Advice Position: {card.get('advice_position', 'N/A')}
            Love Position: {card.get('love_position', 'N/A')}
            Career Position: {card.get('career_position', 'N/A')}
            Yes/No Reading: {card.get('yesorno_cardreading', 'N/A')}
            Pictorial Essence: {card.get('pictorial_essence', {}).get('qdrant_details', 'N/A')}
            """
            for card in selected_cards
        )

        # Format the system prompt with the reader's style and card details
        system_prompt = f"""{tarot_reader_prompt}
        You will use the following user inputs and stored tarot card details to provide insightful, empathetic readings:\n\nThe following cards were drawn:\n{card_descriptions}\n
Your task:

Maintain the order of the cards as chosen by the user.
For each card, analyze its meaning, position in the spread, and its relationship to the chosen variation (e.g., Past, Present, Future, Advice, Outcome).
Use both inDepthMeansofCards and pictorialDescriptionofCards to provide a well-rounded, insightful interpretation of the user's query.

For each card in the spread:

Card <card_number> <card name>
Inference: (Analyze Card <card_number>, considering its specific position in the spread and the selected variation. Incorporate insights from inDepthMeansofCards and pictorialDescriptionofCards to apply the card's significance to the user's situation.)
Final Interpretation:

After analyzing all cards individually, synthesize the information from inDepthMeansofCards and pictorialDescriptionofCards to provide a holistic reading. Ensure coherence across all cards in the spread and their relationship to the variation. Offer clear and practical guidance on topics such as love, finance, or career, ensuring alignment with traditional tarot principles.'''

        """

        # Initialize messages for Groq
        messages = [{"role": "system", "content": system_prompt}]
        
        # Optionally include user input if this is part of an interactive chat
        user_input = request.json.get("user_input", "Please interpret the cards.")
        messages.append({"role": "user", "content": user_input})

        # Send the messages to the Groq API for chat completion
        response = client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192"
        )

        # Extract AI's response
        ai_response = response.choices[0].message.content

        return jsonify({
            "message": "Tarot reading processed successfully.",
            "tarot_reading": tarot_reading,
            "ai_response": ai_response
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
