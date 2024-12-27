# Tarot Reading

This project is a comprehensive tarot reading AI application that integrates multiple technologies, including Flask, MongoDB, PyTorch, and Qdrant, to provide detailed tarot card interpretations and pictorial essences from the Rider-Waite tarot deck.

---

## Virtual Environment Setup

### Create and Activate Virtual Environment
```bash
python3.12 -m venv tarot_venv
source tarot_venv/bin/activate  # For Linux/Mac
# or
tarot_venv\Scripts\activate  # For Windows
```

### Install Dependencies
```bash
pip install flask
pip install pymongo
conda install pytorch torchvision cudatoolkit=10.0 -c pytorch
pip install -U sentence-transformers
pip install qdrant-client
pip install groq
```

---

## MongoDB Setup

### Database and Collection Details

#### Database Name
```
TarrorCardscheetsheetDB
```

#### Collections
1. **cheetSheetDB**: Contains detailed information for tarot reading, including:
   - `arcana`
   - `card_name`
   - `upright_meaning`
   - `reversed_meaning`
   - `advice_position`
   - `love_position`
   - `career_position`
   - `yesorno_cardreading`

2. **spreadS**: Contains selection criteria for tarot card spreads, including:
   - `category`
   - `spread_name`
   - `number_of_cards`
   - `variations`

---

## Qdrant Vector Database Setup

The Qdrant vector database is utilized for storing and retrieving the pictorial essence of tarot cards from the Rider-Waite tarot deck. An embedding model is employed to enable efficient search through the Qdrant database.

### Embedding Model
```
dunzhang/stella_en_400M_v5
```

---

## Summary
This project combines:
1. **Flask** for backend development.
2. **MongoDB** for storing tarot card meanings and spread details.
3. **Qdrant** for managing and searching pictorial tarot card embeddings.
4. **PyTorch** for utilizing advanced embedding models like `dunzhang/stella_en_400M_v5`.

Set up the project as described above to begin using the tarot reading.

