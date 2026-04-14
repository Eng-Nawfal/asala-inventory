import flet as ft
import traceback

def main(page: ft.Page):
    try:


import flet as ft
import sqlite3
import os

def main(page: ft.Page):
    page.title = "نظام مكتب الأصالة الهندسي"
    page.rtl = True
    page.theme_mode = "light"
    page.bgcolor = "#F0F4F8"
    page.padding = 0

    db_path = os.path.join(os.path.expanduser("~"), "al_asala_db.db")
    
    def db_query(query, params=(), fetch=False):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            data = cursor.fetchall() if fetch else None
            conn.commit()
            return data
        except: return []
        finally: conn.close()

    db_query("CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)")
    db_query("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, stock INTEGER, buy_price REAL, sell_price REAL)")

    content_area = ft.Column(expand=True, scroll="adaptive", spacing=15)

    def show_inventory_selection(e=None):
        content_area.controls.clear()
        search_input = ft.TextField(label="اكتب اسم المادة للاستعلام عنها...", border_radius=10, bgcolor="white")
        search_btn = ft.ElevatedButton("بحث الآن", on_click=lambda _: render_inventory_table("بحث", search_input.value), bgcolor="#0D47A1", color="white")

        options_row = ft.Row(scroll="auto", spacing=10)
        options_row.controls.append(ft.ElevatedButton("عرض الكل", on_click=lambda _: render_inventory_table("الكل")))
        
        cats = db_query("SELECT name FROM categories", fetch=True)
        for c in cats:
            options_row.controls.append(ft.OutlinedButton(c[0], on_click=lambda x, n=c[0]: render_inventory_table(n)))

        content_area.controls.extend([
            ft.Text("قسم الاستعلام والجرد", size=22, weight="bold", color="#0D47A1"),
            ft.Row([search_input, search_btn]),
            ft.Divider(),
            ft.Text("تصفح حسب القسم:"),
            options_row
        ])
        page.update()

    def render_inventory_table(mode, value=None):
        content_area.controls.clear()
        content_area.controls.append(ft.Row([
            ft.Text(f"النتائج: {value if mode=='بحث' else mode}", size=20, weight="bold"),
            ft.ElevatedButton("رجوع", on_click=show_inventory_selection)
        ], alignment="spaceBetween"))

        if mode == "بحث":
            query = "SELECT name, category, stock, buy_price, sell_price, id FROM items WHERE name LIKE ?"
            params = (f"%{value}%",)
        elif mode == "الكل":
            query = "SELECT name, category, stock, buy_price, sell_price, id FROM items"
            params = ()
        else:
            query = "SELECT name, category, stock, buy_price, sell_price, id FROM items WHERE category = ?"
            params = (mode,)
        
        data = db_query(query, params, fetch=True)
        
        # أضفنا عمود "القسم" هنا
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("المادة")),
                ft.DataColumn(ft.Text("القسم")),
                ft.DataColumn(ft.Text("العدد")),
                ft.DataColumn(ft.Text("شراء")),
                ft.DataColumn(ft.Text("بيع")),
                ft.DataColumn(ft.Text("إجراء")),
            ],
            rows=[]
        )

        for item in data:
            table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item[0], weight="bold")),
                ft.DataCell(ft.Text(item[1])), # عرض القسم
                ft.DataCell(ft.Text(str(item[2]))),
                ft.DataCell(ft.Text(str(item[3]))),
                ft.DataCell(ft.Text(str(item[4]))),
                ft.DataCell(ft.Row([
                    ft.ElevatedButton("تعديل", on_click=lambda x, i=item: show_edit_dialog(i), height=30),
                    ft.ElevatedButton("حذف", on_click=lambda x, i=item[5]: [db_query("DELETE FROM items WHERE id=?", (i,)), render_inventory_table(mode, value)], bgcolor="red", color="white", height=30)
                ]))
            ]))
        
        content_area.controls.append(ft.Container(content=table, bgcolor="white", border_radius=10, padding=10))
        page.update()

    def show_edit_dialog(item):
        n_edit = ft.TextField(label="الاسم", value=item[0])
        s_edit = ft.TextField(label="العدد", value=str(item[2]))
        b_edit = ft.TextField(label="الشراء", value=str(item[3]))
        sl_edit = ft.TextField(label="البيع", value=str(item[4]))

        def save(e):
            db_query("UPDATE items SET name=?, stock=?, buy_price=?, sell_price=? WHERE id=?", (n_edit.value, s_edit.value, b_edit.value, sl_edit.value, item[5]))
            dialog.open = False
            show_inventory_selection()

        dialog = ft.AlertDialog(
            title=ft.Text("تعديل المادة"),
            content=ft.Column([n_edit, s_edit, b_edit, sl_edit], tight=True),
            actions=[ft.ElevatedButton("حفظ", on_click=save), ft.TextButton("إلغاء", on_click=lambda _: setattr(dialog, "open", False) or page.update())]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def show_add_page(e=None):
        content_area.controls.clear()
        cats = db_query("SELECT name FROM categories", fetch=True)
        cat_opts = [ft.dropdown.Option(c[0]) for c in cats]
        name_in = ft.TextField(label="اسم المادة", border_radius=10, bgcolor="white")
        cat_in = ft.Dropdown(label="القسم", options=cat_opts, border_radius=10, bgcolor="white")
        stock_in = ft.TextField(label="الكمية", keyboard_type="number")
        buy_in = ft.TextField(label="سعر الشراء", keyboard_type="number")
        sell_in = ft.TextField(label="سعر البيع", keyboard_type="number")

        def save(e):
            if name_in.value and cat_in.value:
                db_query("INSERT INTO items (name, category, stock, buy_price, sell_price) VALUES (?, ?, ?, ?, ?)", (name_in.value, cat_in.value, stock_in.value, buy_in.value, sell_in.value))
                show_add_page()

        content_area.controls.extend([
            ft.Text("إضافة مادة جديدة", size=22, weight="bold"),
            name_in, cat_in, ft.Row([stock_in, buy_in, sell_in]),
            ft.ElevatedButton("حفظ البيانات", on_click=save, bgcolor="#0D47A1", color="white", height=50, width=500)
        ])
        page.update()

    def show_manage_cats(e=None):
        content_area.controls.clear()
        new_cat = ft.TextField(label="اسم القسم الجديد", expand=True)
        def add_c(e):
            if new_cat.value:
                db_query("INSERT INTO categories VALUES (?)", (new_cat.value,))
                new_cat.value = ""; show_manage_cats()

        cat_list = ft.Column()
        for c in db_query("SELECT name FROM categories", fetch=True):
            cat_list.controls.append(ft.Row([ft.Text(c[0], size=18, expand=True), ft.ElevatedButton("حذف", on_click=lambda x, n=c[0]: [db_query("DELETE FROM categories WHERE name=?", (n,)), show_manage_cats()], bgcolor="red", color="white")]))

        content_area.controls.extend([ft.Text("إدارة الأقسام", size=22, weight="bold"), ft.Row([new_cat, ft.ElevatedButton("إضافة", on_click=add_c)]), cat_list])
        page.update()

    header = ft.Container(content=ft.Text("معرض ملاك - ابو غفران", color="white", size=24, weight="bold"), bgcolor="#0D47A1", padding=20, alignment=ft.Alignment(0, 0))
    nav = ft.Container(content=ft.Row([ft.ElevatedButton("الاستعلام والجرد", on_click=show_inventory_selection), ft.ElevatedButton("إضافة مادة", on_click=show_add_page), ft.ElevatedButton("الأقسام", on_click=show_manage_cats)], alignment="spaceAround"), bgcolor="#1565C0", padding=10)
    page.add(header, nav, ft.Container(content=content_area, padding=20, expand=True))
    show_inventory_selection()

ft.app(target=main)
page.add(ft.Text("تم تشغيل نظام مكتب الأصالة بنجاح!"))
        # --------------------------------
    except Exception as e:
        # في حال حدوث أي خطأ، سيظهر لك النص الأحمر بدلاً من الشاشة البيضاء
        error_details = traceback.format_exc()
        page.add(ft.Column([
            ft.Text("حدث خطأ أثناء التشغيل:", size=20, color="red"),
            ft.Text(error_details, color="orange", selectable=True)
        ], scroll=True))

ft.app(target=main)
