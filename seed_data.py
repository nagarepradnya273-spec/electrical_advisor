"""
Populates the database with realistic sample data so the API is usable for
development and demos (spec section 41).

Run with:  python seed_data.py
Safe to re-run - existing rows (matched by slug/email) are skipped.
"""
from app.database import SessionLocal, Base, engine
from app import models  # noqa: F401
from app.models.product import Category, Brand, Product, ProductSpecification
from app.models.advisor import AdvisorProblem, AdvisorProductRecommendation
from app.models.user import User, UserRole
from app.utils.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def get_or_create_category(name, slug, description=""):
    cat = db.query(Category).filter_by(slug=slug).first()
    if not cat:
        cat = Category(name=name, slug=slug, description=description)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat


def get_or_create_brand(name, slug):
    brand = db.query(Brand).filter_by(slug=slug).first()
    if not brand:
        brand = Brand(name=name, slug=slug)
        db.add(brand)
        db.commit()
        db.refresh(brand)
    return brand


# --- Categories (subset of spec section 14 - easy to extend) ---
categories = {
    "switches-sockets": get_or_create_category("Switches & Sockets", "switches-sockets"),
    "wires-cables": get_or_create_category("Wires & Cables", "wires-cables"),
    "mcb-protection": get_or_create_category("MCB & Protection Devices", "mcb-protection"),
    "fans": get_or_create_category("Fans", "fans"),
    "lighting": get_or_create_category("Lighting", "lighting"),
    "inverter-ups": get_or_create_category("Inverter & UPS", "inverter-ups"),
}

# --- Brands (real Indian electrical brands, used here only as sample/dev data) ---
brands = {
    "havells": get_or_create_brand("Havells", "havells"),
    "anchor": get_or_create_brand("Anchor by Panasonic", "anchor"),
    "legrand": get_or_create_brand("Legrand", "legrand"),
    "polycab": get_or_create_brand("Polycab", "polycab"),
    "crompton": get_or_create_brand("Crompton", "crompton"),
}

# --- Products ---
sample_products = [
    dict(
        name="Havells 6A Modular Switch", slug="havells-6a-modular-switch",
        category="switches-sockets", brand="havells",
        short_description="Reliable everyday switch for lights and fans",
        description="A standard 6A modular switch suitable for lights, fans and small appliances in homes and offices.",
        who_should_buy="Homeowners, tenants, electricians doing general wiring.",
        before_you_buy="Confirm the switch plate/modular series matches your existing board.",
        price=45, discount_price=39, stock_qty=500, warranty="2 years",
        specs={"Rating": "6A, 240V", "Type": "1-way modular switch"},
    ),
    dict(
        name="Anchor 16A Power Socket", slug="anchor-16a-power-socket",
        category="switches-sockets", brand="anchor",
        short_description="Heavy-duty socket for ACs, geysers and high-load appliances",
        description="16A socket designed for high-current appliances such as air conditioners, geysers and water heaters.",
        who_should_buy="Homeowners installing AC/geyser points, electricians.",
        before_you_buy="Make sure your circuit wiring and MCB are rated for 16A.",
        price=180, discount_price=159, stock_qty=300, warranty="2 years",
        specs={"Rating": "16A, 240V", "Type": "3-pin socket"},
    ),
    dict(
        name="Legrand 32A Single Pole MCB", slug="legrand-32a-mcb",
        category="mcb-protection", brand="legrand",
        short_description="Circuit protection device that trips during overload/short-circuit",
        description="A Miniature Circuit Breaker that automatically cuts power when it detects an overload or short circuit, protecting your wiring and appliances.",
        who_should_buy="Electricians, contractors, homeowners upgrading their distribution board.",
        before_you_buy="MCB rating must match the connected load — consult an electrician if unsure.",
        price=210, discount_price=None, stock_qty=200, warranty="1 year",
        specs={"Rating": "32A", "Poles": "Single pole", "Breaking capacity": "10kA"},
    ),
    dict(
        name="Polycab 1.5 sq mm FR Wire (90m coil)", slug="polycab-1-5-sqmm-wire",
        category="wires-cables", brand="polycab",
        short_description="Flame-retardant copper wire for home wiring",
        description="Flame-retardant PVC insulated copper wire commonly used for lighting and general home circuits.",
        who_should_buy="Electricians and contractors doing house wiring.",
        before_you_buy="Check the correct wire gauge for your circuit's expected load.",
        price=2400, discount_price=2199, stock_qty=100, warranty="NA",
        specs={"Size": "1.5 sq mm", "Length": "90 metres", "Type": "FR PVC insulated"},
    ),
    dict(
        name="Crompton 1200mm Ceiling Fan", slug="crompton-1200mm-ceiling-fan",
        category="fans", brand="crompton",
        short_description="High-speed ceiling fan for bedrooms and living rooms",
        description="A standard 1200mm sweep ceiling fan offering strong airflow, suited to most Indian bedrooms and living rooms.",
        who_should_buy="Homeowners furnishing a new room or replacing an old/noisy fan.",
        before_you_buy="Check your ceiling height and existing fan mount/rod length.",
        price=1899, discount_price=1599, stock_qty=150, warranty="2 years",
        specs={"Sweep": "1200mm", "Speed": "380 RPM", "Colour": "White"},
    ),
    dict(
        name="Havells 9W LED Bulb", slug="havells-9w-led-bulb",
        category="lighting", brand="havells",
        short_description="Bright, energy-efficient LED bulb",
        description="A 9W LED bulb offering bright white light with low power consumption, suitable for most rooms.",
        who_should_buy="Anyone replacing old CFL/incandescent bulbs.",
        before_you_buy="Check your fitting type (B22/E27).",
        price=120, discount_price=99, stock_qty=1000, warranty="1 year",
        specs={"Wattage": "9W", "Colour temperature": "6500K (cool white)", "Fitting": "B22"},
    ),
]

for p in sample_products:
    if db.query(Product).filter_by(slug=p["slug"]).first():
        continue
    product = Product(
        name=p["name"], slug=p["slug"],
        category_id=categories[p["category"]].id,
        brand_id=brands[p["brand"]].id,
        short_description=p["short_description"],
        description=p["description"],
        who_should_buy=p["who_should_buy"],
        before_you_buy=p["before_you_buy"],
        price=p["price"], discount_price=p["discount_price"],
        stock_qty=p["stock_qty"], warranty=p["warranty"],
        rating=4.2, review_count=18,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    for key, value in p["specs"].items():
        db.add(ProductSpecification(product_id=product.id, key=key, value=value))
    db.commit()

# --- Advisor problems (spec sections 9-10) ---
advisor_problems = [
    dict(
        title="Fan running slowly", slug="fan-running-slowly",
        keywords="fan,slow,slowly,fan speed,regulator", place_context="home",
        explanation="Your fan is spinning but not reaching full speed.",
        common_causes="Faulty/worn fan regulator, voltage fluctuation, dust buildup on blades/motor, aging capacitor.",
        safe_checks="Check if other appliances are also affected by low voltage. Try a different regulator if available. Do not open the fan motor yourself.",
        when_to_call_electrician="If the regulator swap doesn't help, or you notice unusual heat, noise, or a burning smell — call an electrician to check the capacitor and wiring.",
        danger_level="low", categories=["fans"],
    ),
    dict(
        title="MCB keeps tripping", slug="mcb-keeps-tripping",
        keywords="mcb,tripping,trips,trip,breaker,keeps tripping,power cuts off", place_context="any",
        explanation="Your MCB (circuit breaker) switches off repeatedly.",
        common_causes="Overloaded circuit (too many appliances), short circuit, faulty appliance, damaged wiring, or a genuinely faulty MCB.",
        safe_checks="Unplug/switch off appliances on that circuit and try resetting the MCB once. Do not repeatedly force-reset it.",
        when_to_call_electrician="If it trips again immediately, or you smell burning — stop and call a qualified electrician immediately. Do not investigate the panel yourself.",
        danger_level="high", categories=["mcb-protection", "wires-cables"],
    ),
    dict(
        title="Switch sparking or making noise", slug="switch-sparking",
        keywords="switch,spark,sparking,buzzing,noise", place_context="any",
        explanation="Your switch sparks, buzzes, or feels warm when used.",
        common_causes="Loose internal wiring, worn-out switch, overloaded circuit, poor-quality switch.",
        safe_checks="Stop using that switch immediately. Do not touch it with wet hands. Turn off the corresponding MCB if possible.",
        when_to_call_electrician="Sparking switches are a fire/shock risk — always get a qualified electrician to inspect and replace it. Do not attempt this yourself.",
        danger_level="high", categories=["switches-sockets"],
    ),
    dict(
        title="Socket damaged or not working", slug="socket-damaged",
        keywords="socket,plug point,damaged,not working,broken socket", place_context="any",
        explanation="A power socket is physically damaged, loose, or has stopped working.",
        common_causes="Wear and tear, loose wiring inside, moisture damage, overloaded socket.",
        safe_checks="Stop using the socket. Avoid touching visible damage. Switch off the circuit at the MCB if the damage looks serious.",
        when_to_call_electrician="For any exposed wiring, burn marks, or a socket that feels hot — get a qualified electrician to replace it rather than DIY.",
        danger_level="medium", categories=["switches-sockets"],
    ),
    dict(
        title="One room has no electricity", slug="room-no-electricity",
        keywords="no electricity,no power,room dark,not working,one room", place_context="home",
        explanation="Power has gone out in a single room while the rest of the house has electricity.",
        common_causes="A tripped MCB for that circuit, a blown fuse, or a loose connection at a switch/socket in that room.",
        safe_checks="Check your distribution board for a tripped MCB specific to that room and try resetting it once.",
        when_to_call_electrician="If resetting doesn't restore power, or the MCB trips again — call an electrician rather than opening switches/sockets yourself.",
        danger_level="medium", categories=["mcb-protection"],
    ),
    dict(
        title="Need an extra socket installed", slug="need-extra-socket",
        keywords="extra socket,additional socket,new socket,need socket", place_context="any",
        explanation="You need an additional power point for a new appliance or furniture layout.",
        common_causes="", safe_checks="",
        when_to_call_electrician="Adding a new socket involves working on live wiring — this should be done by a qualified electrician, not DIY.",
        danger_level="medium", categories=["switches-sockets", "wires-cables"],
    ),
    dict(
        title="Need an inverter for power backup", slug="need-inverter",
        keywords="inverter,power backup,ups,power cut,backup", place_context="home",
        explanation="You want backup power for essential appliances during outages.",
        common_causes="", safe_checks="",
        when_to_call_electrician="Sizing and installing an inverter/UPS system correctly needs a professional load assessment — a consultation is recommended before buying.",
        danger_level="low", categories=["inverter-ups"],
    ),
]

for ap in advisor_problems:
    if db.query(AdvisorProblem).filter_by(slug=ap["slug"]).first():
        continue
    problem = AdvisorProblem(
        title=ap["title"], slug=ap["slug"], keywords=ap["keywords"],
        place_context=ap["place_context"], explanation=ap["explanation"],
        common_causes=ap["common_causes"], safe_checks=ap["safe_checks"],
        when_to_call_electrician=ap["when_to_call_electrician"],
        danger_level=ap["danger_level"],
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    for cat_slug in ap["categories"]:
        db.add(AdvisorProductRecommendation(problem_id=problem.id, category_id=categories[cat_slug].id))
    db.commit()

# --- Demo admin user (change this password before deploying anywhere real) ---
if not db.query(User).filter_by(email="admin@example.com").first():
    db.add(User(
        full_name="Admin User", email="admin@example.com",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.admin,
    ))
    db.commit()

print(f"Categories: {db.query(Category).count()}")
print(f"Brands: {db.query(Brand).count()}")
print(f"Products: {db.query(Product).count()}")
print(f"Advisor problems: {db.query(AdvisorProblem).count()}")

# --- RAG knowledge base (spec sections 14, 46) - chunks + embeds each doc ---
from seed_knowledge import seed_knowledge  # noqa: E402

seed_knowledge(db)

print("Seed data created successfully.")
db.close()
