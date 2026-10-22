# PyScript + event-driven programming
# ------------------------------------------------------------------
# Python reacts to what the visitor does on the page. Each function
# below is an EVENT HANDLER: the @when decorator tells PyScript
# "run this function when <event> happens on <element>".
#
#   Button clicks     -> product filter tabs, "Customize Now", quantity -/+ and presets
#   User input        -> quantity box typing, product radio buttons
#   Calculations      -> price per piece, bulk discount, total, pickup estimate
#   Form submission   -> inquiry form validation + feedback
#
# JavaScript in index.html only handles visual extras (menu, scroll effects,
# dragging stickers, image upload, saved inquiries and chat).
import re

from js import document, window, Object
from pyodide.ffi import create_proxy, to_js
from pyscript import when

# ==================================================================
# DATA
# ==================================================================
# Links each Design Lab product to its label and the inquiry-form option.
LAB_PRODUCTS = {
    "pin": {"label": "Button Pin", "option": "Custom Button Pins"},
    "keychain": {"label": "Keychain", "option": "Custom Keychains"},
    "sticker": {"label": "Sticker", "option": "Custom Stickers"},
    "magnet": {"label": "Memo Magnet", "option": "Custom Memo Magnets"},
}

# Placeholder prices in pesos per piece. Edit to match your real pricing.
PRICES = {"pin": 15, "keychain": 30, "sticker": 10, "magnet": 35}

# (minimum quantity, discount rate), checked from the biggest tier down.
TIERS = [(100, 0.15), (50, 0.10), (25, 0.05)]

MIN_QTY = 1
MAX_QTY = 1000


# ==================================================================
# CALCULATIONS
# ==================================================================
def round_half_up(value):
    """Round like JavaScript's Math.round (Python's round() rounds .5 to even)."""
    return int(value + 0.5)


def peso(amount):
    return "₱" + f"{amount:,}"


def delivery_estimate(qty):
    if qty <= 10:
        return "1 day"
    if qty <= 25:
        return "3 days"
    if qty <= 50:
        return "5 days"
    return "1–2 weeks"


def quote(product_type, qty):
    """Price per piece, bulk discount, and the estimated total."""
    unit = PRICES[product_type]
    rate = 0
    for minimum, tier_rate in TIERS:
        if qty >= minimum:
            rate = tier_rate
            break
    return {
        "unit": unit,
        "rate": rate,
        "saved": round_half_up(unit * qty * rate),
        "total": round_half_up(unit * qty * (1 - rate)),
        "delivery": delivery_estimate(qty),
    }


# ==================================================================
# PRODUCT FILTER TABS  (button click)
# ==================================================================
@when("click", ".filter-tab")
def filter_products(event):
    category = event.currentTarget.getAttribute("data-filter")

    for tab in document.querySelectorAll(".filter-tab"):
        is_selected = tab.getAttribute("data-filter") == category
        tab.classList.toggle("active", is_selected)
        tab.setAttribute("aria-pressed", "true" if is_selected else "false")

    grid = document.querySelector(".product-grid")
    grid.classList.toggle("is-filtered", category != "all")

    for card in document.querySelectorAll(".product-card"):
        show = category == "all" or card.getAttribute("data-category") == category
        card.hidden = not show
        if show:
            # restart the little "pop in" animation
            card.classList.remove("is-pop")
            _ = card.offsetWidth
            card.classList.add("is-pop")


# ==================================================================
# DESIGN LAB  (radio buttons, typing, +/- and preset buttons)
# ==================================================================
def read_qty():
    """Read the quantity box and keep it between 1 and 1000."""
    try:
        qty = int(float(document.querySelector("#lab-qty").value))
    except (ValueError, TypeError):
        qty = MIN_QTY
    return max(MIN_QTY, min(MAX_QTY, qty))


def read_type():
    return document.querySelector('input[name="lab-type"]:checked').value


def update_quote():
    """Recalculate and show the price summary for the current choices."""
    product_type = read_type()
    qty = read_qty()
    q = quote(product_type, qty)

    document.querySelector("#lab-stage").setAttribute("data-type", product_type)
    document.querySelector("#lab-preview-text").textContent = ""

    document.querySelector("#q-unit").textContent = peso(q["unit"])
    document.querySelector("#q-qty").textContent = f"× {qty}"
    document.querySelector("#q-disc-row").hidden = not q["rate"]
    document.querySelector("#q-disc").textContent = (
        f"−{peso(q['saved'])} ({round_half_up(q['rate'] * 100)}%)"
    )
    document.querySelector("#q-total").textContent = peso(q["total"])
    document.querySelector("#q-delivery").textContent = q["delivery"]
    document.querySelector("#lab-status").textContent = ""


# User input: runs on every keystroke / radio selection inside the Lab controls
@when("input", "#lab-controls")
def on_lab_input(event):
    update_quote()


# When the quantity box loses focus, tidy the number (e.g. 5000 -> 1000)
@when("change", "#lab-controls")
def on_lab_change(event):
    document.querySelector("#lab-qty").value = read_qty()
    update_quote()


# Button clicks: the  −  and  +  buttons and the 10 / 25 / 50 / 100 presets
@when("click", "#lab-controls")
def on_lab_click(event):
    button = event.target.closest("[data-step], [data-qty]")
    if button is None:
        return
    preset = button.getAttribute("data-qty")
    step = button.getAttribute("data-step")
    if preset is not None:
        new_qty = int(preset)
    else:
        new_qty = read_qty() + int(step)
    document.querySelector("#lab-qty").value = max(MIN_QTY, min(MAX_QTY, new_qty))
    update_quote()


# ==================================================================
# "CUSTOMIZE NOW" BUTTONS  (button click)
# ==================================================================
@when("click", ".js-customize")
def customize_now(event):
    wanted = event.currentTarget.getAttribute("data-product")

    for key, info in LAB_PRODUCTS.items():
        if info["option"] == wanted:
            document.querySelector(f'input[name="lab-type"][value="{key}"]').checked = True
            update_quote()
            document.querySelector("#lab-status").textContent = (
                f"{info['label']} selected. Design it below ✓"
            )
            break

    document.querySelector("#lab").scrollIntoView()


# ==================================================================
# BRIDGE TO JAVASCRIPT
# ==================================================================
# The "Use this in my inquiry" button (JavaScript) needs the same price
# calculation, so Python shares quote() with it instead of duplicating it.
def js_quote(product_type, qty):
    return to_js(quote(product_type, int(qty)), dict_converter=Object.fromEntries)


window.hightackQuote = create_proxy(js_quote)

# Fill in the quote as soon as Python is ready
update_quote()


# ==================================================================
# INQUIRY FORM  (form submission)
# ==================================================================
FIELD_IDS = ["name", "email", "product", "message"]


def set_feedback(message, kind):
    feedback = document.querySelector("#form-feedback")
    feedback.innerText = message
    feedback.className = f"form-feedback {kind}"


def mark_invalid(invalid_ids):
    """Flag problem fields for screen readers and put the cursor in the first one."""
    for field_id in FIELD_IDS:
        field = document.querySelector("#" + field_id)
        if field_id in invalid_ids:
            field.setAttribute("aria-invalid", "true")
        else:
            field.removeAttribute("aria-invalid")
    if invalid_ids:
        document.querySelector("#" + invalid_ids[0]).focus()


@when("submit", "#inquiry-form")
def validate_inquiry(event):
    event.preventDefault()

    name = document.querySelector("#name").value.strip()
    email = document.querySelector("#email").value.strip()
    product = document.querySelector("#product").value.strip()
    message = document.querySelector("#message").value.strip()

    missing = []
    missing_ids = []

    if not name:
        missing.append("your name")
        missing_ids.append("name")
    if not email:
        missing.append("your email")
        missing_ids.append("email")
    if not product:
        missing.append("a product")
        missing_ids.append("product")
    if not message:
        missing.append("a few details")
        missing_ids.append("message")

    if missing:
        mark_invalid(missing_ids)
        set_feedback("Please add " + ", ".join(missing) + ".", "error")
        return

    # Check the email format
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        mark_invalid(["email"])
        set_feedback("That email looks a little off — please check it and try again.", "error")
        return

    mark_invalid([])
    set_feedback(
        f"Thanks, {name}! Your {product.lower()} inquiry is noted. "
        "We will get back to you shortly.",
        "success"
    )

    document.querySelector("#inquiry-form").reset()