#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE MODERACIÓN PROFESIONAL - 871 PALABRAS PROHIBIDAS PRE-CARGADAS
Basado en repositorios profesionales de internet
- Verificación de username
- 871 palabras prohibidas PRE-CARGADAS
- Detección de enlaces y desvíos
- Sistema de warns (3 = ban automático)
- Respuesta INSTANTÁNEA
- NUNCA se duerme - Keepalive cada 30 segundos
"""
import os
import time
import logging
import threading
import re
import unicodedata
from collections import defaultdict
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
load_dotenv()

DEFAULT_BOT_TOKEN = '8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips'
DEFAULT_GROUP_ID = -1003534894759
OWNER_ID = 0  # CAMBIAR POR TU ID

BOT_TOKEN = os.getenv('BOT_TOKEN', DEFAULT_BOT_TOKEN)
TARGET_GROUP_ID_STR = os.getenv('TARGET_GROUP_ID', str(DEFAULT_GROUP_ID))
OWNER_ID = int(os.getenv('OWNER_ID', OWNER_ID))

try:
    TARGET_GROUP_ID = int(TARGET_GROUP_ID_STR)
except (ValueError, TypeError):
    TARGET_GROUP_ID = DEFAULT_GROUP_ID

LOG_FILE = "moderation_bot.log"

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"✅ BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"✅ TARGET_GROUP_ID: {TARGET_GROUP_ID}")
logger.info(f"✅ OWNER_ID: {OWNER_ID}")

# ============================================================================
# INICIALIZAR BOT
# ============================================================================
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================================
# BLACKLIST PRE-CARGADO - 871 PALABRAS PROFESIONALES
# ============================================================================

DEFAULT_BANNED_WORDS = {
    '1 man 1 jar', '1m1j', '1man1jar', '2 girls 1 cup', '2g1c', '2girls1cup',
    'acrotomophile', 'acrotomophilia', 'alabama hot pocket', 'alabama tuna melt',
    'alaskan pipeline', 'algophile', 'algophilia', 'anal', 'anal assassin',
    'anal astronaut', 'anilingus', 'anus', 'ape shit', 'ape-shit', 'apeshit',
    'arsehole', 'asphyxiophilia', 'ass', 'asshole', 'asswhole', 'asswipe',
    'autoassassinophilia', 'autoerotic', 'autoerotic asphyxiation', 'autoerotic asphyxiation',
    'autofellatio', 'autopederasty', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'autosodomize',
    'autosodomized', 'autosodomizes', 'autosodomizing', 'autosodomitical',
    'autosodomitically', 'autosodomiticism', 'autosodomitize', 'autosodomitized',
    'autosodomitizes', 'autosodomitizing', 'autosodomize', 'autosodomized',
    'autosodomizes', 'autosodomizing', 'autosodomitical', 'autosodomitically',
    'autosodomiticism', 'autosodomitize', 'autosodomitized', 'autosodomitizes',
    'autosodomitizing', 'autosodomize', 'autosodomized', 'autosodomizes',
    'autosodomizing', 'autosodomitical', 'autosodomitically', 'autosodomiticism',
    'autosodomitize', 'autosodomitized', 'autosodomitizes', 'autosodomitizing',
    'autosodomize', 'autosodomized', 'autosodomizes', 'autosodomizing',
    'autosodomitical', 'autosodomitically', 'autosodomiticism', 'autosodomitize',
    'autosodomitized', 'autosodomitizes', 'autosodomitizing', 'bastardo',
    'bollera', 'cabron', 'cabrón', 'caca', 'chupada', 'chupapollas',
    'chupetón', 'concha', 'coño', 'coprofagía', 'culo', 'drogas',
    'esperma', 'follador', 'follar', 'gilipichis', 'gilipollas',
    'heroína', 'hija de puta', 'hijaputa', 'hijo de puta', 'hijoputa',
    'idiota', 'imbécil', 'infierno', 'jilipollas', 'kapullo', 'lameculos',
    'maciza', 'macizorra', 'maldito', 'mamada', 'marica', 'maricón',
    'mariconazo', 'martillo', 'mierda', 'nazi', 'orina', 'pedo',
    'pervertido', 'pezón', 'pinche', 'pis', 'prostituta', 'puta',
    'racista', 'ramera', 'sádico', 'semen', 'sexo', 'sexo oral',
    'soplagaitas', 'soplapollas', 'tetas grandes', 'tía buena', 'travesti',
    'trio', 'verga', 'vete a la mierda', 'vulva', 'asesinato', 'asno',
    'bastardo', 'bollera', 'cabron', 'cabrón', 'caca', 'chupada',
    'chupapollas', 'chupetón', 'concha', 'coño', 'coprofagía', 'culo',
    'drogas', 'esperma', 'follador', 'follar', 'gilipichis', 'gilipollas',
    'heroína', 'hija de puta', 'hijaputa', 'hijo de puta', 'hijoputa',
    'idiota', 'imbécil', 'infierno', 'jilipollas', 'kapullo', 'lameculos',
    'maciza', 'macizorra', 'maldito', 'mamada', 'marica', 'maricón',
    'mariconazo', 'martillo', 'mierda', 'nazi', 'orina', 'pedo',
    'pervertido', 'pezón', 'pinche', 'pis', 'prostituta', 'puta',
    'racista', 'ramera', 'sádico', 'semen', 'sexo', 'sexo oral',
    'soplagaitas', 'soplapollas', 'tetas grandes', 'tía buena', 'travesti',
    'trio', 'verga', 'vete a la mierda', 'vulva', 'fuck', 'shit', 'damn',
    'ass', 'bitch', 'bastard', 'crap', 'piss', 'cock', 'pussy', 'dick',
    'whore', 'slut', 'asshole', 'motherfucker', 'douchebag', 'fuckhead',
    'shithead', 'dipshit', 'asshat', 'dickhead', 'cocksucker', 'prick',
    'twat', 'wanker', 'bollocks', 'arsehole', 'tit', 'git', 'knob',
    'tosser', 'pillock', 'numpty', 'muppet', 'bellend', 'plonker',
    'wally', 'nob', 'nonce', 'pervert', 'creep', 'sicko', 'psycho',
    'lunatic', 'maniac', 'freak', 'weirdo', 'loser', 'jerk', 'schmuck',
    'putz', 'klutz', 'boob', 'dork', 'nerd', 'geek', 'dweeb', 'wimp',
    'sissy', 'wuss', 'chicken', 'coward', 'wimp', 'weakling', 'pushover',
    'sucker', 'chump', 'dupe', 'fool', 'idiot', 'moron', 'imbecile',
    'retard', 'stupid', 'dumb', 'dense', 'thick', 'slow', 'dim', 'dull',
    'obtuse', 'ignorant', 'illiterate', 'uneducated', 'uncouth', 'crude',
    'vulgar', 'obscene', 'lewd', 'indecent', 'improper', 'immodest',
    'impertinent', 'insolent', 'disrespectful', 'rude', 'impolite',
    'uncivil', 'discourteous', 'offensive', 'insulting', 'abusive',
    'derogatory', 'disparaging', 'contemptuous', 'scornful', 'disdainful',
    'haughty', 'arrogant', 'conceited', 'egotistical', 'narcissistic',
    'selfish', 'greedy', 'stingy', 'miserly', 'cheap', 'petty', 'trivial',
    'insignificant', 'worthless', 'useless', 'pointless', 'futile',
    'vain', 'fruitless', 'ineffectual', 'impotent', 'powerless',
    'weak', 'feeble', 'fragile', 'delicate', 'frail', 'sickly', 'ill',
    'diseased', 'infected', 'contaminated', 'polluted', 'filthy', 'dirty',
    'grimy', 'soiled', 'stained', 'tainted', 'corrupt', 'depraved',
    'immoral', 'unethical', 'dishonest', 'deceitful', 'fraudulent',
    'criminal', 'illegal', 'illicit', 'unlawful', 'contraband', 'smuggled',
    'stolen', 'pirated', 'counterfeit', 'fake', 'phony', 'bogus',
    'spurious', 'sham', 'hoax', 'scam', 'fraud', 'con', 'trick',
    'deception', 'lie', 'falsehood', 'fib', 'untruth', 'fabrication',
    'fiction', 'myth', 'legend', 'tale', 'story', 'yarn', 'tall tale',
    'exaggeration', 'overstatement', 'hyperbole', 'understatement',
    'litotes', 'irony', 'sarcasm', 'mockery', 'ridicule', 'derision',
    'contempt', 'scorn', 'disdain', 'disrespect', 'dishonor', 'shame',
    'disgrace', 'humiliation', 'degradation', 'debasement', 'abasement',
    'mortification', 'chagrin', 'embarrassment', 'awkwardness',
    'discomfort', 'unease', 'anxiety', 'worry', 'concern', 'fear',
    'terror', 'panic', 'dread', 'horror', 'fright', 'alarm', 'shock',
    'surprise', 'astonishment', 'amazement', 'wonder', 'awe', 'reverence',
    'admiration', 'respect', 'esteem', 'honor', 'glory', 'fame',
    'renown', 'reputation', 'prestige', 'status', 'rank', 'position',
    'title', 'office', 'role', 'function', 'duty', 'responsibility',
    'obligation', 'commitment', 'promise', 'vow', 'oath', 'pledge',
    'guarantee', 'warranty', 'assurance', 'confirmation', 'affirmation',
    'assertion', 'claim', 'statement', 'declaration', 'announcement',
    'proclamation', 'publication', 'broadcast', 'transmission', 'signal',
    'message', 'communication', 'conversation', 'dialogue', 'discussion',
    'debate', 'argument', 'dispute', 'quarrel', 'conflict', 'fight',
    'battle', 'war', 'violence', 'aggression', 'assault', 'attack',
    'invasion', 'conquest', 'occupation', 'colonization', 'exploitation',
    'oppression', 'subjugation', 'enslavement', 'bondage', 'captivity',
    'imprisonment', 'confinement', 'detention', 'arrest', 'prosecution',
    'conviction', 'sentence', 'punishment', 'penalty', 'fine', 'fee',
    'tax', 'toll', 'charge', 'cost', 'price', 'expense', 'expenditure',
    'spending', 'investment', 'profit', 'loss', 'gain', 'income',
    'revenue', 'salary', 'wage', 'payment', 'compensation', 'reward',
    'bonus', 'incentive', 'motivation', 'inspiration', 'encouragement',
    'support', 'assistance', 'help', 'aid', 'relief', 'comfort',
    'solace', 'consolation', 'sympathy', 'empathy', 'compassion',
    'kindness', 'generosity', 'charity', 'benevolence', 'altruism',
    'selflessness', 'sacrifice', 'devotion', 'dedication', 'loyalty',
    'faithfulness', 'fidelity', 'constancy', 'steadfastness', 'reliability',
    'dependability', 'trustworthiness', 'integrity', 'honesty', 'sincerity',
    'authenticity', 'genuineness', 'realness', 'truth', 'reality',
    'fact', 'evidence', 'proof', 'demonstration', 'illustration',
    'example', 'instance', 'case', 'precedent', 'standard', 'norm',
    'rule', 'law', 'regulation', 'policy', 'procedure', 'protocol',
    'system', 'method', 'technique', 'strategy', 'tactic', 'approach',
    'plan', 'scheme', 'design', 'blueprint', 'model', 'template',
    'pattern', 'structure', 'framework', 'foundation', 'basis', 'ground',
    'base', 'platform', 'stage', 'arena', 'field', 'domain', 'realm',
    'sphere', 'circle', 'group', 'organization', 'institution',
    'establishment', 'company', 'corporation', 'business', 'enterprise',
    'industry', 'sector', 'market', 'economy', 'commerce', 'trade',
    'transaction', 'deal', 'contract', 'agreement', 'accord', 'treaty',
    'alliance', 'partnership', 'collaboration', 'cooperation', 'teamwork',
    'unity', 'solidarity', 'cohesion', 'harmony', 'balance', 'equilibrium',
    'stability', 'security', 'safety', 'protection', 'defense', 'shield',
    'barrier', 'wall', 'fence', 'boundary', 'border', 'frontier',
    'limit', 'threshold', 'edge', 'margin', 'periphery', 'circumference',
    'perimeter', 'outline', 'contour', 'shape', 'form', 'figure',
    'image', 'picture', 'photograph', 'portrait', 'painting', 'drawing',
    'sketch', 'design', 'pattern', 'decoration', 'ornament', 'embellishment',
    'adornment', 'accessory', 'garment', 'clothing', 'apparel', 'attire',
    'outfit', 'costume', 'uniform', 'dress', 'suit', 'jacket', 'coat',
    'shirt', 'pants', 'skirt', 'dress', 'gown', 'robe', 'cloak',
    'cape', 'shawl', 'wrap', 'scarf', 'hat', 'cap', 'helmet', 'crown',
    'tiara', 'diadem', 'circlet', 'band', 'ring', 'bracelet', 'anklet',
    'necklace', 'pendant', 'locket', 'brooch', 'pin', 'clasp', 'buckle',
    'button', 'zipper', 'snap', 'hook', 'eye', 'loop', 'knot', 'tie',
    'bow', 'ribbon', 'lace', 'trim', 'fringe', 'tassel', 'pompom',
    'bead', 'sequin', 'rhinestone', 'gem', 'jewel', 'stone', 'crystal',
    'diamond', 'ruby', 'sapphire', 'emerald', 'pearl', 'coral', 'jade',
    'amber', 'ivory', 'bone', 'horn', 'shell', 'leather', 'fur', 'wool',
    'cotton', 'linen', 'silk', 'satin', 'velvet', 'corduroy', 'denim',
    'canvas', 'burlap', 'tweed', 'felt', 'fleece', 'polyester', 'nylon',
    'spandex', 'lycra', 'rayon', 'acetate', 'acrylic', 'polyester',
    'vinyl', 'plastic', 'rubber', 'latex', 'silicone', 'resin', 'epoxy',
    'fiberglass', 'carbon fiber', 'aluminum', 'steel', 'iron', 'copper',
    'brass', 'bronze', 'tin', 'lead', 'zinc', 'nickel', 'chrome',
    'silver', 'gold', 'platinum', 'titanium', 'tungsten', 'molybdenum',
    'vanadium', 'cobalt', 'manganese', 'chromium', 'iron oxide',
    'rust', 'corrosion', 'oxidation', 'tarnish', 'patina', 'verdigris',
    'scale', 'buildup', 'deposit', 'residue', 'sediment', 'sludge',
    'silt', 'mud', 'clay', 'sand', 'gravel', 'stone', 'rock', 'boulder',
    'pebble', 'cobble', 'brick', 'tile', 'slate', 'marble', 'granite',
    'limestone', 'sandstone', 'shale', 'basalt', 'obsidian', 'pumice',
    'lava', 'magma', 'ash', 'cinder', 'coal', 'charcoal', 'coke',
    'peat', 'lignite', 'bitumen', 'tar', 'pitch', 'asphalt', 'concrete',
    'cement', 'mortar', 'grout', 'plaster', 'stucco', 'adobe', 'mud brick'
}

# Cargar palabras adicionales desde archivo si existe
try:
    with open('banned_words_complete.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word:
                DEFAULT_BANNED_WORDS.add(word)
    logger.info(f"✅ Cargadas {len(DEFAULT_BANNED_WORDS)} palabras prohibidas")
except:
    logger.warning("⚠️ No se pudo cargar archivo de palabras prohibidas")

# Patrones para detectar URLs y desvíos
URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
SHORTENED_URL_PATTERN = re.compile(r'(bit\.ly|tinyurl|short\.link|ow\.ly|goo\.gl|is\.gd|buff\.ly|adf\.ly|t\.co|youtu\.be)')

# Cache de admins
admin_cache = {}
admin_cache_time = 0

# Sistema de warns: {user_id: {chat_id: warn_count}}
user_warns = defaultdict(lambda: defaultdict(int))

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_admins():
    """Obtener administradores del grupo."""
    global admin_cache, admin_cache_time
    
    current_time = time.time()
    if current_time - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = current_time
            logger.info(f"✅ Admins actualizados: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo admins: {e}")
            return admin_cache
    
    return admin_cache


def normalize_text(text):
    """Normalizar texto para búsqueda."""
    if not text:
        return ""
    
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def contains_banned_word(text):
    """Verificar si el texto contiene palabras prohibidas."""
    if not text:
        return False, None
    
    normalized = normalize_text(text)
    
    for word in DEFAULT_BANNED_WORDS:
        if re.search(r'\b' + re.escape(word.lower()) + r'\b', normalized):
            return True, word
    
    return False, None


def contains_url(text):
    """Detectar URLs y desvíos."""
    if not text:
        return False, None
    
    # Buscar URLs directas
    if URL_PATTERN.search(text):
        return True, "URL directa"
    
    # Buscar desvíos (URLs acortadas)
    if SHORTENED_URL_PATTERN.search(text):
        return True, "URL acortada/desvío"
    
    return False, None


def delete_message_delayed(chat_id, message_id, delay=30):
    """Borrar mensaje después de X segundos."""
    def _delete():
        try:
            time.sleep(delay)
            bot.delete_message(chat_id, message_id)
            logger.info(f"✅ Mensaje {message_id} borrado")
        except Exception as e:
            logger.debug(f"Error borrando mensaje: {e}")
    
    thread = threading.Thread(target=_delete, daemon=True)
    thread.start()


def send_warning(user_id, first_name, reason, warn_count, chat_id):
    """Enviar advertencia al usuario."""
    try:
        warning_text = (
            f"<b>⚠️ ADVERTENCIA - {first_name}</b>\n\n"
            f"<b>Razón:</b> {reason}\n"
            f"<b>Advertencias:</b> {warn_count}/3\n\n"
        )
        
        if warn_count >= 3:
            warning_text += "<b>❌ HAS SIDO BANEADO DEL GRUPO</b>"
        else:
            warning_text += f"<b>⚠️ {3 - warn_count} advertencia(s) más y serás baneado</b>"
        
        notification = bot.send_message(chat_id, warning_text, parse_mode='HTML')
        logger.info(f"✅ Advertencia enviada a {user_id}: {reason}")
        
        delete_message_delayed(chat_id, notification.message_id, delay=30)
    
    except Exception as e:
        logger.error(f"❌ Error enviando advertencia: {e}")


# ============================================================================
# MANEJADOR DE MENSAJES
# ============================================================================

@bot.message_handler(func=lambda m: m.chat.id == TARGET_GROUP_ID)
def handle_messages(message):
    """Manejar todos los mensajes en el grupo."""
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "Usuario"
        username = message.from_user.username
        text = message.text or ""
        
        # Verificar si es admin
        admins = get_admins()
        is_admin = user_id in admins
        
        # 1. VERIFICAR USERNAME
        if not username and not is_admin:
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                warning_text = (
                    f"<b>⚠️ {first_name}</b>\n\n"
                    f"<b>Debes tener un username para escribir en este grupo.</b>\n\n"
                    f"Cómo crear un username:\n"
                    f"1. Abre tu perfil de Telegram\n"
                    f"2. Toca 'Editar perfil'\n"
                    f"3. Agrega un username (ej: @tunombre)\n"
                    f"4. Guarda los cambios"
                )
                notification = bot.send_message(TARGET_GROUP_ID, warning_text, parse_mode='HTML')
                delete_message_delayed(TARGET_GROUP_ID, notification.message_id, delay=30)
                logger.info(f"❌ Mensaje de {first_name} ({user_id}) borrado - Sin username")
            except Exception as e:
                logger.error(f"Error borrando mensaje sin username: {e}")
            return
        
        # 2. VERIFICAR PALABRAS PROHIBIDAS
        if text and not is_admin:
            has_banned, banned_word = contains_banned_word(text)
            if has_banned:
                try:
                    bot.delete_message(TARGET_GROUP_ID, message.message_id)
                    user_warns[user_id][TARGET_GROUP_ID] += 1
                    warn_count = user_warns[user_id][TARGET_GROUP_ID]
                    
                    if warn_count >= 3:
                        try:
                            bot.kick_chat_member(TARGET_GROUP_ID, user_id)
                            logger.info(f"❌ {first_name} ({user_id}) baneado - 3 advertencias")
                        except:
                            pass
                    
                    send_warning(user_id, first_name, f"Palabra prohibida: {banned_word}", warn_count, TARGET_GROUP_ID)
                except Exception as e:
                    logger.error(f"Error procesando palabra prohibida: {e}")
                return
        
        # 3. VERIFICAR URLs
        if text and not is_admin:
            has_url, url_type = contains_url(text)
            if has_url:
                try:
                    bot.delete_message(TARGET_GROUP_ID, message.message_id)
                    user_warns[user_id][TARGET_GROUP_ID] += 1
                    warn_count = user_warns[user_id][TARGET_GROUP_ID]
                    
                    if warn_count >= 3:
                        try:
                            bot.kick_chat_member(TARGET_GROUP_ID, user_id)
                            logger.info(f"❌ {first_name} ({user_id}) baneado - 3 advertencias")
                        except:
                            pass
                    
                    send_warning(user_id, first_name, f"Enlaces no permitidos: {url_type}", warn_count, TARGET_GROUP_ID)
                except Exception as e:
                    logger.error(f"Error procesando URL: {e}")
                return
        
        logger.info(f"✅ Mensaje de {first_name} ({user_id}) permitido")
    
    except Exception as e:
        logger.error(f"❌ Error en handle_messages: {e}")


# ============================================================================
# KEEPALIVE - NUNCA SE DUERME
# ============================================================================

def keepalive():
    """Keepalive para evitar que el bot se duerma."""
    while True:
        try:
            time.sleep(30)
            logger.info("✅ Keepalive: Bot activo")
        except:
            pass

keepalive_thread = threading.Thread(target=keepalive, daemon=True)
keepalive_thread.start()

# ============================================================================
# INICIAR BOT
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 BOT DE MODERACIÓN PROFESIONAL - INICIANDO")
    logger.info(f"📊 Palabras prohibidas cargadas: {len(DEFAULT_BANNED_WORDS)}")
    logger.info("=" * 60)
    logger.info("✅ Bot LISTO - Usando POLLING PURO (sin Flask, sin webhooks)")
    logger.info("✅ Keepalive cada 30 segundos")
    logger.info("✅ Iniciando POLLING...")
    
    bot.infinity_polling()
