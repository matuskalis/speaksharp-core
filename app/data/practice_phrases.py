"""
Practice phrase library with phoneme targeting.

Each phrase is associated with specific phonemes for targeted practice.
Phoneme symbols match espeak-ng IPA output.
"""

from typing import List, Dict


PRACTICE_PHRASES: List[Dict] = [
    {"text": "The thin cloth feels smooth", "phonemes": ["θ", "ð"]},
    {"text": "She sells seashells by the seashore", "phonemes": ["ʃ", "s"]},
    {"text": "Red leather yellow leather", "phonemes": ["ɹ", "l"]},
    {"text": "Very worried villagers wave wildly", "phonemes": ["v", "w"]},
    {"text": "Think about thirty three things", "phonemes": ["θ"]},
    {"text": "Please bring blue blocks", "phonemes": ["l", "b"]},
    {"text": "Rarely really early", "phonemes": ["ɹ"]},
    {"text": "Quickly cook the cookies", "phonemes": ["k"]},
    {"text": "Julie chews juicy cherries", "phonemes": ["ʧ", "ʤ"]},
    {"text": "I would like a bottle of water", "phonemes": ["t", "ɾ"]},
    {"text": "The cat sat on the mat", "phonemes": ["æ", "t"]},
    {"text": "How now brown cow", "phonemes": ["aʊ"]},
    {"text": "Peter Piper picked a peck of pickled peppers", "phonemes": ["p"]},
    {"text": "Unique New York", "phonemes": ["j", "ɔː"]},
    {"text": "Toy boat", "phonemes": ["ɔɪ", "oʊ"]},
    {"text": "Irish wristwatch", "phonemes": ["ɪ", "ɹ"]},
    {"text": "Three free throws", "phonemes": ["θ", "ɹ"]},
    {"text": "Which witch is which", "phonemes": ["w", "ɪ"]},
    {"text": "Six thick thistle sticks", "phonemes": ["θ", "s"]},
    {"text": "Lesser leather never weathered wetter weather better", "phonemes": ["ɛ", "ð"]},
]
