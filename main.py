import re
from pyscript import document, when

def set_feedback(message, kind):
    feedback = document.querySelector("#form-feedback")
    feedback.innerText = message
    feedback.className = f"form-feedback {kind}"

@when("submit", "#inquiry-form")
def validate_inquiry(event):
    event.preventDefault()
    name = document.querySelector("#name").value.strip()
    email = document.querySelector("#email").value.strip()
    product = document.querySelector("#product").value.strip()
    message = document.querySelector("#message").value.strip()

    missing = []
    if not name:
        missing.append("your name")
    if not email:
        missing.append("your email")
    if not product:
        missing.append("a product")
    if not message:
        missing.append("a few details")
    if missing:
        set_feedback("Please add " + ", ".join(missing) + ".", "error")
        return
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        set_feedback("That email looks a little off — please check it and try again.", "error")
        return
    set_feedback(f"Thanks, {name}! Your {product.lower()} inquiry is noted. We will get back to you shortly.", "success")
    document.querySelector("#inquiry-form").reset()

@when("click", ".js-customize")
def choose_product(event):
    product_name = event.currentTarget.getAttribute("data-product")
    select_elem = document.querySelector("#product")
    select_elem.value = product_name
    document.querySelector("#contact").scrollIntoView({"behavior": "smooth"})

@when("click", ".filter-tab")
def filter_products(event):
    tabs = document.querySelectorAll(".filter-tab")
    for i in range(tabs.length):
        tabs.item(i).classList.remove("active")
    
    btn = event.currentTarget
    btn.classList.add("active")
    
    category = btn.getAttribute("data-filter")
    cards = document.querySelectorAll(".product-card")
    
    for i in range(cards.length):
        card = cards.item(i)
        card_cat = card.getAttribute("data-category")
        
        if category == "all" or card_cat == category:
            card.style.display = "flex"
        else:
            card.style.display = "none"