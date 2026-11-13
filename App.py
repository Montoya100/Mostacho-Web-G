import gradio as gr
import pandas as pd
import urllib.parse
import json
import os
import shutil
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y CONSTANTES
# ==========================================
LOGO_URL = "https://raw.githubusercontent.com/Montoya100/Mostacho-Botanas-Web/main/logo.png"
DEFAULT_BANNER = "https://raw.githubusercontent.com/Montoya100/Mostacho-Botanas-Web/main/banner.jpg"
DEFAULT_PRODUCT_IMG = "https://raw.githubusercontent.com/Montoya100/Mostacho-Botanas-Web/main/image.jpg"

DATA_FILE = "productos_mostacho.json"
POPULAR_FILE = "populares_mostacho.json"
BANNER_FILE = "banner_mostacho.json"
UPLOAD_DIR = "uploaded_images"

WHATSAPP_PHONE = "522381174698"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ==========================================
# 2. GESTIÓN DE DATOS LOCALES (SIN LOYVERSE)
# ==========================================
def load_saved_banner():
    if os.path.exists(BANNER_FILE):
        try:
            with open(BANNER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    url = str(data.get("url", "")).strip()
                    if url and url.lower() != "nan":
                        return url
        except Exception:
            pass
    return DEFAULT_BANNER

def save_banner_to_file(url):
    try:
        with open(BANNER_FILE, "w", encoding="utf-8") as f:
            json.dump({"url": url}, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def save_products_to_file(prod_list):
    try:
        prod_list = sorted(prod_list, key=lambda x: str(x.get("name", "")).lower())
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(prod_list, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_saved_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    cleaned = []
                    for idx, item in enumerate(data):
                        if isinstance(item, dict):
                            item_id = str(item.get("id", f"auto_{idx}")).strip() or f"auto_{idx}"
                            img_val = str(item.get("image", "")).strip()
                            if not img_val or img_val.lower() == "nan" or "placeholder" in img_val:
                                img_val = DEFAULT_PRODUCT_IMG
                            cleaned.append({
                                "id": item_id,
                                "name": str(item.get("name", "Sin nombre")),
                                "category": str(item.get("category", "Individual")),
                                "price": float(item.get("price", 0.0)),
                                "description": str(item.get("description", "")) if pd.notna(item.get("description")) else "",
                                "image": img_val
                            })
                    if cleaned:
                        return sorted(cleaned, key=lambda x: str(x.get("name", "")).lower())
        except Exception:
            pass
    
    # Productos por defecto si no existe el archivo JSON
    initial = [
        {"id": "p1", "name": "Pistaches Salados (90g)", "category": "Individual", "price": 35.0, "description": "Pistaches tostados con sal de mar.", "image": DEFAULT_PRODUCT_IMG},
        {"id": "p2", "name": "Fritura (Con Chile)", "category": "Para compartir", "price": 25.0, "description": "Crujientes frituras artesanales.", "image": DEFAULT_PRODUCT_IMG},
        {"id": "p3", "name": "Fritura (Sin Chile)", "category": "Para compartir", "price": 25.0, "description": "Ideales para toda la familia.", "image": DEFAULT_PRODUCT_IMG}
    ]
    save_products_to_file(initial)
    return initial

def save_populares_to_file(pop_list):
    try:
        with open(POPULAR_FILE, "w", encoding="utf-8") as f:
            json.dump(pop_list, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_saved_populares():
    if os.path.exists(POPULAR_FILE):
        try:
            with open(POPULAR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    cleaned = []
                    for p in data:
                        if isinstance(p, dict):
                            p_img = str(p.get("image", "")).strip()
                            if not p_img or p_img.lower() == "nan" or "placeholder" in p_img:
                                p["image"] = DEFAULT_PRODUCT_IMG
                            cleaned.append(p)
                    if cleaned:
                        return cleaned
        except Exception:
            pass
    default_pops = [
        {"id": "p1", "name": "Pistaches Salados (90g)", "price": 35.0, "image": DEFAULT_PRODUCT_IMG},
        {"id": "p2", "name": "Fritura (Con Chile)", "price": 25.0, "image": DEFAULT_PRODUCT_IMG}
    ]
    save_populares_to_file(default_pops)
    return default_pops

# ==========================================
# 3. RENDERIZADO HTML DINÁMICO
# ==========================================
def render_catalog_html(products, popular_items, banner_url, selected_cat, search_query, cart):
    banner_src = banner_url if banner_url and banner_url.lower() != "nan" else DEFAULT_BANNER

    # --- SECCIÓN POPULARES ---
    pop_cards_html = ""
    for idx, pop_p in enumerate(popular_items):
        p_id = str(pop_p.get("id", f"pop_{idx}"))
        p_name_raw = str(pop_p.get("name", "Producto"))
        matched = next((p for p in products if str(p.get("id")) == p_id or str(p.get("name", "")).lower().strip() == p_name_raw.lower().strip()), None)
        p_img = matched.get("image") if matched and matched.get("image") else pop_p.get("image", DEFAULT_PRODUCT_IMG)
        p_price = float(matched.get("price") if matched else pop_p.get("price", 0))

        pop_cards_html += f"""
        <div class="pop-card">
            <img src="{p_img}" onerror="this.onerror=null;this.src='{DEFAULT_PRODUCT_IMG}';" />
            <div class="pop-title">{p_name_raw}</div>
            <div class="pop-price">${p_price:.2f} MXN</div>
            <button class="btn-orange-sm" onclick="triggerAction('add', '{p_id}')">Agregar +</button>
        </div>
        """

    # --- PESTAÑAS DE CATEGORÍA ---
    categories = ["Todo", "Individual", "Para compartir"]
    cat_btns_html = ""
    for cat in categories:
        active_cls = "cat-btn active" if selected_cat == cat else "cat-btn"
        label = f"● {cat}" if selected_cat == cat else cat
        cat_btns_html += f"""<button class="{active_cls}" onclick="triggerAction('cat', '{cat}')">{label}</button>"""

    # --- FILTRADO Y AGRUPACIÓN DE PRODUCTOS ---
    q = (search_query or "").lower().strip()
    filtered = []
    for p in products:
        c_val = str(p.get("category", "Individual")).strip()
        if selected_cat != "Todo" and c_val != selected_cat:
            continue
        if q and (q not in str(p.get("name", "")).lower() and q not in str(p.get("description", "")).lower()):
            continue
        filtered.append(p)

    grouped_dict = {}
    for p in filtered:
        name_raw = str(p.get("name", "Producto")).strip()
        base_name = name_raw.split("(")[0].strip() if ("(" in name_raw and ")" in name_raw) else name_raw
        grouped_dict.setdefault(base_name, [])
        if not any(str(it.get("id")) == str(p.get("id")) for it in grouped_dict[base_name]):
            grouped_dict[base_name].append(p)

    group_items = sorted(list(grouped_dict.items()), key=lambda x: 0 if len(x[1]) > 1 else 1)

    grid_html = ""
    if not group_items:
        grid_html = '<div class="empty-box">No se encontraron productos en esta categoría.</div>'
    else:
        for base_name, items_group in group_items:
            rep = items_group[0]
            pid = str(rep.get("id"))
            img_src = rep.get("image") or DEFAULT_PRODUCT_IMG
            desc = str(rep.get("description", "")).strip()
            desc_html = f'<div class="product-desc">{desc}</div>' if desc and desc.lower() != "nan" else ''
            price = float(rep.get("price", 0))

            if len(items_group) > 1:
                total_var_qty = sum(cart.get(str(v.get("id")), 0) for v in items_group)
                badge = f" ({total_var_qty})" if total_var_qty > 0 else ""
                safe_base = base_name.replace("'", "\\'")
                action_html = f"""<button class="btn-red-full" onclick="triggerAction('modal', '{safe_base}')">Ver Opciones{badge}</button>"""
            else:
                qty = cart.get(pid, 0)
                if qty == 0:
                    action_html = f"""<button class="btn-orange-full" onclick="triggerAction('add', '{pid}')">Agregar</button>"""
                else:
                    action_html = f"""
                    <div class="qty-controls">
                        <button class="btn-qty" onclick="triggerAction('remove', '{pid}')">-</button>
                        <span class="qty-val">{qty}</span>
                        <button class="btn-qty" onclick="triggerAction('add', '{pid}')">+</button>
                    </div>
                    """

            grid_html += f"""
            <div class="product-card">
                <div>
                    <img src="{img_src}" class="product-img" onerror="this.onerror=null;this.src='{DEFAULT_PRODUCT_IMG}';" />
                    <div class="product-title">{base_name}</div>
                    {desc_html}
                </div>
                <div>
                    <div class="product-price">${price:.2f} MXN</div>
                    {action_html}
                </div>
            </div>
            """

    return f"""
    <div class="catalog-wrapper">
        <div class="promo-banner">
            🚚 ¡Envíos locales y entregas directas en ruta! Pide fácil y rápido
        </div>

        <div class="banner-box">
            <img src="{banner_src}" class="desktop-banner-img" onerror="this.onerror=null;this.src='{DEFAULT_BANNER}';" />
        </div>

        <h3 class="section-title">Productos Populares</h3>
        <p class="section-sub">Toca cualquier producto popular para agregarlo directo a tu carrito:</p>
        <div class="pop-grid">
            {pop_cards_html}
        </div>

        <hr class="divider" />

        <h3 class="section-title">Categorías</h3>
        <div class="cat-grid">
            {cat_btns_html}
        </div>

        <hr class="divider" />

        <div class="products-grid">
            {grid_html}
        </div>
    </div>
    """

def render_modal_html(modal_base_name, products, cart):
    if not modal_base_name:
        return ""

    variants = []
    for p in products:
        name_raw = str(p.get("name", "")).strip()
        b_name = name_raw.split("(")[0].strip() if ("(" in name_raw and ")" in name_raw) else name_raw
        if b_name == modal_base_name:
            variants.append(p)

    rows_html = ""
    for var in variants:
        v_id = str(var.get("id"))
        v_name = str(var.get("name"))
        v_price = float(var.get("price", 0))
        v_img = var.get("image") or DEFAULT_PRODUCT_IMG
        qty = cart.get(v_id, 0)

        rows_html += f"""
        <div class="modal-item-row">
            <img src="{v_img}" class="modal-item-img" onerror="this.onerror=null;this.src='{DEFAULT_PRODUCT_IMG}';" />
            <div class="modal-item-info">
                <div class="modal-item-name">{v_name}</div>
                <div class="modal-item-price">${v_price:.2f} MXN</div>
            </div>
            <div class="qty-controls modal-qty">
                <button class="btn-qty" onclick="triggerAction('remove', '{v_id}')">-</button>
                <span class="qty-val">{qty}</span>
                <button class="btn-qty" onclick="triggerAction('add', '{v_id}')">+</button>
            </div>
        </div>
        """

    return f"""
    <div class="modal-overlay" onclick="if(event.target === this) triggerAction('close_modal', '')">
        <div class="modal-card">
            <div class="modal-header">
                <h3>{modal_base_name}</h3>
                <p>Escoge la figura y el sabor que deseas:</p>
            </div>
            <div class="modal-body">
                {rows_html}
            </div>
            <div class="modal-footer">
                <button class="btn-red-full" onclick="triggerAction('close_modal', '')">✔ Listo</button>
            </div>
        </div>
    </div>
    """

def render_cart_html(products, cart):
    total_items = sum(cart.values())
    if total_items == 0:
        return """
        <div class="empty-box">
            <h3>🛒 Tu carrito está vacío</h3>
            <p>Agrega productos desde la pantalla principal para armar tu pedido.</p>
        </div>
        """, 0.0, []

    total_price = 0.0
    order_summary = []
    items_html = ""

    for item_id, qty in list(cart.items()):
        p = next((item for item in products if str(item.get("id")) == str(item_id)), None)
        if p:
            price = float(p.get("price", 0))
            subtotal = price * qty
            total_price += subtotal
            order_summary.append(f"- {qty}x {p.get('name')} - ${subtotal:.2f} MXN")
            img_src = p.get("image") or DEFAULT_PRODUCT_IMG

            items_html += f"""
            <div class="cart-item-row">
                <img src="{img_src}" class="cart-item-img" onerror="this.onerror=null;this.src='{DEFAULT_PRODUCT_IMG}';" />
                <div class="cart-item-info">
                    <div class="cart-item-name">{p.get('name')}</div>
                    <div class="cart-item-sub">{qty} x ${price:.2f} = <strong>${subtotal:.2f} MXN</strong></div>
                </div>
                <div class="cart-item-actions">
                    <button class="btn-qty-sm" onclick="triggerAction('remove', '{item_id}')">-</button>
                    <span class="qty-val-sm">{qty}</span>
                    <button class="btn-qty-sm" onclick="triggerAction('add', '{item_id}')">+</button>
                    <button class="btn-del-sm" onclick="triggerAction('delete', '{item_id}')">🗑️</button>
                </div>
            </div>
            """

    html = f"""
    <div class="cart-list-container">
        <div class="cart-count-badge">Artículos seleccionados: <strong>{total_items}</strong></div>
        {items_html}
        <div class="cart-total-box">
            <span>Total a Pagar:</span>
            <span class="cart-total-amount">${total_price:.2f} MXN</span>
        </div>
    </div>
    """
    return html, total_price, order_summary

def render_whatsapp_btn(products, cart, cust_name, cust_addr, cust_notes):
    _, total_price, order_summary = render_cart_html(products, cart)
    if not order_summary:
        return ""

    if cust_name and cust_name.strip() and cust_addr and cust_addr.strip():
        order_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg_header = f"NUEVO PEDIDO\nFecha: {order_date}\n\n"
        msg_items = "DETALLE DE PRODUCTOS:\n" + "\n".join(order_summary) + "\n\n"
        msg_total = f"TOTAL: ${total_price:.2f} MXN\n\n"
        msg_customer = f"CLIENTE: {cust_name.strip()}\n"
        msg_address = f"DIRECCION: {cust_addr.strip()}\n"
        msg_notes = f"NOTAS: {cust_notes.strip()}\n" if cust_notes and cust_notes.strip() else ""

        full_message = msg_header + msg_items + msg_total + msg_customer + msg_address + msg_notes
        encoded = urllib.parse.quote(full_message)
        wa_url = f"https://wa.me/{WHATSAPP_PHONE}?text={encoded}"

        return f"""
        <a href="{wa_url}" target="_blank" class="whatsapp-btn-active">
            💬 Enviar pedido por WhatsApp
        </a>
        """
    else:
        return """
        <div class="whatsapp-btn-disabled">
            Completa Nombre y Dirección para activar el botón de envío
        </div>
        """

def render_fab_and_navbar(nav_view, cart):
    total_items = sum(cart.values())

    # FAB flotante a la DERECHA (visible en catálogo con artículos)
    fab_html = ""
    if nav_view == "catalogo" and total_items > 0:
        fab_html = f"""
        <button class="floating-fab" onclick="triggerAction('nav', 'pedidos')">
            🛒 Ver Carrito ({total_items})
        </button>
        """

    # Navbar blanca con iconos outline (svg) y color activo dinámico
    active_menu = "active" if nav_view == "catalogo" else ""
    active_ped = "active" if nav_view == "pedidos" else ""
    active_conf = "active" if nav_view == "config" else ""
    badge_html = f'<span class="nav-badge">{total_items}</span>' if total_items > 0 else ""

    navbar_html = f"""
    {fab_html}
    <div class="bottom-navbar">
        <button class="nav-item {active_menu}" onclick="triggerAction('nav', 'catalogo')">
            <svg class="nav-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
            <span class="nav-label">Menú</span>
        </button>
        <button class="nav-item {active_ped}" onclick="triggerAction('nav', 'pedidos')">
            <div class="nav-icon-wrap">
                <svg class="nav-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
                {badge_html}
            </div>
            <span class="nav-label">Pedidos</span>
        </button>
        <button class="nav-item {active_conf}" onclick="triggerAction('nav', 'config')">
            <svg class="nav-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <span class="nav-label">Config</span>
        </button>
    </div>
    """
    return navbar_html

# ==========================================
# 4. ESTILOS CSS Y PUENTE JAVASCRIPT
# ==========================================
CUSTOM_CSS = """
footer { display: none !important; }
.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    background-color: #f8fafc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* HEADER FIJO SIEMPRE VISIBLE */
.sticky-header {
    position: sticky;
    top: 0;
    z-index: 900;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.sticky-header img {
    width: 48px;
    height: 48px;
    object-fit: contain;
}
.sticky-header h1 {
    font-size: 1.55rem !important;
    font-weight: 900 !important;
    color: #1e293b !important;
    margin: 0 !important;
    line-height: 1.1 !important;
}
.sticky-header span {
    font-size: 0.8rem !important;
    color: #64748b !important;
    font-weight: 700 !important;
    display: block;
}

/* CONTENEDOR PRINCIPAL */
.main-content-area {
    max-width: 1100px;
    margin: 0 auto;
    padding: 14px 16px 110px 16px !important;
}

/* BUSCADOR FUNCIONAL CON LUPA EN EL CENTRO */
.search-box-wrap {
    position: relative;
    margin-bottom: 16px;
}
.search-box-wrap input {
    background: #ffffff !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 14px !important;
    color: #1e293b !important;
    font-weight: 600 !important;
    padding: 10px 14px 10px 42px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
    width: 100% !important;
}
.search-box-wrap input:focus {
    border-color: #FE8330 !important;
}
.search-icon-svg {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    color: #94a3b8;
    pointer-events: none;
}

/* BANNER PROMO Y PRINCIPAL */
.promo-banner {
    background: linear-gradient(135deg, #FE8330 0%, #FF4500 100%);
    color: #ffffff;
    padding: 12px 16px;
    border-radius: 14px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 14px;
    box-shadow: 0 4px 10px rgba(254, 131, 48, 0.2);
}
.banner-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 6px;
    margin-bottom: 18px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}
.desktop-banner-img {
    width: 100%;
    height: 165px;
    object-fit: cover;
    border-radius: 12px;
    display: block;
}
@media (min-width: 768px) {
    .desktop-banner-img { height: 225px; }
}

.section-title {
    font-size: 1.2rem !important;
    font-weight: 800 !important;
    color: #1e293b !important;
    margin: 4px 0 2px 0 !important;
}
.section-sub {
    font-size: 0.82rem !important;
    color: #64748b !important;
    margin-bottom: 12px !important;
}
.divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 18px 0;
}

/* POPULARES */
.pop-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
    gap: 12px;
}
.pop-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 10px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}
.pop-card img {
    width: 100%;
    height: 95px;
    object-fit: cover;
    border-radius: 10px;
}
.pop-title {
    font-weight: 800;
    font-size: 0.85rem;
    color: #1e293b;
    margin-top: 8px;
}
.pop-price {
    color: #FE8330;
    font-weight: 900;
    font-size: 0.98rem;
    margin: 4px 0 8px 0;
}

/* CATEGORÍAS */
.cat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.cat-btn {
    background: #FE8330;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 0.88rem;
    cursor: pointer;
    transition: 0.2s;
}
.cat-btn.active {
    background: #FF4500;
    box-shadow: 0 4px 12px rgba(255, 69, 0, 0.35);
}

/* CUADRÍCULA DE PRODUCTOS */
.products-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
}
@media (max-width: 767px) {
    .products-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
}
.product-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.product-img {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    border-radius: 12px;
}
.product-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: #1e293b;
    margin-top: 8px;
    line-height: 1.2;
}
.product-desc {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 4px;
}
.product-price {
    font-size: 1.08rem;
    font-weight: 900;
    color: #FE8330;
    margin: 8px 0;
}

/* BOTONES Y CONTROLES DE CANTIDAD */
.btn-orange-sm, .btn-orange-full, .btn-red-full {
    background: #FE8330;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 9px 12px;
    font-weight: 800;
    font-size: 0.88rem;
    cursor: pointer;
    width: 100%;
    transition: 0.2s;
}
.btn-orange-sm:hover, .btn-orange-full:hover { background: #e06c20; }
.btn-red-full {
    background: #FF4500;
    box-shadow: 0 3px 8px rgba(255, 69, 0, 0.25);
}
.btn-red-full:hover { background: #d93800; }

.qty-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 12px;
    padding: 3px;
}
.btn-qty {
    background: #FE8330;
    color: #ffffff;
    border: none;
    border-radius: 9px;
    width: 32px;
    height: 32px;
    font-weight: 900;
    font-size: 1.1rem;
    cursor: pointer;
}
.qty-val {
    font-weight: 900;
    font-size: 1rem;
    color: #1e293b;
}

/* MODAL POP-UP PARA VARIANTES */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.65);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
}
.modal-card {
    background: #ffffff;
    color: #1e293b;
    width: 100%;
    max-width: 520px;
    border-radius: 22px;
    padding: 20px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.25);
    animation: popIn 0.18s ease-out;
}
@keyframes popIn {
    from { transform: scale(0.94); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}
.modal-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 900;
    color: #1e293b;
}
.modal-header p {
    margin: 4px 0 12px 0;
    font-size: 0.85rem;
    color: #64748b;
    font-weight: 600;
}
.modal-body {
    max-height: 55vh;
    overflow-y: auto;
    border-top: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 0;
}
.modal-item-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 4px;
    border-bottom: 1px solid #f1f5f9;
}
.modal-item-row:last-child { border-bottom: none; }
.modal-item-img {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    object-fit: cover;
}
.modal-item-info { flex: 1; }
.modal-item-name {
    font-weight: 800;
    font-size: 0.9rem;
    color: #1e293b;
}
.modal-item-price {
    font-weight: 900;
    font-size: 0.92rem;
    color: #FE8330;
}
.modal-qty { width: 105px; }
.modal-footer { margin-top: 14px; }

/* VISTA DE PEDIDOS / CARRITO */
.cart-count-badge {
    font-size: 0.9rem;
    color: #64748b;
    margin-bottom: 10px;
}
.cart-item-row {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.cart-item-img {
    width: 52px;
    height: 52px;
    border-radius: 10px;
    object-fit: cover;
}
.cart-item-info { flex: 1; }
.cart-item-name {
    font-weight: 800;
    font-size: 0.95rem;
    color: #1e293b;
}
.cart-item-sub {
    font-size: 0.82rem;
    color: #64748b;
    margin-top: 2px;
}
.cart-item-actions {
    display: flex;
    align-items: center;
    gap: 6px;
}
.btn-qty-sm {
    background: #FE8330;
    color: #fff;
    border: none;
    border-radius: 8px;
    width: 28px;
    height: 28px;
    font-weight: 900;
    cursor: pointer;
}
.qty-val-sm {
    font-weight: 900;
    min-width: 18px;
    text-align: center;
    color: #1e293b;
}
.btn-del-sm {
    background: #fee2e2;
    border: none;
    border-radius: 8px;
    padding: 5px 8px;
    cursor: pointer;
    margin-left: 4px;
}
.cart-total-box {
    background: #ffffff;
    border: 2px solid #FE8330;
    border-radius: 14px;
    padding: 14px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 800;
    font-size: 1.1rem;
    color: #1e293b;
    margin: 14px 0;
}
.cart-total-amount {
    color: #FF4500;
    font-size: 1.35rem;
    font-weight: 900;
}
.whatsapp-btn-active {
    background: linear-gradient(135deg, #25D366 0%, #1EBE5D 100%) !important;
    color: #ffffff !important;
    padding: 15px;
    border-radius: 14px;
    text-align: center;
    font-weight: 800;
    font-size: 1.05rem;
    display: block;
    width: 100%;
    text-decoration: none !important;
    box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
    margin-top: 10px;
}
.whatsapp-btn-disabled {
    background: #cbd5e1;
    color: #475569;
    padding: 14px;
    border-radius: 14px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
    margin-top: 10px;
}
.empty-box {
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 16px;
    padding: 32px 16px;
    text-align: center;
    color: #64748b;
}

/* FAB FLOTANTE A LA DERECHA */
.floating-fab {
    position: fixed;
    bottom: 82px;
    right: 20px;
    z-index: 950;
    background: linear-gradient(135deg, #FF4500 0%, #ff6a33 100%);
    color: #ffffff;
    padding: 12px 22px;
    border-radius: 50px;
    font-weight: 800;
    font-size: 0.98rem;
    border: none;
    box-shadow: 0 8px 25px rgba(255, 69, 0, 0.45);
    cursor: pointer;
    transition: transform 0.2s;
}
.floating-fab:hover { transform: scale(1.04); }

/* NAVBAR INFERIOR BLANCA CON ICONOS OUTLINE Y COLOR ACTIVO */
.bottom-navbar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 68px;
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    align-items: center;
    z-index: 960;
    box-shadow: 0 -4px 15px rgba(0,0,0,0.05);
}
.nav-item {
    background: transparent;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    cursor: pointer;
    height: 100%;
    color: #334155;
    transition: 0.15s;
}
.nav-item.active {
    color: #FE8330 !important;
    font-weight: 800;
}
.nav-icon-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.nav-icon {
    width: 24px;
    height: 24px;
    stroke: currentColor;
    fill: none;
}
.nav-label {
    font-size: 0.75rem;
    font-weight: 700;
}
.nav-badge {
    position: absolute;
    top: -5px;
    right: -12px;
    background: #FF4500;
    color: #ffffff;
    font-size: 0.68rem;
    font-weight: 900;
    padding: 2px 6px;
    border-radius: 999px;
    border: 2px solid #ffffff;
}

/* OCULTAR DISPARADOR INTERNO */
#action-bridge {
    position: fixed;
    left: -9999px;
    top: -9999px;
    opacity: 0;
    pointer-events: none;
}
"""

BRIDGE_JS = """
function() {
    window.triggerAction = function(type, payload) {
        const container = document.getElementById('action-bridge');
        if (!container) return;
        const input = container.querySelector('textarea, input');
        if (!input) return;
        const data = JSON.stringify({ type: type, payload: payload, ts: Date.now() });
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set
                          || Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
        if (nativeSetter) {
            nativeSetter.call(input, data);
        } else {
            input.value = data;
        }
        input.dispatchEvent(new Event('input', { bubbles: true }));
    };
}
"""

# ==========================================
# 5. INTERFAZ PRINCIPAL EN GRADIO
# ==========================================
with gr.Blocks(title="Mostacho Botanas", css=CUSTOM_CSS, js=BRIDGE_JS) as demo:
    state_products = gr.State(load_saved_products)
    state_populares = gr.State(load_saved_populares)
    state_banner = gr.State(load_saved_banner)
    state_cart = gr.State({})
    state_nav = gr.State("catalogo")
    state_cat = gr.State("Todo")
    state_modal_base = gr.State("")
    state_admin_auth = gr.State(False)

    action_bridge = gr.Textbox(elem_id="action-bridge", show_label=False)

    # HEADER FIJO SIEMPRE VISIBLE
    gr.HTML(f"""
    <div class="sticky-header">
        <img src="{LOGO_URL}" onerror="this.style.display='none'" />
        <div>
            <h1>Mostacho Botanas</h1>
            <span>Catálogo y pedidos en línea</span>
        </div>
    </div>
    """)

    with gr.Column(elem_classes="main-content-area"):
        # ======================================
        # VISTA 1: CATÁLOGO (MENÚ)
        # ======================================
        with gr.Column(visible=True) as view_catalogo:
            # Buscador con lupa centrada e integrada
            gr.HTML("""
            <div class="search-box-wrap">
                <svg class="search-icon-svg" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
            """)
            search_input = gr.Textbox(
                placeholder="Buscar semillas, cacahuates, pistaches...",
                show_label=False
            )
            catalog_html = gr.HTML()

        # ======================================
        # VISTA 2: PEDIDOS (CARRITO + WHATSAPP)
        # ======================================
        with gr.Column(visible=False) as view_pedidos:
            gr.Markdown("### 🛍️ Carrito de Compras y Pedido")
            cart_html = gr.HTML()
            with gr.Group(visible=False) as delivery_form_group:
                gr.Markdown("#### 🚚 Datos de Entrega")
                cust_name = gr.Textbox(label="Nombre del cliente (Obligatorio)", placeholder="Ej. Juan Pérez")
                cust_addr = gr.Textbox(label="Dirección / Referencias (Obligatorio)", placeholder="Calle, número, colonia...", lines=2)
                cust_notes = gr.Textbox(label="Notas adicionales (Opcional)", placeholder="Ej. Cambio de $500")
                whatsapp_html = gr.HTML()

        # ======================================
        # VISTA 3: CONFIGURACIÓN (PANEL ADMIN)
        # ======================================
        with gr.Column(visible=False) as view_config:
            gr.Markdown("### ⚙️ Panel de Administración y Configuración")

            with gr.Group(visible=True) as admin_login_box:
                admin_pass = gr.Textbox(label="Contraseña de administrador", type="password", placeholder="Clave de 4 dígitos...")
                btn_login = gr.Button("Ingresar", variant="primary")
                login_msg = gr.Markdown("")

            with gr.Group(visible=False) as admin_panel_box:
                with gr.Row():
                    gr.Markdown("✅ **Sesión de administrador activa**")
                    btn_logout = gr.Button("Cerrar Sesión", size="sm")

                with gr.Tabs():
                    with gr.Tab("📦 Editar Productos"):
                        gr.Markdown("💡 *Para agrupar variantes (ej. Frituras con/sin chile), usa el mismo nombre base seguido de la variante entre paréntesis.*")
                        file_excel = gr.File(label="Cargar catálogo desde Excel o CSV (.xlsx, .csv)", file_types=[".xlsx", ".csv"])
                        excel_status = gr.Markdown("")

                        df_products_editor = gr.Dataframe(
                            headers=["id", "name", "category", "price", "description", "image"],
                            datatype=["str", "str", "str", "number", "str", "str"],
                            interactive=True,
                            label="Inventario de Productos (Edita directamente en la tabla)"
                        )
                        btn_save_products = gr.Button("💾 Guardar Cambios de Productos", variant="primary")
                        save_prod_msg = gr.Markdown("")

                    with gr.Tab("⭐ Populares"):
                        pop_selector = gr.CheckboxGroup(label="Selecciona los productos destacados en el inicio")
                        btn_save_pop = gr.Button("💾 Guardar Productos Populares", variant="primary")
                        save_pop_msg = gr.Markdown("")

                    with gr.Tab("🖼️ Imagen Banner"):
                        banner_input = gr.Textbox(label="URL de la imagen del banner (Recomendado: 1200 x 500 px)")
                        btn_save_banner = gr.Button("💾 Guardar Banner", variant="primary")
                        save_banner_msg = gr.Markdown("")

                    with gr.Tab("📤 Subir Imágenes"):
                        upload_img = gr.File(label="Sube una imagen local (PNG, JPG, WEBP)", file_types=["image"])
                        uploaded_path_out = gr.Textbox(label="Ruta generada (cópiala en tu tabla o banner)", interactive=False)

    modal_html = gr.HTML()
    bottom_nav_html = gr.HTML()

    # ==========================================
    # 6. CONTROLADORES Y SINCRONIZACIÓN DE UI
    # ==========================================
    def sync_all_ui(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        valid_ids = {str(p.get("id")) for p in products}
        cart = {k: v for k, v in cart.items() if k in valid_ids and v > 0}

        cat_out = render_catalog_html(products, populares, banner, cat, search_q, cart)
        mod_out = render_modal_html(modal_base, products, cart)
        crt_out, _, order_sum = render_cart_html(products, cart)
        wa_out = render_whatsapp_btn(products, cart, c_name, c_addr, c_notes)
        nav_out = render_fab_and_navbar(nav, cart)

        df_data = pd.DataFrame(products)[["id", "name", "category", "price", "description", "image"]] if products else pd.DataFrame(columns=["id", "name", "category", "price", "description", "image"])
        pop_choices = [f"{p['name']} | {p['id']}" for p in products]
        pop_ids = {str(p.get("id")) for p in populares}
        pop_selected = [f"{p['name']} | {p['id']}" for p in products if str(p.get("id")) in pop_ids]

        return (
            cart,
            gr.update(visible=(nav == "catalogo")),
            gr.update(visible=(nav == "pedidos")),
            gr.update(visible=(nav == "config")),
            cat_out,
            mod_out,
            crt_out,
            gr.update(visible=(len(order_sum) > 0)),
            wa_out,
            nav_out,
            gr.update(visible=(not is_auth)),
            gr.update(visible=is_auth),
            df_data,
            gr.update(choices=pop_choices, value=pop_selected),
            banner
        )

    UI_OUTPUTS = [
        state_cart, view_catalogo, view_pedidos, view_config,
        catalog_html, modal_html, cart_html, delivery_form_group,
        whatsapp_html, bottom_nav_html, admin_login_box, admin_panel_box,
        df_products_editor, pop_selector, banner_input
    ]

    ALL_STATES = [
        state_products, state_populares, state_banner, state_cart,
        state_nav, state_cat, state_modal_base, search_input,
        cust_name, cust_addr, cust_notes, state_admin_auth
    ]

    demo.load(fn=sync_all_ui, inputs=ALL_STATES, outputs=UI_OUTPUTS)

    def handle_bridge_action(raw_json, products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        if raw_json:
            try:
                data = json.loads(raw_json)
                act = data.get("type")
                payload = str(data.get("payload", ""))

                if act == "add":
                    cart[payload] = cart.get(payload, 0) + 1
                elif act == "remove":
                    if payload in cart:
                        if cart[payload] > 1:
                            cart[payload] -= 1
                        else:
                            del cart[payload]
                elif act == "delete":
                    cart.pop(payload, None)
                elif act == "cat":
                    cat = payload
                elif act == "modal":
                    modal_base = payload
                elif act == "close_modal":
                    modal_base = ""
                elif act == "nav":
                    nav = payload
                    modal_base = ""
            except Exception:
                pass

        res = sync_all_ui(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)
        return (nav, cat, modal_base) + res

    action_bridge.input(
        fn=handle_bridge_action,
        inputs=[action_bridge] + ALL_STATES,
        outputs=[state_nav, state_cat, state_modal_base] + UI_OUTPUTS
    )

    search_input.input(fn=sync_all_ui, inputs=ALL_STATES, outputs=UI_OUTPUTS)

    for inp in [cust_name, cust_addr, cust_notes]:
        inp.input(
            fn=render_whatsapp_btn,
            inputs=[state_products, state_cart, cust_name, cust_addr, cust_notes],
            outputs=whatsapp_html
        )

    def check_admin_login(pwd, products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes):
        if pwd == "7031":
            res = sync_all_ui(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, True)
            return (True, "", "") + res
        else:
            res = sync_all_ui(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, False)
            return (False, "❌ Contraseña incorrecta.", pwd) + res

    btn_login.click(
        fn=check_admin_login,
        inputs=[admin_pass, state_products, state_populares, state_banner, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes],
        outputs=[state_admin_auth, login_msg, admin_pass] + UI_OUTPUTS
    )

    def admin_logout(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes):
        res = sync_all_ui(products, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, False)
        return (False,) + res

    btn_logout.click(
        fn=admin_logout,
        inputs=[state_products, state_populares, state_banner, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes],
        outputs=[state_admin_auth] + UI_OUTPUTS
    )

    def process_excel_upload(file_obj, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        if file_obj is None:
            return gr.update(), "", *sync_all_ui(load_saved_products(), populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)
        try:
            if file_obj.name.endswith(".csv"):
                df_up = pd.read_csv(file_obj.name)
            else:
                df_up = pd.read_excel(file_obj.name)

            if "name" not in df_up.columns or "price" not in df_up.columns:
                prods = load_saved_products()
                return prods, "❌ El archivo debe contener al menos las columnas `name` y `price`.", *sync_all_ui(prods, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

            new_list = []
            for idx, row in df_up.iterrows():
                r_id = str(row.get("id", f"excel_{idx}")).strip()
                r_desc = str(row.get("description", "")).strip() if pd.notna(row.get("description")) else ""
                r_img = str(row.get("image", "")).strip()
                img_val = r_img if r_img and r_img.lower() != "nan" and "placeholder" not in r_img else DEFAULT_PRODUCT_IMG

                new_list.append({
                    "id": r_id if r_id and r_id != "nan" else f"excel_{idx}",
                    "name": str(row.get("name", "Producto")),
                    "category": str(row.get("category", "Individual")),
                    "price": float(row.get("price", 0.0)),
                    "description": r_desc if r_desc != "nan" else "",
                    "image": img_val
                })
            new_list = sorted(new_list, key=lambda x: str(x.get("name", "")).lower())
            save_products_to_file(new_list)
            return new_list, "✅ ¡Catálogo cargado y ordenado alfabéticamente!", *sync_all_ui(new_list, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)
        except Exception as e:
            prods = load_saved_products()
            return prods, f"❌ Error al procesar: {e}", *sync_all_ui(prods, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

    file_excel.upload(
        fn=process_excel_upload,
        inputs=[file_excel, state_populares, state_banner, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes, state_admin_auth],
        outputs=[state_products, excel_status] + UI_OUTPUTS
    )

    def save_edited_products(df_edited, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        updated_list = []
        for idx, row in df_edited.iterrows():
            name_val = str(row.get("name", "")).strip()
            if not name_val or name_val.lower() == "nan":
                continue
            raw_id = str(row.get("id", "")).strip()
            prod_id = raw_id if raw_id and raw_id.lower() != "nan" else f"prod_{int(datetime.now().timestamp())}_{idx}"
            raw_img = str(row.get("image", "")).strip()
            prod_img = raw_img if raw_img and raw_img.lower() != "nan" and "placeholder" not in raw_img else DEFAULT_PRODUCT_IMG
            raw_desc = str(row.get("description", "")).strip()
            prod_desc = raw_desc if raw_desc and raw_desc.lower() != "nan" else ""
            cat_val = str(row.get("category", "Individual")).strip()
            if cat_val not in ["Individual", "Para compartir"]:
                cat_val = "Individual"

            try:
                price_val = float(row.get("price", 0.0))
            except Exception:
                price_val = 0.0

            updated_list.append({
                "id": prod_id,
                "name": name_val,
                "category": cat_val,
                "price": price_val,
                "description": prod_desc,
                "image": prod_img
            })

        updated_list = sorted(updated_list, key=lambda x: str(x.get("name", "")).lower())
        save_products_to_file(updated_list)
        return updated_list, "✅ ¡Productos guardados y ordenados!", *sync_all_ui(updated_list, populares, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

    btn_save_products.click(
        fn=save_edited_products,
        inputs=[df_products_editor, state_populares, state_banner, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes, state_admin_auth],
        outputs=[state_products, save_prod_msg] + UI_OUTPUTS
    )

    def save_selected_populares(selected_list, products, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        if not selected_list:
            return gr.update(), "⚠️ Selecciona al menos un producto.", *sync_all_ui(products, load_saved_populares(), banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

        selected_ids = {item.split(" | ")[-1].strip() for item in selected_list}
        new_pops = [
            {
                "id": str(p["id"]),
                "name": p["name"],
                "price": p["price"],
                "image": p.get("image", DEFAULT_PRODUCT_IMG)
            }
            for p in products if str(p["id"]) in selected_ids
        ]
        save_populares_to_file(new_pops)
        return new_pops, "✅ ¡Productos populares actualizados!", *sync_all_ui(products, new_pops, banner, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

    btn_save_pop.click(
        fn=save_selected_populares,
        inputs=[pop_selector, state_products, state_banner, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes, state_admin_auth],
        outputs=[state_populares, save_pop_msg] + UI_OUTPUTS
    )

    def save_new_banner(new_url, products, populares, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth):
        url_clean = (new_url or "").strip() or DEFAULT_BANNER
        save_banner_to_file(url_clean)
        return url_clean, "✅ ¡Banner actualizado con éxito!", *sync_all_ui(products, populares, url_clean, cart, nav, cat, modal_base, search_q, c_name, c_addr, c_notes, is_auth)

    btn_save_banner.click(
        fn=save_new_banner,
        inputs=[banner_input, state_products, state_populares, state_cart, state_nav, state_cat, state_modal_base, search_input, cust_name, cust_addr, cust_notes, state_admin_auth],
        outputs=[state_banner, save_banner_msg] + UI_OUTPUTS
    )

    def handle_image_upload(file_obj):
        if file_obj is None:
            return ""
        filename = os.path.basename(file_obj.name)
        dest_path = os.path.join(UPLOAD_DIR, filename)
        shutil.copy(file_obj.name, dest_path)
        return f"file={UPLOAD_DIR}/{filename}"

    upload_img.upload(fn=handle_image_upload, inputs=upload_img, outputs=uploaded_path_out)

if __name__ == "__main__":
    demo.launch(allowed_paths=[UPLOAD_DIR])