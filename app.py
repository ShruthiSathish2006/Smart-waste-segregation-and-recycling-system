from __future__ import annotations

import html
import json
import mimetypes
import random
import secrets
import sqlite3
from datetime import date
from http import cookies
from pathlib import Path
from urllib.parse import parse_qs, quote_plus
from wsgiref.simple_server import make_server


ROOT_DIR = Path(__file__).parent
ASSETS_DIR = ROOT_DIR / "assets"
ITEMS_DB_PATH = ROOT_DIR / "waste_items.db"
SORTING_DB_PATH = ROOT_DIR / "sorting_game.db"
QUIZ_DB_PATH = ROOT_DIR / "quiz.db"
FACTS_DB_PATH = ROOT_DIR / "facts.db"
STATE_DB_PATH = ROOT_DIR / "app_state.db"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORTS = (8000, 8001, 8002)

TARGET_WASTE_ITEM_COUNT = 1_000_000
TARGET_SORTING_CHALLENGE_COUNT = 100_000
TARGET_QUIZ_QUESTION_COUNT = 100_000
TARGET_FACT_COUNT = 1_900
PREVIEW_WASTE_ITEM_LIMIT = 200
SESSION_ROUND_SIZE = 5
FACTS_PER_REFRESH = 6

CATEGORY_GUIDE = {
    "Wet Waste": {
        "bin": "Green Bin",
        "color": "#58C94C",
        "summary": "Food and garden waste that can break down naturally.",
    },
    "Dry Waste": {
        "bin": "Blue Bin",
        "color": "#3A86FF",
        "summary": "Paper, plastic, glass, and metal that can often be recycled.",
    },
    "Hazardous Waste": {
        "bin": "Red Bin",
        "color": "#FF5D5D",
        "summary": "Items that need careful handling and safe disposal.",
    },
}

PAGE_ART = {
    "dashboard": "dashboard-hero.svg",
    "finder": "finder-hero.svg",
    "game": "game-hero.svg",
    "quiz": "quiz-hero.svg",
    "learn": "learn-hero.svg",
}

ECO_TIPS = [
    "Carry a reusable water bottle instead of buying single-use bottles.",
    "Switch off lights and fans when leaving a room.",
    "Use both sides of paper before recycling it.",
    "Keep wet waste separate so it can become compost.",
    "Store used batteries safely until they reach a collection center.",
    "Choose products with less packaging when shopping.",
    "Repair and reuse items before throwing them away.",
]

RECYCLING_TIPS = [
    "Rinse jars, cans, and bottles before placing them in the dry waste bin.",
    "Flatten cardboard boxes to save storage and collection space.",
    "Keep compostable waste away from paper and plastic.",
    "Do not mix chemicals, batteries, or medicines with regular household waste.",
]

FACT_THEMES = [
    "Preventing water pollution in rivers and drains",
    "Reducing air pollution through cleaner travel",
    "Managing e-waste from old electronics safely",
    "Practicing sustainability in daily life",
    "Composting fruit and vegetable scraps",
    "Reusing school notebooks and paper",
    "Saving water during daily routines",
    "Switching off unused lights and fans",
    "Carrying a reusable water bottle",
    "Taking cloth bags while shopping",
    "Recycling clean glass containers",
    "Recycling metal cans and lids",
    "Keeping batteries in safe collection boxes",
    "Planting and caring for native trees",
    "Planning meals to reduce food waste",
    "Donating toys, books, and clothes",
    "Repairing items before replacing them",
    "Keeping beaches, parks, and streets litter-free",
    "Joining school or neighborhood cleanup drives",
]

FACT_CONTEXTS = [
    "at home",
    "at school",
    "during a cleanup drive",
    "in the garden",
    "in the classroom",
    "during lunch break",
    "on a weekend activity",
    "during a community event",
    "in a neighborhood project",
    "on a field trip",
]

FACT_BENEFITS = [
    "helps reduce landfill waste",
    "keeps public spaces cleaner",
    "saves natural resources",
    "cuts down pollution",
    "protects animals and plants",
    "builds good daily habits",
    "makes recycling easier",
    "saves energy and effort",
    "supports a healthier environment",
    "teaches responsible eco habits",
]

TARGET_FACT_COUNT = len(FACT_THEMES) * len(FACT_CONTEXTS) * len(FACT_BENEFITS)

FACT_ARTICLE_LIBRARY = {
    "Composting fruit and vegetable scraps": {
        "eyebrow": "Soil Story",
        "title": "Compost Turns Kitchen Scraps Into Fresh Soil",
        "summary": "Fruit peels and vegetable ends are not useless leftovers. When they stay separate from plastic and metal, they can become compost instead of messy landfill waste.",
        "impact": "That one sorting habit keeps dry recyclables cleaner and sends nutrients back into gardens, trees, and community soil.",
        "actions": [
            "Keep a small covered bowl nearby for peels and scraps.",
            "Add a little dry leaf matter to balance moisture.",
            "Empty the bowl into compost or the wet-waste bin each day.",
        ],
        "stats": [
            {"label": "Cleaner Recycling", "text": "Dry waste stays usable instead of getting soggy."},
            {"label": "Better Soil", "text": "Finished compost feeds plants naturally."},
            {"label": "Less Landfill", "text": "Organic waste gets a second life."},
        ],
        "accent": "#58C94C",
        "art_key": "compost",
    },
    "Reusing school notebooks and paper": {
        "eyebrow": "Reuse First",
        "title": "Paper Works Harder When We Use It Twice",
        "summary": "Half-used notebooks and clean sheets still have plenty of life left. Reusing them first slows down waste before recycling even begins.",
        "impact": "That means fewer new paper products, less clutter, and a clearer path for the pages that finally do need recycling.",
        "actions": [
            "Save unfinished notebooks for rough work or practice.",
            "Keep a tray for single-sided sheets near the study area.",
            "Recycle paper only when it is fully used or damaged.",
        ],
        "stats": [
            {"label": "Less New Paper", "text": "One extra use reduces replacement demand."},
            {"label": "Longer Use", "text": "Each sheet does more before it leaves."},
            {"label": "Easy Habit", "text": "A reuse tray makes the choice obvious."},
        ],
        "accent": "#F2B134",
        "art_key": "paper",
    },
    "Saving water during daily routines": {
        "eyebrow": "Water Wise",
        "title": "Small Tap Habits Save More Water Than We Notice",
        "summary": "A few seconds with the tap off during brushing, washing, or rinsing add up surprisingly fast across a whole week.",
        "impact": "Saving water also saves the energy needed to pump, clean, and deliver it to homes, schools, and neighborhoods.",
        "actions": [
            "Turn the tap off while brushing or soaping hands.",
            "Fill a mug or bottle instead of letting water run.",
            "Report drips and leaks before they become a bigger loss.",
        ],
        "stats": [
            {"label": "Less Waste", "text": "Shorter tap time protects clean water."},
            {"label": "Lower Energy", "text": "Water systems use power too."},
            {"label": "Daily Control", "text": "This change fits into ordinary routines."},
        ],
        "accent": "#39A9DB",
        "art_key": "water",
    },
    "Switching off unused lights and fans": {
        "eyebrow": "Power Check",
        "title": "A Quick Switch-Off Habit Cuts Hidden Energy Waste",
        "summary": "Empty rooms do not need lights, fans, or chargers running in the background. A quick glance before leaving can trim a lot of wasted power.",
        "impact": "Using less electricity lowers demand on the grid and builds a stronger awareness of what is truly needed in the moment.",
        "actions": [
            "Make the last person out responsible for the switches.",
            "Use daylight before turning on lights where possible.",
            "Check fans, lamps, and chargers during breaks.",
        ],
        "stats": [
            {"label": "Less Electricity", "text": "Unused devices stop pulling power."},
            {"label": "Longer Device Life", "text": "Equipment gets fewer unnecessary hours."},
            {"label": "Sharper Habit", "text": "Awareness turns into routine quickly."},
        ],
        "accent": "#FFB703",
        "art_key": "energy",
    },
    "Carrying a reusable water bottle": {
        "eyebrow": "Carry Refill",
        "title": "One Refillable Bottle Replaces a Trail of Plastic",
        "summary": "A bottle you carry and refill again and again can prevent a long line of throwaway bottles from ever entering the waste stream.",
        "impact": "It also makes it easier to stay hydrated without needing packaged drinks every time you leave home.",
        "actions": [
            "Keep a bottle in your bag so it is always ready.",
            "Wash and refill it as part of your evening routine.",
            "Choose refill stations before buying a single-use drink.",
        ],
        "stats": [
            {"label": "Fewer Plastics", "text": "Repeated refills reduce bottle waste."},
            {"label": "Lower Cost", "text": "Refill habits are cheaper over time."},
            {"label": "Ready Water", "text": "Hydration becomes easier to remember."},
        ],
        "accent": "#1D9BF0",
        "art_key": "bottle",
    },
    "Taking cloth bags while shopping": {
        "eyebrow": "Bag Swap",
        "title": "Cloth Bags Turn Shopping Into a Reuse Routine",
        "summary": "A strong reusable bag does the work of many thin plastic carry bags and keeps packaging waste from piling up after every errand.",
        "impact": "Once the bag already lives in your backpack or near the door, the lower-waste choice becomes the easier choice.",
        "actions": [
            "Fold one cloth bag into your backpack or scooter box.",
            "Keep extras near the entrance for quick trips.",
            "Use sturdier bags for heavier goods so they last longer.",
        ],
        "stats": [
            {"label": "Less Plastic", "text": "One bag replaces many disposable ones."},
            {"label": "Stronger Carry", "text": "Reusable fabric handles heavier loads."},
            {"label": "Easy Repeat", "text": "Placement makes the habit stick."},
        ],
        "accent": "#F9844A",
        "art_key": "bag",
    },
    "Recycling clean glass containers": {
        "eyebrow": "Glass Loop",
        "title": "Clean Glass Containers Are Ready for Another Round",
        "summary": "Glass can be recycled again and again, but it works best when jars and bottles are empty, clean, and separated properly.",
        "impact": "A quick rinse keeps smells down, improves sorting, and helps valuable material move back into use instead of being rejected.",
        "actions": [
            "Empty jars fully before placing them aside.",
            "Rinse away food residue and let them dry lightly.",
            "Reuse sturdy jars at home before recycling them.",
        ],
        "stats": [
            {"label": "Repeat Recycling", "text": "Glass can come back many times over."},
            {"label": "Cleaner Sorting", "text": "Residue-free containers are easier to handle."},
            {"label": "Safer Storage", "text": "Dry, empty jars create less mess."},
        ],
        "accent": "#2A9D8F",
        "art_key": "glass",
    },
    "Recycling metal cans and lids": {
        "eyebrow": "Metal Return",
        "title": "Clean Cans and Lids Keep Valuable Metal in Circulation",
        "summary": "Metal is one of the most useful recyclable materials in a household bin, but it needs a little care before it gets there.",
        "impact": "Rinsed cans and safely handled lids are easier to collect, process, and turn back into something useful.",
        "actions": [
            "Rinse food cans after use so residue does not harden.",
            "Press sharp lids inward or store them safely together.",
            "Keep metal separate from wet food scraps and paper.",
        ],
        "stats": [
            {"label": "High Material Value", "text": "Metal is worth recovering cleanly."},
            {"label": "Less Contamination", "text": "Dry and clean items sort better."},
            {"label": "Safer Handling", "text": "Careful lids reduce cuts and mess."},
        ],
        "accent": "#4D7CFE",
        "art_key": "metal",
    },
    "Managing e-waste from old electronics safely": {
        "eyebrow": "E-Waste Route",
        "title": "Old Electronics Need a Smarter Exit Than the Bin",
        "summary": "Phones, chargers, and gadgets contain useful metals along with materials that do not belong in regular household waste.",
        "impact": "E-waste centers recover what can be reused and handle the risky parts in a controlled, safer way.",
        "actions": [
            "Store old electronics in one dry box instead of mixing them into bins.",
            "Erase personal data from devices before drop-off.",
            "Use an authorized e-waste point when the box fills up.",
        ],
        "stats": [
            {"label": "Safer Disposal", "text": "Hazardous parts stay out of household waste."},
            {"label": "Material Recovery", "text": "Useful metals can be reclaimed properly."},
            {"label": "Cleaner Homes", "text": "Broken gadgets stop becoming drawer clutter."},
        ],
        "accent": "#577590",
        "art_key": "ewaste",
    },
    "Keeping batteries in safe collection boxes": {
        "eyebrow": "Battery Safe",
        "title": "A Small Collection Box Prevents Bigger Battery Problems",
        "summary": "Batteries look harmless once they are used up, but the chemicals inside them still need careful storage and disposal.",
        "impact": "A separate battery box reduces leaks, sparks, and contamination while making final drop-off far easier.",
        "actions": [
            "Tape loose battery ends before storing them together.",
            "Keep used batteries in a lidded jar or collection box.",
            "Drop them at a battery collection point regularly.",
        ],
        "stats": [
            {"label": "Safer Storage", "text": "Loose batteries stay contained and dry."},
            {"label": "Lower Chemical Risk", "text": "Leaks are easier to prevent and notice."},
            {"label": "Cleaner Bins", "text": "Hazardous items stay out of regular waste."},
        ],
        "accent": "#F94144",
        "art_key": "battery",
    },
    "Planting and caring for native trees": {
        "eyebrow": "Native Growth",
        "title": "Native Trees Do More When They Truly Belong Here",
        "summary": "Trees that match the local climate and soil usually need less struggle and support more nearby birds, insects, and shade.",
        "impact": "Planting is only the first step. Watering, protecting, and caring for young trees is what helps them actually survive.",
        "actions": [
            "Choose species that already grow well in your area.",
            "Water new trees consistently during the early months.",
            "Protect the base from litter, trampling, and damage.",
        ],
        "stats": [
            {"label": "More Shade", "text": "Healthy trees cool streets and yards."},
            {"label": "Better Biodiversity", "text": "Local species support local life."},
            {"label": "Longer Survival", "text": "Care matters more than planting day alone."},
        ],
        "accent": "#43AA8B",
        "art_key": "tree",
    },
    "Reducing air pollution through cleaner travel": {
        "eyebrow": "Air Check",
        "title": "Cleaner Travel Choices Can Cut Everyday Air Pollution",
        "summary": "Short trips, shared rides, and lower-emission travel choices reduce the smoke and exhaust that build up around roads, schools, and neighborhoods.",
        "impact": "That change improves air quality, reduces fuel burn, and makes the connection between transport habits and pollution much easier to see.",
        "actions": [
            "Walk short distances when the route is safe.",
            "Pair up rides for regular school or work trips.",
            "Choose cycles or public transport for predictable routes.",
        ],
        "stats": [
            {"label": "Cleaner Air", "text": "Fewer exhaust emissions reach the street."},
            {"label": "Less Fuel", "text": "Shared or active travel uses fewer resources."},
            {"label": "Healthier Routine", "text": "Movement becomes part of the day."},
        ],
        "accent": "#277DA1",
        "art_key": "transport",
    },
    "Planning meals to reduce food waste": {
        "eyebrow": "Food Plan",
        "title": "Meal Planning Stops Good Food From Becoming Waste",
        "summary": "A little planning before cooking or shopping can prevent ingredients from being forgotten, spoiled, or bought twice.",
        "impact": "That protects not just the food itself, but also the water, transport, and energy that went into bringing it home.",
        "actions": [
            "Check the kitchen before making a shopping list.",
            "Plan meals around what will spoil first.",
            "Keep leftovers visible and easy to reuse.",
        ],
        "stats": [
            {"label": "Less Food Waste", "text": "Ingredients are used while still fresh."},
            {"label": "Smarter Shopping", "text": "Lists match what is already available."},
            {"label": "Lower Waste Load", "text": "Fewer scraps and spoiled items go out."},
        ],
        "accent": "#90BE6D",
        "art_key": "meal",
    },
    "Donating toys, books, and clothes": {
        "eyebrow": "Pass It On",
        "title": "Useful Things Can Keep Helping After We Finish With Them",
        "summary": "Many toys, books, and clothes still have value long after one person stops using them.",
        "impact": "Donation keeps items in circulation longer and reduces the need for brand-new replacements, packaging, and disposal.",
        "actions": [
            "Sort items that are clean, working, and still useful.",
            "Wash or repair them before giving them away.",
            "Pass them on quickly while they still match a real need.",
        ],
        "stats": [
            {"label": "Longer Product Life", "text": "Good items stay in use instead of storage."},
            {"label": "Less Clutter", "text": "Homes free space without wasting value."},
            {"label": "More Sharing", "text": "Communities benefit from reuse loops."},
        ],
        "accent": "#F8961E",
        "art_key": "donate",
    },
    "Repairing items before replacing them": {
        "eyebrow": "Fix First",
        "title": "Repair Often Beats Replacement When the Damage Is Small",
        "summary": "A loose cable, missing button, or tiny crack does not always mean the whole item is finished.",
        "impact": "Repairing first slows waste, saves money, and reduces the materials and packaging needed to make a replacement.",
        "actions": [
            "Look for simple fixes before deciding an item is done.",
            "Use local repair help when a tool or part is beyond home basics.",
            "Keep a small kit for glue, tape, spare buttons, and simple tools.",
        ],
        "stats": [
            {"label": "Less Waste", "text": "Products stay useful for longer."},
            {"label": "Money Saved", "text": "Minor fixes cost less than replacements."},
            {"label": "Care Skills", "text": "Repair builds confidence and attention."},
        ],
        "accent": "#BC6C25",
        "art_key": "repair",
    },
    "Keeping beaches, parks, and streets litter-free": {
        "eyebrow": "Clean Spaces",
        "title": "Public Places Stay Healthier When Litter Never Settles In",
        "summary": "Waste left in parks, streets, and beaches can travel into drains, soil, and animal habitats long after we stop seeing it.",
        "impact": "Picking it up early keeps public areas safer, cleaner, and easier for everyone else to respect and enjoy.",
        "actions": [
            "Carry a small litter pouch during outings.",
            "Use the nearest correct bin instead of leaving waste behind.",
            "Pick up lightweight litter when it is safe to do so.",
        ],
        "stats": [
            {"label": "Cleaner Places", "text": "Shared spaces stay welcoming and usable."},
            {"label": "Safer Wildlife", "text": "Less loose waste reaches animals."},
            {"label": "Visible Pride", "text": "Care changes how places are treated."},
        ],
        "accent": "#3A86FF",
        "art_key": "litter",
    },
    "Joining school or neighborhood cleanup drives": {
        "eyebrow": "Together Works",
        "title": "Cleanup Drives Turn Small Efforts Into Visible Change",
        "summary": "One person can collect a little, but a group can transform a whole stretch of road, schoolyard, or neighborhood corner in one session.",
        "impact": "Cleanup drives also reveal what kinds of waste show up most, which helps people change habits at the source.",
        "actions": [
            "Bring gloves and reusable collection bags if the event allows.",
            "Sort collected waste during the drive when possible.",
            "Share the biggest lesson from the cleanup afterward.",
        ],
        "stats": [
            {"label": "Fast Impact", "text": "Group action changes a place quickly."},
            {"label": "Stronger Habits", "text": "Participation makes waste visible."},
            {"label": "Shared Ownership", "text": "People protect places they helped clean."},
        ],
        "accent": "#4CAF50",
        "art_key": "cleanup",
    },
    "Practicing sustainability in daily life": {
        "eyebrow": "Daily Sustain",
        "title": "Sustainability Gets Real When It Shows Up in Daily Choices",
        "summary": "Sustainability is not one giant action. It grows from repeatable habits like buying thoughtfully, reusing what still works, and choosing options that create less waste overall.",
        "impact": "Those small choices reduce pressure on materials, transport, packaging, and disposal systems all at once, which is what makes sustainability feel broad instead of narrow.",
        "actions": [
            "Compare options and pick the one that uses fewer resources over time.",
            "Choose refill, repair, or reuse whenever it makes sense.",
            "Keep one low-waste habit visible enough that it becomes automatic.",
        ],
        "stats": [
            {"label": "Less Waste", "text": "Daily choices reduce what needs disposal later."},
            {"label": "Longer Use", "text": "Sustainable habits keep materials working longer."},
            {"label": "Broader Impact", "text": "One careful choice often improves several systems at once."},
        ],
        "accent": "#E76F51",
        "art_key": "packaging",
    },
    "Preventing water pollution in rivers and drains": {
        "eyebrow": "Water Guard",
        "title": "What Goes Down a Drain Can Travel Much Further Than It Looks",
        "summary": "Paint, cleaners, oils, and harsh liquids do not simply disappear after being poured away. They move into water systems and nearby soil.",
        "impact": "Keeping chemicals out of drains protects waterways, reduces contamination, and prevents hidden long-term damage.",
        "actions": [
            "Never pour unknown chemicals into a sink or street drain.",
            "Seal containers tightly after using strong products.",
            "Use hazardous-waste collection for leftovers and residues.",
        ],
        "stats": [
            {"label": "Cleaner Waterways", "text": "Fewer pollutants reach rivers and lakes."},
            {"label": "Safer Soil", "text": "Ground and roots avoid toxic residue."},
            {"label": "Long-Term Care", "text": "Prevention matters more than cleanup later."},
        ],
        "accent": "#118AB2",
        "art_key": "river",
    },
}

DEFAULT_FACT_ARTICLE = {
    "eyebrow": "Eco Story",
    "title": "A Small Eco Habit Can Create a Bigger Ripple",
    "summary": "Every simple waste and resource habit gets stronger when it is repeated in ordinary daily life.",
    "impact": "The best environmental changes are often the ones that feel easy enough to keep doing.",
    "actions": [
        "Choose one habit and make it visible in your routine.",
        "Keep related items in one obvious place.",
        "Share the habit with someone else so it spreads.",
    ],
    "stats": [
        {"label": "Daily Action", "text": "Small moves work best when repeated."},
        {"label": "Clear Routine", "text": "Visible cues make the habit easier."},
        {"label": "Shared Impact", "text": "One action can influence a group."},
    ],
    "accent": "#43AA8B",
    "art_key": "generic",
}

WASTE_BASES = [
    {"name": "banana peel", "category": "Wet Waste", "tip": "Place it in compost or the wet waste bin.", "note": "Fruit peels break down naturally.", "graphic": "banana"},
    {"name": "apple core", "category": "Wet Waste", "tip": "Put it in compost or wet waste collection.", "note": "Food leftovers are biodegradable.", "graphic": "apple"},
    {"name": "orange peel", "category": "Wet Waste", "tip": "Add it to compost or a wet waste container.", "note": "Citrus peels are organic waste.", "graphic": "orange"},
    {"name": "tea leaves", "category": "Wet Waste", "tip": "Mix them into compost or garden soil.", "note": "Tea leaves enrich compost.", "graphic": "leaf"},
    {"name": "coffee grounds", "category": "Wet Waste", "tip": "Use them in compost or soil mixes.", "note": "Coffee grounds are compost-friendly.", "graphic": "coffee"},
    {"name": "vegetable scraps", "category": "Wet Waste", "tip": "Collect them for composting.", "note": "Vegetable scraps decompose quickly.", "graphic": "carrot"},
    {"name": "dry leaves", "category": "Wet Waste", "tip": "Use them as compost or mulch.", "note": "Leaves help create rich soil.", "graphic": "leaf"},
    {"name": "grass clippings", "category": "Wet Waste", "tip": "Keep them in compost or green waste collection.", "note": "Grass clippings are natural organic waste.", "graphic": "grass"},
    {"name": "eggshells", "category": "Wet Waste", "tip": "Crush and add them to compost.", "note": "Eggshells are biodegradable.", "graphic": "eggshell"},
    {"name": "flower waste", "category": "Wet Waste", "tip": "Put it in compost or wet waste.", "note": "Used flowers can return to the soil.", "graphic": "flower"},
    {"name": "fruit scraps", "category": "Wet Waste", "tip": "Add them to compost or the wet waste bin.", "note": "Fruit scraps are ideal compost material.", "graphic": "fruit"},
    {"name": "rice leftovers", "category": "Wet Waste", "tip": "Place them in wet waste or compost where allowed.", "note": "Cooked food scraps should stay out of dry recycling.", "graphic": "rice"},
    {"name": "bread crumbs", "category": "Wet Waste", "tip": "Place them in wet waste or compost.", "note": "Food crumbs are biodegradable.", "graphic": "bread"},
    {"name": "coconut shell", "category": "Wet Waste", "tip": "Send it to composting or natural waste collection.", "note": "Natural shells break down over time.", "graphic": "coconut"},
    {"name": "corn husk", "category": "Wet Waste", "tip": "Put it in compost or wet waste.", "note": "Corn husk is plant-based waste.", "graphic": "corn"},
    {"name": "tomato stems", "category": "Wet Waste", "tip": "Add them to compost or wet waste.", "note": "Plant stems belong with organic waste.", "graphic": "tomato"},
    {"name": "paper", "category": "Dry Waste", "tip": "Keep it dry and send it for paper recycling.", "note": "Clean paper can be recycled.", "graphic": "paper"},
    {"name": "newspaper", "category": "Dry Waste", "tip": "Fold it neatly and keep it dry for recycling.", "note": "Newspapers belong in dry recycling.", "graphic": "newspaper"},
    {"name": "notebook", "category": "Dry Waste", "tip": "Recycle the paper after removing extra plastic parts.", "note": "Paper notebooks are usually recyclable.", "graphic": "notebook"},
    {"name": "cardboard box", "category": "Dry Waste", "tip": "Flatten it before placing it in dry waste.", "note": "Cardboard is recyclable when clean.", "graphic": "box"},
    {"name": "cereal box", "category": "Dry Waste", "tip": "Flatten it and place it in dry waste.", "note": "Paperboard packaging is recyclable.", "graphic": "box"},
    {"name": "paper bag", "category": "Dry Waste", "tip": "Keep it dry and place it in dry recycling.", "note": "Paper bags can be reused or recycled.", "graphic": "bag"},
    {"name": "plastic bottle", "category": "Dry Waste", "tip": "Rinse it and place it in dry recycling.", "note": "Plastic bottles should be clean before recycling.", "graphic": "bottle"},
    {"name": "milk packet", "category": "Dry Waste", "tip": "Wash it and place it in dry waste.", "note": "Clean packaging is easier to process.", "graphic": "carton"},
    {"name": "glass jar", "category": "Dry Waste", "tip": "Reuse it if possible or place it in glass recycling.", "note": "Glass is highly recyclable.", "graphic": "jar"},
    {"name": "metal can", "category": "Dry Waste", "tip": "Rinse it and send it for metal recycling.", "note": "Metal recycling saves materials and energy.", "graphic": "can"},
    {"name": "aluminum foil", "category": "Dry Waste", "tip": "Clean it and place it in dry recycling if accepted locally.", "note": "Metal foil belongs with dry recyclables when clean.", "graphic": "foil"},
    {"name": "plastic wrapper", "category": "Dry Waste", "tip": "Place it in dry waste after emptying it.", "note": "Plastic packaging should stay out of wet waste.", "graphic": "wrapper"},
    {"name": "yogurt cup", "category": "Dry Waste", "tip": "Rinse it and place it in dry recycling where accepted.", "note": "Clean plastic cups belong with dry waste.", "graphic": "cup"},
    {"name": "juice carton", "category": "Dry Waste", "tip": "Empty it, rinse it, and place it in dry waste.", "note": "Cartons must be clean for better recycling.", "graphic": "carton"},
    {"name": "shampoo bottle", "category": "Dry Waste", "tip": "Empty and rinse it before recycling.", "note": "Clean bottles are easier to recycle.", "graphic": "bottle"},
    {"name": "detergent bottle", "category": "Dry Waste", "tip": "Rinse it and place it in dry waste if empty.", "note": "Household containers belong in dry recycling when clean.", "graphic": "bottle"},
    {"name": "cloth bag", "category": "Dry Waste", "tip": "Reuse it as long as possible or send it to textile recycling.", "note": "Reusable cloth items reduce plastic use.", "graphic": "bag"},
    {"name": "toy block", "category": "Dry Waste", "tip": "Reuse or donate it first; recycle if accepted.", "note": "Hard plastic items should stay out of wet waste.", "graphic": "toy"},
    {"name": "magazine", "category": "Dry Waste", "tip": "Keep it dry and place it with paper recycling.", "note": "Printed paper belongs in dry waste.", "graphic": "book"},
    {"name": "cardboard tube", "category": "Dry Waste", "tip": "Place it in dry paper recycling.", "note": "Cardboard tubes are recyclable.", "graphic": "tube"},
    {"name": "steel lid", "category": "Dry Waste", "tip": "Place it with clean metal recyclables.", "note": "Metal lids belong in dry recycling.", "graphic": "lid"},
    {"name": "soda can", "category": "Dry Waste", "tip": "Rinse it and place it in metal recycling.", "note": "Aluminum cans are valuable recyclables.", "graphic": "can"},
    {"name": "plastic cup", "category": "Dry Waste", "tip": "Rinse it before placing it in dry waste.", "note": "Clean cups belong in dry recycling.", "graphic": "cup"},
    {"name": "envelope", "category": "Dry Waste", "tip": "Place it in paper recycling.", "note": "Paper envelopes belong with dry paper waste.", "graphic": "envelope"},
    {"name": "battery", "category": "Hazardous Waste", "tip": "Store it safely and send it to a battery collection center.", "note": "Batteries contain chemicals that need careful handling.", "graphic": "battery"},
    {"name": "medicine blister", "category": "Hazardous Waste", "tip": "Use a safe medicine take-back or hazardous waste collection point.", "note": "Medicines and medical packaging need safe disposal.", "graphic": "blister"},
    {"name": "paint can", "category": "Hazardous Waste", "tip": "Seal it and use hazardous waste collection.", "note": "Paint residue can harm soil and water.", "graphic": "paint"},
    {"name": "bulb", "category": "Hazardous Waste", "tip": "Wrap it carefully and dispose of it through safe collection.", "note": "Some bulbs contain materials that need special care.", "graphic": "bulb"},
    {"name": "aerosol can", "category": "Hazardous Waste", "tip": "Dispose of it through hazardous waste collection if required locally.", "note": "Pressurized containers need careful handling.", "graphic": "spray"},
    {"name": "charger cable", "category": "Hazardous Waste", "tip": "Send it to an e-waste center.", "note": "Electronic accessories belong in e-waste collection.", "graphic": "cable"},
    {"name": "old phone", "category": "Hazardous Waste", "tip": "Use an authorized e-waste drop-off point.", "note": "Electronics contain valuable and harmful materials.", "graphic": "phone"},
    {"name": "ink cartridge", "category": "Hazardous Waste", "tip": "Return it through a refill or cartridge recycling program.", "note": "Printer cartridges should not go in regular bins.", "graphic": "cartridge"},
    {"name": "chemical bottle", "category": "Hazardous Waste", "tip": "Follow the label and dispose of it through hazardous waste collection.", "note": "Chemical containers may retain unsafe residue.", "graphic": "chemical"},
    {"name": "pesticide bottle", "category": "Hazardous Waste", "tip": "Use a hazardous waste collection service.", "note": "Pesticide containers should never mix with regular waste.", "graphic": "chemical"},
    {"name": "tube light", "category": "Hazardous Waste", "tip": "Dispose of it through a safe lighting or e-waste program.", "note": "Tube lights can contain materials that need special disposal.", "graphic": "tubelight"},
    {"name": "button cell", "category": "Hazardous Waste", "tip": "Store it in a sealed container until safe drop-off.", "note": "Small batteries still require special handling.", "graphic": "coinbattery"},
    {"name": "glue tube", "category": "Hazardous Waste", "tip": "Follow local guidance for chemical containers and adhesives.", "note": "Adhesive residue can be harmful.", "graphic": "tube"},
    {"name": "thermometer", "category": "Hazardous Waste", "tip": "Take it to a hazardous waste or medical disposal point.", "note": "Some thermometers contain unsafe substances.", "graphic": "thermometer"},
    {"name": "nail polish bottle", "category": "Hazardous Waste", "tip": "Dispose of it through safe chemical or cosmetic waste collection.", "note": "Cosmetic chemicals should be handled carefully.", "graphic": "polish"},
    {"name": "electronic chip", "category": "Hazardous Waste", "tip": "Send it to an e-waste collection center.", "note": "Electronic parts belong in e-waste, not household bins.", "graphic": "chip"},
]

GAME_SCENES = [
    "school fair",
    "science lab cleanup",
    "park picnic",
    "community drive",
    "garden day",
    "sports event",
    "beach walk",
    "library week",
    "craft workshop",
    "canteen break",
    "class project",
    "eco club rally",
    "playground duty",
    "street cleanup",
    "market visit",
    "farm day",
    "neighborhood patrol",
    "bus stop cleanup",
    "festival morning",
    "campus round",
]

GAME_OBJECTIVES = [
    "before the timer ends",
    "before the next bell rings",
    "before the cleanup cart leaves",
    "before the eco coach checks the bins",
    "before the team score locks in",
    "before the next round starts",
    "before the sorting alarm sounds",
    "before the recycling relay begins",
    "before the green badge challenge closes",
    "before the mission board refreshes",
]

GAME_TEAMS = [
    "eco squad",
    "green team",
    "cleanup crew",
    "recycling rangers",
    "planet patrol",
    "class champions",
    "campus crew",
    "nature helpers",
    "garden group",
    "street stars",
]

GAME_PROMPT_TEMPLATES = [
    "At the {scene}, the {team} need to place {item} in the correct bin {objective}.",
    "During the {scene}, your {team} found {item}. Which bin should take it {objective}?",
    "The {team} are racing through the {scene}. Sort {item} into the right bin {objective}.",
    "A cleanup cart stops at the {scene}. Help the {team} sort {item} correctly {objective}.",
    "The {team} picked up {item} at the {scene}. Choose its bin {objective}.",
    "Mission check: the {team} must sort {item} from the {scene} {objective}.",
    "The {scene} left the {team} with {item}. Send it to the correct bin {objective}.",
    "Sorting alert for the {team}: place {item} from the {scene} in the right bin {objective}.",
    "The {team} are cleaning the {scene}. Decide where {item} belongs {objective}.",
    "Before the {scene} ends, the {team} need the right bin for {item} {objective}.",
]

QUIZ_TOPICS = [
    {"topic": "saving water", "answer": "Turn off the tap while brushing your teeth.", "explanation": "Small daily actions save a lot of clean water."},
    {"topic": "saving electricity", "answer": "Switch off lights and fans when leaving a room.", "explanation": "Using less electricity saves energy and reduces pollution."},
    {"topic": "reducing plastic", "answer": "Carry a reusable bottle and lunch box.", "explanation": "Reusable items cut down on throwaway plastic."},
    {"topic": "composting", "answer": "Collect fruit peels and vegetable scraps for compost.", "explanation": "Composting turns organic waste into useful soil material."},
    {"topic": "protecting trees", "answer": "Use both sides of paper and plant native trees.", "explanation": "Saving paper and planting trees help forests stay healthy."},
    {"topic": "protecting wildlife", "answer": "Keep litter and plastic away from animals.", "explanation": "Animals can be injured by litter left in nature."},
    {"topic": "clean travel", "answer": "Walk, cycle, or use public transport when possible.", "explanation": "Cleaner travel choices help reduce air pollution."},
    {"topic": "e-waste safety", "answer": "Take old electronics to an e-waste collection center.", "explanation": "Electronics contain parts that need special recycling."},
    {"topic": "glass recycling", "answer": "Rinse glass containers and place them in recycling.", "explanation": "Clean glass is easier to recycle into new containers."},
    {"topic": "reducing food waste", "answer": "Serve only what you can eat and save leftovers safely.", "explanation": "Planning meals helps reduce wasted food."},
    {"topic": "reuse habits", "answer": "Repair and reuse containers before throwing them away.", "explanation": "Using items longer reduces waste."},
    {"topic": "smart shopping", "answer": "Carry a cloth bag instead of taking a new plastic bag.", "explanation": "Reusable bags cut down on disposable packaging."},
    {"topic": "beach care", "answer": "Pick up litter and sort it before leaving the beach.", "explanation": "Clean beaches protect marine life and keep places safe."},
    {"topic": "battery safety", "answer": "Store used batteries separately for safe drop-off.", "explanation": "Batteries should not mix with everyday trash."},
    {"topic": "paper reuse", "answer": "Use scrap paper for rough work before recycling it.", "explanation": "Reusing paper first gets more value from each sheet."},
    {"topic": "clean air", "answer": "Avoid burning waste and keep smoke out of the air.", "explanation": "Burning waste releases harmful pollutants."},
    {"topic": "school cleanliness", "answer": "Place wrappers in the correct bin instead of littering.", "explanation": "Clean shared spaces are safer and healthier for everyone."},
    {"topic": "garden care", "answer": "Use dry leaves as mulch or compost.", "explanation": "Leaf waste can help protect and enrich soil."},
    {"topic": "water protection", "answer": "Keep chemicals out of drains, lakes, and rivers.", "explanation": "Chemicals in water can harm people, animals, and plants."},
    {"topic": "sharing resources", "answer": "Donate usable books, clothes, or toys.", "explanation": "Sharing usable items reduces waste and helps others."},
    {"topic": "solar energy", "answer": "Use sunlight or solar devices when available.", "explanation": "Solar power is a cleaner energy option."},
    {"topic": "refill habits", "answer": "Refill water bottles instead of buying new ones.", "explanation": "Refilling containers reduces plastic waste."},
    {"topic": "community cleanup", "answer": "Join local cleanup drives and sort collected waste.", "explanation": "Community action keeps shared places cleaner."},
    {"topic": "wildlife habitat", "answer": "Plant native flowers and trees for birds and insects.", "explanation": "Native plants support local wildlife."},
    {"topic": "less packaging", "answer": "Choose products with less packaging.", "explanation": "Smarter buying choices create less waste."},
]

QUIZ_PLACES = [
    "classroom",
    "playground",
    "garden",
    "school hall",
    "library",
    "cafeteria",
    "park",
    "beach",
    "neighborhood",
    "market",
    "kitchen",
    "terrace",
    "science room",
    "sports ground",
    "bus stop",
    "community center",
    "street corner",
    "picnic area",
    "farm patch",
    "art room",
]

QUIZ_GROUPS = [
    "eco club",
    "class team",
    "science group",
    "garden team",
    "cleanup squad",
    "reading club",
    "sports team",
    "music group",
    "family group",
    "neighborhood kids",
    "project team",
    "festival volunteers",
    "lunch monitors",
    "art club",
    "green leaders",
    "school council",
    "community helpers",
    "nature explorers",
    "recycling team",
    "young planners",
]

QUIZ_SCENARIOS = [
    "morning cleanup",
    "project day",
    "weekend activity",
    "celebration event",
    "after-school session",
    "community visit",
    "green fair",
    "holiday workshop",
    "practice round",
    "awareness campaign",
]

QUIZ_TEMPLATES = [
    "At the {place}, the {group} want to help with {topic}. Which action is the best choice during {scenario}?",
    "The {group} are planning a green habit for the {place}. Which step best supports {topic} on {scenario}?",
    "During {scenario} in the {place}, what should the {group} do first to improve {topic}?",
    "Which everyday action would best teach the {group} about {topic} at the {place} during {scenario}?",
    "If the {group} want a cleaner {place} on {scenario}, which idea best matches {topic}?",
]

BASE_CSS = """
:root {
    --ink: #16332b;
    --soft-ink: #61746f;
    --panel: rgba(255, 255, 255, 0.92);
    --line: rgba(22, 51, 43, 0.12);
    --pink: #ff8dbb;
    --sky: #55c8ff;
    --mint: #65d66f;
    --gold: #ffd666;
}
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    color: var(--ink);
    font-family: "Trebuchet MS", "Verdana", sans-serif;
    background:
        radial-gradient(circle at 10% 10%, rgba(255,255,255,0.85), rgba(255,255,255,0) 22%),
        radial-gradient(circle at 84% 12%, rgba(255,239,169,0.8), rgba(255,239,169,0) 18%),
        linear-gradient(180deg, #9ae8ff 0%, #d9ffdf 48%, #fff1c4 100%);
    min-height: 100vh;
}
.nav a,
.card,
.quick-card,
.guide-card,
.fact-card,
button,
.chip,
.table-art,
.hero-art {
    transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease, background 0.22s ease;
}
.topbar {
    padding: 28px 30px 32px;
    background: linear-gradient(135deg, #4bc8ff 0%, #88f7c7 52%, #ffe08b 100%);
    border-bottom: 3px solid rgba(255,255,255,0.5);
}
.topbar h1 {
    margin: 0;
    font-size: clamp(2rem, 5vw, 3rem);
    font-family: "Cooper Black", "Trebuchet MS", sans-serif;
}
.topbar p {
    margin: 10px 0 0;
    max-width: 720px;
}
.nav {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    padding: 18px 28px 0;
}
.nav a {
    text-decoration: none;
    color: var(--ink);
    background: rgba(255,255,255,0.88);
    border: 1px solid rgba(255,255,255,0.95);
    padding: 11px 16px;
    border-radius: 999px;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(22,51,43,0.08);
}
.nav a:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px rgba(74, 133, 255, 0.22), 0 0 16px rgba(255, 141, 187, 0.18);
}
.nav a.active {
    color: white;
    background: linear-gradient(135deg, #ff86b2, #748cff);
}
.page {
    max-width: 1220px;
    margin: 0 auto;
    padding: 24px 28px 40px;
}
.meta-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}
.meta-pill {
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.84);
    border: 1px solid rgba(255,255,255,0.94);
    box-shadow: 0 8px 18px rgba(22,51,43,0.06);
}
.page-hero,
.split-layout,
.learn-layout {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 18px;
}
.card {
    background: var(--panel);
    border-radius: 28px;
    padding: 22px;
    border: 1px solid rgba(255,255,255,0.96);
    box-shadow: 0 16px 38px rgba(22,51,43,0.08);
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 22px 46px rgba(22,51,43,0.12), 0 0 18px rgba(117, 168, 255, 0.12);
}
.hero-art-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 280px;
}
.hero-art {
    width: min(100%, 360px);
    display: block;
}
.title {
    margin: 0 0 10px;
    font-size: clamp(1.7rem, 3vw, 2.4rem);
    font-family: "Cooper Black", "Trebuchet MS", sans-serif;
    line-height: 1.08;
}
.lead {
    margin: 0;
    color: var(--soft-ink);
    font-size: 1.02rem;
}
.eyebrow {
    display: inline-block;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.84);
    font-weight: 800;
    margin-bottom: 14px;
}
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px;
    margin-top: 18px;
}
.stat-bubble {
    background: rgba(255,255,255,0.82);
    border-radius: 22px;
    padding: 16px;
    text-align: center;
}
.stat-bubble strong {
    display: block;
    font-size: 1.55rem;
    font-family: "Cooper Black", "Trebuchet MS", sans-serif;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
}
.guide-card {
    padding: 18px;
    border-radius: 24px;
    color: white;
    min-height: 170px;
}
.guide-card h3 {
    margin-top: 0;
}
.quick-grid {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.quick-card {
    flex: 1 1 220px;
    display: block;
    padding: 18px;
    border-radius: 22px;
    color: white;
    text-decoration: none;
}
.quick-card:hover {
    transform: translateY(-5px) scale(1.01);
    box-shadow: 0 18px 34px rgba(22,51,43,0.18), 0 0 18px rgba(255,255,255,0.2);
}
.quick-card h3 {
    margin-top: 0;
}
.button-row,
form.inline,
.option-grid,
.chip-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
}
input[type="text"] {
    width: min(100%, 360px);
    padding: 14px 16px;
    border: 2px solid rgba(22,51,43,0.1);
    border-radius: 16px;
    font-size: 1rem;
    background: white;
}
button,
.button-link,
.chip {
    border: none;
    border-radius: 18px;
    padding: 13px 18px;
    font-size: 0.98rem;
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
}
button:hover,
.button-link:hover,
.chip:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22,51,43,0.14), 0 0 14px rgba(255, 148, 167, 0.14);
}
.guide-card:hover,
.fact-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 34px rgba(22,51,43,0.14), 0 0 16px rgba(255,255,255,0.16);
}
.hero-art:hover,
.table-art:hover {
    transform: translateY(-3px) scale(1.03);
    filter: drop-shadow(0 10px 18px rgba(22,51,43,0.16));
}
.primary {
    color: white;
    background: linear-gradient(135deg, #ff8c66, #ff5f96);
}
.secondary {
    color: var(--ink);
    background: linear-gradient(135deg, #ffffff, #eff8ff);
}
.bin-button {
    min-width: 220px;
    color: white;
}
.quiz-option {
    min-width: 260px;
    color: var(--ink);
    background: linear-gradient(135deg, #ffffff, #eef7ff);
}
.quiz-option.correct {
    background: linear-gradient(135deg, #c6ffd4, #74db82);
}
.quiz-option.wrong {
    background: linear-gradient(135deg, #ffd8d8, #ff9f9f);
}
.status,
.result-panel {
    margin-top: 16px;
    padding: 18px;
    border-radius: 22px;
    background: rgba(255,255,255,0.86);
    border: 1px solid rgba(255,255,255,0.94);
}
.result-panel {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 18px;
    align-items: center;
}
.item-stage,
.question-stage {
    margin-top: 18px;
    padding: 22px;
    border-radius: 30px;
    background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,250,255,0.9));
    text-align: center;
}
.item-art-large {
    width: min(100%, 260px);
    display: block;
    margin: 0 auto 14px;
}
.finder-art {
    width: 120px;
    display: block;
}
.table-wrap {
    overflow-x: auto;
}
table {
    width: 100%;
    min-width: 860px;
    border-collapse: collapse;
}
th,
td {
    text-align: left;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(22,51,43,0.08);
}
th {
    color: #2c64c8;
}
.table-art {
    width: 54px;
    height: 54px;
    display: block;
}
.fact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
}
.fact-card {
    appearance: none;
    width: 100%;
    text-align: left;
    background:
        radial-gradient(circle at top right, rgba(255,255,255,0.98), rgba(255,255,255,0) 34%),
        linear-gradient(160deg, rgba(255,255,255,0.96), rgba(242,250,255,0.9));
    border: 1px solid rgba(22,51,43,0.08);
    border-radius: 22px;
    padding: 18px;
    position: relative;
    overflow: hidden;
    color: var(--ink);
}
.fact-card::before {
    content: "";
    position: absolute;
    inset: auto -36px -36px auto;
    width: 110px;
    height: 110px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(85,200,255,0.34), rgba(85,200,255,0) 70%);
}
.fact-card h3,
.fact-card p {
    position: relative;
    z-index: 1;
}
.fact-card h3 {
    margin: 0 0 10px;
}
.fact-card p {
    margin: 0;
}
.fact-card p + p {
    margin-top: 10px;
}
.fact-card-theme {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.83rem;
    font-weight: 800;
    color: #1c6a7f;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
}
.fact-card-theme::before {
    content: "";
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: linear-gradient(135deg, #55c8ff, #65d66f);
    box-shadow: 0 0 0 6px rgba(85,200,255,0.12);
}
.fact-card-cta {
    margin-top: 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #e85d75;
    font-weight: 800;
}
.fact-card-cta::after {
    content: ">";
    font-size: 1rem;
}
.fact-card:focus-visible,
.fact-article-close:focus-visible {
    outline: 3px solid rgba(85,200,255,0.55);
    outline-offset: 3px;
}
.fact-article-overlay[hidden] {
    display: none;
}
.fact-article-overlay {
    position: fixed;
    inset: 0;
    z-index: 90;
    padding: 24px;
    overflow-y: auto;
    background: rgba(13, 29, 28, 0.5);
    backdrop-filter: blur(10px);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.26s ease;
}
.fact-article-overlay.visible {
    opacity: 1;
    pointer-events: auto;
}
body.article-open {
    overflow: hidden;
}
.fact-article-shell {
    --article-accent: #58C94C;
    max-width: 1080px;
    margin: 12px auto;
    border-radius: 30px;
    padding: 24px;
    background:
        radial-gradient(circle at top right, rgba(255,255,255,0.82), rgba(255,255,255,0) 24%),
        linear-gradient(160deg, rgba(255,255,255,0.98), rgba(244,250,252,0.96));
    border: 1px solid rgba(255,255,255,0.78);
    box-shadow: 0 30px 80px rgba(7,24,18,0.26);
    transform: translateY(28px) scale(0.98);
    transition: transform 0.32s ease;
}
.fact-article-overlay.visible .fact-article-shell {
    transform: translateY(0) scale(1);
}
.fact-article-topbar {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
}
.fact-article-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.92);
    box-shadow: inset 0 0 0 2px rgba(22,51,43,0.04);
    color: var(--ink);
    font-weight: 800;
    margin-bottom: 12px;
}
.fact-article-badge::before {
    content: "";
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: var(--article-accent);
}
.fact-article-close {
    flex: 0 0 auto;
    background: white;
    color: var(--ink);
    border: 1px solid rgba(22,51,43,0.08);
}
.fact-article-layout {
    display: grid;
    grid-template-columns: minmax(0, 1.02fr) minmax(300px, 0.98fr);
    gap: 22px;
    margin-top: 16px;
}
.fact-article-copy {
    min-width: 0;
}
.fact-article-copy h2 {
    margin: 0 0 12px;
    font-size: clamp(2rem, 3.4vw, 3rem);
    line-height: 1.04;
    font-family: "Cooper Black", "Trebuchet MS", sans-serif;
}
.fact-article-copy .lead {
    font-size: 1.06rem;
}
.fact-article-quote {
    margin: 18px 0;
    padding: 18px 20px;
    border-radius: 22px;
    background: linear-gradient(140deg, rgba(255,255,255,0.98), rgba(240,247,251,0.95));
    border: 1px solid rgba(22,51,43,0.08);
    border-top: 4px solid var(--article-accent);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.6);
}
.fact-article-quote p {
    margin: 0;
    font-size: 1.08rem;
}
.fact-article-body {
    display: grid;
    gap: 16px;
}
.fact-article-body p {
    margin: 0;
    color: #34514b;
    line-height: 1.65;
}
.article-action-list,
.article-stat-grid,
.article-strip {
    display: grid;
    gap: 12px;
}
.article-action-list {
    margin-top: 16px;
}
.article-action {
    display: grid;
    grid-template-columns: 36px 1fr;
    gap: 12px;
    align-items: start;
    padding: 14px 16px;
    border-radius: 20px;
    background: rgba(255,255,255,0.84);
    border: 1px solid rgba(22,51,43,0.08);
}
.article-action-index {
    width: 36px;
    height: 36px;
    border-radius: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: white;
    background: linear-gradient(135deg, var(--article-accent), #16332b);
}
.article-action p {
    margin: 0;
    line-height: 1.55;
}
.article-stat-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-top: 18px;
}
.article-stat {
    padding: 16px;
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(255,255,255,0.96), rgba(240,247,251,0.94));
    border: 1px solid rgba(22,51,43,0.08);
    min-height: 124px;
    animation: fact-card-rise 0.55s ease both;
}
.article-stat strong {
    display: block;
    margin-bottom: 8px;
    font-size: 1rem;
}
.article-stat p {
    margin: 0;
    color: #44625b;
    line-height: 1.55;
}
.fact-article-visuals {
    min-width: 0;
}
.article-hero-frame,
.article-thumb {
    position: relative;
    overflow: hidden;
    border-radius: 28px;
    background: linear-gradient(160deg, rgba(255,255,255,0.98), rgba(240,247,251,0.94));
    border: 1px solid rgba(22,51,43,0.08);
}
.article-hero-frame {
    padding: 16px;
    box-shadow: 0 18px 40px rgba(22,51,43,0.12);
}
.article-hero-frame img {
    width: 100%;
    display: block;
    animation: fact-float 6s ease-in-out infinite;
}
.article-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-top: 14px;
}
.article-thumb {
    padding: 14px;
    animation: fact-card-rise 0.6s ease both;
}
.article-thumb:nth-child(2) {
    animation-delay: 0.08s;
}
.article-thumb img {
    width: 100%;
    display: block;
    border-radius: 20px;
}
.article-thumb figcaption {
    margin-top: 12px;
}
.article-thumb strong,
.article-thumb span {
    display: block;
}
.article-thumb span {
    margin-top: 5px;
    color: #4d6761;
    line-height: 1.5;
}
@keyframes fact-float {
    0%,
    100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-8px);
    }
}
@keyframes fact-card-rise {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.tiny {
    font-size: 0.92rem;
    color: var(--soft-ink);
}
ul.clean {
    margin: 0;
    padding-left: 20px;
}
@media (max-width: 920px) {
    .page-hero,
    .split-layout,
    .learn-layout,
    .result-panel {
        grid-template-columns: 1fr;
    }
    .fact-article-layout,
    .article-stat-grid,
    .article-strip {
        grid-template-columns: 1fr;
    }
    .hero-art {
        max-width: 280px;
    }
    .fact-article-overlay {
        padding: 12px;
    }
    .fact-article-shell {
        padding: 18px;
        border-radius: 24px;
    }
    .fact-article-copy h2 {
        font-size: 2rem;
    }
    .fact-article-topbar {
        align-items: stretch;
        flex-direction: column;
    }
}
"""


def _base_bin(category: str) -> str:
    return CATEGORY_GUIDE[category]["bin"]


def _simple_item_name(item_id: int, base_name: str, base_count: int) -> str:
    serial = ((item_id - 1) // base_count) + 1
    return f"{base_name} {serial:05d}"


class MultiDbRepository:
    def __init__(self) -> None:
        self.items_conn = sqlite3.connect(ITEMS_DB_PATH)
        self.sorting_conn = sqlite3.connect(SORTING_DB_PATH)
        self.quiz_conn = sqlite3.connect(QUIZ_DB_PATH)
        self.facts_conn = sqlite3.connect(FACTS_DB_PATH)
        self.state_conn = sqlite3.connect(STATE_DB_PATH)

        for conn in (self.items_conn, self.sorting_conn, self.quiz_conn, self.facts_conn, self.state_conn):
            conn.row_factory = sqlite3.Row

        self._setup_items_db()
        self._setup_sorting_db()
        self._setup_quiz_db()
        self._setup_facts_db()
        self._setup_state_db()

    def close(self) -> None:
        for conn in (self.items_conn, self.sorting_conn, self.quiz_conn, self.facts_conn, self.state_conn):
            conn.close()

    def _setup_items_db(self) -> None:
        cur = self.items_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS item_bases (
                id INTEGER PRIMARY KEY,
                base_name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                bin_name TEXT NOT NULL,
                disposal_tip TEXT NOT NULL,
                learn_note TEXT NOT NULL,
                graphic_key TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                base_id INTEGER NOT NULL,
                FOREIGN KEY(base_id) REFERENCES item_bases(id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_items_base_id ON items(base_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
        self.items_conn.commit()

        base_count = cur.execute("SELECT COUNT(*) FROM item_bases").fetchone()[0]
        item_count = cur.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        expected_base_count = len(WASTE_BASES)

        if base_count == expected_base_count and item_count == TARGET_WASTE_ITEM_COUNT:
            return

        cur.execute("DELETE FROM items")
        cur.execute("DELETE FROM item_bases")
        self.items_conn.commit()

        cur.executemany(
            """
            INSERT INTO item_bases (id, base_name, category, bin_name, disposal_tip, learn_note, graphic_key)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    item["name"],
                    item["category"],
                    _base_bin(item["category"]),
                    item["tip"],
                    item["note"],
                    item["graphic"],
                )
                for index, item in enumerate(WASTE_BASES, start=1)
            ],
        )
        self.items_conn.commit()

        batch = []
        batch_size = 10000
        base_total = len(WASTE_BASES)
        for item_id in range(1, TARGET_WASTE_ITEM_COUNT + 1):
            base_id = ((item_id - 1) % base_total) + 1
            base_name = WASTE_BASES[base_id - 1]["name"]
            batch.append((item_id, _simple_item_name(item_id, base_name, base_total), base_id))
            if len(batch) >= batch_size:
                cur.executemany("INSERT INTO items (id, name, base_id) VALUES (?, ?, ?)", batch)
                self.items_conn.commit()
                batch.clear()
        if batch:
            cur.executemany("INSERT INTO items (id, name, base_id) VALUES (?, ?, ?)", batch)
            self.items_conn.commit()

    def _setup_sorting_db(self) -> None:
        cur = self.sorting_conn.cursor()
        self.sorting_conn.execute("PRAGMA user_version")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                mission_title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                hint TEXT NOT NULL
            )
            """
        )
        self.sorting_conn.commit()

        version = self.sorting_conn.execute("PRAGMA user_version").fetchone()[0]
        count = cur.execute("SELECT COUNT(*) FROM challenges").fetchone()[0]
        if count == TARGET_SORTING_CHALLENGE_COUNT and version == 2:
            return

        cur.execute("DELETE FROM challenges")
        self.sorting_conn.commit()

        base_total = len(WASTE_BASES)
        batch = []
        batch_size = 5000
        for challenge_id in range(1, TARGET_SORTING_CHALLENGE_COUNT + 1):
            item_id = ((challenge_id * 7919) % TARGET_WASTE_ITEM_COUNT) + 1
            base_id = ((item_id - 1) % base_total) + 1
            base = WASTE_BASES[base_id - 1]
            scene = GAME_SCENES[(challenge_id - 1) % len(GAME_SCENES)]
            objective = GAME_OBJECTIVES[(challenge_id - 1) % len(GAME_OBJECTIVES)]
            team = GAME_TEAMS[(challenge_id - 1) % len(GAME_TEAMS)]
            prompt_template = GAME_PROMPT_TEMPLATES[(challenge_id - 1) % len(GAME_PROMPT_TEMPLATES)]
            mission_title = f"Mission {challenge_id:05d}"
            prompt = prompt_template.format(
                scene=scene,
                team=team,
                item=base["name"],
                objective=objective,
            )
            batch.append((challenge_id, item_id, mission_title, prompt, base["note"]))
            if len(batch) >= batch_size:
                cur.executemany(
                    "INSERT INTO challenges (id, item_id, mission_title, prompt, hint) VALUES (?, ?, ?, ?, ?)",
                    batch,
                )
                self.sorting_conn.commit()
                batch.clear()
        if batch:
            cur.executemany(
                "INSERT INTO challenges (id, item_id, mission_title, prompt, hint) VALUES (?, ?, ?, ?, ?)",
                batch,
            )
            self.sorting_conn.commit()
        self.sorting_conn.execute("PRAGMA user_version = 2")
        self.sorting_conn.commit()

    def _setup_quiz_db(self) -> None:
        cur = self.quiz_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                prompt TEXT NOT NULL,
                options_json TEXT NOT NULL,
                correct_index INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                topic TEXT NOT NULL
            )
            """
        )
        self.quiz_conn.commit()

        count = cur.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if count == TARGET_QUIZ_QUESTION_COUNT:
            return

        cur.execute("DELETE FROM questions")
        self.quiz_conn.commit()

        topic_total = len(QUIZ_TOPICS)
        place_total = len(QUIZ_PLACES)
        group_total = len(QUIZ_GROUPS)
        scenario_total = len(QUIZ_SCENARIOS)
        template_total = len(QUIZ_TEMPLATES)

        batch = []
        batch_size = 4000
        for question_id in range(1, TARGET_QUIZ_QUESTION_COUNT + 1):
            value = question_id - 1
            topic = QUIZ_TOPICS[value % topic_total]
            value //= topic_total
            place = QUIZ_PLACES[value % place_total]
            value //= place_total
            group = QUIZ_GROUPS[value % group_total]
            value //= group_total
            scenario = QUIZ_SCENARIOS[value % scenario_total]

            template = QUIZ_TEMPLATES[(question_id - 1) % template_total]
            prompt = template.format(
                place=place,
                group=group,
                topic=topic["topic"],
                scenario=scenario,
            )

            distractors = []
            offset = 1
            while len(distractors) < 3:
                other = QUIZ_TOPICS[(question_id + offset) % topic_total]
                if other["answer"] != topic["answer"] and other["answer"] not in distractors:
                    distractors.append(other["answer"])
                offset += 1

            options = [topic["answer"], *distractors]
            order = list(range(4))
            random.Random(question_id).shuffle(order)
            shuffled = [options[index] for index in order]
            correct_index = shuffled.index(topic["answer"])

            batch.append(
                (
                    question_id,
                    prompt,
                    json.dumps(shuffled),
                    correct_index,
                    topic["explanation"],
                    topic["topic"],
                )
            )
            if len(batch) >= batch_size:
                cur.executemany(
                    """
                    INSERT INTO questions (id, prompt, options_json, correct_index, explanation, topic)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                self.quiz_conn.commit()
                batch.clear()
        if batch:
            cur.executemany(
                """
                INSERT INTO questions (id, prompt, options_json, correct_index, explanation, topic)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                batch,
            )
            self.quiz_conn.commit()

    def _setup_facts_db(self) -> None:
        cur = self.facts_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                fact_text TEXT NOT NULL UNIQUE,
                theme TEXT NOT NULL
            )
            """
        )
        self.facts_conn.commit()

        count = cur.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        theme_rows = cur.execute("SELECT DISTINCT theme FROM facts").fetchall()
        stored_themes = {row["theme"] for row in theme_rows}
        if count == TARGET_FACT_COUNT and stored_themes == set(FACT_THEMES):
            return

        cur.execute("DELETE FROM facts")
        self.facts_conn.commit()

        batch = []
        fact_id = 1
        for theme in FACT_THEMES:
            for context in FACT_CONTEXTS:
                for benefit in FACT_BENEFITS:
                    batch.append(
                        (
                            fact_id,
                            f"{theme} {context} {benefit}.",
                            theme,
                        )
                    )
                    fact_id += 1

        cur.executemany(
            "INSERT INTO facts (id, fact_text, theme) VALUES (?, ?, ?)",
            batch,
        )
        self.facts_conn.commit()

    def _setup_state_db(self) -> None:
        cur = self.state_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL
            )
            """
        )
        self.state_conn.commit()

        cur.execute(
            "INSERT OR IGNORE INTO app_state (state_key, state_value) VALUES (?, ?)",
            ("username", "Eco Learner"),
        )
        cur.execute(
            "INSERT OR REPLACE INTO app_state (state_key, state_value) VALUES (?, ?)",
            ("score", "0"),
        )
        self.state_conn.commit()

    def get_state(self, key: str, default: str = "") -> str:
        row = self.state_conn.execute(
            "SELECT state_value FROM app_state WHERE state_key = ?",
            (key,),
        ).fetchone()
        return row["state_value"] if row else default

    def set_state(self, key: str, value: str) -> None:
        self.state_conn.execute(
            """
            INSERT INTO app_state (state_key, state_value)
            VALUES (?, ?)
            ON CONFLICT(state_key) DO UPDATE SET state_value = excluded.state_value
            """,
            (key, value),
        )
        self.state_conn.commit()

    def get_score(self) -> int:
        return int(self.get_state("score", "0"))

    def add_score(self, points: int) -> int:
        updated = self.get_score() + points
        self.set_state("score", str(updated))
        return updated

    def get_item_count(self) -> int:
        return TARGET_WASTE_ITEM_COUNT

    def get_sorting_challenge_count(self) -> int:
        return TARGET_SORTING_CHALLENGE_COUNT

    def get_quiz_question_count(self) -> int:
        return TARGET_QUIZ_QUESTION_COUNT

    def get_fact_count(self) -> int:
        return self.facts_conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    def _item_from_row(self, row: sqlite3.Row | None) -> dict[str, object] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "base_name": row["base_name"],
            "category": row["category"],
            "bin_name": row["bin_name"],
            "disposal_tip": row["disposal_tip"],
            "learn_note": row["learn_note"],
            "graphic_key": row["graphic_key"],
        }

    def get_item_by_id(self, item_id: int) -> dict[str, object] | None:
        row = self.items_conn.execute(
            """
            SELECT items.id, items.name, item_bases.base_name, item_bases.category, item_bases.bin_name,
                   item_bases.disposal_tip, item_bases.learn_note, item_bases.graphic_key
            FROM items
            JOIN item_bases ON item_bases.id = items.base_id
            WHERE items.id = ?
            """,
            (item_id,),
        ).fetchone()
        return self._item_from_row(row)

    def get_items_preview(self, limit: int) -> list[dict[str, object]]:
        rows = self.items_conn.execute(
            """
            SELECT items.id, items.name, item_bases.base_name, item_bases.category, item_bases.bin_name,
                   item_bases.disposal_tip, item_bases.learn_note, item_bases.graphic_key
            FROM items
            JOIN item_bases ON item_bases.id = items.base_id
            ORDER BY items.id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def search_item(self, query: str):
        query = query.strip().lower()
        if not query:
            return None, []

        exact = self.items_conn.execute(
            """
            SELECT items.id, items.name, item_bases.base_name, item_bases.category, item_bases.bin_name,
                   item_bases.disposal_tip, item_bases.learn_note, item_bases.graphic_key
            FROM items
            JOIN item_bases ON item_bases.id = items.base_id
            WHERE lower(items.name) = ?
            LIMIT 1
            """,
            (query,),
        ).fetchone()
        if exact:
            return self._item_from_row(exact), []

        base_match = self.items_conn.execute(
            """
            SELECT items.id, items.name, item_bases.base_name, item_bases.category, item_bases.bin_name,
                   item_bases.disposal_tip, item_bases.learn_note, item_bases.graphic_key
            FROM items
            JOIN item_bases ON item_bases.id = items.base_id
            WHERE lower(item_bases.base_name) = ?
            ORDER BY items.id
            LIMIT 1
            """,
            (query,),
        ).fetchone()
        if base_match:
            return self._item_from_row(base_match), []

        suggestions = self.items_conn.execute(
            """
            SELECT base_name
            FROM item_bases
            WHERE lower(base_name) LIKE ?
            ORDER BY base_name
            LIMIT 5
            """,
            (f"%{query}%",),
        ).fetchall()

        suggestion_items = []
        for row in suggestions:
            sample = self.items_conn.execute(
                """
                SELECT items.id, items.name, item_bases.base_name, item_bases.category, item_bases.bin_name,
                       item_bases.disposal_tip, item_bases.learn_note, item_bases.graphic_key
                FROM items
                JOIN item_bases ON item_bases.id = items.base_id
                WHERE item_bases.base_name = ?
                ORDER BY items.id
                LIMIT 1
                """,
                (row["base_name"],),
            ).fetchone()
            if sample:
                suggestion_items.append(self._item_from_row(sample))
        return None, suggestion_items

    def get_random_sorting_ids(self, count: int) -> list[int]:
        return random.sample(range(1, TARGET_SORTING_CHALLENGE_COUNT + 1), k=count)

    def get_sorting_challenge(self, challenge_id: int) -> dict[str, object] | None:
        row = self.sorting_conn.execute(
            "SELECT * FROM challenges WHERE id = ?",
            (challenge_id,),
        ).fetchone()
        if row is None:
            return None
        item = self.get_item_by_id(row["item_id"])
        if item is None:
            return None
        return {
            "id": row["id"],
            "mission_title": row["mission_title"],
            "prompt": row["prompt"],
            "hint": row["hint"],
            "item": item,
            "correct_category": item["category"],
        }

    def get_random_quiz_ids(self, count: int) -> list[int]:
        return random.sample(range(1, TARGET_QUIZ_QUESTION_COUNT + 1), k=count)

    def get_quiz_question(self, question_id: int) -> dict[str, object] | None:
        row = self.quiz_conn.execute(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "prompt": row["prompt"],
            "options": json.loads(row["options_json"]),
            "correct_index": row["correct_index"],
            "explanation": row["explanation"],
            "topic": row["topic"],
        }

    def get_fact_batch(self, start_index: int, count: int) -> list[dict[str, object]]:
        if count <= 0:
            return []
        total = self.get_fact_count()
        if total == 0:
            return []

        theme_count = len(FACT_THEMES)
        context_count = len(FACT_CONTEXTS)
        benefit_count = len(FACT_BENEFITS)
        batch_number = start_index // count
        theme_start = start_index % theme_count
        context_index = batch_number % context_count
        benefit_index = (batch_number // context_count) % benefit_count

        fact_ids = []
        for offset in range(count):
            theme_index = (theme_start + offset) % theme_count
            local_context = (context_index + (offset // theme_count)) % context_count
            local_benefit = (benefit_index + offset) % benefit_count
            fact_id = (
                theme_index * context_count * benefit_count
                + local_context * benefit_count
                + local_benefit
                + 1
            )
            fact_ids.append(fact_id)

        facts = []
        for fact_id in fact_ids:
            fact = self.get_fact_by_id(fact_id)
            if fact is not None:
                facts.append(fact)
        return facts

    def get_fact_by_id(self, fact_id: int) -> dict[str, object] | None:
        row = self.facts_conn.execute(
            """
            SELECT id, fact_text, theme
            FROM facts
            WHERE id = ?
            """,
            (fact_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "text": row["fact_text"],
            "theme": row["theme"],
        }


def render_item_svg(item: dict[str, object]) -> str:
    key = str(item["graphic_key"])
    category = str(item["category"])
    color = CATEGORY_GUIDE[category]["color"]
    label = html.escape(str(item["base_name"]).title())
    bg_top = "#f7fdff"
    bg_bottom = "#eefcf2" if category == "Wet Waste" else "#eef5ff" if category == "Dry Waste" else "#fff1f1"

    def svg_body(graphic_body: str) -> str:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 220" role="img" aria-label="{label}">
<rect width="260" height="220" rx="28" fill="{bg_top}"/>
<rect width="260" height="220" rx="28" fill="url(#grad)"/>
<defs>
  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{bg_top}"/>
    <stop offset="100%" stop-color="{bg_bottom}"/>
  </linearGradient>
</defs>
<circle cx="42" cy="38" r="12" fill="{color}" opacity="0.18"/>
<circle cx="214" cy="34" r="16" fill="{color}" opacity="0.14"/>
<rect x="18" y="18" width="224" height="150" rx="24" fill="white" opacity="0.92"/>
{graphic_body}
<rect x="24" y="180" width="212" height="24" rx="12" fill="{color}" opacity="0.12"/>
<text x="130" y="196" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="14" fill="#18332b">{label}</text>
</svg>"""

    if key == "banana":
        body = '<path d="M82 112c18-40 56-58 90-54-10 46-42 84-90 92-22 4-38-18-28-38 5 6 15 10 28 0Z" fill="#ffd44d" stroke="#c49200" stroke-width="4"/>'
    elif key == "apple":
        body = '<path d="M130 58c8-10 20-18 32-20-6 16-16 24-32 28Z" fill="#4da34d"/><circle cx="112" cy="102" r="36" fill="#e84c4c"/><circle cx="148" cy="102" r="36" fill="#e84c4c"/><path d="M96 112c10 26 56 26 68 0" fill="#ffd7a8"/>'
    elif key == "orange":
        body = '<circle cx="130" cy="100" r="48" fill="#ff9d2f" stroke="#d6780f" stroke-width="4"/><path d="M130 52v96M82 100h96M96 66l68 68M164 66l-68 68" stroke="#fff0c9" stroke-width="6" stroke-linecap="round"/>'
    elif key == "leaf":
        body = '<path d="M132 54c44 18 52 66 8 94-40-14-56-54-8-94Z" fill="#5bbf59"/><path d="M132 54c-6 36-14 64-24 90" stroke="#2d7a33" stroke-width="4" stroke-linecap="round"/>'
    elif key == "coffee":
        body = '<rect x="84" y="72" width="84" height="62" rx="12" fill="#8b5a3c"/><path d="M168 84h18c10 0 18 8 18 18s-8 18-18 18h-18" fill="none" stroke="#8b5a3c" stroke-width="8"/><path d="M102 58c0 10 8 14 8 24M126 58c0 10 8 14 8 24M150 58c0 10 8 14 8 24" stroke="#cbb09a" stroke-width="4" stroke-linecap="round"/>'
    elif key == "carrot":
        body = '<path d="M132 62c24 24 28 74 0 98-28-24-24-74 0-98Z" fill="#ff8c32"/><path d="M120 56l-10-18M132 56V34M144 56l12-18" stroke="#49a649" stroke-width="6" stroke-linecap="round"/>'
    elif key == "grass":
        body = '<path d="M84 138c8-24 10-50 8-74M110 142c6-28 8-56 4-86M132 142c0-30 2-58 8-86M154 142c-4-28 0-56 12-82M178 142c-10-22-10-48-2-70" stroke="#57b84f" stroke-width="8" stroke-linecap="round"/>'
    elif key == "eggshell":
        body = '<path d="M92 132c-12-18-10-48 10-68 20-20 54-20 74 0 20 20 22 50 10 68l-20-10-18 12-16-10-18 12Z" fill="#fff6df" stroke="#d1c3a1" stroke-width="4"/>'
    elif key == "flower":
        body = '<circle cx="130" cy="102" r="18" fill="#ffd45a"/><circle cx="130" cy="70" r="20" fill="#ff7db0"/><circle cx="130" cy="134" r="20" fill="#ff7db0"/><circle cx="98" cy="102" r="20" fill="#ff7db0"/><circle cx="162" cy="102" r="20" fill="#ff7db0"/><path d="M130 122v30" stroke="#4da34d" stroke-width="6" stroke-linecap="round"/>'
    elif key == "fruit":
        body = '<circle cx="104" cy="106" r="26" fill="#ff5c5c"/><circle cx="136" cy="94" r="24" fill="#ffd34d"/><circle cx="160" cy="114" r="22" fill="#6fd66d"/><path d="M102 78c8-12 18-18 28-18" stroke="#4da34d" stroke-width="5" stroke-linecap="round"/>'
    elif key == "rice":
        body = '<path d="M84 132c14-38 78-38 92 0Z" fill="#f4f0df" stroke="#d8cfb2" stroke-width="4"/><path d="M96 122h68" stroke="#d8cfb2" stroke-width="4" stroke-linecap="round"/>'
    elif key == "bread":
        body = '<path d="M92 136V92c0-22 18-38 38-38 12 0 22 6 28 14 6-8 16-14 28-14 20 0 38 16 38 38v44Z" fill="#d89a52" stroke="#aa6e32" stroke-width="4"/>'
    elif key == "coconut":
        body = '<path d="M82 126c0-26 22-48 48-48 18 0 34 10 42 26 8 16 8 40-8 52H90c-6-8-8-18-8-30Z" fill="#8b5a3c"/><path d="M108 112c8-6 18-10 28-10 12 0 24 4 34 12" stroke="#fff2d4" stroke-width="4" stroke-linecap="round"/>'
    elif key == "corn":
        body = '<rect x="108" y="58" width="44" height="96" rx="22" fill="#ffd44d" stroke="#c79a10" stroke-width="4"/><path d="M96 82c-12 16-16 40-10 66M164 82c12 16 16 40 10 66" stroke="#5fb857" stroke-width="8" stroke-linecap="round"/>'
    elif key == "tomato":
        body = '<circle cx="130" cy="106" r="42" fill="#ef4d4d"/><path d="M130 60l-16-12M130 60l16-12M130 60V42" stroke="#4ea44e" stroke-width="6" stroke-linecap="round"/>'
    elif key == "paper":
        body = '<rect x="90" y="56" width="80" height="102" rx="8" fill="#ffffff" stroke="#cfd8e1" stroke-width="4"/><line x1="106" y1="84" x2="154" y2="84" stroke="#78a7ff" stroke-width="4" stroke-linecap="round"/><line x1="106" y1="102" x2="154" y2="102" stroke="#78a7ff" stroke-width="4" stroke-linecap="round"/><line x1="106" y1="120" x2="142" y2="120" stroke="#78a7ff" stroke-width="4" stroke-linecap="round"/>'
    elif key == "newspaper":
        body = '<rect x="82" y="62" width="96" height="92" rx="10" fill="#ffffff" stroke="#cfd8e1" stroke-width="4"/><rect x="96" y="78" width="26" height="24" rx="4" fill="#dbe7ff"/><line x1="130" y1="84" x2="164" y2="84" stroke="#8aa4c4" stroke-width="4" stroke-linecap="round"/><line x1="96" y1="114" x2="164" y2="114" stroke="#8aa4c4" stroke-width="4" stroke-linecap="round"/><line x1="96" y1="130" x2="164" y2="130" stroke="#8aa4c4" stroke-width="4" stroke-linecap="round"/>'
    elif key == "notebook":
        body = '<rect x="90" y="56" width="84" height="104" rx="10" fill="#ffd86a" stroke="#d7a92c" stroke-width="4"/><line x1="108" y1="56" x2="108" y2="160" stroke="#ffffff" stroke-width="6"/><circle cx="108" cy="76" r="4" fill="#7b5d00"/><circle cx="108" cy="96" r="4" fill="#7b5d00"/><circle cx="108" cy="116" r="4" fill="#7b5d00"/>'
    elif key == "box":
        body = '<path d="M90 82l40-24 40 24-40 24Z" fill="#d6a66a"/><path d="M90 82v46l40 24V106ZM170 82v46l-40 24V106Z" fill="#c89252"/>'
    elif key == "bag":
        body = '<path d="M94 80c0-14 10-24 24-24h24c14 0 24 10 24 24v58c0 10-8 18-18 18h-36c-10 0-18-8-18-18Z" fill="#d8b48a"/><path d="M108 78c0-14 8-24 22-24s22 10 22 24" fill="none" stroke="#99673d" stroke-width="6"/>'
    elif key == "bottle":
        body = '<rect x="112" y="48" width="36" height="22" rx="8" fill="#53c8ff"/><rect x="102" y="68" width="56" height="84" rx="18" fill="#8de3ff" stroke="#39a9db" stroke-width="4"/><rect x="112" y="94" width="36" height="24" rx="6" fill="#ffffff" opacity="0.7"/>'
    elif key == "carton":
        body = '<path d="M108 54h44l12 18v76c0 8-6 14-14 14h-56c-8 0-14-6-14-14V68Z" fill="#8bd7ff" stroke="#3b9dd1" stroke-width="4"/><path d="M108 54l22 18 22-18" fill="#dff5ff"/><rect x="112" y="92" width="40" height="28" rx="6" fill="#ffffff" opacity="0.8"/>'
    elif key == "jar":
        body = '<rect x="100" y="56" width="60" height="18" rx="6" fill="#6aa4d8"/><rect x="94" y="72" width="72" height="84" rx="18" fill="#d7efff" stroke="#78a9d8" stroke-width="4"/><circle cx="130" cy="116" r="18" fill="#b8ddff" opacity="0.8"/>'
    elif key == "can":
        body = '<rect x="98" y="58" width="64" height="96" rx="14" fill="#dbe2ea" stroke="#9aa7b3" stroke-width="4"/><ellipse cx="130" cy="58" rx="32" ry="10" fill="#edf3f8" stroke="#9aa7b3" stroke-width="4"/><ellipse cx="130" cy="154" rx="32" ry="10" fill="#c6d1db" stroke="#9aa7b3" stroke-width="4"/>'
    elif key == "foil":
        body = '<path d="M94 78l36-20 42 18 10 38-22 32-44 6-24-26Z" fill="#d7dde4" stroke="#a2aab3" stroke-width="4"/><path d="M112 88l48 44" stroke="#b7bec6" stroke-width="4" stroke-linecap="round"/>'
    elif key == "wrapper":
        body = '<path d="M76 106l24-20h60l24 20-24 20h-60Z" fill="#ff8dbb" stroke="#d4588a" stroke-width="4"/><path d="M76 106l-18-16v32ZM184 106l18-16v32Z" fill="#ffd469" stroke="#d8a82f" stroke-width="4"/>'
    elif key == "cup":
        body = '<path d="M98 70h64l-10 78c-2 10-10 16-20 16h-4c-10 0-18-6-20-16Z" fill="#ffffff" stroke="#a9b7c4" stroke-width="4"/><rect x="90" y="62" width="80" height="12" rx="6" fill="#d8e5ef"/>'
    elif key == "toy":
        body = '<rect x="90" y="84" width="34" height="34" rx="6" fill="#ff7cab"/><rect x="124" y="84" width="46" height="34" rx="6" fill="#4bc8ff"/><rect x="104" y="118" width="50" height="34" rx="6" fill="#ffd666"/>'
    elif key == "book":
        body = '<rect x="88" y="62" width="40" height="90" rx="8" fill="#ffb85c"/><rect x="132" y="62" width="40" height="90" rx="8" fill="#7dc0ff"/><line x1="130" y1="62" x2="130" y2="152" stroke="#ffffff" stroke-width="4"/>'
    elif key == "tube":
        body = '<rect x="92" y="90" width="76" height="42" rx="16" fill="#d7e3f3" stroke="#8da0b4" stroke-width="4"/><rect x="168" y="96" width="18" height="30" rx="4" fill="#a2b2c0"/>'
    elif key == "lid":
        body = '<ellipse cx="130" cy="110" rx="52" ry="30" fill="#d7e0ea" stroke="#96a4b0" stroke-width="4"/><ellipse cx="130" cy="110" rx="22" ry="10" fill="#f4f8fb"/>'
    elif key == "envelope":
        body = '<rect x="82" y="76" width="96" height="70" rx="10" fill="#fff8ef" stroke="#d6b894" stroke-width="4"/><path d="M82 84l48 34 48-34" fill="none" stroke="#d6b894" stroke-width="4"/>'
    elif key == "battery":
        body = '<rect x="98" y="64" width="64" height="90" rx="12" fill="#ff6d6d" stroke="#c63c3c" stroke-width="4"/><rect x="118" y="52" width="24" height="14" rx="4" fill="#575757"/><rect x="122" y="92" width="16" height="34" rx="4" fill="#fff"/><rect x="114" y="101" width="32" height="16" rx="4" fill="#fff"/>'
    elif key == "blister":
        body = '<rect x="86" y="70" width="88" height="72" rx="12" fill="#dde7f1" stroke="#9db0c2" stroke-width="4"/><circle cx="106" cy="92" r="10" fill="#fff"/><circle cx="130" cy="92" r="10" fill="#fff"/><circle cx="154" cy="92" r="10" fill="#fff"/><circle cx="118" cy="118" r="10" fill="#fff"/><circle cx="142" cy="118" r="10" fill="#fff"/>'
    elif key == "paint":
        body = '<rect x="98" y="70" width="64" height="72" rx="10" fill="#8aa4d8" stroke="#5a78b7" stroke-width="4"/><rect x="92" y="58" width="76" height="18" rx="6" fill="#dbe3ef"/><path d="M104 138c14-16 30-16 44 0 10 12 26 12 34 0v22H90v-16c4-10 8-14 14-6Z" fill="#ff8dbb"/>'
    elif key == "bulb":
        body = '<path d="M130 56c28 0 48 20 48 44 0 16-10 28-18 36-6 6-10 14-10 22h-40c0-8-4-16-10-22-8-8-18-20-18-36 0-24 20-44 48-44Z" fill="#ffd85a" stroke="#c89d17" stroke-width="4"/><rect x="110" y="156" width="40" height="18" rx="6" fill="#8b95a2"/>'
    elif key == "spray":
        body = '<rect x="104" y="64" width="52" height="90" rx="12" fill="#9fd4ff" stroke="#4b9de0" stroke-width="4"/><rect x="112" y="48" width="24" height="16" rx="4" fill="#67717f"/><path d="M156 72h18" stroke="#67717f" stroke-width="6" stroke-linecap="round"/><path d="M182 66l22-8M182 72h24M182 78l22 8" stroke="#8fc6ff" stroke-width="4" stroke-linecap="round"/>'
    elif key == "cable":
        body = '<path d="M92 118c18-42 68-42 86 0 8 18 0 34-18 34-14 0-18-12-18-22v-34h-24v40" fill="none" stroke="#545e6d" stroke-width="10" stroke-linecap="round"/><rect x="144" y="120" width="12" height="20" rx="4" fill="#9fb1c4"/>'
    elif key == "phone":
        body = '<rect x="104" y="50" width="52" height="110" rx="12" fill="#2a394a"/><rect x="112" y="64" width="36" height="72" rx="6" fill="#b8e2ff"/><circle cx="130" cy="146" r="4" fill="#bfc8d0"/>'
    elif key == "cartridge":
        body = '<rect x="92" y="76" width="76" height="62" rx="12" fill="#2f2f36"/><rect x="102" y="88" width="56" height="18" rx="6" fill="#7a88a1"/><path d="M108 120h44" stroke="#8b5cff" stroke-width="8" stroke-linecap="round"/>'
    elif key == "chemical":
        body = '<rect x="106" y="54" width="48" height="20" rx="8" fill="#6c8aa3"/><rect x="96" y="72" width="68" height="82" rx="18" fill="#ffeb8c" stroke="#d4ad27" stroke-width="4"/><path d="M130 92l10 18h-20ZM130 118l10 18h-20Z" fill="#444"/>'
    elif key == "tubelight":
        body = '<rect x="54" y="98" width="152" height="20" rx="10" fill="#f2f7fb" stroke="#b6c7d5" stroke-width="4"/><rect x="44" y="100" width="10" height="16" rx="4" fill="#8e9cab"/><rect x="206" y="100" width="10" height="16" rx="4" fill="#8e9cab"/>'
    elif key == "coinbattery":
        body = '<circle cx="130" cy="106" r="42" fill="#d8e0e8" stroke="#97a3ae" stroke-width="4"/><line x1="110" y1="106" x2="150" y2="106" stroke="#6d7883" stroke-width="6" stroke-linecap="round"/><line x1="130" y1="86" x2="130" y2="126" stroke="#6d7883" stroke-width="6" stroke-linecap="round"/>'
    elif key == "thermometer":
        body = '<rect x="120" y="54" width="20" height="82" rx="10" fill="#f5f7fb" stroke="#a7b3c0" stroke-width="4"/><circle cx="130" cy="148" r="20" fill="#ff6d6d"/><rect x="124" y="88" width="12" height="44" rx="6" fill="#ff6d6d"/>'
    elif key == "polish":
        body = '<rect x="112" y="48" width="36" height="28" rx="6" fill="#444d5a"/><rect x="100" y="76" width="60" height="72" rx="12" fill="#ff8dbb" stroke="#d45a8d" stroke-width="4"/>'
    elif key == "chip":
        body = '<rect x="96" y="72" width="68" height="68" rx="10" fill="#3b6f72"/><rect x="112" y="88" width="36" height="36" rx="6" fill="#88d0c9"/>' \
               '<path d="M96 88H80M96 104H80M96 120H80M164 88h16M164 104h16M164 120h16M112 72V56M128 72V56M144 72V56M112 140v16M128 140v16M144 140v16" stroke="#6aa5a4" stroke-width="4" stroke-linecap="round"/>'
    else:
        body = '<circle cx="130" cy="106" r="44" fill="#d8edf7" stroke="#93b6ca" stroke-width="4"/>'

    return svg_body(body)


def _fact_article_config(theme: str) -> dict[str, object]:
    return FACT_ARTICLE_LIBRARY.get(theme, DEFAULT_FACT_ARTICLE)


def render_fact_svg(fact: dict[str, object], variant: str = "hero") -> str:
    config = _fact_article_config(str(fact["theme"]))
    accent = str(config["accent"])
    eyebrow = html.escape(str(config["eyebrow"]))
    title = html.escape(str(config["title"]))
    variant_name = {
        "hero": "Article View",
        "routine": "Daily Routine",
        "impact": "Why It Works",
    }.get(variant, "Eco View")
    variant_caption = html.escape(variant_name)
    art_key = str(config["art_key"])

    if art_key == "compost":
        body = """
<g>
  <ellipse cx="130" cy="176" rx="78" ry="18" fill="#d8efe2"/>
  <rect x="76" y="88" width="108" height="76" rx="18" fill="#81593a"/>
  <rect x="84" y="76" width="92" height="24" rx="12" fill="#9b6b45"/>
  <path d="M104 88c12-24 22-24 34 0" fill="none" stroke="#65d66f" stroke-width="6" stroke-linecap="round"/>
  <path d="M136 88c10-22 20-22 30 0" fill="none" stroke="#78c850" stroke-width="6" stroke-linecap="round"/>
  <path d="M95 112c20-20 34-22 46-4-16 28-42 38-56 20-6-6-4-12 10-16Z" fill="#ffd44d" stroke="#c49200" stroke-width="3"/>
  <path d="M146 112c8-20 30-24 38-8-6 22-28 36-46 34-10-2-10-12 8-26Z" fill="#ff9f66" stroke="#d96f2f" stroke-width="3"/>
  <g>
    <path d="M92 62c14-20 34-20 40 0-16 8-28 8-40 0Z" fill="#65d66f"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -6; 0 0" dur="4.8s" repeatCount="indefinite"/>
  </g>
  <g>
    <path d="M148 56c14-18 30-16 34 4-14 6-26 4-34-4Z" fill="#4caf50"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -8; 0 0" dur="5.4s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "paper":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="74" ry="18" fill="#e9edf0"/>
  <rect x="88" y="72" width="84" height="102" rx="14" fill="#ffe7a3" stroke="#e3b23c" stroke-width="4"/>
  <rect x="104" y="86" width="84" height="102" rx="14" fill="white" stroke="#c6d7ef" stroke-width="4"/>
  <path d="M120 108h44M120 126h52M120 144h46M120 162h36" stroke="#7aa6d9" stroke-width="4" stroke-linecap="round"/>
  <rect x="76" y="122" width="48" height="36" rx="10" fill="#55c8ff" opacity="0.8"/>
  <path d="M84 140h32" stroke="white" stroke-width="4" stroke-linecap="round"/>
  <g>
    <rect x="64" y="90" width="34" height="26" rx="8" fill="#ffd666" opacity="0.8"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -5; 0 0" dur="4.2s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "water":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="78" ry="18" fill="#dff3ff"/>
  <path d="M70 88h76a18 18 0 0 1 18 18v8h-22v-6a8 8 0 0 0-8-8H70Z" fill="#7f9db5"/>
  <rect x="92" y="114" width="22" height="46" rx="10" fill="#9abed1"/>
  <path d="M126 118c0 18 12 26 12 42 0 10-8 18-18 18s-18-8-18-18c0-16 12-24 24-42Z" fill="#55c8ff" opacity="0.9">
    <animate attributeName="d" dur="3.6s" repeatCount="indefinite"
      values="M126 118c0 18 12 26 12 42 0 10-8 18-18 18s-18-8-18-18c0-16 12-24 24-42Z;
              M126 112c0 16 14 24 14 40 0 12-8 20-20 20s-20-8-20-20c0-16 14-24 26-40Z;
              M126 118c0 18 12 26 12 42 0 10-8 18-18 18s-18-8-18-18c0-16 12-24 24-42Z"/>
  </path>
  <circle cx="168" cy="140" r="12" fill="#b7ebff">
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -8; 0 0" dur="4.8s" repeatCount="indefinite"/>
  </circle>
</g>
"""
    elif art_key == "energy":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="76" ry="18" fill="#f8efcf"/>
  <path d="M118 66c-20 6-34 24-34 46 0 22 16 38 46 38s46-16 46-38c0-22-14-40-34-46" fill="#ffd666" stroke="#f1b400" stroke-width="4"/>
  <rect x="118" y="144" width="24" height="18" rx="6" fill="#6d5d44"/>
  <rect x="110" y="160" width="40" height="12" rx="6" fill="#8f7a58"/>
  <path d="M128 82l-12 22h14l-8 20 24-28h-14l10-14" fill="#ff8c66"/>
  <rect x="72" y="112" width="28" height="54" rx="12" fill="#e6eef3" stroke="#9cb6c5" stroke-width="4"/>
  <circle cx="86" cy="128" r="5" fill="#6bcf73"/>
  <rect x="82" y="138" width="8" height="18" rx="4" fill="#6d7f88"/>
  <g>
    <circle cx="186" cy="92" r="8" fill="#ffe08b" opacity="0.95"/>
    <circle cx="200" cy="110" r="5" fill="#ffd666" opacity="0.85"/>
    <circle cx="174" cy="114" r="4" fill="#ffd666" opacity="0.8"/>
    <animateTransform attributeName="transform" type="scale" values="1;1.08;1" dur="3.6s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "bottle":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="74" ry="18" fill="#e4f7ff"/>
  <rect x="110" y="58" width="40" height="22" rx="8" fill="#1d9bf0"/>
  <rect x="94" y="78" width="72" height="92" rx="28" fill="#aee7ff" stroke="#1d9bf0" stroke-width="4"/>
  <rect x="106" y="100" width="48" height="40" rx="18" fill="white" opacity="0.74"/>
  <path d="M122 94c0 10 8 16 8 24 0 6-4 10-10 10s-10-4-10-10c0-8 8-14 12-24Z" fill="#55c8ff"/>
  <g>
    <circle cx="74" cy="110" r="10" fill="#c8f1ff"/>
    <circle cx="190" cy="126" r="14" fill="#dff6ff"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -6; 0 0" dur="4.6s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "bag":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="74" ry="18" fill="#f7eadf"/>
  <path d="M86 84h88l10 84H76Z" fill="#f5c26b" stroke="#c98a2f" stroke-width="4"/>
  <path d="M104 86c0-18 12-30 26-30s26 12 26 30" fill="none" stroke="#8b5e34" stroke-width="6" stroke-linecap="round"/>
  <path d="M124 112c12-18 30-12 32 8-14 12-28 18-42 18-10-10-8-22 10-26Z" fill="#65d66f"/>
  <circle cx="102" cy="128" r="10" fill="#ff8c66"/>
  <circle cx="154" cy="128" r="10" fill="#55c8ff"/>
  <g>
    <path d="M196 94c10-12 22-10 26 4-10 6-18 6-26-4Z" fill="#6bcf73"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -7; 0 0" dur="5.1s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "glass":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="78" ry="18" fill="#dff8f5"/>
  <rect x="96" y="68" width="68" height="100" rx="18" fill="#dffaf3" stroke="#2a9d8f" stroke-width="4"/>
  <rect x="102" y="58" width="56" height="18" rx="8" fill="#9be3db"/>
  <path d="M116 102c10-14 22-22 34-24" fill="none" stroke="white" stroke-width="5" stroke-linecap="round" opacity="0.9"/>
  <path d="M76 120c18-24 54-24 72 0" fill="none" stroke="#2a9d8f" stroke-width="8" stroke-linecap="round"/>
  <path d="M144 120l-10-12" stroke="#2a9d8f" stroke-width="8" stroke-linecap="round"/>
  <path d="M186 132c-18 24-54 24-72 0" fill="none" stroke="#55c8ff" stroke-width="8" stroke-linecap="round"/>
  <path d="M118 132l10 12" stroke="#55c8ff" stroke-width="8" stroke-linecap="round"/>
  <g>
    <circle cx="186" cy="96" r="10" fill="#c8f7f2"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -8; 0 0" dur="4.4s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "metal":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="78" ry="18" fill="#e9eef3"/>
  <ellipse cx="106" cy="100" rx="28" ry="12" fill="#dbe7ef" stroke="#7b96aa" stroke-width="4"/>
  <rect x="78" y="100" width="56" height="58" fill="#c6d7e4" stroke="#7b96aa" stroke-width="4"/>
  <ellipse cx="106" cy="158" rx="28" ry="12" fill="#b9ccd9" stroke="#7b96aa" stroke-width="4"/>
  <ellipse cx="154" cy="112" rx="26" ry="10" fill="#dde8ef" stroke="#7b96aa" stroke-width="4"/>
  <rect x="128" y="112" width="52" height="46" fill="#d3e1ea" stroke="#7b96aa" stroke-width="4"/>
  <ellipse cx="154" cy="158" rx="26" ry="10" fill="#bfced8" stroke="#7b96aa" stroke-width="4"/>
  <circle cx="188" cy="88" r="14" fill="#ffd666" opacity="0.86">
    <animateTransform attributeName="transform" type="rotate" values="0 188 88;360 188 88" dur="8s" repeatCount="indefinite"/>
  </circle>
</g>
"""
    elif art_key == "ewaste":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="78" ry="18" fill="#e8eef2"/>
  <rect x="84" y="62" width="60" height="106" rx="14" fill="#314552"/>
  <rect x="92" y="72" width="44" height="76" rx="10" fill="#88d0c9"/>
  <circle cx="114" cy="156" r="4" fill="#c7d6df"/>
  <rect x="152" y="84" width="42" height="54" rx="8" fill="#58717e"/>
  <path d="M152 98h-12M152 110h-12M152 122h-12M194 98h12M194 110h12M194 122h12M166 84V72M180 84V72M166 138v12M180 138v12" stroke="#8eb0bf" stroke-width="4" stroke-linecap="round"/>
  <path d="M70 142c14-12 24-14 34-6 8 8 16 8 24 0" fill="none" stroke="#55c8ff" stroke-width="5" stroke-linecap="round">
    <animate attributeName="stroke-dasharray" values="0 120;40 80;0 120" dur="4.5s" repeatCount="indefinite"/>
  </path>
</g>
"""
    elif art_key == "battery":
        body = """
<g>
  <ellipse cx="130" cy="178" rx="78" ry="18" fill="#fde5e5"/>
  <rect x="78" y="92" width="104" height="68" rx="18" fill="#fff4f4" stroke="#f94144" stroke-width="4"/>
  <rect x="106" y="72" width="48" height="26" rx="10" fill="#f94144"/>
  <rect x="96" y="108" width="20" height="34" rx="8" fill="#ffd666"/>
  <rect x="120" y="108" width="20" height="34" rx="8" fill="#9fe5ff"/>
  <rect x="144" y="108" width="20" height="34" rx="8" fill="#a7e4a0"/>
  <path d="M112 118h6M109 121h12" stroke="#7f5d00" stroke-width="3" stroke-linecap="round"/>
  <path d="M126 118h8" stroke="#126b88" stroke-width="3" stroke-linecap="round"/>
  <path d="M150 118h6M147 121h12" stroke="#2a7f2a" stroke-width="3" stroke-linecap="round"/>
  <g>
    <circle cx="188" cy="100" r="8" fill="#ffd6d6"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -8; 0 0" dur="4.3s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "tree":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#dfeecf"/>
  <rect x="118" y="112" width="24" height="48" rx="10" fill="#8b5e34"/>
  <circle cx="110" cy="102" r="28" fill="#70c86b"/>
  <circle cx="140" cy="92" r="30" fill="#58c94c"/>
  <circle cx="156" cy="114" r="24" fill="#86d97d"/>
  <path d="M84 164c16-16 30-18 44-4" fill="none" stroke="#4caf50" stroke-width="5" stroke-linecap="round"/>
  <path d="M88 166c8-18 18-24 28-18-2 14-12 24-28 18Z" fill="#7edb74"/>
  <g>
    <circle cx="182" cy="74" r="12" fill="#ffe08b"/>
    <animateTransform attributeName="transform" type="rotate" values="0 182 74;360 182 74" dur="12s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "transport":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#e5eef6"/>
  <path d="M70 152h120" stroke="#7aa6d9" stroke-width="8" stroke-linecap="round"/>
  <circle cx="102" cy="146" r="22" fill="none" stroke="#277da1" stroke-width="6"/>
  <circle cx="158" cy="146" r="22" fill="none" stroke="#277da1" stroke-width="6"/>
  <path d="M102 146l24-32h22l10 32h-22l-12-18-18 18Z" fill="none" stroke="#43aa8b" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M130 104h20" stroke="#43aa8b" stroke-width="6" stroke-linecap="round"/>
  <path d="M186 106c10-12 18-14 28-8" fill="none" stroke="#ff8c66" stroke-width="5" stroke-linecap="round">
    <animateTransform attributeName="transform" type="translate" values="0 0; 6 0; 0 0" dur="3.8s" repeatCount="indefinite"/>
  </path>
</g>
"""
    elif art_key == "meal":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="80" ry="18" fill="#e8f0d2"/>
  <circle cx="122" cy="120" r="42" fill="#fff8e7" stroke="#d6c58e" stroke-width="4"/>
  <path d="M100 120c10-14 22-18 38-16" fill="none" stroke="#90be6d" stroke-width="6" stroke-linecap="round"/>
  <circle cx="146" cy="114" r="10" fill="#ff9f66"/>
  <circle cx="116" cy="134" r="8" fill="#55c8ff"/>
  <path d="M174 88h24M174 108h24M174 128h18" stroke="#7aa866" stroke-width="5" stroke-linecap="round"/>
  <path d="M78 90v52M70 98h16M70 114h16M70 130h16" stroke="#b58f5f" stroke-width="5" stroke-linecap="round"/>
</g>
"""
    elif art_key == "donate":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#f6e8d9"/>
  <rect x="82" y="96" width="96" height="68" rx="14" fill="#d9a86c" stroke="#b67c35" stroke-width="4"/>
  <path d="M82 110h96" stroke="#b67c35" stroke-width="4"/>
  <path d="M116 126c0-10 8-18 18-18s18 8 18 18c0 18-18 26-18 26s-18-8-18-26Z" fill="#ff6f91"/>
  <rect x="96" y="78" width="24" height="18" rx="6" fill="#55c8ff"/>
  <rect x="140" y="76" width="26" height="20" rx="6" fill="#ffd666"/>
  <g>
    <circle cx="188" cy="104" r="8" fill="#ffe7a3"/>
    <animateTransform attributeName="transform" type="translate" values="0 0; 0 -7; 0 0" dur="4.6s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "repair":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#ece3d8"/>
  <path d="M86 150l28-28 12 12-28 28c-6 6-18 4-22-2-4-6-2-16 10-10Z" fill="#bc6c25"/>
  <path d="M120 118c16-18 36-28 56-24-8 10-8 22 0 32-20 4-40-6-56-24Z" fill="#d4a373"/>
  <circle cx="168" cy="130" r="24" fill="none" stroke="#7f5539" stroke-width="6"/>
  <path d="M168 98v16M168 146v16M136 130h16M184 130h16M146 108l10 10M180 142l10 10M146 152l10-10M180 118l10-10" stroke="#7f5539" stroke-width="5" stroke-linecap="round"/>
</g>
"""
    elif art_key == "litter":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#d9f0dc"/>
  <path d="M58 160h144" stroke="#8bc98f" stroke-width="10" stroke-linecap="round"/>
  <rect x="158" y="92" width="34" height="62" rx="10" fill="#4caf50"/>
  <rect x="164" y="78" width="22" height="18" rx="6" fill="#357a38"/>
  <path d="M104 118l10 12M116 118l-10 12M96 144h10M126 142h10" stroke="#ff8c66" stroke-width="5" stroke-linecap="round"/>
  <path d="M118 132c20 0 34-4 50-18" fill="none" stroke="#3a86ff" stroke-width="6" stroke-linecap="round">
    <animate attributeName="stroke-dasharray" values="0 120;50 70;0 120" dur="4.2s" repeatCount="indefinite"/>
  </path>
</g>
"""
    elif art_key == "cleanup":
        body = """
<g>
  <ellipse cx="130" cy="184" rx="82" ry="16" fill="#dbeed8"/>
  <path d="M92 118c18-12 42-12 60 0l18 48H74Z" fill="#86d97d" stroke="#4caf50" stroke-width="4"/>
  <path d="M102 110c0-10 8-18 18-18M158 110c0-10-8-18-18-18" fill="none" stroke="#4caf50" stroke-width="5" stroke-linecap="round"/>
  <rect x="78" y="120" width="18" height="34" rx="8" fill="#ffd6a5"/>
  <rect x="164" y="120" width="18" height="34" rx="8" fill="#ffd6a5"/>
  <circle cx="118" cy="142" r="6" fill="white"/>
  <circle cx="142" cy="136" r="6" fill="#55c8ff"/>
  <g>
    <path d="M196 100l6 12 12 6-12 6-6 12-6-12-12-6 12-6Z" fill="#ffd666"/>
    <animateTransform attributeName="transform" type="scale" values="1;1.08;1" dur="3.4s" repeatCount="indefinite"/>
  </g>
</g>
"""
    elif art_key == "packaging":
        body = """
<g>
  <ellipse cx="130" cy="182" rx="82" ry="18" fill="#f6e7de"/>
  <path d="M92 98l38-22 38 22-38 22Z" fill="#f4b183"/>
  <path d="M92 98v42l38 22 38-22V98" fill="#ef9f6d" stroke="#d17b45" stroke-width="4"/>
  <path d="M130 120c14-18 32-14 36 6-14 12-26 16-40 14-8-8-8-18 4-20Z" fill="#90be6d"/>
  <path d="M70 132c14-10 24-12 32-6" fill="none" stroke="#55c8ff" stroke-width="5" stroke-linecap="round"/>
  <path d="M172 120c14-8 24-8 34 4" fill="none" stroke="#ff8c66" stroke-width="5" stroke-linecap="round"/>
</g>
"""
    elif art_key == "river":
        body = """
<g>
  <ellipse cx="130" cy="184" rx="82" ry="16" fill="#dff0f6"/>
  <path d="M54 150c18-12 34-12 52 0s34 12 52 0 34-12 52 0" fill="none" stroke="#55c8ff" stroke-width="8" stroke-linecap="round"/>
  <path d="M54 166c18-12 34-12 52 0s34 12 52 0 34-12 52 0" fill="none" stroke="#118ab2" stroke-width="8" stroke-linecap="round"/>
  <rect x="88" y="74" width="40" height="72" rx="10" fill="#90a4ae"/>
  <rect x="96" y="60" width="24" height="18" rx="8" fill="#6d7f88"/>
  <path d="M150 76l42 42M192 76l-42 42" stroke="#f94144" stroke-width="8" stroke-linecap="round"/>
  <circle cx="171" cy="97" r="36" fill="none" stroke="#f94144" stroke-width="6"/>
</g>
"""
    else:
        body = """
<g>
  <circle cx="130" cy="118" r="46" fill="#dff7ea" stroke="#43aa8b" stroke-width="4"/>
  <path d="M130 74c18 0 32 8 42 22-10 14-24 24-42 24-18 0-32-10-42-24 10-14 24-22 42-22Z" fill="#90be6d"/>
  <path d="M130 120c0 18-10 32-24 42 18 4 36 2 48-6 10-6 18-18 20-32" fill="#55c8ff" opacity="0.8"/>
  <g>
    <circle cx="186" cy="86" r="10" fill="#ffd666"/>
    <animateTransform attributeName="transform" type="rotate" values="0 186 86;360 186 86" dur="10s" repeatCount="indefinite"/>
  </g>
</g>
"""

    if variant == "routine":
        overlay = """
<g opacity="0.95">
  <path d="M72 188h116" stroke="#9db6c8" stroke-width="4" stroke-dasharray="6 8" stroke-linecap="round"/>
  <circle cx="82" cy="188" r="12" fill="#55c8ff"/>
  <circle cx="130" cy="188" r="12" fill="#ffd666"/>
  <circle cx="178" cy="188" r="12" fill="#65d66f"/>
  <text x="82" y="192" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="11" fill="white">1</text>
  <text x="130" y="192" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="11" fill="#6a5200">2</text>
  <text x="178" y="192" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="11" fill="white">3</text>
</g>
"""
    elif variant == "impact":
        overlay = f"""
<g>
  <path d="M198 54l7 13 13 7-13 7-7 13-7-13-13-7 13-7Z" fill="{accent}" opacity="0.92">
    <animateTransform attributeName="transform" type="scale" values="1;1.08;1" dur="3.2s" repeatCount="indefinite"/>
  </path>
  <circle cx="74" cy="64" r="18" fill="white" stroke="{accent}" stroke-width="4"/>
  <path d="M66 64l6 6 12-14" fill="none" stroke="{accent}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</g>
"""
    else:
        overlay = f"""
<g opacity="0.9">
  <circle cx="68" cy="68" r="16" fill="{accent}" opacity="0.12"/>
  <circle cx="192" cy="62" r="14" fill="{accent}" opacity="0.18"/>
  <circle cx="210" cy="138" r="10" fill="{accent}" opacity="0.1"/>
</g>
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 220" role="img" aria-label="{title}">
<rect width="260" height="220" rx="28" fill="#f7fdff"/>
<rect width="260" height="220" rx="28" fill="url(#factGrad)"/>
<defs>
  <linearGradient id="factGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#ffffff"/>
    <stop offset="100%" stop-color="#edf9f4"/>
  </linearGradient>
</defs>
<rect x="18" y="18" width="224" height="184" rx="24" fill="white" opacity="0.94"/>
<rect x="28" y="28" width="76" height="26" rx="13" fill="{accent}" opacity="0.15"/>
<text x="66" y="45" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="12" fill="#16332b">{eyebrow}</text>
{overlay}
{body}
<rect x="28" y="186" width="204" height="18" rx="9" fill="{accent}" opacity="0.12"/>
<text x="130" y="199" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="12" fill="#2a4a42">{variant_caption}</text>
</svg>"""


class WasteWebApp:
    def __init__(self, repo: MultiDbRepository) -> None:
        self.repo = repo

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "/")
        if path.startswith("/assets/"):
            return self._serve_asset(path, start_response)
        if path.startswith("/graphics/item/"):
            return self._serve_item_graphic(path, start_response)
        if path.startswith("/graphics/fact/"):
            return self._serve_fact_graphic(path, environ, start_response)

        session_id, session, is_new = self._get_session(environ)
        headers = [("Content-Type", "text/html; charset=utf-8")]
        if is_new:
            headers.append(("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly"))

        try:
            method = environ.get("REQUEST_METHOD", "GET").upper()
            if method == "POST":
                form = self._parse_form(environ)
                redirect = self._handle_post(path, form, session, headers)
                if redirect is not None:
                    return redirect(start_response)

            page = self._handle_get(path, environ, session)
            start_response("200 OK", headers)
            return [page.encode("utf-8")]
        except Exception as exc:
            start_response("500 Internal Server Error", headers)
            return [self._render_error(str(exc)).encode("utf-8")]

    def _serve_asset(self, path: str, start_response):
        asset_root = ASSETS_DIR.resolve()
        asset_path = (asset_root / path.removeprefix("/assets/")).resolve()
        if asset_root not in asset_path.parents and asset_path != asset_root:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Asset not found"]
        if not asset_path.is_file():
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Asset not found"]

        mime_type, _ = mimetypes.guess_type(asset_path.name)
        start_response("200 OK", [("Content-Type", mime_type or "application/octet-stream")])
        return [asset_path.read_bytes()]

    def _serve_item_graphic(self, path: str, start_response):
        try:
            item_id = int(path.removeprefix("/graphics/item/").removesuffix(".svg"))
        except ValueError:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Graphic not found"]

        item = self.repo.get_item_by_id(item_id)
        if item is None:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Graphic not found"]

        start_response("200 OK", [("Content-Type", "image/svg+xml; charset=utf-8")])
        return [render_item_svg(item).encode("utf-8")]

    def _serve_fact_graphic(self, path: str, environ, start_response):
        try:
            fact_id = int(path.removeprefix("/graphics/fact/").removesuffix(".svg"))
        except ValueError:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Graphic not found"]

        fact = self.repo.get_fact_by_id(fact_id)
        if fact is None:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Graphic not found"]

        variant = parse_qs(environ.get("QUERY_STRING", "")).get("variant", ["hero"])[0]
        start_response("200 OK", [("Content-Type", "image/svg+xml; charset=utf-8")])
        return [render_fact_svg(fact, variant).encode("utf-8")]

    def _get_session(self, environ):
        jar = cookies.SimpleCookie()
        jar.load(environ.get("HTTP_COOKIE", ""))
        session_id = jar["session_id"].value if "session_id" in jar else None
        if not session_id or session_id not in SESSIONS:
            session_id = secrets.token_hex(16)
            SESSIONS[session_id] = {}
            return session_id, SESSIONS[session_id], True
        return session_id, SESSIONS[session_id], False

    def _parse_form(self, environ) -> dict[str, list[str]]:
        length = int((environ.get("CONTENT_LENGTH", "0") or "0").strip())
        raw = environ["wsgi.input"].read(length).decode("utf-8") if length else ""
        return parse_qs(raw)

    def _redirect(self, location: str, headers):
        def responder(start_response):
            response_headers = list(headers)
            response_headers.append(("Location", location))
            start_response("303 See Other", response_headers)
            return [b""]

        return responder

    def _handle_post(self, path: str, form: dict[str, list[str]], session: dict, headers):
        if path == "/save-name":
            username = form.get("username", [""])[0].strip()
            if username:
                self.repo.set_state("username", username)
            return self._redirect("/", headers)

        if path == "/game/start":
            self._reset_game(session)
            return self._redirect("/game", headers)

        if path == "/game/answer":
            self._answer_game(form.get("category", [""])[0], session)
            return self._redirect("/game", headers)

        if path == "/quiz/start":
            self._reset_quiz(session)
            return self._redirect("/quiz", headers)

        if path == "/quiz/answer":
            self._answer_quiz(form.get("choice", ["-1"])[0], session)
            return self._redirect("/quiz", headers)

        if path == "/quiz/next":
            self._advance_quiz(session)
            return self._redirect("/quiz", headers)

        return None

    def _handle_get(self, path: str, environ, session: dict) -> str:
        if path == "/":
            return self._render_dashboard()
        if path == "/finder":
            query = parse_qs(environ.get("QUERY_STRING", "")).get("item", [""])[0]
            return self._render_finder(query)
        if path == "/game":
            if "game_ids" not in session:
                self._reset_game(session)
            return self._render_game(session)
        if path == "/quiz":
            if "quiz_ids" not in session:
                self._reset_quiz(session)
            return self._render_quiz(session)
        if path == "/learn":
            return self._render_learn(session)
        return self._layout(
            "Not Found",
            "none",
            """
            <div class="card">
                <h2 class="title">Page not found</h2>
                <p class="lead">Use the navigation above to jump back into the project.</p>
            </div>
            """,
        )

    def _daily_tip(self) -> str:
        return ECO_TIPS[date.today().toordinal() % len(ECO_TIPS)]

    def _art_path(self, page_name: str) -> str:
        return f"/assets/{PAGE_ART[page_name]}"

    def _item_label(self, item: dict[str, object]) -> str:
        return str(item["base_name"]).title()

    def _fact_details(self, fact: dict[str, object]) -> dict[str, str]:
        theme = str(fact["theme"])
        fact_text = str(fact["text"]).strip()
        sentence = fact_text[:-1] if fact_text.endswith(".") else fact_text
        remainder = sentence[len(theme):].strip() if sentence.startswith(theme) else sentence
        context = ""
        benefit = ""

        for candidate in FACT_BENEFITS:
            if remainder.endswith(candidate):
                benefit = candidate
                context = remainder[: -len(candidate)].strip()
                break

        if not context:
            for candidate in FACT_CONTEXTS:
                if remainder.startswith(candidate):
                    context = candidate
                    benefit = remainder[len(candidate):].strip()
                    break

        if not context:
            context = "in daily life"
        if not benefit:
            benefit = "supports better environmental choices"

        return {
            "theme": theme,
            "fact_text": fact_text,
            "sentence": sentence,
            "context": context,
            "benefit": benefit,
        }

    def _fact_article_actions(self, fact_id: int, theme_phrase: str, context: str, benefit: str) -> list[str]:
        openers = [
            "Look closely {context} and find the moment where {theme_phrase} can replace a wasteful default.",
            "Picture a normal routine {context} and identify the point where {theme_phrase} makes the biggest difference.",
            "Treat the routine {context} like a real-life case study and notice where {theme_phrase} belongs in the flow of the day.",
        ]
        practical_steps = [
            "Choose one practical move that shows how this choice {benefit}.",
            "Turn the idea into one visible action so the habit clearly {benefit}.",
            "Anchor the article in one concrete decision that proves this habit {benefit}.",
        ]
        closers = [
            "Repeat that version often enough that {theme_phrase} starts to feel built into the routine.",
            "Stay with the same move until {theme_phrase} feels natural in that setting rather than added on.",
            "Once the step is easy to repeat, {theme_phrase} stops being advice and becomes part of the day.",
        ]
        opener = openers[fact_id % len(openers)].format(context=context, theme_phrase=theme_phrase)
        practical = practical_steps[(fact_id // 2) % len(practical_steps)].format(benefit=benefit)
        closer = closers[(fact_id // 3) % len(closers)].format(theme_phrase=theme_phrase)
        return [opener, practical, closer]

    def _fact_article_payload(self, fact: dict[str, object]) -> dict[str, object]:
        details = self._fact_details(fact)
        theme = details["theme"]
        context = details["context"]
        benefit = details["benefit"]
        fact_text = details["fact_text"]
        sentence = details["sentence"]
        config = _fact_article_config(theme)
        fact_id = int(fact["id"])
        theme_phrase = theme[:1].lower() + theme[1:] if theme else "small eco habits"
        summary = (
            f"{config['summary']} This tab looks specifically at how {theme_phrase} works {context} "
            f"and why that version of the habit {benefit}."
        )
        impact = (
            f"{config['impact']} In this article, the clearest outcome is that the choice {benefit}, "
            f"which gives this tab its own angle even when the wider theme stays the same."
        )
        closing = (
            f"This version stays grounded {context}, so the article is not just repeating the theme. "
            f"It is showing one distinct way the habit {benefit}."
        )
        return {
            "id": fact_id,
            "theme": f"{theme} | {context}",
            "eyebrow": str(config["eyebrow"]),
            "title": sentence,
            "summary": summary,
            "impact": impact,
            "closing": closing,
            "fact_text": fact_text,
            "actions": self._fact_article_actions(fact_id, theme_phrase, context, benefit),
            "stats": [
                {"label": "Habit Focus", "text": f"This tab stays centered on {theme_phrase}."},
                {"label": "Where It Happens", "text": f"The article is grounded {context}, which changes the situation around the habit."},
                {"label": "Main Result", "text": f"The unique payoff here is that the habit {benefit}."},
            ],
            "accent": str(config["accent"]),
            "hero_image": {
                "src": f"/graphics/fact/{fact_id}.svg?variant=hero",
                "alt": f"{sentence} illustration",
            },
            "gallery": [
                {
                    "src": f"/graphics/fact/{fact_id}.svg?variant=routine",
                    "alt": f"{sentence} routine illustration",
                    "label": "Routine",
                    "note": f"This panel shows how the habit can fit naturally {context}.",
                },
                {
                    "src": f"/graphics/fact/{fact_id}.svg?variant=impact",
                    "alt": f"{sentence} impact illustration",
                    "label": "Impact",
                    "note": f"This panel focuses on why the choice {benefit} when it is repeated.",
                },
            ],
        }

    def _learn_page_script(self) -> str:
        return """
<script>
(() => {
  const overlay = document.getElementById("fact-article-overlay");
  const shell = document.getElementById("fact-article-shell");
  const dataNode = document.getElementById("fact-articles-data");
  if (!overlay || !shell || !dataNode) {
    return;
  }

  let articles = {};
  try {
    articles = JSON.parse(dataNode.textContent || "{}");
  } catch (error) {
    return;
  }

  const closeButton = document.getElementById("fact-article-close");
  const themeNode = document.getElementById("fact-article-theme");
  const titleNode = document.getElementById("fact-article-title");
  const summaryNode = document.getElementById("fact-article-summary");
  const quoteNode = document.getElementById("fact-article-quote");
  const impactNode = document.getElementById("fact-article-impact");
  const closingNode = document.getElementById("fact-article-closing");
  const heroImage = document.getElementById("fact-article-hero");
  const actionsNode = document.getElementById("fact-article-actions");
  const statsNode = document.getElementById("fact-article-stats");
  const galleryNode = document.getElementById("fact-article-gallery");
  let lastTrigger = null;

  function renderActions(actions) {
    actionsNode.replaceChildren();
    actions.forEach((action, index) => {
      const row = document.createElement("div");
      row.className = "article-action";

      const marker = document.createElement("span");
      marker.className = "article-action-index";
      marker.textContent = String(index + 1);

      const text = document.createElement("p");
      text.textContent = action;

      row.append(marker, text);
      actionsNode.appendChild(row);
    });
  }

  function renderStats(stats) {
    statsNode.replaceChildren();
    stats.forEach((stat) => {
      const card = document.createElement("div");
      card.className = "article-stat";

      const strong = document.createElement("strong");
      strong.textContent = stat.label;

      const text = document.createElement("p");
      text.textContent = stat.text;

      card.append(strong, text);
      statsNode.appendChild(card);
    });
  }

  function renderGallery(gallery) {
    galleryNode.replaceChildren();
    gallery.forEach((image) => {
      const figure = document.createElement("figure");
      figure.className = "article-thumb";

      const img = document.createElement("img");
      img.src = image.src;
      img.alt = image.alt;

      const caption = document.createElement("figcaption");
      const label = document.createElement("strong");
      label.textContent = image.label;
      const note = document.createElement("span");
      note.textContent = image.note;

      caption.append(label, note);
      figure.append(img, caption);
      galleryNode.appendChild(figure);
    });
  }

  function openArticle(article, trigger) {
    lastTrigger = trigger || document.activeElement;
    shell.style.setProperty("--article-accent", article.accent);
    themeNode.textContent = article.theme;
    titleNode.textContent = article.title;
    summaryNode.textContent = article.summary;
    quoteNode.textContent = article.fact_text;
    impactNode.textContent = article.impact;
    closingNode.textContent = article.closing;
    heroImage.src = article.hero_image.src;
    heroImage.alt = article.hero_image.alt;
    renderActions(article.actions || []);
    renderStats(article.stats || []);
    renderGallery(article.gallery || []);

    overlay.hidden = false;
    requestAnimationFrame(() => {
      overlay.classList.add("visible");
      document.body.classList.add("article-open");
      closeButton.focus();
    });
  }

  function closeArticle() {
    if (overlay.hidden || !overlay.classList.contains("visible")) {
      return;
    }
    overlay.classList.remove("visible");
    document.body.classList.remove("article-open");
    const restore = () => {
      overlay.hidden = true;
      heroImage.removeAttribute("src");
      if (lastTrigger && typeof lastTrigger.focus === "function") {
        lastTrigger.focus();
      }
    };
    overlay.addEventListener("transitionend", restore, { once: true });
  }

  document.querySelectorAll("[data-fact-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const article = articles[button.dataset.factId];
      if (article) {
        openArticle(article, button);
      }
    });
  });

  overlay.addEventListener("click", (event) => {
    if (event.target === overlay || event.target.closest("[data-close-fact-article]")) {
      closeArticle();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeArticle();
    }
  });
})();
</script>
"""

    def _reset_game(self, session: dict) -> None:
        session["game_ids"] = self.repo.get_random_sorting_ids(SESSION_ROUND_SIZE)
        session["game_index"] = 0
        session["game_feedback"] = ""

    def _current_game(self, session: dict):
        ids = session.get("game_ids", [])
        index = session.get("game_index", 0)
        if index >= len(ids):
            return None
        return self.repo.get_sorting_challenge(ids[index])

    def _answer_game(self, selected_category: str, session: dict) -> None:
        challenge = self._current_game(session)
        if challenge is None:
            session["game_feedback"] = "Start a new sorting round to continue."
            return

        if selected_category == challenge["correct_category"]:
            updated = self.repo.add_score(10)
            session["game_feedback"] = (
                f"Correct. {self._item_label(challenge['item'])} goes to the {challenge['item']['bin_name']}. "
                f"Score: {updated}."
            )
            session["game_index"] += 1
        else:
            session["game_feedback"] = f"Try again. Hint: {challenge['hint']}"

    def _reset_quiz(self, session: dict) -> None:
        session["quiz_ids"] = self.repo.get_random_quiz_ids(SESSION_ROUND_SIZE)
        session["quiz_index"] = 0
        session["quiz_feedback"] = "Quiz questions come from a separate database and focus on general eco knowledge."
        session["quiz_answered"] = False
        session["quiz_selected"] = None
        session["quiz_correct"] = None

    def _current_quiz(self, session: dict):
        ids = session.get("quiz_ids", [])
        index = session.get("quiz_index", 0)
        if index >= len(ids):
            return None
        return self.repo.get_quiz_question(ids[index])

    def _answer_quiz(self, choice_value: str, session: dict) -> None:
        question = self._current_quiz(session)
        if question is None or session.get("quiz_answered"):
            return

        try:
            selected = int(choice_value)
        except ValueError:
            return

        session["quiz_answered"] = True
        session["quiz_selected"] = selected
        session["quiz_correct"] = question["correct_index"]

        if selected == question["correct_index"]:
            updated = self.repo.add_score(5)
            session["quiz_feedback"] = f"Correct. Score: {updated}."
        else:
            session["quiz_feedback"] = "Not quite. Read the explanation and try the next question."

    def _advance_quiz(self, session: dict) -> None:
        if not session.get("quiz_answered"):
            return
        session["quiz_index"] += 1
        session["quiz_answered"] = False
        session["quiz_selected"] = None
        session["quiz_correct"] = None
        session["quiz_feedback"] = "Quiz questions come from a separate database and focus on general eco knowledge."

    def _layout(self, title: str, active: str, content: str) -> str:
        score = self.repo.get_score()
        username = html.escape(self.repo.get_state("username", "Eco Learner"))
        nav_items = [
            ("/", "dashboard", "Dashboard"),
            ("/finder", "finder", "Item Finder"),
            ("/game", "game", "Sorting Game"),
            ("/quiz", "quiz", "General Quiz"),
            ("/learn", "learn", "Learn"),
        ]
        nav_html = "".join(
            f'<a href="{href}" class="{"active" if key == active else ""}">{label}</a>'
            for href, key, label in nav_items
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}</style>
</head>
<body>
  <div class="topbar">
    <h1>Smart Waste Segregation and Recycling System</h1>
    <p>Sort bright, think green, and turn everyday cleanup into a planet-saving adventure.</p>
  </div>
  <div class="nav">{nav_html}</div>
  <div class="page">
    <div class="meta-row">
      <div class="meta-pill">Learner: <strong>{username}</strong></div>
      <div class="meta-pill">Score: <strong>{score}</strong></div>
    </div>
    {content}
  </div>
</body>
</html>"""

    def _render_dashboard(self) -> str:
        username = html.escape(self.repo.get_state("username", "Eco Learner"))
        score = self.repo.get_score()
        item_count = self.repo.get_item_count()
        game_count = self.repo.get_sorting_challenge_count()
        quiz_count = self.repo.get_quiz_question_count()

        guide_cards = []
        for category, details in CATEGORY_GUIDE.items():
            guide_cards.append(
                f"""
                <div class="guide-card" style="background:{details['color']}">
                    <h3>{html.escape(category)}</h3>
                    <p><strong>{html.escape(details['bin'])}</strong></p>
                    <p>{html.escape(details['summary'])}</p>
                </div>
                """
            )

        quick_cards = [
            ("linear-gradient(135deg, #ff9dc7, #ffc96b)", "/finder", "Search Items", "Find simple waste items from the waste item database."),
            ("linear-gradient(135deg, #4bc8ff, #7a8cff)", "/game", "Sorting Missions", "Use item graphics and different bins in the sorting game."),
            ("linear-gradient(135deg, #73e3a5, #47bf67)", "/quiz", "General Quiz", "Answer colorful eco trivia and smart green habit questions."),
        ]

        quick_html = "".join(
            f'<a class="quick-card" href="{href}" style="background:{bg}"><h3>{title}</h3><p>{desc}</p></a>'
            for bg, href, title, desc in quick_cards
        )
        tips_html = "".join(f"<li>{html.escape(tip)}</li>" for tip in RECYCLING_TIPS)

        return self._layout(
            "Dashboard",
            "dashboard",
            f"""
            <div class="page-hero">
              <div class="card">
                <div class="eyebrow">Project Overview</div>
                <h2 class="title">Welcome, {username}</h2>
                <p class="lead">This version uses separate databases, simple waste item names, a graphics-based sorting game, and a general eco quiz.</p>
                <form class="inline" method="post" action="/save-name" style="margin-top:18px;">
                  <input type="text" name="username" value="{username}" placeholder="Enter learner name">
                  <button class="primary" type="submit">Save Name</button>
                </form>
                <div class="stat-grid">
                  <div class="stat-bubble"><strong>{item_count:,}</strong> unique waste items</div>
                  <div class="stat-bubble"><strong>{game_count:,}</strong> sorting missions</div>
                  <div class="stat-bubble"><strong>{quiz_count:,}</strong> general quiz questions</div>
                  <div class="stat-bubble"><strong>{score}</strong> score after reset on launch</div>
                </div>
              </div>
              <div class="card hero-art-wrap">
                <img class="hero-art" src="{self._art_path('dashboard')}" alt="Dashboard illustration">
              </div>
            </div>
            <div class="card" style="margin-top:18px;">
              <div class="eyebrow">Color Guide</div>
              <h2 class="title">Waste categories</h2>
              <div class="grid">
                {''.join(guide_cards)}
              </div>
            </div>
            <div class="quick-grid" style="margin-top:18px;">
              {quick_html}
            </div>
            <div class="page-hero" style="margin-top:18px;">
              <div class="card">
                <div class="eyebrow">Daily Tip</div>
                <h2 class="title">Tiny action, big effect</h2>
                <p class="lead">{html.escape(self._daily_tip())}</p>
                <p class="tiny">Date: {date.today().isoformat()}</p>
              </div>
              <div class="card">
                <div class="eyebrow">Recycling Tips</div>
                <ul class="clean">{tips_html}</ul>
              </div>
            </div>
            """,
        )

    def _render_finder(self, query: str) -> str:
        item, suggestions = self.repo.search_item(query)
        result_html = """
        <div class="status">
          Enter a simple item name such as battery, paper, banana peel, or glass jar.
        </div>
        """
        if item:
            category = item["category"]
            color = CATEGORY_GUIDE[category]["color"]
            result_html = f"""
            <div class="result-panel">
              <img class="finder-art" src="/graphics/item/{item['id']}.svg" alt="{html.escape(self._item_label(item))}">
              <div>
                <p><strong>Item:</strong> {html.escape(self._item_label(item))}</p>
                <p><strong>Category:</strong> <span style="color:{color}; font-weight:700;">{html.escape(category)}</span></p>
                <p><strong>Bin:</strong> {html.escape(str(item['bin_name']))}</p>
                <p><strong>Disposal tip:</strong> {html.escape(str(item['disposal_tip']))}</p>
                <p><strong>Why it matters:</strong> {html.escape(str(item['learn_note']))}</p>
              </div>
            </div>
            """
        elif query.strip():
            chips = suggestions or []
            if chips:
                suggestion_html = "".join(
                    f'<a class="chip" href="/finder?item={quote_plus(str(s["base_name"]))}">{html.escape(str(s["base_name"]).title())}</a>'
                    for s in chips
                )
            else:
                suggestion_html = "".join(
                    f'<a class="chip" href="/finder?item={quote_plus(name)}">{html.escape(name.title())}</a>'
                    for name in ["battery", "paper", "banana peel", "plastic bottle", "glass jar"]
                )
            result_html = f"""
            <div class="status">
              <p><strong>No exact match found.</strong> Try one of these base item names:</p>
              <div class="chip-row" style="margin-top:12px;">{suggestion_html}</div>
            </div>
            """

        return self._layout(
            "Item Finder",
            "finder",
            f"""
            <div class="split-layout">
              <div class="card">
                <div class="eyebrow">Item Finder</div>
                <h2 class="title">Search the waste item database</h2>
                <p class="lead">The waste item database keeps names simple while still storing one million unique sample items.</p>
                <form class="inline" method="get" action="/finder" style="margin-top:18px;">
                  <input type="text" name="item" value="{html.escape(query)}" placeholder="Try: battery">
                  <button class="primary" type="submit">Find Item</button>
                </form>
                {result_html}
              </div>
              <div class="card hero-art-wrap">
                <img class="hero-art" src="{self._art_path('finder')}" alt="Finder illustration">
              </div>
            </div>
            """,
        )

    def _render_game(self, session: dict) -> str:
        challenge = self._current_game(session)
        feedback = html.escape(session.get("game_feedback", ""))
        feedback_html = f'<div class="status">{feedback}</div>' if feedback else ""

        if challenge is None:
            return self._layout(
                "Sorting Game",
                "game",
                f"""
                <div class="split-layout">
                  <div class="card">
                    <div class="eyebrow">Sorting Game</div>
                    <h2 class="title">Round complete</h2>
                    <p class="lead">You finished this set of sorting missions.</p>
                    <form method="post" action="/game/start" style="margin-top:18px;">
                      <button class="primary" type="submit">Start New Round</button>
                    </form>
                    {feedback_html}
                  </div>
                  <div class="card hero-art-wrap">
                    <img class="hero-art" src="{self._art_path('game')}" alt="Sorting illustration">
                  </div>
                </div>
                """,
            )

        item = challenge["item"]
        buttons = []
        for category, details in CATEGORY_GUIDE.items():
            buttons.append(
                f"""
                <form method="post" action="/game/answer">
                  <input type="hidden" name="category" value="{html.escape(category)}">
                  <button class="bin-button" style="background:{details['color']}" type="submit">{html.escape(details['bin'])}<br>{html.escape(category)}</button>
                </form>
                """
            )

        return self._layout(
            "Sorting Game",
            "game",
            f"""
            <div class="split-layout">
              <div class="card">
                <div class="button-row" style="justify-content:space-between;">
                  <div class="eyebrow">Sorting Missions</div>
                  <form method="post" action="/game/start">
                    <button class="secondary" type="submit">Restart Sorting Round</button>
                  </form>
                </div>
                <h2 class="title">Sort the item using its graphic</h2>
                <p class="lead">Mission {session.get('game_index', 0) + 1} of {len(session.get('game_ids', []))} from a dedicated database of {self.repo.get_sorting_challenge_count():,} sorting challenges.</p>
                <div class="status"><strong>{html.escape(str(challenge['mission_title']))}</strong><br>{html.escape(str(challenge['prompt']))}</div>
                <div class="item-stage">
                  <img class="item-art-large" src="/graphics/item/{item['id']}.svg" alt="{html.escape(self._item_label(item))}">
                  <h3>{html.escape(self._item_label(item))}</h3>
                </div>
                <div class="option-grid" style="margin-top:18px;">{''.join(buttons)}</div>
                {feedback_html}
              </div>
              <div class="card hero-art-wrap">
                <img class="hero-art" src="{self._art_path('game')}" alt="Sorting game illustration">
              </div>
            </div>
            """,
        )

    def _render_quiz(self, session: dict) -> str:
        question = self._current_quiz(session)
        feedback = html.escape(session.get("quiz_feedback", ""))

        if question is None:
            return self._layout(
                "General Quiz",
                "quiz",
                f"""
                <div class="split-layout">
                  <div class="card">
                    <div class="eyebrow">General Quiz</div>
                    <h2 class="title">Quiz complete</h2>
                    <p class="lead">You finished this set of general environment questions.</p>
                    <form method="post" action="/quiz/start" style="margin-top:18px;">
                      <button class="primary" type="submit">Start New Quiz</button>
                    </form>
                    <div class="status">{feedback}</div>
                  </div>
                  <div class="card hero-art-wrap">
                    <img class="hero-art" src="{self._art_path('quiz')}" alt="Quiz illustration">
                  </div>
                </div>
                """,
            )

        answered = session.get("quiz_answered", False)
        selected = session.get("quiz_selected")
        correct = session.get("quiz_correct")
        option_html = []
        for index, option in enumerate(question["options"]):
            classes = ["quiz-option"]
            if answered and index == correct:
                classes.append("correct")
            elif answered and index == selected and selected != correct:
                classes.append("wrong")

            label = option
            if answered and index == correct:
                label = f"{label} (Correct)"
            elif answered and index == selected and selected != correct:
                label = f"{label} (Selected)"

            option_html.append(
                f"""
                <form method="post" action="/quiz/answer">
                  <input type="hidden" name="choice" value="{index}">
                  <button class="{' '.join(classes)}" type="submit" {'disabled' if answered else ''}>{html.escape(label)}</button>
                </form>
                """
            )

        next_button = ""
        explanation = ""
        if answered:
            next_button = """
            <form method="post" action="/quiz/next" style="margin-top:16px;">
              <button class="primary" type="submit">Next Question</button>
            </form>
            """
            explanation = f"<br><span class=\"tiny\">Explanation: {html.escape(str(question['explanation']))}</span>"

        return self._layout(
            "General Quiz",
            "quiz",
            f"""
            <div class="split-layout">
              <div class="card">
                <div class="button-row" style="justify-content:space-between;">
                  <div class="eyebrow">General Eco Quiz</div>
                  <form method="post" action="/quiz/start">
                    <button class="secondary" type="submit">Restart Quiz</button>
                  </form>
                </div>
                <h2 class="title">Think green and answer smart</h2>
                <p class="lead">Question {session.get('quiz_index', 0) + 1} of {len(session.get('quiz_ids', []))} from a separate database of {self.repo.get_quiz_question_count():,} environment questions.</p>
                <div class="question-stage">
                  <h3>{html.escape(str(question['prompt']))}</h3>
                  <p class="tiny">Topic: {html.escape(str(question['topic']).title())}</p>
                </div>
                <div class="option-grid" style="margin-top:18px;">{''.join(option_html)}</div>
                {next_button}
                <div class="status">{feedback}{explanation}</div>
              </div>
              <div class="card hero-art-wrap">
                <img class="hero-art" src="{self._art_path('quiz')}" alt="Quiz illustration">
              </div>
            </div>
            """,
        )

    def _render_learn(self, session: dict) -> str:
        preview = self.repo.get_items_preview(PREVIEW_WASTE_ITEM_LIMIT)
        fact_offset = session.get("fact_offset", 0)
        facts = self.repo.get_fact_batch(fact_offset, FACTS_PER_REFRESH)
        session["fact_offset"] = (fact_offset + FACTS_PER_REFRESH) % self.repo.get_fact_count()
        fact_cards = []
        article_lookup = {}
        for index, fact in enumerate(facts, start=1):
            article_lookup[str(fact["id"])] = self._fact_article_payload(fact)
            fact_cards.append(
                f"""
                <button class="fact-card" type="button" data-fact-id="{fact['id']}" aria-haspopup="dialog" aria-controls="fact-article-overlay">
                  <span class="fact-card-theme">{html.escape(str(fact['theme']))}</span>
                  <h3>Fact {index}</h3>
                  <p>{html.escape(str(fact['text']))}</p>
                  <span class="fact-card-cta">Read article</span>
                </button>
                """
            )

        rows = []
        for item in preview:
            rows.append(
                f"""
                <tr>
                  <td><img class="table-art" src="/graphics/item/{item['id']}.svg" alt="{html.escape(self._item_label(item))}"></td>
                  <td>{html.escape(self._item_label(item))}</td>
                  <td>{html.escape(str(item['category']))}</td>
                  <td>{html.escape(str(item['bin_name']))}</td>
                  <td>{html.escape(str(item['disposal_tip']))}</td>
                </tr>
                """
            )

        article_data_json = json.dumps(article_lookup).replace("</", "<\\/")

        return self._layout(
            "Learn",
            "learn",
            f"""
            <div class="learn-layout">
              <div class="card">
                <div class="eyebrow">Learning Center</div>
                <h2 class="title">Preview the item and question system</h2>
                <p class="lead">Facts now come from a dedicated database with {self.repo.get_fact_count():,} unique entries, and each refresh shows a new batch.</p>
                <div class="button-row" style="margin-top:16px;">
                  <a class="button-link primary" href="/learn">Refresh Facts</a>
                </div>
                <div class="fact-grid" style="margin-top:18px;">
                  {''.join(fact_cards)}
                </div>
                <p class="tiny" style="margin-top:14px;">Click any fact card to open a themed article with animated visuals.</p>
              </div>
              <div class="card hero-art-wrap">
                <img class="hero-art" src="{self._art_path('learn')}" alt="Learning illustration">
              </div>
            </div>
            <div class="card" style="margin-top:18px;">
              <div class="eyebrow">Waste Item Preview</div>
              <h2 class="title">First {PREVIEW_WASTE_ITEM_LIMIT:,} items from the waste item database</h2>
              <p class="lead">The full waste item database contains {self.repo.get_item_count():,} unique items with simple names.</p>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Graphic</th>
                      <th>Item</th>
                      <th>Category</th>
                      <th>Bin</th>
                      <th>Disposal Tip</th>
                    </tr>
                  </thead>
                  <tbody>
                    {''.join(rows)}
                  </tbody>
                </table>
              </div>
            </div>
            <div class="fact-article-overlay" id="fact-article-overlay" hidden>
              <div class="fact-article-shell" id="fact-article-shell" role="dialog" aria-modal="true" aria-labelledby="fact-article-title" tabindex="-1">
                <div class="fact-article-topbar">
                  <div>
                    <div class="fact-article-badge" id="fact-article-theme"></div>
                    <div class="eyebrow" style="margin-bottom:0;">Fact Deep Dive</div>
                  </div>
                  <button class="fact-article-close" id="fact-article-close" type="button" data-close-fact-article>Close</button>
                </div>
                <div class="fact-article-layout">
                  <div class="fact-article-copy">
                    <h2 id="fact-article-title"></h2>
                    <p class="lead" id="fact-article-summary"></p>
                    <div class="fact-article-quote">
                      <p id="fact-article-quote"></p>
                    </div>
                    <div class="fact-article-body">
                      <p id="fact-article-impact"></p>
                      <p id="fact-article-closing"></p>
                    </div>
                    <div class="article-action-list" id="fact-article-actions"></div>
                    <div class="article-stat-grid" id="fact-article-stats"></div>
                  </div>
                  <div class="fact-article-visuals">
                    <div class="article-hero-frame">
                      <img id="fact-article-hero" alt="">
                    </div>
                    <div class="article-strip" id="fact-article-gallery"></div>
                  </div>
                </div>
              </div>
            </div>
            <script id="fact-articles-data" type="application/json">{article_data_json}</script>
            {self._learn_page_script()}
            """,
        )

    def _render_error(self, message: str) -> str:
        return self._layout(
            "Error",
            "none",
            f"""
            <div class="card">
              <h2 class="title">Something went wrong</h2>
              <p class="lead">{html.escape(message)}</p>
            </div>
            """,
        )


SESSIONS: dict[str, dict] = {}


def run_server() -> None:
    repo = MultiDbRepository()
    app = WasteWebApp(repo)
    server = None
    chosen_port = None

    for port in DEFAULT_PORTS:
        try:
            server = make_server(DEFAULT_HOST, port, app)
            chosen_port = port
            break
        except OSError:
            continue

    if server is None or chosen_port is None:
        repo.close()
        raise RuntimeError("Could not start local server on ports 8000, 8001, or 8002.")

    print(f"Smart Waste app running at http://{DEFAULT_HOST}:{chosen_port}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
        repo.close()


if __name__ == "__main__":
    run_server()
