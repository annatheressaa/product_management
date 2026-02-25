import customtkinter as ctk
import mysql.connector
from tkinter import messagebox
import datetime

# --- SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_db():
    try:
        return mysql.connector.connect(
            host="localhost", user="root", password="", database="NexusSupply"
        )
    except Exception as e:
        messagebox.showerror("Connection Error", f"Is XAMPP MySQL running?\n{e}")
        return None

class NexusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NexusSupply | Management & History")
        self.geometry("1300x850")
        self.role = None
        self.cart = []  # List to store items before confirming order
        self.login_page()

    def clear(self):
        for widget in self.winfo_children(): widget.destroy()

    # --- LOGIN PAGE ---
    def login_page(self):
        self.clear()
        self.cart = [] # Reset cart on logout
        frame = ctk.CTkFrame(self, width=400, height=450, corner_radius=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(frame, text="NEXUS SUPPLY", font=("Impact", 45), text_color="#3B8ED0").pack(pady=(40, 10))
        ctk.CTkLabel(frame, text="Inventory Ecosystem", font=("Arial", 12), text_color="gray").pack(pady=(0, 30))
        
        self.role_select = ctk.CTkOptionMenu(frame, values=["admin", "customer"], width=250, corner_radius=10)
        self.role_select.pack(pady=10)
        
        self.p_entry = ctk.CTkEntry(frame, placeholder_text="Password (use 123)", show="*", width=250, corner_radius=10)
        self.p_entry.pack(pady=10)
        
        ctk.CTkButton(frame, text="LOGIN", width=250, height=45, corner_radius=10, font=("Arial", 14, "bold"), command=self.auth).pack(pady=30)

    def auth(self):
        if self.p_entry.get() == "123":
            self.role = self.role_select.get()
            self.dashboard(self.role)
        else:
            messagebox.showerror("Error", "Invalid Password.")

    # --- MAIN DASHBOARD ---
    def dashboard(self, role):
        self.clear()
        
        # Sidebar
        sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(sidebar, text=f"NEXUS\n{role.upper()}", font=("Bahnschrift", 24, "bold"), text_color="#3B8ED0").pack(pady=40)

        # Main Navigation
        ctk.CTkButton(sidebar, text="📦 Inventory", height=45, corner_radius=12, command=self.show_inventory).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(sidebar, text="📜 History", height=45, corner_radius=12, command=self.show_history).pack(pady=10, padx=20, fill="x")
        
        if role == 'admin':
            ctk.CTkButton(sidebar, text="🛠️ Manage Items", height=45, corner_radius=12, fg_color="#2980b9", command=self.show_admin_controls).pack(pady=10, padx=20, fill="x")
            ctk.CTkButton(sidebar, text="📊 Financials", height=45, corner_radius=12, fg_color="#27AE60", command=self.show_report).pack(pady=10, padx=20, fill="x")
        
        ctk.CTkButton(sidebar, text="🚪 Logout", height=45, corner_radius=12, fg_color="#C0392B", hover_color="#922B21", command=self.login_page).pack(side="bottom", pady=30, padx=20, fill="x")

        # Dynamic Content Area
        self.main_view = ctk.CTkFrame(self, corner_radius=20, fg_color="transparent")
        self.main_view.pack(side="left", fill="both", expand=True, padx=25, pady=25)

        # Cart View for Customers
        if role == 'customer':
            self.cart_view = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#1e1e1e")
            self.cart_view.pack(side="right", fill="y")
            self.update_cart_display()

        self.show_inventory()

    # --- INVENTORY & CART LOGIC ---
    def show_inventory(self):
        for w in self.main_view.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Product Catalog", font=("Arial", 28, "bold")).pack(side="left")
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_grid())
        ctk.CTkEntry(header, textvariable=self.search_var, placeholder_text="🔍 Search products...", width=300, corner_radius=20).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.refresh_grid()

    def refresh_grid(self):
        for w in self.scroll.winfo_children(): w.destroy()
        db = get_db()
        if not db: return
        cursor = db.cursor()
        cursor.execute("SELECT ProductID, Name, Price, StockLevel FROM Products WHERE Name LIKE %s", (f"%{self.search_var.get()}%",))
        
        for pid, name, price, stock in cursor.fetchall():
            card = ctk.CTkFrame(self.scroll, height=90, corner_radius=15, fg_color="#2B2B2B")
            card.pack(pady=8, padx=10, fill="x")
            
            ctk.CTkLabel(card, text=name, font=("Arial", 16, "bold"), width=250, anchor="w").pack(side="left", padx=20)
            ctk.CTkLabel(card, text=f"${price:.2f}", font=("Arial", 14), text_color="#3B8ED0", width=100).pack(side="left")
            
            if self.role == 'customer':
                q_var = ctk.IntVar(value=1)
                ctk.CTkButton(card, text="ADD TO CART", width=110, height=35, fg_color="#3498DB", corner_radius=8,
                              command=lambda p=pid, n=name, pr=price, q=q_var: self.add_to_cart(p, n, pr, q.get())).pack(side="right", padx=15)
                ctk.CTkButton(card, text="+", width=30, height=30, command=lambda v=q_var: v.set(v.get()+1)).pack(side="right")
                ctk.CTkLabel(card, textvariable=q_var, width=35, font=("Arial", 14, "bold")).pack(side="right")
                ctk.CTkButton(card, text="-", width=30, height=30, command=lambda v=q_var: v.set(max(1, v.get()-1))).pack(side="right")
            else:
                ctk.CTkLabel(card, text=f"Stock: {stock}", width=100, text_color="gray").pack(side="right", padx=20)
        db.close()

    def add_to_cart(self, pid, name, price, qty):
        for item in self.cart:
            if item['id'] == pid:
                item['qty'] += qty
                self.update_cart_display()
                return
        self.cart.append({'id': pid, 'name': name, 'price': float(price), 'qty': qty})
        self.update_cart_display()

    def update_cart_display(self):
        for w in self.cart_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.cart_view, text="SHOPPING CART", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=25)
        
        scroll_cart = ctk.CTkScrollableFrame(self.cart_view, fg_color="transparent", height=450)
        scroll_cart.pack(fill="both", expand=True, padx=10)

        total = 0
        for item in self.cart:
            subtotal = item['price'] * item['qty']
            total += subtotal
            item_frame = ctk.CTkFrame(scroll_cart, fg_color="#262626", corner_radius=8)
            item_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(item_frame, text=f"{item['name']}\n{item['qty']} x ${item['price']:.2f}", font=("Arial", 12), justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(item_frame, text=f"${subtotal:.2f}", font=("Arial", 13, "bold"), text_color="#3B8ED0").pack(side="right", padx=10)
        
        ctk.CTkLabel(self.cart_view, text=f"TOTAL: ${total:.2f}", font=("Arial", 24, "bold"), text_color="#27AE60").pack(pady=20)
        
        if self.cart:
            ctk.CTkButton(self.cart_view, text="✅ CONFIRM ORDER", height=50, fg_color="#27AE60", font=("Arial", 14, "bold"), 
                          command=self.process_full_order).pack(pady=10, padx=20, fill="x")
            ctk.CTkButton(self.cart_view, text="Clear Cart", fg_color="#C0392B", command=lambda: [self.cart.clear(), self.update_cart_display()]).pack(pady=5, padx=20, fill="x")

    def process_full_order(self):
        db = get_db(); cursor = db.cursor()
        try:
            grand_total = sum(item['price'] * item['qty'] for item in self.cart)
            cursor.execute("INSERT INTO Orders (TotalAmount) VALUES (%s)", (grand_total,))
            order_id = cursor.lastrowid

            for item in self.cart:
                cursor.execute("INSERT INTO Order_Items (OrderID, ProductID, Quantity, PriceAtSale) VALUES (%s, %s, %s, %s)", 
                               (order_id, item['id'], item['qty'], item['price']))
            
            db.commit()
            self.generate_receipt(order_id, grand_total) # New Invoice Generator
            messagebox.showinfo("Success", f"ORDER IS SUCCESSFUL!\n\nOrder ID: {order_id}\nInvoice saved to project folder.")
            self.cart = []
            self.update_cart_display()
            self.refresh_grid()
        except Exception as e:
            messagebox.showerror("Error", f"Order Failed: {e}")
        finally:
            db.close()

    def generate_receipt(self, order_id, total):
        filename = f"Receipt_Order_{order_id}.txt"
        with open(filename, "w") as f:
            f.write("="*30 + "\n")
            f.write("   NEXUS SUPPLY INVOICE\n")
            f.write("="*30 + "\n")
            f.write(f"Order ID: {order_id}\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 30 + "\n")
            for item in self.cart:
                f.write(f"{item['name']:<15} x{item['qty']}  ${item['price']*item['qty']:.2f}\n")
            f.write("-" * 30 + "\n")
            f.write(f"GRAND TOTAL:        ${total:.2f}\n")
            f.write("="*30 + "\n")
            f.write("   THANK YOU FOR SHOPPING!\n")

    # --- HISTORY VIEW ---
    def show_history(self):
        for w in self.main_view.winfo_children(): w.destroy()
        
        header_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Transaction Records", font=("Arial", 28, "bold")).pack(side="left")

        # Search by Order ID
        self.hist_search = ctk.CTkEntry(header_frame, placeholder_text="Enter Order ID (e.g. 7)", width=200)
        self.hist_search.pack(side="right", padx=10)
        ctk.CTkButton(header_frame, text="Find Order", width=100, command=self.view_specific_order).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        db = get_db(); cursor = db.cursor()
        # This query gets a summary of each order
        cursor.execute("SELECT OrderID, SUM(TotalPrice), OrderDate FROM vw_OrderHistory GROUP BY OrderID ORDER BY OrderDate DESC")
        
        for oid, total, odate in cursor.fetchall():
            f = ctk.CTkFrame(scroll, fg_color="#2B2B2B", corner_radius=10)
            f.pack(fill="x", pady=3)
            
            ctk.CTkLabel(f, text=f"ORDER #{oid}", font=("Arial", 14, "bold"), width=120).pack(side="left", padx=15)
            ctk.CTkLabel(f, text=f"Total: ${total:.2f}", text_color="#27AE60", width=150).pack(side="left")
            ctk.CTkLabel(f, text=str(odate), text_color="gray").pack(side="left", padx=20)
            
            # Button to see everything in this Order ID
            ctk.CTkButton(f, text="VIEW ITEMS", width=100, height=30, fg_color="#3498DB",
                          command=lambda o=oid: self.view_specific_order(o)).pack(side="right", padx=15)
        db.close()
    def view_specific_order(self, order_id=None):
        # Use search box if no ID passed from button
        if not order_id:
            order_id = self.hist_search.get()
        
        if not order_id: return

        # Create a popup window
        pop = ctk.CTkToplevel(self)
        pop.title(f"Details for Order #{order_id}")
        pop.geometry("500x400")
        pop.attributes("-topmost", True) # Keep it on top

        ctk.CTkLabel(pop, text=f"ORDER RECEIPT #{order_id}", font=("Arial", 20, "bold")).pack(pady=20)
        
        txt_area = ctk.CTkTextbox(pop, width=450, height=250)
        txt_area.pack(pady=10, padx=20)
        
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT ProductName, Quantity, TotalPrice FROM vw_OrderHistory WHERE OrderID = %s", (order_id,))
        
        rows = cursor.fetchall()
        if not rows:
            txt_area.insert("0.0", "No data found for this Order ID.")
        else:
            txt_area.insert("0.0", f"{'Product':<20} | {'Qty':<5} | {'Subtotal'}\n")
            txt_area.insert("end", "-"*45 + "\n")
            grand_total = 0
            for name, qty, price in rows:
                txt_area.insert("end", f"{name:<20} | {qty:<5} | ${price:.2f}\n")
                grand_total += price
            
            txt_area.insert("end", "\n" + "-"*45)
            txt_area.insert("end", f"\nGRAND TOTAL: ${grand_total:.2f}")
        
        db.close()
        ctk.CTkButton(pop, text="CLOSE", command=pop.destroy).pack(pady=10)
    # --- ADMIN CONTROLS ---
    def show_admin_controls(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="Stock Management", font=("Arial", 28, "bold")).pack(pady=(0, 20), anchor="w")
        
        container = ctk.CTkFrame(self.main_view, fg_color="transparent"); container.pack(fill="both", expand=True)
        
        f1 = ctk.CTkFrame(container, corner_radius=15); f1.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f1, text="Add Item", font=("Arial", 18, "bold"), text_color="#3B8ED0").pack(pady=15)
        self.en_name = ctk.CTkEntry(f1, placeholder_text="Product Name", width=220); self.en_name.pack(pady=8)
        self.en_sku = ctk.CTkEntry(f1, placeholder_text="SKU (Unique)", width=220); self.en_sku.pack(pady=8)
        self.en_pr = ctk.CTkEntry(f1, placeholder_text="Price (Numbers)", width=220); self.en_pr.pack(pady=8)
        self.en_st = ctk.CTkEntry(f1, placeholder_text="Initial Stock", width=220); self.en_st.pack(pady=8)
        ctk.CTkButton(f1, text="💾 Save to Database", fg_color="#27AE60", command=self.add_product_action).pack(pady=20)
        
        f2 = ctk.CTkFrame(container, corner_radius=15); f2.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f2, text="Edit / Wipe", font=("Arial", 18, "bold"), text_color="#C0392B").pack(pady=15)
        self.target = ctk.CTkEntry(f2, placeholder_text="Item Name to Edit", width=220); self.target.pack(pady=8)
        self.new_p = ctk.CTkEntry(f2, placeholder_text="New Price", width=220); self.new_p.pack(pady=8)
        ctk.CTkButton(f2, text="Update Price", command=self.update_price_action).pack(pady=10)
        ctk.CTkButton(f2, text="Delete Item", fg_color="#C0392B", command=self.delete_product_action).pack(pady=30)

    def add_product_action(self):
        db = get_db(); cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO Products (Name, SKU, Price, StockLevel, CategoryID, SupplierID) VALUES (%s, %s, %s, %s, 1, 1)", 
                           (self.en_name.get(), self.en_sku.get(), self.en_pr.get(), self.en_st.get()))
            db.commit(); messagebox.showinfo("Success", "Item Added!"); self.show_inventory()
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: db.close()

    def update_price_action(self):
        db = get_db(); cursor = db.cursor()
        cursor.execute("UPDATE Products SET Price = %s WHERE Name = %s", (self.new_p.get(), self.target.get()))
        db.commit(); db.close(); messagebox.showinfo("Updated", "Sync Complete."); self.show_inventory()

    def delete_product_action(self):
        db = get_db(); cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM Products WHERE Name = %s", (self.target.get(),))
            db.commit(); messagebox.showinfo("Deleted", "Item Removed."); self.show_inventory()
        except: messagebox.showerror("Constraint", "Cannot delete item with active history."); db.close()

    # --- FINANCIAL REPORT ---
    def show_report(self):
        for w in self.main_view.winfo_children(): w.destroy()
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT COUNT(*), SUM(TotalAmount) FROM Orders")
        res = cursor.fetchone()
        
        ctk.CTkLabel(self.main_view, text="Financial Report", font=("Arial", 32, "bold")).pack(pady=30)
        
        box = ctk.CTkFrame(self.main_view, corner_radius=20, fg_color="#2B2B2B", width=400, height=200)
        box.pack(pady=10)
        ctk.CTkLabel(box, text=f"Total Sales: {res[0]}", font=("Arial", 18)).pack(pady=15)
        ctk.CTkLabel(box, text=f"${res[1] or 0:.2f}", font=("Arial", 45, "bold"), text_color="#27AE60").pack(pady=10)
        
        ctk.CTkButton(self.main_view, text="RESET ALL SALES DATA", fg_color="#C0392B", command=self.reset_db).pack(pady=80)
        db.close()

    def reset_db(self):
        if messagebox.askyesno("Confirm", "Wipe all orders? This cannot be undone."):
            db = get_db(); cursor = db.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE Order_Items")
            cursor.execute("TRUNCATE TABLE Orders")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            db.commit(); db.close()
            messagebox.showinfo("Wiped", "System Reset Complete."); self.show_report()

if __name__ == "__main__":
    app = NexusApp()
    app.mainloop()