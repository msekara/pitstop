import sqlite3
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import Style
from tkinter import messagebox
from datetime import datetime, timedelta
import csv
from tkinter import filedialog
import uuid
import os

class CarManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PitStop - Car Parts and Service Manager")
        self.root.geometry("1200x800")

        # Apply theme
        style = Style(theme='flatly')
        style.configure('Overdue.Treeview', background='#ffcccc')
        style.configure('AltPart.Treeview.Row', font=('Helvetica', 10, 'italic'))

        # Initialize database
        db_dir = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), 'pitstop')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'pitstop.db')
        self.conn = sqlite3.connect(db_path)
        self.migrate_database()
        self.create_tables()

        # Main container
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill='both', expand=True)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame, bootstyle=PRIMARY)
        self.parts_tab = ttk.Frame(self.notebook)
        self.vehicles_tab = ttk.Frame(self.notebook)
        self.services_tab = ttk.Frame(self.notebook)
        self.service_types_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.parts_tab, text=' Parts Inventory ')
        self.notebook.add(self.vehicles_tab, text=' Vehicles ')
        self.notebook.add(self.services_tab, text=' Service Records ')
        self.notebook.add(self.service_types_tab, text=' Service Types ')
        self.notebook.add(self.about_tab, text=' About ')
        self.notebook.pack(fill='both', expand=True, pady=10)

        # Sorting state
        self.sort_column_state = {
            'parts': {'column': None, 'reverse': False},
            'vehicles': {'column': None, 'reverse': False},
            'services': {'column': None, 'reverse': False},
            'service_parts': {'column': None, 'reverse': False},
            'service_types': {'column': None, 'reverse': False}
        }

        # Initialize tabs
        self.setup_parts_tab()
        self.setup_vehicles_tab()
        self.setup_services_tab()
        self.setup_service_types_tab()
        self.setup_about_tab()

    def setup_about_tab(self):
        about_container = ttk.Frame(self.about_tab, padding=20)
        about_container.pack(fill='both', expand=True)

        about_frame = ttk.LabelFrame(about_container, text='About PitStop', bootstyle=INFO, padding=20)
        about_frame.pack(fill='both', expand=True)

        ttk.Label(about_frame, 
                 text="PitStop - Car Parts and Service Manager\n\n"
                      "Version: 1.0\n\n"
                      "Description: PitStop is a comprehensive application for managing car parts inventory, "
                      "vehicle details, and service records. It allows users to track parts, alternative parts, "
                      "vehicle information, service types, and maintenance schedules with an intuitive interface.\n\n"
                      "Author: Mladen Sekara\n\n"
                      "Purpose: Designed to help car enthusiasts and mechanics organize and maintain "
                      "vehicle-related data efficiently.",
                 font=('Helvetica', 12), 
                 justify='left',
                 wraplength=600).pack(anchor='center', pady=20)

    def migrate_database(self):
        cursor = self.conn.cursor()
        # Check if parts table needs migration for unique constraint on (part_number, vehicle_id)
        cursor.execute("PRAGMA table_info(parts)")
        columns = {col[1]: col for col in cursor.fetchall()}
        if 'part_number' in columns and 'vehicle_id' in columns:
            # Create temp table with UNIQUE constraint on (part_number, vehicle_id)
            cursor.execute('''
                CREATE TABLE parts_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    manufacturer TEXT,
                    part_number TEXT NOT NULL,
                    description TEXT,
                    price INTEGER,
                    vehicle_id INTEGER NOT NULL,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                    UNIQUE (part_number, vehicle_id)
                )
            ''')
            # Copy data
            cursor.execute('''
                INSERT INTO parts_temp (id, name, manufacturer, part_number, description, price, vehicle_id)
                SELECT id, name, manufacturer, part_number, description, price, vehicle_id
                FROM parts
            ''')
            cursor.execute('DROP TABLE parts')
            cursor.execute('ALTER TABLE parts_temp RENAME TO parts')

        # Check if alt_parts table needs migration for unique constraint on (part_number, part_id)
        cursor.execute("PRAGMA table_info(alt_parts)")
        columns = {col[1]: col for col in cursor.fetchall()}
        if 'part_number' in columns and 'part_id' in columns:
            # Create temp table with UNIQUE constraint on (part_number, part_id)
            cursor.execute('''
                CREATE TABLE alt_parts_temp (
                    alt_id TEXT PRIMARY KEY,
                    part_id INTEGER NOT NULL,
                    manufacturer TEXT,
                    part_number TEXT NOT NULL,
                    FOREIGN KEY (part_id) REFERENCES parts(id),
                    UNIQUE (part_number, part_id)
                )
            ''')
            # Copy data
            cursor.execute('''
                INSERT INTO alt_parts_temp (alt_id, part_id, manufacturer, part_number)
                SELECT alt_id, part_id, manufacturer, part_number
                FROM alt_parts
            ''')
            cursor.execute('DROP TABLE alt_parts')
            cursor.execute('ALTER TABLE alt_parts_temp RENAME TO alt_parts')

        self.conn.commit()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                part_number TEXT NOT NULL,
                description TEXT,
                price INTEGER,
                vehicle_id INTEGER NOT NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                UNIQUE (part_number, vehicle_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alt_parts (
                alt_id TEXT PRIMARY KEY,
                part_id INTEGER NOT NULL,
                manufacturer TEXT,
                part_number TEXT NOT NULL,
                FOREIGN KEY (part_id) REFERENCES parts(id),
                UNIQUE (part_number, part_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                year INTEGER,
                model TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                service_type_id INTEGER,
                date TEXT NOT NULL,
                odometer INTEGER,
                description TEXT,
                cost INTEGER,
                service_interval_miles INTEGER,
                service_interval_days INTEGER,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                FOREIGN KEY (service_type_id) REFERENCES service_types(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_parts (
                service_id INTEGER,
                part_id INTEGER,
                alt_part_id TEXT,
                quantity_used INTEGER,
                PRIMARY KEY (service_id, part_id, alt_part_id),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (part_id) REFERENCES parts(id),
                FOREIGN KEY (alt_part_id) REFERENCES alt_parts(alt_id)
            )
        ''')
        self.conn.commit()

    def sort_column(self, tree, col, tab_name):
        current_col = self.sort_column_state[tab_name]['column']
        current_reverse = self.sort_column_state[tab_name]['reverse']
        reverse = not current_reverse if col == current_col else False

        items = []
        for item in tree.get_children(''):
            value = tree.set(item, col)
            full_values = tree.item(item, 'values')
            tags = tree.item(item, 'tags')
            children = [(tree.set(child, col), tree.item(child, 'values'), tree.item(child, 'tags'), child)
                        for child in tree.get_children(item)]
            items.append((value, full_values, tags, item, children))

        if tab_name == 'parts':
            if col == 'ID' or col == 'Price':
                key_func = lambda x: int(x[0]) if x[0] else 0
            else:
                key_func = lambda x: x[0].lower() if x[0] else ''
        elif tab_name == 'vehicles':
            if col == 'ID' or col == 'Year':
                key_func = lambda x: int(x[0]) if x[0] else 0
            else:
                key_func = lambda x: x[0].lower() if x[0] else ''
        elif tab_name == 'services':
            if col == 'ID':
                key_func = lambda x: int(x[0]) if x[0] else 0
            elif col == 'Date':
                def date_key(val):
                    try:
                        return datetime.strptime(val, '%d/%m/%Y') if val else datetime.min
                    except ValueError:
                        return datetime.min
                key_func = lambda x: date_key(x[0])
            elif col == 'Next Service':
                def next_service_key(val):
                    if 'Date: ' in val:
                        try:
                            date_part = val.split('Date: ')[1].split(' or ')[0]
                            return datetime.strptime(date_part, '%d/%m/%Y') if date_part else datetime.min
                        except (ValueError, IndexError):
                            return datetime.min
                    return datetime.min
                key_func = lambda x: next_service_key(x[0])
            elif col in ('Odometer', 'Cost', 'Interval Miles', 'Interval Days'):
                key_func = lambda x: int(x[0]) if x[0] else 0
            else:
                key_func = lambda x: x[0].lower() if x[0] else ''
        elif tab_name == 'service_parts':
            if col in ('Part ID', 'Quantity Used'):
                key_func = lambda x: (x[0] if x[0] else '0')  # Handle alt_id (text)
            else:
                key_func = lambda x: x[0].lower() if x[0] else ''
        elif tab_name == 'service_types':
            if col == 'ID':
                key_func = lambda x: int(x[0]) if x[0] else 0
            else:
                key_func = lambda x: x[0].lower() if x[0] else ''

        items.sort(key=lambda x: key_func(x[0]), reverse=reverse)

        for item in tree.get_children(''):
            tree.delete(item)
        for _, values, tags, item_id, children in items:
            new_item = tree.insert('', 'end', iid=item_id, values=values, tags=tags)
            for _, child_values, child_tags, _ in children:
                tree.insert(new_item, 'end', values=child_values, tags=child_tags)

        self.sort_column_state[tab_name]['column'] = col
        self.sort_column_state[tab_name]['reverse'] = reverse

    def setup_parts_tab(self):
        self.parts_container = ttk.Frame(self.parts_tab, padding=10)
        self.parts_container.pack(fill='both', expand=True)

        search_frame = ttk.Frame(self.parts_container, padding=5)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text='Search Parts:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.parts_search_entry = ttk.Entry(search_frame, bootstyle=SECONDARY)
        self.parts_search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.parts_search_entry.bind('<KeyRelease>', self.filter_parts)

        ttk.Button(search_frame, text='Export to CSV', command=self.export_parts, bootstyle=INFO).pack(side='right', padx=5)

        tree_frame = ttk.LabelFrame(self.parts_container, text='Parts Inventory', bootstyle=INFO, padding=10)
        tree_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.parts_tree = ttk.Treeview(tree_frame, columns=('ID', 'Name', 'Manufacturer', 'Part Number', 'Description', 'Price', 'Vehicle'), show='headings', bootstyle='primary')
        self.parts_tree.heading('ID', text='ID', anchor='center')
        self.parts_tree.heading('Name', text='Name', anchor='center')
        self.parts_tree.heading('Manufacturer', text='Manufacturer', anchor='center')
        self.parts_tree.heading('Part Number', text='Part Number', anchor='center')
        self.parts_tree.heading('Description', text='Description', anchor='center')
        self.parts_tree.heading('Price', text='Price ($)', anchor='center')
        self.parts_tree.heading('Vehicle', text='Vehicle', anchor='center')
        self.parts_tree.column('ID', width=60, anchor='center')
        self.parts_tree.column('Name', width=200, anchor='center')
        self.parts_tree.column('Manufacturer', width=150, anchor='center')
        self.parts_tree.column('Part Number', width=120, anchor='center')
        self.parts_tree.column('Description', width=250, anchor='center')
        self.parts_tree.column('Price', width=100, anchor='center')
        self.parts_tree.column('Vehicle', width=200, anchor='center')
        self.parts_tree.pack(fill='both', expand=True)

        self.parts_tree.tag_configure('alt_part', font=('Helvetica', 10, 'italic'))

        for col in ('ID', 'Name', 'Manufacturer', 'Part Number', 'Description', 'Price', 'Vehicle'):
            self.parts_tree.heading(col, command=lambda c=col: self.sort_column(self.parts_tree, c, 'parts'))

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.parts_tree.yview, bootstyle=PRIMARY)
        self.parts_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        form_frame = ttk.LabelFrame(self.parts_container, text='Manage Part', bootstyle=INFO, padding=10)
        form_frame.pack(side='right', fill='y', padx=5, pady=5)

        ttk.Label(form_frame, text='Part Name:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_name_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.part_name_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Manufacturer:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_manufacturer_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.part_manufacturer_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Part Number:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_number_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.part_number_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Description:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_description_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.part_description_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Price ($):', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_price_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.part_price_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Vehicle:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.part_vehicle_combo = ttk.Combobox(form_frame, state='readonly', bootstyle=SECONDARY)
        self.part_vehicle_combo.pack(fill='x', pady=2)
        self.load_vehicle_combo()

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text='Add Part', command=self.add_part, bootstyle=SUCCESS).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Update Part', command=self.update_part, bootstyle=WARNING).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Delete Part', command=self.delete_part, bootstyle=DANGER).pack(side='left', fill='x', expand=True, padx=2)

        alt_parts_frame = ttk.LabelFrame(form_frame, text='Alternative Parts', bootstyle=INFO, padding=10)
        alt_parts_frame.pack(fill='x', pady=10)

        self.alt_parts_tree = ttk.Treeview(alt_parts_frame, columns=('ID', 'Manufacturer', 'Part Number'), show='headings', bootstyle='primary')
        self.alt_parts_tree.heading('ID', text='Alt ID', anchor='center')
        self.alt_parts_tree.heading('Manufacturer', text='Manufacturer', anchor='center')
        self.alt_parts_tree.heading('Part Number', text='Part Number', anchor='center')
        self.alt_parts_tree.column('ID', width=60, anchor='center')
        self.alt_parts_tree.column('Manufacturer', width=150, anchor='center')
        self.alt_parts_tree.column('Part Number', width=120, anchor='center')
        self.alt_parts_tree.pack(fill='both', expand=True)

        add_alt_frame = ttk.Frame(alt_parts_frame)
        add_alt_frame.pack(fill='x', pady=5)

        ttk.Label(add_alt_frame, text='Manufacturer:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.alt_manufacturer_entry = ttk.Entry(add_alt_frame, bootstyle=SECONDARY, width=15)
        self.alt_manufacturer_entry.pack(side='left', padx=5)

        ttk.Label(add_alt_frame, text='Part Number:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.alt_part_number_entry = ttk.Entry(add_alt_frame, bootstyle=SECONDARY, width=15)
        self.alt_part_number_entry.pack(side='left', padx=5)

        ttk.Button(add_alt_frame, text='Add Alt', command=self.add_alt_part, bootstyle=SUCCESS).pack(side='left', padx=5)
        ttk.Button(add_alt_frame, text='Remove Alt', command=self.remove_alt_part, bootstyle=DANGER).pack(side='left', padx=5)

        self.load_parts()
        self.parts_tree.bind('<<TreeviewSelect>>', self.select_part)

    def filter_parts(self, event):
        search_term = self.parts_search_entry.get().lower()
        for item in self.parts_tree.get_children():
            self.parts_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT p.id, p.name, p.manufacturer, p.part_number, p.description, p.price,
                   COALESCE(v.name || (CASE WHEN v.year IS NOT NULL AND v.model IS NOT NULL THEN ' (' || v.year || ' ' || v.model || ')' ELSE '' END), 'N/A')
            FROM parts p
            LEFT JOIN alt_parts ap ON p.id = ap.part_id
            LEFT JOIN vehicles v ON p.vehicle_id = v.id
            WHERE lower(p.name) LIKE ? OR lower(p.part_number) LIKE ?
            OR lower(ap.manufacturer) LIKE ? OR lower(ap.part_number) LIKE ?
            OR lower(v.name) LIKE ? OR lower(v.model) LIKE ?
            ORDER BY p.id ASC
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        for row in cursor.fetchall():
            part_id = row[0]
            main_item = self.parts_tree.insert('', 'end', iid=part_id, values=row)
            cursor.execute('SELECT alt_id, manufacturer, part_number FROM alt_parts WHERE part_id = ? ORDER BY alt_id ASC', (part_id,))
            for alt_row in cursor.fetchall():
                self.parts_tree.insert(main_item, 'end', values=(alt_row[0], '', alt_row[1], alt_row[2], '', '', row[6]), tags=('alt_part',))

    def load_parts(self):
        for item in self.parts_tree.get_children():
            self.parts_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.manufacturer, p.part_number, p.description, p.price,
                   COALESCE(v.name || (CASE WHEN v.year IS NOT NULL AND v.model IS NOT NULL THEN ' (' || v.year || ' ' || v.model || ')' ELSE '' END), 'N/A')
            FROM parts p
            LEFT JOIN vehicles v ON p.vehicle_id = v.id
            ORDER BY p.id ASC
        ''')
        for row in cursor.fetchall():
            part_id = row[0]
            main_item = self.parts_tree.insert('', 'end', iid=part_id, values=row)
            cursor.execute('SELECT alt_id, manufacturer, part_number FROM alt_parts WHERE part_id = ? ORDER BY alt_id ASC', (part_id,))
            for alt_row in cursor.fetchall():
                self.parts_tree.insert(main_item, 'end', values=(alt_row[0], '', alt_row[1], alt_row[2], '', '', row[6]), tags=('alt_part',))

    def add_part(self):
        name = self.part_name_entry.get()
        manufacturer = self.part_manufacturer_entry.get()
        part_number = self.part_number_entry.get()
        description = self.part_description_entry.get()
        price = self.part_price_entry.get()
        vehicle_selection = self.part_vehicle_combo.get()
        vehicle_id = self.vehicle_id_map.get(vehicle_selection) if vehicle_selection else None
        if not name:
            messagebox.showerror('Error', 'Name is required')
            return
        if not vehicle_id:
            messagebox.showerror('Error', 'Vehicle selection is required')
            return
        if not part_number:
            messagebox.showerror('Error', 'Part number is required')
            return
        price_value = None
        if price:
            try:
                price_value = int(price)
            except ValueError:
                messagebox.showerror('Error', 'Price must be an integer if provided')
                return
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO parts (name, manufacturer, part_number, description, price, vehicle_id) VALUES (?, ?, ?, ?, ?, ?)',
                           (name, manufacturer, part_number, description or None, price_value, vehicle_id))
            self.conn.commit()
            self.load_parts()
            self.clear_part_entries()
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Part number already exists for this vehicle. Please use a unique part number.')
            return

    def select_part(self, event):
        selected = self.parts_tree.focus()
        if selected:
            if self.parts_tree.parent(selected):
                parent = self.parts_tree.parent(selected)
                self.parts_tree.selection_set(parent)
                selected = parent
            values = self.parts_tree.item(selected, 'values')
            self.part_name_entry.delete(0, ttk.END)
            self.part_name_entry.insert(0, values[1])
            self.part_manufacturer_entry.delete(0, ttk.END)
            self.part_manufacturer_entry.insert(0, values[2] if values[2] else '')
            self.part_number_entry.delete(0, ttk.END)
            self.part_number_entry.insert(0, values[3] if values[3] else '')
            self.part_description_entry.delete(0, ttk.END)
            self.part_description_entry.insert(0, values[4] if values[4] else '')
            self.part_price_entry.delete(0, ttk.END)
            self.part_price_entry.insert(0, values[5] if values[5] else '')
            cursor = self.conn.cursor()
            cursor.execute('SELECT vehicle_id FROM parts WHERE id = ?', (values[0],))
            vehicle_id = cursor.fetchone()[0]
            if vehicle_id:
                cursor.execute('SELECT name, year, model FROM vehicles WHERE id = ?', (vehicle_id,))
                vehicle = cursor.fetchone()
                vehicle_display = f"{vehicle_id} - {vehicle[0]}{f' ({vehicle[1]} {vehicle[2]})' if vehicle[1] and vehicle[2] else ''}"
                self.part_vehicle_combo.set(vehicle_display)
            else:
                self.part_vehicle_combo.set('')
            self.load_alt_parts(selected)

    def update_part(self):
        selected = self.parts_tree.focus()
        if not selected or self.parts_tree.parent(selected):
            messagebox.showerror('Error', 'Select a main part to update')
            return
        id_ = self.parts_tree.item(selected, 'values')[0]
        name = self.part_name_entry.get()
        manufacturer = self.part_manufacturer_entry.get()
        part_number = self.part_number_entry.get()
        description = self.part_description_entry.get()
        price = self.part_price_entry.get()
        vehicle_selection = self.part_vehicle_combo.get()
        vehicle_id = self.vehicle_id_map.get(vehicle_selection) if vehicle_selection else None
        if not name:
            messagebox.showerror('Error', 'Name is required')
            return
        if not vehicle_id:
            messagebox.showerror('Error', 'Vehicle selection is required')
            return
        if not part_number:
            messagebox.showerror('Error', 'Part number is required')
            return
        price_value = None
        if price:
            try:
                price_value = int(price)
            except ValueError:
                messagebox.showerror('Error', 'Price must be an integer if provided')
                return
        cursor = self.conn.cursor()
        # Check if the new part_number is unique for this vehicle (excluding the current part)
        cursor.execute('SELECT id FROM parts WHERE part_number = ? AND vehicle_id = ? AND id != ?', (part_number, vehicle_id, id_))
        if cursor.fetchone():
            messagebox.showerror('Error', 'Part number already exists for this vehicle. Please use a unique part number.')
            return
        cursor.execute('UPDATE parts SET name=?, manufacturer=?, part_number=?, description=?, price=?, vehicle_id=? WHERE id=?',
                       (name, manufacturer, part_number, description or None, price_value, vehicle_id, id_))
        self.conn.commit()
        self.load_parts()
        self.clear_part_entries()

    def delete_part(self):
        selected = self.parts_tree.focus()
        if not selected or self.parts_tree.parent(selected):
            messagebox.showerror('Error', 'Select a main part to delete')
            return
        id_ = self.parts_tree.item(selected, 'values')[0]
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM parts WHERE id=?', (id_,))
        cursor.execute('DELETE FROM service_parts WHERE part_id=?', (id_,))
        cursor.execute('DELETE FROM alt_parts WHERE part_id=?', (id_,))
        self.conn.commit()
        self.load_parts()
        self.clear_part_entries()

    def clear_part_entries(self):
        self.part_name_entry.delete(0, ttk.END)
        self.part_manufacturer_entry.delete(0, ttk.END)
        self.part_number_entry.delete(0, ttk.END)
        self.part_description_entry.delete(0, ttk.END)
        self.part_price_entry.delete(0, ttk.END)
        self.part_vehicle_combo.set('')
        self.alt_manufacturer_entry.delete(0, ttk.END)
        self.alt_part_number_entry.delete(0, ttk.END)
        for item in self.alt_parts_tree.get_children():
            self.alt_parts_tree.delete(item)

    def load_alt_parts(self, part_id):
        for item in self.alt_parts_tree.get_children():
            self.alt_parts_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('SELECT alt_id, manufacturer, part_number FROM alt_parts WHERE part_id = ? ORDER BY alt_id ASC', (part_id,))
        for row in cursor.fetchall():
            self.alt_parts_tree.insert('', 'end', values=row)

    def add_alt_part(self):
        selected = self.parts_tree.focus()
        if not selected or self.parts_tree.parent(selected):
            messagebox.showerror('Error', 'Select a main part first')
            return
        part_id = selected
        manufacturer = self.alt_manufacturer_entry.get()
        part_number = self.alt_part_number_entry.get()
        if not manufacturer or not part_number:
            messagebox.showerror('Error', 'Manufacturer and Part Number are required for alternative parts')
            return
        cursor = self.conn.cursor()
        # Get vehicle_id for the part
        cursor.execute('SELECT vehicle_id FROM parts WHERE id = ?', (part_id,))
        vehicle_id = cursor.fetchone()[0]
        # Check if part_number is unique for this vehicle in parts and alt_parts
        cursor.execute('SELECT id FROM parts WHERE part_number = ? AND vehicle_id = ?', (part_number, vehicle_id))
        if cursor.fetchone():
            messagebox.showerror('Error', 'Part number already exists for this vehicle in main parts.')
            return
        cursor.execute('SELECT alt_id FROM alt_parts WHERE part_number = ? AND part_id IN (SELECT id FROM parts WHERE vehicle_id = ?)', (part_number, vehicle_id))
        if cursor.fetchone():
            messagebox.showerror('Error', 'Part number already exists for this vehicle in alternative parts.')
            return
        # Find the next available alt_id (e.g., 1a, 1b, etc.)
        cursor.execute('SELECT alt_id FROM alt_parts WHERE part_id = ? ORDER BY alt_id ASC', (part_id,))
        existing_ids = [row[0] for row in cursor.fetchall()]
        used_letters = [alt_id[len(str(part_id)):] for alt_id in existing_ids if alt_id.startswith(str(part_id))]
        next_letter = 'a'
        while next_letter in used_letters:
            next_letter = chr(ord(next_letter) + 1)
        alt_id = f"{part_id}{next_letter}"
        cursor.execute('INSERT INTO alt_parts (alt_id, part_id, manufacturer, part_number) VALUES (?, ?, ?, ?)',
                       (alt_id, part_id, manufacturer, part_number))
        self.conn.commit()
        self.load_alt_parts(part_id)
        self.load_parts()
        self.alt_manufacturer_entry.delete(0, ttk.END)
        self.alt_part_number_entry.delete(0, ttk.END)

    def remove_alt_part(self):
        selected = self.alt_parts_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select an alternative part to remove')
            return
        values = self.alt_parts_tree.item(selected, 'values')
        alt_id = values[0]
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM service_parts WHERE alt_part_id = ?', (alt_id,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror('Error', 'Cannot delete alternative part used in services')
            return
        cursor.execute('DELETE FROM alt_parts WHERE alt_id = ?', (alt_id,))
        self.conn.commit()
        part_id = self.parts_tree.focus()
        if part_id:
            self.load_alt_parts(part_id)
            self.load_parts()

    def export_parts(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.manufacturer, p.part_number, p.description, p.price,
                   COALESCE(v.name || (CASE WHEN v.year IS NOT NULL AND v.model IS NOT NULL THEN ' (' || v.year || ' ' || v.model || ')' ELSE '' END), 'N/A')
            FROM parts p
            LEFT JOIN vehicles v ON p.vehicle_id = v.id
        ''')
        parts = cursor.fetchall()
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Name', 'Manufacturer', 'Part Number', 'Description', 'Price', 'Vehicle'])
            for row in parts:
                writer.writerow(row)
        messagebox.showinfo('Export Successful', 'Parts exported to CSV successfully')

    def setup_vehicles_tab(self):
        self.vehicles_container = ttk.Frame(self.vehicles_tab, padding=10)
        self.vehicles_container.pack(fill='both', expand=True)

        tree_frame = ttk.LabelFrame(self.vehicles_container, text='Vehicles', bootstyle=INFO, padding=10)
        tree_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.vehicles_tree = ttk.Treeview(tree_frame, columns=('ID', 'Name', 'Year', 'Model'), show='headings', bootstyle='primary')
        self.vehicles_tree.heading('ID', text='ID', anchor='center')
        self.vehicles_tree.heading('Name', text='Vehicle Name', anchor='center')
        self.vehicles_tree.heading('Year', text='Year', anchor='center')
        self.vehicles_tree.heading('Model', text='Model', anchor='center')
        self.vehicles_tree.column('ID', width=60, anchor='center')
        self.vehicles_tree.column('Name', width=200, anchor='center')
        self.vehicles_tree.column('Year', width=80, anchor='center')
        self.vehicles_tree.column('Model', width=150, anchor='center')
        self.vehicles_tree.pack(fill='both', expand=True)

        for col in ('ID', 'Name', 'Year', 'Model'):
            self.vehicles_tree.heading(col, command=lambda c=col: self.sort_column(self.vehicles_tree, c, 'vehicles'))

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.vehicles_tree.yview, bootstyle=PRIMARY)
        self.vehicles_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        form_frame = ttk.LabelFrame(self.vehicles_container, text='Manage Vehicle', bootstyle=INFO, padding=10)
        form_frame.pack(side='right', fill='y', padx=5, pady=5)

        ttk.Label(form_frame, text='Vehicle Name:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.vehicle_name_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.vehicle_name_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Year:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.vehicle_year_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.vehicle_year_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Model:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.vehicle_model_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.vehicle_model_entry.pack(fill='x', pady=2)

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text='Add Vehicle', command=self.add_vehicle, bootstyle=SUCCESS).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Update Vehicle', command=self.update_vehicle, bootstyle=WARNING).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Delete Vehicle', command=self.delete_vehicle, bootstyle=DANGER).pack(side='left', fill='x', expand=True, padx=2)

        self.load_vehicles()
        self.vehicles_tree.bind('<<TreeviewSelect>>', self.select_vehicle)

    def load_vehicles(self):
        for item in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vehicles ORDER BY id ASC')
        for row in cursor.fetchall():
            self.vehicles_tree.insert('', 'end', values=row)
        self.load_vehicle_combo()

    def add_vehicle(self):
        name = self.vehicle_name_entry.get()
        year = self.vehicle_year_entry.get()
        model = self.vehicle_model_entry.get()
        if not name:
            messagebox.showerror('Error', 'Vehicle Name is required')
            return
        year_value = None
        if year:
            try:
                year_value = int(year)
                if year_value < 1900 or year_value > datetime.now().year + 1:
                    messagebox.showerror('Error', 'Year must be a valid year (1900 to current year + 1)')
                    return
            except ValueError:
                messagebox.showerror('Error', 'Year must be an integer if provided')
                return
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO vehicles (name, year, model) VALUES (?, ?, ?)',
                       (name, year_value, model or None))
        self.conn.commit()
        self.load_vehicles()
        self.clear_vehicle_entries()

    def select_vehicle(self, event):
        selected = self.vehicles_tree.focus()
        if selected:
            values = self.vehicles_tree.item(selected, 'values')
            self.vehicle_name_entry.delete(0, ttk.END)
            self.vehicle_name_entry.insert(0, values[1])
            self.vehicle_year_entry.delete(0, ttk.END)
            self.vehicle_year_entry.insert(0, values[2] if values[2] else '')
            self.vehicle_model_entry.delete(0, ttk.END)
            self.vehicle_model_entry.insert(0, values[3] if values[3] else '')
            self.load_services()

    def update_vehicle(self):
        selected = self.vehicles_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a vehicle to update')
            return
        id_ = self.vehicles_tree.item(selected, 'values')[0]
        name = self.vehicle_name_entry.get()
        year = self.vehicle_year_entry.get()
        model = self.vehicle_model_entry.get()
        if not name:
            messagebox.showerror('Error', 'Vehicle Name is required')
            return
        year_value = None
        if year:
            try:
                year_value = int(year)
                if year_value < 1900 or year_value > datetime.now().year + 1:
                    messagebox.showerror('Error', 'Year must be a valid year (1900 to current year + 1)')
                    return
            except ValueError:
                messagebox.showerror('Error', 'Year must be an integer if provided')
                return
        cursor = self.conn.cursor()
        cursor.execute('UPDATE vehicles SET name=?, year=?, model=? WHERE id=?',
                       (name, year_value, model or None, id_))
        self.conn.commit()
        self.load_vehicles()
        self.clear_vehicle_entries()

    def delete_vehicle(self):
        selected = self.vehicles_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a vehicle to delete')
            return
        id_ = self.vehicles_tree.item(selected, 'values')[0]
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM parts WHERE vehicle_id=?', (id_,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror('Error', 'Cannot delete vehicle with associated parts')
            return
        cursor.execute('SELECT COUNT(*) FROM services WHERE vehicle_id=?', (id_,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror('Error', 'Cannot delete vehicle with associated services')
            return
        cursor.execute('DELETE FROM vehicles WHERE id=?', (id_,))
        self.conn.commit()
        self.load_vehicles()
        self.clear_vehicle_entries()
        if hasattr(self, 'service_vehicle_combo'):
            self.clear_service_entries()
            self.clear_service_parts_tree()

    def clear_vehicle_entries(self):
        self.vehicle_name_entry.delete(0, ttk.END)
        self.vehicle_year_entry.delete(0, ttk.END)
        self.vehicle_model_entry.delete(0, ttk.END)

    def setup_service_types_tab(self):
        self.service_types_container = ttk.Frame(self.service_types_tab, padding=10)
        self.service_types_container.pack(fill='both', expand=True)

        tree_frame = ttk.LabelFrame(self.service_types_container, text='Service Types', bootstyle=INFO, padding=10)
        tree_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.service_types_tree = ttk.Treeview(tree_frame, columns=('ID', 'Name'), show='headings', bootstyle='primary')
        self.service_types_tree.heading('ID', text='ID', anchor='center')
        self.service_types_tree.heading('Name', text='Service Type Name', anchor='center')
        self.service_types_tree.column('ID', width=60, anchor='center')
        self.service_types_tree.column('Name', width=300, anchor='center')
        self.service_types_tree.pack(fill='both', expand=True)

        for col in ('ID', 'Name'):
            self.service_types_tree.heading(col, command=lambda c=col: self.sort_column(self.service_types_tree, c, 'service_types'))

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.service_types_tree.yview, bootstyle=PRIMARY)
        self.service_types_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        form_frame = ttk.LabelFrame(self.service_types_container, text='Manage Service Type', bootstyle=INFO, padding=10)
        form_frame.pack(side='right', fill='y', padx=5, pady=5)

        ttk.Label(form_frame, text='Service Type Name:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_type_name_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_type_name_entry.pack(fill='x', pady=2)

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text='Add Service Type', command=self.add_service_type, bootstyle=SUCCESS).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Update Service Type', command=self.update_service_type, bootstyle=WARNING).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Delete Service Type', command=self.delete_service_type, bootstyle=DANGER).pack(side='left', fill='x', expand=True, padx=2)

        self.load_service_types()
        self.service_types_tree.bind('<<TreeviewSelect>>', self.select_service_type)

    def load_service_types(self):
        for item in self.service_types_tree.get_children():
            self.service_types_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM service_types ORDER BY id ASC')
        for row in cursor.fetchall():
            self.service_types_tree.insert('', 'end', values=row)
        self.load_service_type_combo()

    def add_service_type(self):
        name = self.service_type_name_entry.get()
        if not name:
            messagebox.showerror('Error', 'Service Type Name is required')
            return
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO service_types (name) VALUES (?)', (name,))
        self.conn.commit()
        self.load_service_types()
        self.clear_service_type_entries()

    def select_service_type(self, event):
        selected = self.service_types_tree.focus()
        if selected:
            values = self.service_types_tree.item(selected, 'values')
            self.service_type_name_entry.delete(0, ttk.END)
            self.service_type_name_entry.insert(0, values[1])

    def update_service_type(self):
        selected = self.service_types_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a service type to update')
            return
        id_ = self.service_types_tree.item(selected, 'values')[0]
        name = self.service_type_name_entry.get()
        if not name:
            messagebox.showerror('Error', 'Service Type Name is required')
            return
        cursor = self.conn.cursor()
        cursor.execute('UPDATE service_types SET name=? WHERE id=?', (name, id_))
        self.conn.commit()
        self.load_service_types()
        self.clear_service_type_entries()

    def delete_service_type(self):
        selected = self.service_types_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a service type to delete')
            return
        id_ = self.service_types_tree.item(selected, 'values')[0]
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM services WHERE service_type_id=?', (id_,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror('Error', 'Cannot delete service type used in services')
            return
        cursor.execute('DELETE FROM service_types WHERE id=?', (id_,))
        self.conn.commit()
        self.load_service_types()
        self.clear_service_type_entries()

    def clear_service_type_entries(self):
        self.service_type_name_entry.delete(0, ttk.END)

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, '%d/%m/%Y')
            return True
        except ValueError:
            return False

    def setup_services_tab(self):
        self.services_container = ttk.Frame(self.services_tab, padding=10)
        self.services_container.pack(fill='both', expand=True)

        search_frame = ttk.Frame(self.services_container, padding=5)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text='Search Services:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.services_search_entry = ttk.Entry(search_frame, bootstyle=SECONDARY)
        self.services_search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.services_search_entry.bind('<KeyRelease>', self.filter_services)

        ttk.Button(search_frame, text='Export to CSV', command=self.export_services, bootstyle=INFO).pack(side='right', padx=5)

        tree_frame = ttk.LabelFrame(self.services_container, text='Service Records', bootstyle=INFO, padding=10)
        tree_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.services_tree = ttk.Treeview(tree_frame, columns=('ID', 'Vehicle', 'Type', 'Date', 'Odometer', 'Description', 'Cost', 'Interval Miles', 'Interval Days', 'Next Service'), show='headings', bootstyle='primary')
        self.services_tree.heading('ID', text='ID', anchor='center')
        self.services_tree.heading('Vehicle', text='Vehicle', anchor='center')
        self.services_tree.heading('Type', text='Service Type', anchor='center')
        self.services_tree.heading('Date', text='Date', anchor='center')
        self.services_tree.heading('Odometer', text='Odometer', anchor='center')
        self.services_tree.heading('Description', text='Description', anchor='center')
        self.services_tree.heading('Cost', text='Cost ($)', anchor='center')
        self.services_tree.heading('Interval Miles', text='Interval Miles', anchor='center')
        self.services_tree.heading('Interval Days', text='Interval Days', anchor='center')
        self.services_tree.heading('Next Service', text='Next Service', anchor='center')
        self.services_tree.column('ID', width=60, anchor='center')
        self.services_tree.column('Vehicle', width=200, anchor='center')
        self.services_tree.column('Type', width=150, anchor='center')
        self.services_tree.column('Date', width=120, anchor='center')
        self.services_tree.column('Odometer', width=100, anchor='center')
        self.services_tree.column('Description', width=250, anchor='center')
        self.services_tree.column('Cost', width=100, anchor='center')
        self.services_tree.column('Interval Miles', width=120, anchor='center')
        self.services_tree.column('Interval Days', width=120, anchor='center')
        self.services_tree.column('Next Service', width=200, anchor='center')
        self.services_tree.pack(fill='both', expand=True)

        for col in ('ID', 'Vehicle', 'Type', 'Date', 'Odometer', 'Description', 'Cost', 'Interval Miles', 'Interval Days', 'Next Service'):
            self.services_tree.heading(col, command=lambda c=col: self.sort_column(self.services_tree, c, 'services'))

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.services_tree.yview, bootstyle=PRIMARY)
        self.services_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        right_frame = ttk.Frame(self.services_container, padding=10)
        right_frame.pack(side='right', fill='y', padx=5)

        form_frame = ttk.LabelFrame(right_frame, text='Manage Service', bootstyle=INFO, padding=10)
        form_frame.pack(fill='x', pady=5)

        ttk.Label(form_frame, text='Vehicle:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_vehicle_combo = ttk.Combobox(form_frame, state='readonly', bootstyle=SECONDARY)
        self.service_vehicle_combo.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Service Type:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_type_combo = ttk.Combobox(form_frame, state='readonly', bootstyle=SECONDARY)
        self.service_type_combo.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Date (DD/MM/YYYY):', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_date_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_date_entry.pack(fill='x', pady=2)
        self.service_date_entry.insert(0, datetime.now().strftime('%d/%m/%Y'))

        ttk.Label(form_frame, text='Odometer:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_odometer_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_odometer_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Service Interval Miles:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_interval_miles_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_interval_miles_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Service Interval Days:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_interval_days_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_interval_days_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Description:', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_desc_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_desc_entry.pack(fill='x', pady=2)

        ttk.Label(form_frame, text='Cost ($):', font=('Helvetica', 10)).pack(anchor='w', pady=2)
        self.service_cost_entry = ttk.Entry(form_frame, bootstyle=SECONDARY)
        self.service_cost_entry.pack(fill='x', pady=2)

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text='Add Service', command=self.add_service, bootstyle=SUCCESS).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Update Service', command=self.update_service, bootstyle=WARNING).pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(button_frame, text='Delete Service', command=self.delete_service, bootstyle=DANGER).pack(side='left', fill='x', expand=True, padx=2)

        parts_used_frame = ttk.LabelFrame(right_frame, text='Parts Used in Service', bootstyle=INFO, padding=10)
        parts_used_frame.pack(fill='both', expand=True, pady=10)

        self.service_parts_tree = ttk.Treeview(parts_used_frame, columns=('ID', 'Name', 'Manufacturer', 'Part Number', 'Quantity Used'), show='headings', bootstyle='primary')
        self.service_parts_tree.heading('ID', text='ID', anchor='center')
        self.service_parts_tree.heading('Name', text='Name', anchor='center')
        self.service_parts_tree.heading('Manufacturer', text='Manufacturer', anchor='center')
        self.service_parts_tree.heading('Part Number', text='Part Number', anchor='center')
        self.service_parts_tree.heading('Quantity Used', text='Qty Used', anchor='center')
        self.service_parts_tree.column('ID', width=60, anchor='center')
        self.service_parts_tree.column('Name', width=200, anchor='center')
        self.service_parts_tree.column('Manufacturer', width=150, anchor='center')
        self.service_parts_tree.column('Part Number', width=120, anchor='center')
        self.service_parts_tree.column('Quantity Used', width=80, anchor='center')
        self.service_parts_tree.pack(fill='both', expand=True)

        for col in ('ID', 'Name', 'Manufacturer', 'Part Number', 'Quantity Used'):
            self.service_parts_tree.heading(col, command=lambda c=col: self.sort_column(self.service_parts_tree, c, 'service_parts'))

        add_part_frame = ttk.Frame(parts_used_frame)
        add_part_frame.pack(fill='x', pady=5)

        ttk.Label(add_part_frame, text='Select Part:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.part_combo = ttk.Combobox(add_part_frame, state='readonly', bootstyle=SECONDARY)
        self.part_combo.pack(side='left', fill='x', expand=True, padx=5)
        self.load_part_combo()

        ttk.Label(add_part_frame, text='Qty:', font=('Helvetica', 10)).pack(side='left', padx=5)
        self.part_qty_used_entry = ttk.Entry(add_part_frame, width=5, bootstyle=SECONDARY)
        self.part_qty_used_entry.pack(side='left', padx=5)

        ttk.Button(add_part_frame, text='Add Part', command=self.add_part_to_service, bootstyle=SUCCESS).pack(side='left', padx=5)
        ttk.Button(add_part_frame, text='Remove Part', command=self.remove_part_from_service, bootstyle=DANGER).pack(side='left', padx=5)

        self.load_vehicle_combo()
        self.load_service_type_combo()
        self.load_services()
        self.services_tree.bind('<<TreeviewSelect>>', self.select_service)

    def load_vehicle_combo(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, year, model FROM vehicles ORDER BY id ASC')
        vehicles = [(f"{row[0]} - {row[1]}{f' ({row[2]} {row[3]})' if row[2] and row[3] else ''}", row[0]) for row in cursor.fetchall()]
        self.vehicle_id_map = {v[0]: v[1] for v in vehicles}
        if hasattr(self, 'service_vehicle_combo'):
            self.service_vehicle_combo['values'] = [v[0] for v in vehicles]
        if hasattr(self, 'part_vehicle_combo'):
            self.part_vehicle_combo['values'] = [v[0] for v in vehicles]

    def load_service_type_combo(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM service_types ORDER BY id ASC')
        service_types = [(f"{row[0]} - {row[1]}", row[0]) for row in cursor.fetchall()]
        self.service_type_id_map = {st[0]: st[1] for st in service_types}
        if hasattr(self, 'service_type_combo'):
            self.service_type_combo['values'] = [st[0] for st in service_types]

    def load_part_combo(self, vehicle_id=None):
        cursor = self.conn.cursor()
        parts = []
        query = 'SELECT id, name FROM parts'
        params = []
        if vehicle_id:
            query += ' WHERE vehicle_id = ?'
            params.append(vehicle_id)
        query += ' ORDER BY id ASC'
        cursor.execute(query, params)
        for row in cursor.fetchall():
            parts.append((f"{row[0]} - {row[1]}", row[0], None))
        if vehicle_id:
            query = '''
                SELECT ap.alt_id, p.name, ap.manufacturer, ap.part_number
                FROM alt_parts ap
                JOIN parts p ON ap.part_id = p.id
                WHERE p.vehicle_id = ?
                ORDER BY ap.alt_id ASC
            '''
            cursor.execute(query, (vehicle_id,))
            for row in cursor.fetchall():
                parts.append((f"{row[0]} - {row[1]} (Alt: {row[2]} {row[3]})", row[0][:-1], row[0]))
        parts.sort(key=lambda x: (int(x[1]), x[2] or ''))
        self.part_combo['values'] = [p[0] for p in parts]
        self.part_id_map = {p[0]: (p[1], p[2]) for p in parts}
        self.part_combo.set('')

    def load_services(self):
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        cursor = self.conn.cursor()
        selected_vehicle = self.vehicles_tree.focus()
        vehicle_id = None
        if selected_vehicle:
            vehicle_id = self.vehicles_tree.item(selected_vehicle, 'values')[0]
        query = '''
            SELECT s.id, COALESCE(v.name || (CASE WHEN v.model IS NOT NULL THEN ' (' || v.model || ')' ELSE '' END), v.name), st.name, s.date, s.odometer, s.description, s.cost, s.service_interval_miles, s.service_interval_days
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.id
            LEFT JOIN service_types st ON s.service_type_id = st.id
        '''
        params = []
        if vehicle_id:
            query += ' WHERE s.vehicle_id = ?'
            params = [vehicle_id]
        query += ' ORDER BY s.id ASC'
        cursor.execute(query, params)
        current_date = datetime.now()
        for row in cursor.fetchall():
            service_id, vehicle_name, service_type, date, odometer, description, cost, interval_miles, interval_days = row
            next_service = self.calculate_next_service(date, odometer, interval_miles, interval_days)
            is_overdue = False
            if interval_days or interval_miles:
                cursor.execute('''
                    SELECT date, odometer
                    FROM services
                    WHERE vehicle_id = (SELECT vehicle_id FROM services WHERE id = ?)
                    AND id != ?
                    ORDER BY date DESC LIMIT 1
                ''', (service_id, service_id))
                last_service = cursor.fetchone()
                try:
                    service_date = datetime.strptime(date, '%d/%m/%Y')
                except ValueError:
                    continue
                if last_service:
                    last_date, last_odometer = last_service
                    try:
                        last_date = datetime.strptime(last_date, '%d/%m/%Y')
                    except ValueError:
                        continue
                    if interval_days and (current_date - last_date).days > interval_days:
                        is_overdue = True
                    if interval_miles and last_odometer and odometer and (odometer - last_odometer) > interval_miles:
                        is_overdue = True
                else:
                    if interval_days and (current_date - service_date).days > interval_days:
                        is_overdue = True
            tag = 'overdue' if is_overdue else ''
            self.services_tree.insert('', 'end', values=(service_id, vehicle_name, service_type, date, odometer, description, cost, interval_miles, interval_days, next_service), tags=(tag,))
        self.services_tree.tag_configure('overdue', background='#ffcccc')

    def calculate_next_service(self, date, odometer, interval_miles, interval_days):
        next_service = []
        if date:
            try:
                service_date = datetime.strptime(date, '%d/%m/%Y')
                if interval_days:
                    next_date = service_date + timedelta(days=interval_days)
                    next_service.append(f"Date: {next_date.strftime('%d/%m/%Y')}")
                if interval_miles and odometer:
                    next_odometer = odometer + interval_miles
                    next_service.append(f"Miles: {next_odometer}")
            except ValueError:
                return ''
        return ' or '.join(next_service) if next_service else ''

    def filter_services(self, event):
        search_term = self.services_search_entry.get().lower()
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        cursor = self.conn.cursor()
        selected_vehicle = self.vehicles_tree.focus()
        vehicle_id = None
        if selected_vehicle:
            vehicle_id = self.vehicles_tree.item(selected_vehicle, 'values')[0]
        query = '''
            SELECT s.id, COALESCE(v.name || (CASE WHEN v.model IS NOT NULL THEN ' (' || v.model || ')' ELSE '' END), v.name), st.name, s.date, s.odometer, s.description, s.cost, s.service_interval_miles, s.service_interval_days
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.id
            LEFT JOIN service_types st ON s.service_type_id = st.id
            WHERE (lower(st.name) LIKE ? OR lower(v.name) LIKE ? OR lower(v.model) LIKE ?)
        '''
        params = [f'%{search_term}%', f'%{search_term}%', f'%{search_term}%']
        if vehicle_id:
            query += ' AND s.vehicle_id = ?'
            params.append(vehicle_id)
        query += ' ORDER BY s.id ASC'
        cursor.execute(query, params)
        current_date = datetime.now()
        for row in cursor.fetchall():
            service_id, vehicle_name, service_type, date, odometer, description, cost, interval_miles, interval_days = row
            next_service = self.calculate_next_service(date, odometer, interval_miles, interval_days)
            is_overdue = False
            if interval_days or interval_miles:
                cursor.execute('''
                    SELECT date, odometer
                    FROM services
                    WHERE vehicle_id = (SELECT vehicle_id FROM services WHERE id = ?)
                    AND id != ?
                    ORDER BY date DESC LIMIT 1
                ''', (service_id, service_id))
                last_service = cursor.fetchone()
                try:
                    service_date = datetime.strptime(date, '%d/%m/%Y')
                except ValueError:
                    continue
                if last_service:
                    last_date, last_odometer = last_service
                    try:
                        last_date = datetime.strptime(last_date, '%d/%m/%Y')
                    except ValueError:
                        continue
                    if interval_days and (current_date - last_date).days > interval_days:
                        is_overdue = True
                    if interval_miles and last_odometer and odometer and (odometer - last_odometer) > interval_miles:
                        is_overdue = True
                else:
                    if interval_days and (current_date - service_date).days > interval_days:
                        is_overdue = True
            tag = 'overdue' if is_overdue else ''
            self.services_tree.insert('', 'end', values=(service_id, vehicle_name, service_type, date, odometer, description, cost, interval_miles, interval_days, next_service), tags=(tag,))
        self.services_tree.tag_configure('overdue', background='#ffcccc')

    def export_services(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.id, COALESCE(v.name || (CASE WHEN v.model IS NOT NULL THEN ' (' || v.model || ')' ELSE '' END), v.name), st.name, s.date, s.odometer, s.description, s.cost, s.service_interval_miles, s.service_interval_days
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.id
            LEFT JOIN service_types st ON s.service_type_id = st.id
        ''')
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Vehicle', 'Type', 'Date', 'Odometer', 'Description', 'Cost', 'Interval Miles', 'Interval Days'])
            for row in cursor.fetchall():
                writer.writerow(row)
        messagebox.showinfo('Export Successful', 'Services exported to CSV successfully')

    def add_service(self):
        vehicle_selection = self.service_vehicle_combo.get()
        if not vehicle_selection:
            messagebox.showerror('Error', 'Select a vehicle')
            return
        vehicle_id = self.vehicle_id_map.get(vehicle_selection)
        service_type_selection = self.service_type_combo.get()
        service_type_id = self.service_type_id_map.get(service_type_selection) if service_type_selection else None
        date = self.service_date_entry.get()
        if not self.validate_date(date):
            messagebox.showerror('Error', 'Date must be in DD/MM/YYYY format (e.g., 31/12/2025)')
            return
        odometer = self.service_odometer_entry.get()
        interval_miles = self.service_interval_miles_entry.get()
        interval_days = self.service_interval_days_entry.get()
        description = self.service_desc_entry.get()
        cost = self.service_cost_entry.get()
        if not vehicle_id or not date:
            messagebox.showerror('Error', 'Vehicle and Date are required')
            return
        odometer_value = None
        if odometer:
            try:
                odometer_value = int(odometer)
            except ValueError:
                messagebox.showerror('Error', 'Odometer must be an integer if provided')
                return
        interval_miles_value = None
        if interval_miles:
            try:
                interval_miles_value = int(interval_miles)
            except ValueError:
                messagebox.showerror('Error', 'Service Interval Miles must be an integer if provided')
                return
        interval_days_value = None
        if interval_days:
            try:
                interval_days_value = int(interval_days)
            except ValueError:
                messagebox.showerror('Error', 'Service Interval Days must be an integer if provided')
                return
        cost_value = None
        if cost:
            try:
                cost_value = int(cost)
            except ValueError:
                messagebox.showerror('Error', 'Cost must be an integer if provided')
                return
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO services (vehicle_id, service_type_id, date, odometer, description, cost, service_interval_miles, service_interval_days) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (vehicle_id, service_type_id, date, odometer_value, description or None, cost_value, interval_miles_value, interval_days_value))
        self.conn.commit()
        self.load_services()
        self.clear_service_entries()
        self.clear_service_parts_tree()

    def select_service(self, event):
        selected = self.services_tree.focus()
        if selected:
            values = self.services_tree.item(selected, 'values')
            cursor = self.conn.cursor()
            cursor.execute('SELECT vehicle_id, service_type_id FROM services WHERE id = ?', (values[0],))
            vehicle_id, service_type_id = cursor.fetchone()
            cursor.execute('SELECT name, year, model FROM vehicles WHERE id = ?', (vehicle_id,))
            vehicle = cursor.fetchone()
            vehicle_display = f"{vehicle_id} - {vehicle[0]}{f' ({vehicle[1]} {vehicle[2]})' if vehicle[1] and vehicle[2] else ''}"
            self.service_vehicle_combo.set(vehicle_display)
            self.service_type_combo.set('')
            if service_type_id:
                cursor.execute('SELECT name FROM service_types WHERE id = ?', (service_type_id,))
                service_type_name = cursor.fetchone()[0]
                self.service_type_combo.set(f"{service_type_id} - {service_type_name}")
            self.service_date_entry.delete(0, ttk.END)
            self.service_date_entry.insert(0, values[3])
            self.service_odometer_entry.delete(0, ttk.END)
            self.service_odometer_entry.insert(0, values[4] if values[4] else '')
            self.service_interval_miles_entry.delete(0, ttk.END)
            self.service_interval_miles_entry.insert(0, values[7] if values[7] else '')
            self.service_interval_days_entry.delete(0, ttk.END)
            self.service_interval_days_entry.insert(0, values[8] if values[8] else '')
            self.service_desc_entry.delete(0, ttk.END)
            self.service_desc_entry.insert(0, values[5] if values[5] else '')
            self.service_cost_entry.delete(0, ttk.END)
            self.service_cost_entry.insert(0, values[6] if values[6] else '')
            self.load_service_parts(values[0])
            self.load_part_combo(vehicle_id=vehicle_id)
        else:
            self.load_part_combo()

    def load_service_parts(self, service_id):
        for item in self.service_parts_tree.get_children():
            self.service_parts_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COALESCE(sp.alt_part_id, p.id) AS part_id, p.name, 
                   COALESCE(ap.manufacturer, p.manufacturer) AS manufacturer, 
                   COALESCE(ap.part_number, p.part_number) AS part_number, 
                   sp.quantity_used
            FROM service_parts sp
            JOIN parts p ON sp.part_id = p.id
            LEFT JOIN alt_parts ap ON sp.alt_part_id = ap.alt_id
            WHERE sp.service_id = ?
            ORDER BY sp.part_id ASC, sp.alt_part_id ASC
        ''', (service_id,))
        for row in cursor.fetchall():
            self.service_parts_tree.insert('', 'end', values=row)

    def add_part_to_service(self):
        selected_service = self.services_tree.focus()
        if not selected_service:
            messagebox.showerror('Error', 'Select a service first')
            return
        service_id = self.services_tree.item(selected_service, 'values')[0]
        part_selection = self.part_combo.get()
        if not part_selection:
            messagebox.showerror('Error', 'Select a part')
            return
        part_id, alt_part_id = self.part_id_map.get(part_selection)
        qty_used = self.part_qty_used_entry.get()
        qty_used_value = 1  # Default to 1 if empty
        if qty_used:
            try:
                qty_used_value = int(qty_used)
                if qty_used_value <= 0:
                    messagebox.showerror('Error', 'Quantity must be a positive integer if provided')
                    return
            except ValueError:
                messagebox.showerror('Error', 'Quantity must be a positive integer if provided')
                return
        cursor = self.conn.cursor()
        # Check if the part (main or alternative) is already added to this service
        if alt_part_id:
            cursor.execute('SELECT COUNT(*) FROM service_parts WHERE service_id = ? AND alt_part_id = ?', (service_id, alt_part_id))
        else:
            cursor.execute('SELECT COUNT(*) FROM service_parts WHERE service_id = ? AND part_id = ? AND alt_part_id IS NULL', (service_id, part_id))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror('Error', 'This part or alternative part is already added to the service')
            return
        try:
            cursor.execute('INSERT INTO service_parts (service_id, part_id, alt_part_id, quantity_used) VALUES (?, ?, ?, ?)',
                           (service_id, part_id, alt_part_id, qty_used_value))
            self.conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'An unexpected error occurred while adding the part to the service')
            return
        self.load_service_parts(service_id)
        self.part_qty_used_entry.delete(0, ttk.END)

    def remove_part_from_service(self):
        selected_service = self.services_tree.focus()
        if not selected_service:
            messagebox.showerror('Error', 'Select a service first')
            return
        service_id = self.services_tree.item(selected_service, 'values')[0]
        selected_part = self.service_parts_tree.focus()
        if not selected_part:
            messagebox.showerror('Error', 'Select a part to remove')
            return
        part_id = self.service_parts_tree.item(selected_part, 'values')[0]
        cursor = self.conn.cursor()
        if part_id.isdigit():
            cursor.execute('DELETE FROM service_parts WHERE service_id=? AND part_id=? AND alt_part_id IS NULL', (service_id, part_id))
        else:
            cursor.execute('DELETE FROM service_parts WHERE service_id=? AND alt_part_id=?', (service_id, part_id))
        self.conn.commit()
        self.load_service_parts(service_id)

    def update_service(self):
        selected = self.services_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a service to update')
            return
        id_ = self.services_tree.item(selected, 'values')[0]
        vehicle_selection = self.service_vehicle_combo.get()
        if not vehicle_selection:
            messagebox.showerror('Error', 'Select a vehicle')
            return
        vehicle_id = self.vehicle_id_map.get(vehicle_selection)
        service_type_selection = self.service_type_combo.get()
        service_type_id = self.service_type_id_map.get(service_type_selection) if service_type_selection else None
        date = self.service_date_entry.get()
        if not self.validate_date(date):
            messagebox.showerror('Error', 'Date must be in DD/MM/YYYY format (e.g., 31/12/2025)')
            return
        odometer = self.service_odometer_entry.get()
        interval_miles = self.service_interval_miles_entry.get()
        interval_days = self.service_interval_days_entry.get()
        description = self.service_desc_entry.get()
        cost = self.service_cost_entry.get()
        if not vehicle_id or not date:
            messagebox.showerror('Error', 'Vehicle and Date are required')
            return
        odometer_value = None
        if odometer:
            try:
                odometer_value = int(odometer)
            except ValueError:
                messagebox.showerror('Error', 'Odometer must be an integer if provided')
                return
        interval_miles_value = None
        if interval_miles:
            try:
                interval_miles_value = int(interval_miles)
            except ValueError:
                messagebox.showerror('Error', 'Service Interval Miles must be an integer if provided')
                return
        interval_days_value = None
        if interval_days:
            try:
                interval_days_value = int(interval_days)
            except ValueError:
                messagebox.showerror('Error', 'Service Interval Days must be an integer if provided')
                return
        cost_value = None
        if cost:
            try:
                cost_value = int(cost)
            except ValueError:
                messagebox.showerror('Error', 'Cost must be an integer if provided')
                return
        cursor = self.conn.cursor()
        cursor.execute('UPDATE services SET vehicle_id=?, service_type_id=?, date=?, odometer=?, description=?, cost=?, service_interval_miles=?, service_interval_days=? WHERE id=?',
                       (vehicle_id, service_type_id, date, odometer_value, description or None, cost_value, interval_miles_value, interval_days_value, id_))
        self.conn.commit()
        self.load_services()
        self.clear_service_entries()

    def delete_service(self):
        selected = self.services_tree.focus()
        if not selected:
            messagebox.showerror('Error', 'Select a service to delete')
            return
        id_ = self.services_tree.item(selected, 'values')[0]
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM services WHERE id=?', (id_,))
        cursor.execute('DELETE FROM service_parts WHERE service_id=?', (id_,))
        self.conn.commit()
        self.load_services()
        self.clear_service_entries()
        self.clear_service_parts_tree()

    def clear_service_entries(self):
        if hasattr(self, 'service_vehicle_combo'):
            self.service_vehicle_combo.set('')
        if hasattr(self, 'service_type_combo'):
            self.service_type_combo.set('')
        self.service_date_entry.delete(0, ttk.END)
        self.service_date_entry.insert(0, datetime.now().strftime('%d/%m/%Y'))
        self.service_odometer_entry.delete(0, ttk.END)
        self.service_interval_miles_entry.delete(0, ttk.END)
        self.service_interval_days_entry.delete(0, ttk.END)
        self.service_desc_entry.delete(0, ttk.END)
        self.service_cost_entry.delete(0, ttk.END)
        self.clear_service_parts_tree()
        self.load_part_combo()

    def clear_service_parts_tree(self):
        for item in self.service_parts_tree.get_children():
            self.service_parts_tree.delete(item)

if __name__ == "__main__":
    root = ttk.Window()
    app = CarManagementApp(root)
    root.mainloop()
