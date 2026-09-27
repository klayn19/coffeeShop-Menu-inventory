import customtkinter as ctk
import sqlite3
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from PIL import Image, ImageTk

# ─────────────────────────────────────────────
#  APPEARANCE
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COFFEE_BROWN  = "#6F4E37"
COFFEE_LIGHT  = "#C4956A"
COFFEE_CREAM  = "#F5E6D3"
COFFEE_DARK   = "#2C1810"
ACCENT        = "#D4956A"

# ─────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────
DB_NAME = "CoffeeShop_DB.sqlite"

def connect_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect_db()
    cur  = conn.cursor()
    # Products / menu items
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code   TEXT    NOT NULL UNIQUE,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL,
            description TEXT
        )
    """)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN image_path TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    # Ingredients / raw stock
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL UNIQUE,
            unit     TEXT    NOT NULL,
            quantity REAL    NOT NULL,
            min_qty  REAL    NOT NULL
        )
    """)
    # Sales transactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name   TEXT    NOT NULL,
            quantity    INTEGER NOT NULL,
            total_price REAL    NOT NULL,
            date        TEXT    NOT NULL
        )
    """)
    conn.commit()

    # Seed sample data if empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample = [
            ("C001","Hot Coffee",    "Hot",   8.00, 50, "Prepared from roasted coffee beans.", "images/C001.png"),
            ("C002","Espresso",      "Hot",   3.00, 40, "One shot of espresso served in a small cup.", "images/C002.png"),
            ("C003","Cappuccino",    "Hot",   7.50, 35, "Prepared from roasted coffee beans.", "images/C003.png"),
            ("C004","Caramel Latte", "Hot",   7.50, 30, "Coffee chilled with ice, milk and vanilla syrup.", "images/C004.png"),
            ("C005","Macchiato",     "Hot",   8.50, 25, "Espresso, dollop of foam, a bold up.", "images/C005.png"),
            ("C006","Caramel Macchiato","Hot",9.50, 20, "Espresso, dollop of foam, caramel or choice of syrup.", "images/C006.png"),
            ("C007","Iced Capp",     "Iced",  9.30, 45, "Espresso, frothy milk, ice, blissful cappuccino magic.", "images/C007.png"),
            ("C008","Iced Coffee",   "Iced",  8.30, 40, "Coffee chilled with ice, milk and vanilla syrup.", "images/C008.png"),
        ]
        cur.executemany(
            "INSERT INTO products (item_code,name,category,price,stock,description,image_path) VALUES (?,?,?,?,?,?,?)",
            sample
        )
        ingredients_sample = [
            ("Coffee Beans","kg",  10.0, 2.0),
            ("Milk",        "L",   15.0, 3.0),
            ("Sugar",       "kg",  5.0,  1.0),
            ("Caramel Syrup","L",  3.0,  0.5),
            ("Ice",         "kg",  8.0,  2.0),
            ("Cups (Small)","pcs", 100,  20.0),
            ("Cups (Large)","pcs", 100,  20.0),
        ]
        cur.executemany(
            "INSERT INTO ingredients (name,unit,quantity,min_qty) VALUES (?,?,?,?)",
            ingredients_sample
        )
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
app = ctk.CTk()
app.title("☕  Coffee Shop Inventory System")
app.geometry("1200x720")
app.resizable(True, True)

# ── Treeview style ────────────────────────────
style = ttk.Style()
style.theme_use("clam")
style.configure("Coffee.Treeview",
                background="#1a0f0a",
                foreground="#f5e6d3",
                rowheight=30,
                fieldbackground="#1a0f0a",
                font=("Segoe UI", 10))
style.configure("Coffee.Treeview.Heading",
                background="#6F4E37",
                foreground="#f5e6d3",
                font=("Segoe UI", 10, "bold"),
                relief="flat")
style.map("Coffee.Treeview",
          background=[("selected","#C4956A")],
          foreground=[("selected","#1a0f0a")])

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
sidebar = ctk.CTkFrame(app, width=200, fg_color="#1a0f0a", corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# Logo area
logo_frame = ctk.CTkFrame(sidebar, fg_color="#2C1810", corner_radius=0, height=100)
logo_frame.pack(fill="x")
logo_frame.pack_propagate(False)
ctk.CTkLabel(logo_frame, text="☕", font=("Segoe UI", 36)).pack(pady=(12,0))
ctk.CTkLabel(logo_frame, text="BREW & BEAN",
             font=("Segoe UI", 11, "bold"),
             text_color=COFFEE_LIGHT).pack()

ctk.CTkLabel(sidebar, text="NAVIGATION",
             font=("Segoe UI", 9),
             text_color="#6F4E37").pack(pady=(20,6), padx=16, anchor="w")

nav_btns = {}
pages    = ["Dashboard", "Menu Items", "Ingredients", "Sales", "Reports"]
icons    = ["🏠","🍵","🌾","💰","📊"]

current_page = ctk.StringVar(value="Dashboard")

def switch_page(page):
    current_page.set(page)
    for name, btn in nav_btns.items():
        if name == page:
            btn.configure(fg_color=COFFEE_BROWN, text_color=COFFEE_CREAM)
        else:
            btn.configure(fg_color="transparent", text_color="#888")
    show_page(page)

for icon, page in zip(icons, pages):
    btn = ctk.CTkButton(
        sidebar, text=f"  {icon}  {page}",
        anchor="w", height=42,
        fg_color="transparent",
        text_color="#888",
        hover_color="#2C1810",
        font=("Segoe UI", 12),
        corner_radius=8,
        command=lambda p=page: switch_page(p)
    )
    btn.pack(fill="x", padx=10, pady=2)
    nav_btns[page] = btn

# Bottom info
ctk.CTkLabel(sidebar, text="v1.0  |  2025",
             font=("Segoe UI", 9),
             text_color="#444").pack(side="bottom", pady=10)

# ─────────────────────────────────────────────
#  MAIN CONTENT AREA
# ─────────────────────────────────────────────
main_area = ctk.CTkFrame(app, fg_color="#120a06", corner_radius=0)
main_area.pack(side="left", fill="both", expand=True)

# Header
header = ctk.CTkFrame(main_area, height=60, fg_color="#1a0f0a", corner_radius=0)
header.pack(fill="x")
header.pack_propagate(False)
lbl_header = ctk.CTkLabel(header, text="Dashboard",
                           font=("Segoe UI", 20, "bold"),
                           text_color=COFFEE_CREAM)
lbl_header.pack(side="left", padx=20, pady=15)
lbl_datetime = ctk.CTkLabel(header, text="",
                             font=("Segoe UI", 10),
                             text_color="#666")
lbl_datetime.pack(side="right", padx=20)

def update_clock():
    lbl_datetime.configure(text=datetime.now().strftime("%A, %B %d %Y   %I:%M %p"))
    app.after(1000, update_clock)
update_clock()

# Page container
page_container = ctk.CTkFrame(main_area, fg_color="#120a06", corner_radius=0)
page_container.pack(fill="both", expand=True, padx=0, pady=0)

pages_frames = {}

def make_frame():
    f = ctk.CTkFrame(page_container, fg_color="#120a06", corner_radius=0)
    return f

# ══════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════
pg_dash = make_frame()
pages_frames["Dashboard"] = pg_dash

def refresh_dashboard():
    for w in pg_dash.winfo_children():
        w.destroy()

    conn = connect_db()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    total_items = cur.fetchone()[0]
    cur.execute("SELECT SUM(quantity) FROM sales")
    total_sold = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(total_price) FROM sales")
    total_revenue = cur.fetchone()[0] or 0.0
    cur.execute("SELECT COUNT(*) FROM ingredients WHERE quantity <= min_qty")
    low_stock = cur.fetchone()[0]
    conn.close()

    # Stat cards row
    cards_frame = ctk.CTkFrame(pg_dash, fg_color="transparent")
    cards_frame.pack(fill="x", padx=20, pady=(20,10))

    stats = [
        ("☕ Menu Items",   str(total_items),       "#6F4E37"),
        ("💰 Total Revenue",f"₱{total_revenue:,.2f}","#2d6a4f"),
        ("📦 Items Sold",   str(total_sold),         "#1f538d"),
        ("⚠️ Low Stock",    str(low_stock),          "#9b2226"),
    ]
    for title, val, color in stats:
        card = ctk.CTkFrame(cards_frame, fg_color=color,
                            corner_radius=12, width=200, height=100)
        card.pack(side="left", padx=8, expand=True, fill="x")
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title,
                     font=("Segoe UI", 11),
                     text_color="#fff").pack(pady=(18,2))
        ctk.CTkLabel(card, text=val,
                     font=("Segoe UI", 22, "bold"),
                     text_color="#fff").pack()

    # Two column section
    two_col = ctk.CTkFrame(pg_dash, fg_color="transparent")
    two_col.pack(fill="both", expand=True, padx=20, pady=10)

    # Recent sales
    left = ctk.CTkFrame(two_col, fg_color="#1a0f0a", corner_radius=12)
    left.pack(side="left", fill="both", expand=True, padx=(0,8))
    ctk.CTkLabel(left, text="Recent Sales",
                 font=("Segoe UI", 13, "bold"),
                 text_color=COFFEE_LIGHT).pack(anchor="w", padx=16, pady=12)
    cols = ("Item","Qty","Total","Date")
    t = ttk.Treeview(left, columns=cols, show="headings",
                     height=8, style="Coffee.Treeview")
    for c in cols:
        t.heading(c, text=c)
    t.column("Item",  width=140)
    t.column("Qty",   width=50,  anchor="center")
    t.column("Total", width=90,  anchor="e")
    t.column("Date",  width=130)
    t.pack(fill="both", expand=True, padx=10, pady=(0,10))
    conn = connect_db()
    cur  = conn.cursor()
    cur.execute("SELECT item_name,quantity,total_price,date FROM sales ORDER BY id DESC LIMIT 10")
    for row in cur.fetchall():
        t.insert("","end", values=(row[0], row[1],
                                   f"₱{row[2]:,.2f}", row[3]))
    conn.close()

    # Low ingredient alert
    right = ctk.CTkFrame(two_col, fg_color="#1a0f0a", corner_radius=12, width=280)
    right.pack(side="right", fill="y", padx=(8,0))
    right.pack_propagate(False)
    ctk.CTkLabel(right, text="⚠️ Low Ingredients",
                 font=("Segoe UI", 13, "bold"),
                 text_color="#e76f51").pack(anchor="w", padx=16, pady=12)
    conn = connect_db()
    cur  = conn.cursor()
    cur.execute("SELECT name,quantity,min_qty,unit FROM ingredients WHERE quantity <= min_qty")
    rows = cur.fetchall()
    conn.close()
    if rows:
        for r in rows:
            f = ctk.CTkFrame(right, fg_color="#2C1810", corner_radius=8)
            f.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(f, text=f"🔴  {r[0]}",
                         font=("Segoe UI", 11, "bold"),
                         text_color=COFFEE_CREAM).pack(anchor="w", padx=10, pady=(6,0))
            ctk.CTkLabel(f, text=f"  Current: {r[1]} {r[3]}  |  Min: {r[2]} {r[3]}",
                         font=("Segoe UI", 9),
                         text_color="#aaa").pack(anchor="w", padx=10, pady=(0,6))
    else:
        ctk.CTkLabel(right, text="✅ All ingredients\nare sufficiently stocked!",
                     font=("Segoe UI", 11),
                     text_color="#4fc3f7").pack(pady=30)


# ══════════════════════════════════════════════
#  PAGE: MENU ITEMS  (full CRUD)
# ══════════════════════════════════════════════
pg_menu = make_frame()
pages_frames["Menu Items"] = pg_menu

# Input row
inp_frame = ctk.CTkFrame(pg_menu, fg_color="#1a0f0a", corner_radius=12)
inp_frame.pack(fill="x", padx=20, pady=(16,6))

fields_menu = {}
field_defs = [
    ("Item Code", "e.g. C009",  100),
    ("Name",      "e.g. Mocha", 160),
    ("Category",  "Hot/Iced",   100),
    ("Price ₱",   "0.00",       90),
    ("Stock",     "0",          70),
    ("Description","optional",  200),
]
for col,(label,ph,w) in enumerate(field_defs):
    ctk.CTkLabel(inp_frame, text=label,
                 font=("Segoe UI",10)).grid(row=0,column=col*2, padx=(10,2), pady=10, sticky="w")
    e = ctk.CTkEntry(inp_frame, placeholder_text=ph, width=w)
    e.grid(row=0, column=col*2+1, padx=(0,6), pady=10)
    fields_menu[label] = e

img_frame = ctk.CTkFrame(inp_frame, fg_color="transparent")
img_frame.grid(row=0, column=12, padx=10, sticky="e")
lbl_menu_img = ctk.CTkLabel(img_frame, text="No Image", width=60, height=60, fg_color="#2C1810")
lbl_menu_img.pack(side="left", padx=5)

current_menu_img_path = ctk.StringVar(value="")

def browse_menu_image():
    path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if path:
        set_menu_image_preview(path)

def set_menu_image_preview(path):
    current_menu_img_path.set(path)
    if os.path.exists(path):
        try:
            pil_img = Image.open(path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60,60))
            lbl_menu_img.configure(image=ctk_img, text="")
            lbl_menu_img._image = ctk_img # keep ref
        except:
            lbl_menu_img.configure(image=None, text="Error")
    else:
        lbl_menu_img.configure(image=None, text="No Image")

ctk.CTkButton(img_frame, text="🖼️ Browse", width=70, height=28, command=browse_menu_image).pack(side="left")

# Category quick buttons
cat_frame = ctk.CTkFrame(pg_menu, fg_color="transparent")
cat_frame.pack(fill="x", padx=20)
ctk.CTkLabel(cat_frame, text="Quick Category:", font=("Segoe UI",10), text_color="#888").pack(side="left",padx=(0,8))
for cat in ["Hot","Iced","Frappe","Tea","Others"]:
    ctk.CTkButton(cat_frame, text=cat, width=70, height=26,
                  fg_color=COFFEE_BROWN, hover_color=COFFEE_DARK,
                  font=("Segoe UI",10),
                  command=lambda c=cat: (fields_menu["Category"].delete(0,"end"),
                                         fields_menu["Category"].insert(0,c))
                  ).pack(side="left", padx=3)

# Action buttons
btn_frame = ctk.CTkFrame(pg_menu, fg_color="transparent")
btn_frame.pack(fill="x", padx=20, pady=6)

# Table
tbl_frame = ctk.CTkFrame(pg_menu, fg_color="#1a0f0a", corner_radius=12)
tbl_frame.pack(fill="both", expand=True, padx=20, pady=(4,16))

cols_menu = ("ID","Code","Name","Category","Price ₱","Stock","Description","Image")
tree_menu = ttk.Treeview(tbl_frame, columns=cols_menu,
                          show="headings", height=14, style="Coffee.Treeview")
for c in cols_menu:
    tree_menu.heading(c, text=c)
tree_menu.column("ID",          width=40,  anchor="center")
tree_menu.column("Code",        width=80,  anchor="center")
tree_menu.column("Name",        width=150)
tree_menu.column("Category",    width=90,  anchor="center")
tree_menu.column("Price ₱",     width=90,  anchor="e")
tree_menu.column("Stock",       width=70,  anchor="center")
tree_menu.column("Description", width=200)
tree_menu.column("Image",       width=100)

sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree_menu.yview)
tree_menu.configure(yscrollcommand=sb.set)
tree_menu.pack(side="left", fill="both", expand=True, padx=4, pady=4)
sb.pack(side="right", fill="y")

def clear_menu_fields():
    for e in fields_menu.values():
        e.delete(0,"end")
    set_menu_image_preview("")

def load_menu():
    for r in tree_menu.get_children():
        tree_menu.delete(r)
    conn = connect_db()
    cur  = conn.cursor()
    cur.execute("SELECT id,item_code,name,category,price,stock,description,image_path FROM products ORDER BY category,name")
    for row in cur.fetchall():
        tree_menu.insert("","end", values=(
            row[0], row[1], row[2], row[3],
            f"₱{row[4]:,.2f}", row[5], row[6] or "", row[7] or ""
        ))
    conn.close()

def add_menu_item():
    code = fields_menu["Item Code"].get().strip()
    name = fields_menu["Name"].get().strip()
    cat  = fields_menu["Category"].get().strip()
    price= fields_menu["Price ₱"].get().strip()
    stock= fields_menu["Stock"].get().strip()
    desc = fields_menu["Description"].get().strip()
    img_path = current_menu_img_path.get()
    
    if not all([code,name,cat,price,stock]):
        messagebox.showerror("Error","All fields (except description) are required.")
        return
    try:
        price = float(price); stock = int(stock)
        if price<0 or stock<0: raise ValueError
    except ValueError:
        messagebox.showerror("Error","Price must be a positive number; Stock must be a non-negative integer.")
        return
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO products (item_code,name,category,price,stock,description,image_path) VALUES (?,?,?,?,?,?,?)",
                    (code,name,cat,price,stock,desc,img_path))
        conn.commit()
        messagebox.showinfo("Success",f"'{name}' added to menu!")
        clear_menu_fields(); load_menu()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error",f"Item code '{code}' already exists.")
    finally:
        conn.close()

def update_menu_item():
    sel = tree_menu.selection()
    if not sel:
        messagebox.showwarning("Warning","Select a menu item to update.")
        return
    row_id = tree_menu.item(sel[0])["values"][0]
    code = fields_menu["Item Code"].get().strip()
    name = fields_menu["Name"].get().strip()
    cat  = fields_menu["Category"].get().strip()
    price= fields_menu["Price ₱"].get().strip()
    stock= fields_menu["Stock"].get().strip()
    desc = fields_menu["Description"].get().strip()
    img_path = current_menu_img_path.get()
    
    if not all([code,name,cat,price,stock]):
        messagebox.showerror("Error","All fields (except description) are required.")
        return
    try:
        price = float(price); stock = int(stock)
        if price<0 or stock<0: raise ValueError
    except ValueError:
        messagebox.showerror("Error","Invalid price or stock value.")
        return
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("""UPDATE products SET item_code=?,name=?,category=?,price=?,stock=?,description=?,image_path=?
                       WHERE id=?""",(code,name,cat,price,stock,desc,img_path,row_id))
        conn.commit()
        messagebox.showinfo("Success",f"'{name}' updated!")
        clear_menu_fields(); load_menu()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error","Item code already exists on another record.")
    finally:
        conn.close()

def delete_menu_item():
    sel = tree_menu.selection()
    if not sel:
        messagebox.showwarning("Warning","Select a menu item to delete.")
        return
    vals = tree_menu.item(sel[0])["values"]
    if not messagebox.askyesno("Confirm",f"Delete '{vals[2]}'?"):
        return
    conn = connect_db(); cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (vals[0],))
    conn.commit(); conn.close()
    clear_menu_fields(); load_menu()
    messagebox.showinfo("Deleted",f"'{vals[2]}' removed from menu.")

def on_menu_select(event):
    sel = tree_menu.selection()
    if not sel: return
    vals = tree_menu.item(sel[0])["values"]
    keys = list(fields_menu.keys())
    data = [vals[1], vals[2], vals[3],
            str(vals[4]).replace("₱","").replace(",",""),
            str(vals[5]), vals[6]]
    for k,v in zip(keys, data):
        fields_menu[k].delete(0,"end")
        fields_menu[k].insert(0, str(v))
    
    # Retrieve and safely handle the image path (it may be "None" or empty)
    img_val = vals[7] if len(vals)>7 and vals[7] and str(vals[7]) != "None" else ""
    set_menu_image_preview(str(img_val))

tree_menu.bind("<<TreeviewSelect>>", on_menu_select)

for txt,cmd,color in [
    ("➕ Add Item",    add_menu_item,    COFFEE_BROWN),
    ("✏️ Update",      update_menu_item, "#2d6a4f"),
    ("🗑 Delete",      delete_menu_item, "#9b2226"),
    ("🔄 Refresh",     load_menu,        "#555"),
    ("✖ Clear Fields", clear_menu_fields,"#333"),
]:
    ctk.CTkButton(btn_frame, text=txt, command=cmd,
                  fg_color=color, width=130, height=34).pack(side="left", padx=5)


# ══════════════════════════════════════════════
#  PAGE: INGREDIENTS
# ══════════════════════════════════════════════
pg_ingr = make_frame()
pages_frames["Ingredients"] = pg_ingr

ingr_inp = ctk.CTkFrame(pg_ingr, fg_color="#1a0f0a", corner_radius=12)
ingr_inp.pack(fill="x", padx=20, pady=(16,6))

fields_ingr = {}
ingr_defs = [
    ("Ingredient Name","e.g. Oat Milk", 180),
    ("Unit",           "kg/L/pcs",       90),
    ("Quantity",       "0.0",            90),
    ("Min. Quantity",  "0.0",            90),
]
for col,(label,ph,w) in enumerate(ingr_defs):
    ctk.CTkLabel(ingr_inp, text=label,
                 font=("Segoe UI",10)).grid(row=0,column=col*2, padx=(12,4), pady=12, sticky="w")
    e = ctk.CTkEntry(ingr_inp, placeholder_text=ph, width=w)
    e.grid(row=0, column=col*2+1, padx=(0,8), pady=12)
    fields_ingr[label] = e

ingr_btn = ctk.CTkFrame(pg_ingr, fg_color="transparent")
ingr_btn.pack(fill="x", padx=20, pady=4)

ingr_tbl = ctk.CTkFrame(pg_ingr, fg_color="#1a0f0a", corner_radius=12)
ingr_tbl.pack(fill="both", expand=True, padx=20, pady=(4,16))

cols_ingr = ("ID","Name","Unit","Quantity","Min Qty","Status")
tree_ingr = ttk.Treeview(ingr_tbl, columns=cols_ingr,
                          show="headings", height=14, style="Coffee.Treeview")
for c in cols_ingr:
    tree_ingr.heading(c, text=c)
tree_ingr.column("ID",       width=50,  anchor="center")
tree_ingr.column("Name",     width=200)
tree_ingr.column("Unit",     width=80,  anchor="center")
tree_ingr.column("Quantity", width=110, anchor="center")
tree_ingr.column("Min Qty",  width=110, anchor="center")
tree_ingr.column("Status",   width=120, anchor="center")

sb2 = ttk.Scrollbar(ingr_tbl, orient="vertical", command=tree_ingr.yview)
tree_ingr.configure(yscrollcommand=sb2.set)
tree_ingr.pack(side="left", fill="both", expand=True, padx=4, pady=4)
sb2.pack(side="right", fill="y")

def clear_ingr_fields():
    for e in fields_ingr.values():
        e.delete(0,"end")

def load_ingredients():
    for r in tree_ingr.get_children():
        tree_ingr.delete(r)
    conn = connect_db(); cur = conn.cursor()
    cur.execute("SELECT id,name,unit,quantity,min_qty FROM ingredients ORDER BY name")
    for row in cur.fetchall():
        status = "✅ OK" if row[3] > row[4] else "⚠️ LOW"
        tree_ingr.insert("","end", values=(row[0],row[1],row[2],
                                            f"{row[3]} {row[2]}",
                                            f"{row[4]} {row[2]}", status))
    conn.close()

def add_ingredient():
    name = fields_ingr["Ingredient Name"].get().strip()
    unit = fields_ingr["Unit"].get().strip()
    qty  = fields_ingr["Quantity"].get().strip()
    mq   = fields_ingr["Min. Quantity"].get().strip()
    if not all([name,unit,qty,mq]):
        messagebox.showerror("Error","All fields are required."); return
    try:
        qty=float(qty); mq=float(mq)
        if qty<0 or mq<0: raise ValueError
    except ValueError:
        messagebox.showerror("Error","Quantity values must be positive numbers."); return
    conn=connect_db(); cur=conn.cursor()
    try:
        cur.execute("INSERT INTO ingredients (name,unit,quantity,min_qty) VALUES (?,?,?,?)",
                    (name,unit,qty,mq))
        conn.commit()
        messagebox.showinfo("Success",f"Ingredient '{name}' added!")
        clear_ingr_fields(); load_ingredients()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error",f"Ingredient '{name}' already exists.")
    finally:
        conn.close()

def update_ingredient():
    sel = tree_ingr.selection()
    if not sel:
        messagebox.showwarning("Warning","Select an ingredient to update."); return
    row_id = tree_ingr.item(sel[0])["values"][0]
    name = fields_ingr["Ingredient Name"].get().strip()
    unit = fields_ingr["Unit"].get().strip()
    qty  = fields_ingr["Quantity"].get().strip()
    mq   = fields_ingr["Min. Quantity"].get().strip()
    if not all([name,unit,qty,mq]):
        messagebox.showerror("Error","All fields are required."); return
    try:
        qty=float(qty); mq=float(mq)
    except ValueError:
        messagebox.showerror("Error","Invalid quantity values."); return
    conn=connect_db(); cur=conn.cursor()
    cur.execute("UPDATE ingredients SET name=?,unit=?,quantity=?,min_qty=? WHERE id=?",
                (name,unit,qty,mq,row_id))
    conn.commit(); conn.close()
    messagebox.showinfo("Success","Ingredient updated!")
    clear_ingr_fields(); load_ingredients()

def delete_ingredient():
    sel = tree_ingr.selection()
    if not sel:
        messagebox.showwarning("Warning","Select an ingredient to delete."); return
    vals = tree_ingr.item(sel[0])["values"]
    if not messagebox.askyesno("Confirm",f"Delete '{vals[1]}'?"): return
    conn=connect_db(); cur=conn.cursor()
    cur.execute("DELETE FROM ingredients WHERE id=?", (vals[0],))
    conn.commit(); conn.close()
    clear_ingr_fields(); load_ingredients()

def on_ingr_select(event):
    sel = tree_ingr.selection()
    if not sel: return
    vals = tree_ingr.item(sel[0])["values"]
    keys = list(fields_ingr.keys())
    raw_qty = str(vals[3]).split()[0]
    raw_mq  = str(vals[4]).split()[0]
    for k,v in zip(keys,[vals[1],vals[2],raw_qty,raw_mq]):
        fields_ingr[k].delete(0,"end")
        fields_ingr[k].insert(0,str(v))

tree_ingr.bind("<<TreeviewSelect>>", on_ingr_select)

for txt,cmd,color in [
    ("➕ Add",         add_ingredient,    COFFEE_BROWN),
    ("✏️ Update",      update_ingredient, "#2d6a4f"),
    ("🗑 Delete",      delete_ingredient, "#9b2226"),
    ("🔄 Refresh",     load_ingredients,  "#555"),
    ("✖ Clear",        clear_ingr_fields, "#333"),
]:
    ctk.CTkButton(ingr_btn, text=txt, command=cmd,
                  fg_color=color, width=120, height=34).pack(side="left", padx=5)


# ══════════════════════════════════════════════
#  PAGE: SALES
# ══════════════════════════════════════════════
pg_sales = make_frame()
pages_frames["Sales"] = pg_sales

cart_items = []

# Top controls
sales_top = ctk.CTkFrame(pg_sales, fg_color="#1a0f0a", corner_radius=12)
sales_top.pack(fill="x", padx=20, pady=(16,6))

lbl_sales_img = ctk.CTkLabel(sales_top, text="No Img", width=60, height=60, fg_color="#2C1810")
lbl_sales_img.grid(row=0,column=0, padx=12, pady=12, rowspan=2)

ctk.CTkLabel(sales_top, text="Select Item:", font=("Segoe UI",11)).grid(row=0,column=1, padx=4, pady=12, sticky="w")
combo_item = ctk.CTkComboBox(sales_top, values=[], width=200)
combo_item.grid(row=0,column=2, padx=8, pady=12)

ctk.CTkLabel(sales_top, text="Qty:", font=("Segoe UI",11)).grid(row=0,column=3, padx=8, pady=12, sticky="w")
entry_sale_qty = ctk.CTkEntry(sales_top, placeholder_text="1", width=70)
entry_sale_qty.grid(row=0,column=4, padx=8, pady=12)

lbl_item_info = ctk.CTkLabel(sales_top, text="", font=("Segoe UI",10), text_color=COFFEE_LIGHT)
lbl_item_info.grid(row=0,column=5, padx=16, pady=12, sticky="w")

def refresh_sales_dropdown():
    conn=connect_db(); cur=conn.cursor()
    cur.execute("SELECT name FROM products WHERE stock>0 ORDER BY name")
    names=[r[0] for r in cur.fetchall()]
    conn.close()
    combo_item.configure(values=names)
    if names: combo_item.set(names[0]); update_item_info()
    else: combo_item.set("")

def update_item_info(event=None):
    name=combo_item.get()
    if not name: return
    conn=connect_db(); cur=conn.cursor()
    cur.execute("SELECT price,stock,category,image_path FROM products WHERE name=?", (name,))
    row=cur.fetchone(); conn.close()
    if row:
        lbl_item_info.configure(
            text=f"Category: {row[2]}   |   Price: ₱{row[0]:,.2f}   |   Stock: {row[1]}")
        img_path = row[3]
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60,60))
                lbl_sales_img.configure(image=ctk_img, text="")
                lbl_sales_img._image = ctk_img
            except:
                lbl_sales_img.configure(image=None, text="Error")
        else:
            lbl_sales_img.configure(image=None, text="No Img")

combo_item.configure(command=update_item_info)

def add_to_cart():
    name=combo_item.get().strip()
    qty_s=entry_sale_qty.get().strip()
    if not name:
        messagebox.showerror("Error","Select a product."); return
    if not qty_s:
        messagebox.showerror("Error","Quantity is required."); return
    try:
        qty=int(qty_s)
        if qty<=0: raise ValueError
    except ValueError:
        messagebox.showerror("Error","Quantity must be a positive integer."); return
    conn=connect_db(); cur=conn.cursor()
    cur.execute("SELECT price,stock FROM products WHERE name=?", (name,))
    row=cur.fetchone(); conn.close()
    if not row: return
    price,stock=row
    existing=sum(i["qty"] for i in cart_items if i["name"]==name)
    if existing+qty>stock:
        messagebox.showerror("Error",
            f"Not enough stock!\nAvailable: {stock}  |  In cart already: {existing}"); return
    for item in cart_items:
        if item["name"]==name:
            item["qty"]+=qty; item["subtotal"]=item["qty"]*price; break
    else:
        cart_items.append({"name":name,"price":price,"qty":qty,"subtotal":qty*price})
    entry_sale_qty.delete(0,"end")
    refresh_cart()

ctk.CTkButton(sales_top, text="➕ Add to Cart", command=add_to_cart,
              fg_color=COFFEE_BROWN, width=130).grid(row=0,column=6,padx=12,pady=12)

# Cart table
cart_frame = ctk.CTkFrame(pg_sales, fg_color="#1a0f0a", corner_radius=12)
cart_frame.pack(fill="both", expand=True, padx=20, pady=6)

cols_cart = ("Item","Unit Price","Qty","Subtotal")
tree_cart = ttk.Treeview(cart_frame, columns=cols_cart,
                          show="headings", height=10, style="Coffee.Treeview")
for c in cols_cart:
    tree_cart.heading(c, text=c)
tree_cart.column("Item",       width=250)
tree_cart.column("Unit Price", width=120, anchor="e")
tree_cart.column("Qty",        width=80,  anchor="center")
tree_cart.column("Subtotal",   width=130, anchor="e")
tree_cart.pack(fill="both", expand=True, padx=6, pady=6)

# Bottom bar
sales_bot = ctk.CTkFrame(pg_sales, fg_color="#1a0f0a", corner_radius=12)
sales_bot.pack(fill="x", padx=20, pady=(4,16))

lbl_cart_total = ctk.CTkLabel(sales_bot, text="Total:  ₱0.00",
                               font=("Segoe UI",18,"bold"), text_color=COFFEE_LIGHT)
lbl_cart_total.pack(side="left", padx=20, pady=12)

def refresh_cart():
    for r in tree_cart.get_children(): tree_cart.delete(r)
    total=0.0
    for item in cart_items:
        tree_cart.insert("","end", values=(
            item["name"], f"₱{item['price']:,.2f}",
            item["qty"],  f"₱{item['subtotal']:,.2f}"))
        total+=item["subtotal"]
    lbl_cart_total.configure(text=f"Total:  ₱{total:,.2f}")

def remove_from_cart():
    sel=tree_cart.selection()
    if not sel:
        messagebox.showwarning("Warning","Select an item to remove."); return
    idx=tree_cart.index(sel[0])
    cart_items.pop(idx); refresh_cart()

def clear_cart():
    cart_items.clear(); refresh_cart()

def complete_sale():
    if not cart_items:
        messagebox.showwarning("Warning","Cart is empty!"); return
    conn=connect_db(); cur=conn.cursor()
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_all=0.0
    try:
        for item in cart_items:
            cur.execute("SELECT stock FROM products WHERE name=?", (item["name"],))
            r=cur.fetchone()
            if not r or r[0]<item["qty"]:
                messagebox.showerror("Error",f"Insufficient stock for '{item['name']}'."); conn.close(); return
            cur.execute("UPDATE products SET stock=stock-? WHERE name=?", (item["qty"],item["name"]))
            cur.execute("INSERT INTO sales (item_name,quantity,total_price,date) VALUES (?,?,?,?)",
                        (item["name"],item["qty"],item["subtotal"],now))
            total_all+=item["subtotal"]
        conn.commit()
        summary="\n".join(f"  {i['name']} x{i['qty']}  =  ₱{i['subtotal']:,.2f}" for i in cart_items)
        messagebox.showinfo("✅ Sale Complete!",
            f"Transaction recorded!\n\n{summary}\n{'─'*38}\n  TOTAL:  ₱{total_all:,.2f}\n  {now}")
        cart_items.clear(); refresh_cart()
        refresh_sales_dropdown(); load_menu()
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Error",f"Sale failed:\n{e}")
    finally:
        conn.close()

for txt,cmd,color in [
    ("🗑 Remove Selected", remove_from_cart, "#9b2226"),
    ("❌ Clear Cart",       clear_cart,       "#555"),
    ("✅ Complete Sale",    complete_sale,    "#2d6a4f"),
]:
    ctk.CTkButton(sales_bot, text=txt, command=cmd,
                  fg_color=color, width=170).pack(side="right", padx=8, pady=10)


# ══════════════════════════════════════════════
#  PAGE: REPORTS
# ══════════════════════════════════════════════
pg_report = make_frame()
pages_frames["Reports"] = pg_report

def refresh_reports():
    for w in pg_report.winfo_children(): w.destroy()

    conn=connect_db(); cur=conn.cursor()

    # Top row – summary boxes
    top=ctk.CTkFrame(pg_report, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(16,10))

    cur.execute("SELECT SUM(total_price) FROM sales")
    rev=cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(quantity) FROM sales")
    sold=cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT date) FROM sales")
    days=cur.fetchone()[0] or 1
    avg=rev/days if days else 0

    for title,val,color in [
        ("Total Revenue",  f"₱{rev:,.2f}",   "#2d6a4f"),
        ("Items Sold",     str(sold),          COFFEE_BROWN),
        ("Avg Daily Sales",f"₱{avg:,.2f}",   "#1f538d"),
    ]:
        box=ctk.CTkFrame(top, fg_color=color, corner_radius=12, height=90)
        box.pack(side="left", fill="x", expand=True, padx=8)
        box.pack_propagate(False)
        ctk.CTkLabel(box, text=title, font=("Segoe UI",11), text_color="#fff").pack(pady=(16,2))
        ctk.CTkLabel(box, text=val, font=("Segoe UI",20,"bold"), text_color="#fff").pack()

    two=ctk.CTkFrame(pg_report, fg_color="transparent")
    two.pack(fill="both", expand=True, padx=20, pady=8)

    # Best sellers
    left=ctk.CTkFrame(two, fg_color="#1a0f0a", corner_radius=12)
    left.pack(side="left", fill="both", expand=True, padx=(0,8))
    ctk.CTkLabel(left, text="🏆 Best Selling Items",
                 font=("Segoe UI",13,"bold"), text_color=COFFEE_LIGHT).pack(anchor="w",padx=16,pady=12)
    cols_bs=("Rank","Item","Total Sold","Revenue")
    t_bs=ttk.Treeview(left, columns=cols_bs, show="headings", height=8, style="Coffee.Treeview")
    for c in cols_bs: t_bs.heading(c,text=c)
    t_bs.column("Rank",       width=50,  anchor="center")
    t_bs.column("Item",       width=180)
    t_bs.column("Total Sold", width=100, anchor="center")
    t_bs.column("Revenue",    width=110, anchor="e")
    t_bs.pack(fill="both", expand=True, padx=8, pady=(0,8))
    cur.execute("""SELECT item_name, SUM(quantity), SUM(total_price)
                   FROM sales GROUP BY item_name ORDER BY SUM(quantity) DESC LIMIT 10""")
    for rank,row in enumerate(cur.fetchall(),1):
        t_bs.insert("","end", values=(f"#{rank}", row[0], row[1], f"₱{row[2]:,.2f}"))

    # Sales history
    right=ctk.CTkFrame(two, fg_color="#1a0f0a", corner_radius=12, width=360)
    right.pack(side="right", fill="y", padx=(8,0))
    right.pack_propagate(False)
    ctk.CTkLabel(right, text="📋 Full Sales History",
                 font=("Segoe UI",13,"bold"), text_color=COFFEE_LIGHT).pack(anchor="w",padx=16,pady=12)
    cols_sh=("Item","Qty","Total","Date")
    t_sh=ttk.Treeview(right, columns=cols_sh, show="headings", height=8, style="Coffee.Treeview")
    for c in cols_sh: t_sh.heading(c,text=c)
    t_sh.column("Item",  width=120)
    t_sh.column("Qty",   width=50, anchor="center")
    t_sh.column("Total", width=90, anchor="e")
    t_sh.column("Date",  width=130)
    t_sh.pack(fill="both", expand=True, padx=8, pady=(0,8))
    cur.execute("SELECT item_name,quantity,total_price,date FROM sales ORDER BY id DESC")
    for row in cur.fetchall():
        t_sh.insert("","end", values=(row[0],row[1],f"₱{row[2]:,.2f}",row[3]))

    conn.close()


# ══════════════════════════════════════════════
#  PAGE SWITCHER
# ══════════════════════════════════════════════
def show_page(page):
    lbl_header.configure(text=page)
    for f in pages_frames.values():
        f.pack_forget()
    pages_frames[page].pack(fill="both", expand=True)
    if   page=="Dashboard":  refresh_dashboard()
    elif page=="Menu Items": load_menu()
    elif page=="Ingredients":load_ingredients()
    elif page=="Sales":      refresh_sales_dropdown()
    elif page=="Reports":    refresh_reports()

# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────
switch_page("Dashboard")
app.mainloop()