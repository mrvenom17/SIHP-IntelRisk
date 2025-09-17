# tests/conftest.py
import os
import sys
import nltk

# Disable tokenizers parallelism
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Ensure NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.download('punkt_tab', quiet=True)
        except:
            nltk.download('punkt', quiet=True)