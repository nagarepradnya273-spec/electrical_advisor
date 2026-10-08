"""
Seeds the RAG knowledge base with the demo educational content described in
spec section 46 (MCB/RCCB/RCBO basics, switches, sockets, wires, fans,
lighting, safety, home planning, inverters, buying guide).

Safe to re-run - existing docs (matched by slug) are skipped and NOT
re-ingested, so this won't recompute embeddings on every seed run. To
refresh an existing document's embeddings (e.g. after adding
VOYAGE_API_KEY), use the admin `POST /knowledge/documents/{slug}/reindex`
endpoint instead.

Run with: python seed_knowledge.py
(seed_data.py also calls this automatically, so a plain `python seed_data.py`
sets up products AND the knowledge base together.)
"""
from app.database import SessionLocal, Base, engine
from app import models  # noqa: F401
from app.models.knowledge import KnowledgeDocument
from app.services.rag_service import ingest_document

Base.metadata.create_all(bind=engine)


DOCUMENTS = [
    dict(
        slug="mcb-basics",
        title="MCB Basics: What It Is and How to Choose One",
        category="protection",
        content="""
An MCB (Miniature Circuit Breaker) is a switch that automatically cuts off electricity to a circuit when it detects excess current, protecting your wiring and appliances from overload and short-circuit damage. It replaces older rewireable fuses and can be reset by hand after it trips, instead of needing a new fuse wire.

MCBs are described by their trip curve and current rating. The trip curve (B, C, or D) determines how quickly the MCB reacts to a current surge. Type B trips fastest and suits resistive loads like lighting and heating circuits. Type C tolerates a brief higher inrush current and suits circuits with motors, such as fans and pumps. Type D tolerates the largest inrush and is used for heavy motor loads, transformers, and some industrial equipment. Using the wrong curve type can cause nuisance tripping or, in the wrong direction, reduce protection.

The current rating (commonly 6A, 10A, 16A, 20A, 25A, 32A for domestic use) should match the wiring and load on that circuit, not just the appliance's maximum draw - an electrician calculates this based on the wire size and connected load, not guesswork.

MCBs also come in different pole configurations: Single Pole (1P) switches only the live wire and is standard for most household lighting and socket circuits; Double Pole (2P) switches both live and neutral, often used for higher-risk appliances; and Triple Pole (3P) or Four Pole (4P) are used for three-phase supplies in larger homes, shops, and commercial premises.

An MCB is not the same as an RCCB or RCBO - an MCB protects against overload and short circuit, but does not by itself protect a person from electric shock caused by current leaking to earth. See the RCCB/RCBO guide for that distinction.

When choosing an MCB, match the curve type and rating to the circuit it protects (a qualified electrician or your existing distribution board documentation can confirm this), prefer models carrying the ISI mark, and check the breaking capacity (kA rating) is appropriate for your supply. Installation and any changes to a distribution board should always be done by a qualified electrician.
""",
    ),
    dict(
        slug="rccb-rcbo-basics",
        title="RCCB, RCBO and MCB: What's the Difference",
        category="protection",
        content="""
These three protection devices are often confused because they sit in the same distribution board, but they protect against different things.

An MCB protects your wiring from overload and short-circuit current - it responds to too much current flowing through the circuit itself.

An RCCB (Residual Current Circuit Breaker) protects people from electric shock. It continuously compares the current flowing out through the live wire with the current returning through the neutral wire; if even a small amount is leaking elsewhere - for example, through a person, a damaged appliance, or water - it trips very quickly, typically within milliseconds. A household RCCB is usually rated at 30mA sensitivity, which is considered safe for protecting people. RCCBs do not, on their own, protect against overload or short circuit - that is still the MCB's job.

An RCBO (Residual Current Breaker with Overcurrent protection) combines both functions in a single device, protecting one circuit from both overload/short-circuit and earth leakage. RCBOs are more expensive per circuit than a shared RCCB, but a fault trips only that one circuit rather than the whole board.

In a typical Indian home setup, either a single main RCCB protects the whole distribution board (simpler, cheaper, but a fault anywhere trips all circuits), or individual RCBOs protect each circuit separately (more resilient, costs more). Bathrooms, kitchens, outdoor points, and any socket near water should always have RCD (RCCB or RCBO) protection - this is a widely recommended safety practice, not optional in wet areas.

Like MCBs, RCCBs and RCBOs are rated by current (e.g. 25A, 40A, 63A) and should be sized to match the circuit or board they protect. Choosing and installing these devices, and deciding how to divide circuits across them, should be done by a qualified electrician as part of your distribution board design - this guide is for understanding what you're buying, not for self-installation.
""",
    ),
    dict(
        slug="switches-sockets-buying-guide",
        title="Choosing Switches and Sockets",
        category="switches_sockets",
        content="""
Switches and sockets are rated by current, most commonly 6A and 16A for domestic use. As a general rule, 6A points are used for lighting and small devices (fans, chargers, TVs), while 16A points are used for higher-load appliances like air conditioners, water heaters, refrigerators, washing machines, and irons. Using a lower-rated socket for a high-load appliance can cause the socket to overheat over time.

Modular switches and sockets share a common plate size across brands within the same modular 'series', which matters if you're mixing brands or replacing just one unit later - check that the series/module size matches your existing plates before buying.

For sockets, look for: a shutter mechanism (a spring-loaded cover over the pin holes that keeps out dust and small objects, especially important in homes with children), whether it's a combined switch-socket unit or separate, and whether it includes a USB charging port if you want one built in rather than using a separate adapter.

For AC (air conditioner) points specifically, use a dedicated 16A (or higher, per the unit's rating) switch-socket on its own circuit rather than sharing it with other appliances, since ACs draw sustained high current.

When comparing products, warranty length and the manufacturer's after-sales/service network matter more for switches and sockets than for many other electrical products, since a fault usually means replacing the whole unit rather than a repairable part. Prefer products with the ISI mark where an Indian Standard exists for that category.

Installation or replacement of switches and sockets involves working with wiring behind the plate - even though this looks simple, always switch off the relevant MCB first, and if you're not confident distinguishing live, neutral, and earth wiring, have a qualified electrician do the swap.
""",
    ),
    dict(
        slug="wires-cables-buying-guide",
        title="Understanding Wire Sizes (sq mm) and Types",
        category="wiring",
        content="""
House wiring cables are sized by their cross-sectional area in square millimetres (sq mm), not by a simple 'thin/thick' description. The size needed depends on the current the circuit will carry and the length of the run - a longer run or a higher-current appliance needs a larger sq mm to avoid excessive voltage drop and overheating.

As general reference points used in Indian residential wiring (always to be confirmed against your actual load and run length by a qualified electrician, not chosen by guesswork): 1.5 sq mm is commonly used for lighting circuits and low-load points; 2.5 sq mm for general socket/plug circuits; 4 sq mm and 6 sq mm for higher-load circuits such as air conditioners, water heaters, and kitchen appliances; and larger sizes for the main incoming supply line and distribution board feeders.

Cables are also described by their insulation type. FR (Flame Retardant) and FRLS (Flame Retardant Low Smoke) insulation resist catching fire and, in the case of FRLS, release less toxic smoke if they do - FRLS is now widely preferred for residential and commercial wiring in India. HRFR (Heat Resistant Flame Retardant) is a further variant rated for higher temperature tolerance.

Wires are made with either solid single-strand copper or multi-strand (flexible) copper conductors. Multi-strand wire is generally preferred for house wiring because it's easier to route through conduits and slightly more tolerant of minor movement/vibration. Pure copper conductors conduct better and are more durable than aluminium, which is why copper is the standard choice for household wiring despite costing more than aluminium alternatives.

Flexible cables (as opposed to single-core house wire) are used for connecting appliances, extension boards, and anywhere the cable needs to bend or move, rather than being fixed in a conduit.

Buying the wrong wire size for a circuit is a genuine fire risk, not just an inefficiency - always have circuit sizing confirmed by a qualified electrician for anything beyond replacing an existing, identical run.
""",
    ),
    dict(
        slug="fans-buying-and-care",
        title="Choosing and Caring for Ceiling and Other Fans",
        category="fans",
        content="""
Ceiling fans are commonly sold by 'sweep' size - the diameter of the blade circle, in millimetres (e.g. 1200mm, 1400mm) - which should be chosen based on room size; a larger room generally needs a larger sweep or an additional fan for even air circulation.

A fan's speed is controlled by a regulator, which reduces the voltage (or, in electronic/BLDC regulators, adjusts power more efficiently) reaching the motor. Older resistor-based regulators waste more energy as heat at lower speeds; electronic and BLDC (Brushless DC) fan-regulator combinations are more energy-efficient and increasingly common.

A capacitor helps start the fan motor and keeps it running smoothly; a weak or faulty capacitor is one of the most common reasons a fan starts slowly, hums without turning, or runs at reduced speed even at full regulator setting. This is a component a qualified electrician or technician replaces - it is not a user-serviceable part, since it involves opening the motor housing and working near live wiring.

If a fan is slow: this can be caused by a faulty regulator, a weakening capacitor, voltage fluctuation in the supply, or dust buildup affecting the motor and blade balance. Checking whether other appliances are also affected by low voltage, and trying a different regulator if you have a spare, are reasonable first steps. If the fan is also noisy, wobbling, or smells hot, stop using it and have it inspected rather than continuing to run it.

Other fan types include exhaust fans (for bathrooms/kitchens, rated by air-displacement capacity - CMH or CFM - matched to room size) and wall/pedestal fans (rated similarly to ceiling fans by sweep size, chosen for portability rather than fixed installation).

Warranty on fans typically covers the motor for longer than accessories like the regulator or blades - check what's covered separately when comparing products.
""",
    ),
    dict(
        slug="led-lighting-guide",
        title="Choosing LED Bulbs and Lights",
        category="lighting",
        content="""
LED brightness is measured in lumens, not watts. Wattage tells you how much power the bulb draws, not how bright it is - comparing two LED bulbs by wattage alone can be misleading, since efficiency (lumens per watt) varies by product. When comparing an LED replacement to an old incandescent or CFL bulb, compare lumens, or use the manufacturer's stated 'equivalent to Xw incandescent' guidance if lumens aren't listed.

Colour temperature, measured in Kelvin (K), describes the tone of the light: around 2700-3000K is 'warm white' (yellowish, similar to traditional bulbs, often preferred for bedrooms and living rooms), around 4000K is 'neutral/cool white', and 6000-6500K is 'daylight' (bluish-white, often preferred for kitchens, bathrooms, and work areas). This is a preference choice, not a safety or efficiency difference.

Common bulb fittings in India are B22 (bayonet, push-and-twist) and E27 (Edison screw) - check your existing fitting before buying a replacement bulb, since they are not interchangeable without an adapter.

For fixed lighting like panels and downlights, check the cut-out size (for recessed fittings) or mounting type (for surface fittings) matches your ceiling, and check the driver (the internal power-conversion circuit) is rated for continuous use - cheaper LED fittings sometimes use drivers that degrade faster with heat.

Look for the BIS/ISI mark where applicable, and check the warranty period - LED products with a longer warranty (2 years or more) generally reflect the manufacturer's confidence in driver and chip quality, since premature failure in LEDs is usually a driver fault rather than the LED chip itself.

Outdoor lighting should specifically be rated for outdoor/damp use (check the IP rating - the first digit covers dust resistance, the second covers water resistance) rather than using an indoor-rated fitting outdoors.
""",
    ),
    dict(
        slug="electrical-safety-basics",
        title="Household Electrical Safety Basics",
        category="safety",
        content="""
A few safety principles apply across almost every household electrical situation, and are worth knowing even if you never do electrical work yourself.

Never touch a switch, socket, or appliance with wet hands, and never handle electrical equipment while standing in water or on a wet floor - water dramatically increases the risk and severity of electric shock.

If you see sparks, smell burning, notice a switch or socket that feels warm/hot, or hear buzzing from an electrical point, stop using it immediately and switch off the circuit at the MCB if you can safely do so - then contact a qualified electrician. Do not continue using a fitting that has shown any of these signs, even if it seems to work again afterward.

Earthing (grounding) is a safety system that gives fault current a safe path to the ground instead of through a person who touches a faulty appliance. A proper earth connection at your distribution board, and 3-pin (earthed) plugs on appliances with metal bodies, are both part of this system - removing the earth pin from a 3-pin plug to fit a 2-pin socket defeats this protection and should be avoided; get the correct socket installed instead.

Repeated MCB trips are a signal, not a nuisance to just override - resetting an MCB once after switching off the load on that circuit is a reasonable check, but if it trips again immediately, that indicates a genuine fault (overload, short circuit, or a failing device) and needs a qualified electrician, not repeated resetting.

Never open a distribution board, switch panel, or appliance casing to inspect or work on live wiring yourself unless you are a trained, qualified electrician. This applies even to seemingly simple tasks like replacing a socket or adding a point - the risk is not the visible plate, it's the live wiring behind it.

For any electrical work in high-risk settings - bathrooms, outdoor areas, commercial kitchens, or any space with water or heavy machinery nearby - always use a qualified, ideally licensed, electrician rather than attempting it yourself.
""",
    ),
    dict(
        slug="home-wiring-planning-guide",
        title="Planning Electrical Points for a New Home or Renovation",
        category="planning",
        content="""
When planning electrical work for a new home, renovation, or additional points, it helps to think room by room about what you'll actually use, since retrofitting later is more disruptive than planning it upfront.

A typical starting checklist by room (to be refined with your electrician based on your actual layout and appliances, not used as a final wiring plan):

Living room: ceiling fan point, general lighting points, multiple 6A sockets for lamps/electronics, at least one 16A socket for a TV/set-top box/entertainment setup if power-hungry equipment will be used.

Bedroom: ceiling fan point, lighting (including a bedside switch if wired for two-way control), several 6A sockets for chargers/lamps, and a 16A point if an AC is planned.

Kitchen: dedicated 16A points for high-load appliances (refrigerator, microwave, water heater/geyser if applicable), several general-purpose sockets at counter height for smaller appliances, and RCD (RCCB/RCBO) protection given the proximity to water.

Bathroom: RCD-protected points only, typically for a water heater and/or exhaust fan, kept well away from direct water contact and at a safe height, following local safety norms.

Balcony/outdoor: weatherproof (appropriately IP-rated) fittings only, RCD-protected.

Beyond individual points, plan the distribution board itself: how many circuits you want (splitting lighting from sockets, and high-load appliances onto their own circuits, is common practice so one fault or overload doesn't affect everything), and whether you want RCBOs per circuit or a shared main RCCB (see the RCCB/RCBO guide).

Treat any quantities or layouts from a planning tool as a starting estimate to discuss with your electrician, not a final design - actual circuit design, load calculation, and wire/MCB sizing should always be confirmed by a qualified electrician against your specific building and appliance load, especially for anything beyond a straightforward home.
""",
    ),
    dict(
        slug="inverter-ups-basics",
        title="Inverter and UPS Basics for Power Backup",
        category="power_backup",
        content="""
'Inverter' and 'UPS' are often used loosely, but they describe slightly different backup behaviour. A home inverter typically has a short switchover delay (a fraction of a second to a couple of seconds) when the main power fails - fine for lights, fans, and most home appliances, but potentially disruptive for computers or sensitive equipment. A UPS (Uninterruptible Power Supply), especially an 'online' UPS, switches over near-instantly, which is why UPS units are standard for computers and sensitive electronics, while inverters are standard for whole-home or whole-room backup.

Backup capacity is described in VA (Volt-Amperes) for the inverter/UPS unit itself, and in Ah (Amp-hours) for the battery. A higher VA rating supports more connected load running at once; a higher Ah battery capacity (often paired with the inverter's VA rating) gives longer backup duration for a given load. Sizing an inverter/UPS system means adding up the wattage of everything you actually want to keep running during a cut, then choosing VA and battery capacity to match - a rough guide, not a substitute for a proper load assessment, especially if you're backing up more than a few lights and fans.

Battery types commonly available include flooded lead-acid (cheaper, needs periodic water top-up, shorter life), tubular lead-acid (longer life, low maintenance, widely used for home inverters), and lithium-ion (higher upfront cost, longer life, no maintenance, more compact - increasingly common but still a premium option).

Installation involves connecting to your distribution board, usually with the backup circuit(s) kept separate from non-backed-up circuits (so, for example, high-load appliances like ACs and water heaters aren't accidentally drawing from a home inverter sized for lights and fans). This wiring change, along with correctly sizing the system for your actual load, should be done with a professional's input rather than purely from online research - this guide is meant to help you understand your options, not to replace that assessment.
""",
    ),
    dict(
        slug="buying-electrical-products-guide",
        title="How to Evaluate Electrical Products Before Buying",
        category="buying_guide",
        content="""
A few checks apply across almost any electrical product purchase, beyond just comparing price.

The ISI mark (for products where BIS certification is mandatory in India, such as switches, MCBs, and certain cables) indicates the product meets a defined Indian Standard for safety and performance. For product categories without mandatory certification, check whether the brand publishes independent test/compliance information.

Warranty terms vary more than people expect - check not just the duration, but what's actually covered (full replacement vs. repair-only, parts vs. labour) and how claims are handled (through the retailer, or directly with the manufacturer's service network). A longer warranty is generally a reasonable proxy for the manufacturer's confidence in the product, but only if the service network is actually accessible in your area.

For any product with published specifications, match them to your actual requirement rather than buying based on brand reputation alone - a correctly speced budget product will usually serve you better than an oversized or undersized premium one. If you're unsure what specification you need (current rating, wire gauge, sweep size, VA rating, etc.), the relevant category guide, or the AI Electrical Advisor, can help narrow it down before you compare specific products.

When comparing brands, remember that 'better' is application-specific - one brand's strength might be its service network in your city, another's might be a wider range at a lower price point, and another's might be premium build quality at a higher price. A fair comparison looks at your actual requirement (application, budget, and any must-have specifications) against what's verifiably different between the options, rather than declaring one brand universally best.

Reviews and ratings are useful for spotting recurring problems (a pattern of complaints about a specific failure) but are less reliable for comparing fine specification differences between similar products - for that, rely on the published specifications and, where it matters, the manufacturer's datasheet.
""",
    ),
]


def seed_knowledge(db=None) -> int:
    owns_session = db is None
    if db is None:
        db = SessionLocal()

    created = 0
    for doc in DOCUMENTS:
        if db.query(KnowledgeDocument).filter_by(slug=doc["slug"]).first():
            continue
        record = KnowledgeDocument(
            title=doc["title"],
            slug=doc["slug"],
            category=doc["category"],
            content=doc["content"].strip(),
            is_demo=True,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        ingest_document(db, record)
        created += 1

    print(f"Knowledge documents: {db.query(KnowledgeDocument).count()} ({created} newly created)")
    if owns_session:
        db.close()
    return created


if __name__ == "__main__":
    seed_knowledge()
