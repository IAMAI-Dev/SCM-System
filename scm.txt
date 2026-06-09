import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

import mysql.connector

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("SCM_DB_HOST", "localhost"),
    "user": os.getenv("SCM_DB_USER", "root"),
    "password": os.getenv("SCM_DB_PASSWORD", ""),
    "database": os.getenv("SCM_DB_NAME", "exp1"),
}


class SCMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("供应链管理系统")
        self.root.geometry("1200x800")

        # 创建数据库连接
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

        # 界面布局
        self.create_widgets()

    def create_widgets(self):
        # 左侧导航栏
        nav_frame = tk.Frame(self.root, width=200, bg="#f0f0f0")
        nav_frame.pack(side="left", fill="y")

        # 导航按钮
        buttons = [
            ("订单管理", self.show_orders),
            ("库存查询", self.show_inventory),
            ("供应商分析", self.show_suppliers),
            ("客户管理", self.show_customers)
        ]

        for text, command in buttons:
            btn = tk.Button(nav_frame, text=text, width=15,
                            command=command, relief="flat", bg="#e0e0e0")
            btn.pack(pady=5, padx=10)

        # 主内容区域
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side="right", fill="both", expand=True)

        # 默认显示订单管理
        self.show_orders()

    # -------------------- 客户管理模块（新增） --------------------
    def show_customers(self):
        self.clear_main_frame()

        # 客户搜索区域
        search_frame = tk.Frame(self.main_frame)
        search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(search_frame, text="客户ID/名称:").pack(side="left")
        self.customer_search_entry = tk.Entry(search_frame, width=30)
        self.customer_search_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="搜索", command=self.search_customers).pack(side="left")
        tk.Button(search_frame, text="刷新", command=self.load_customers).pack(side="left", padx=10)
        tk.Button(search_frame, text="添加客户", command=self.add_customer).pack(side="right", padx=5)
        tk.Button(search_frame, text="删除客户", command=self.delete_customer).pack(side="right", padx=5)

        # 客户表格
        columns = ("客户ID", "姓名", "地址", "国家", "电话", "余额")
        self.customer_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")

        for col in columns:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=120)

        self.customer_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # 加载客户数据
        self.load_customers()

    def load_customers(self):
        # 清空表格
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)

        # 从数据库加载客户数据
        query = """
        SELECT 
            c.Custkey,
            c.Name,
            c.Address,
            n.Name,
            c.Phone,
            c.Acctbal
        FROM Customer c
        JOIN Nation n ON c.Nationkey = n.Nationkey
        LIMIT 100
        """
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            self.customer_tree.insert("", "end", values=row)

    def search_customers(self):
        keyword = self.customer_search_entry.get()
        query = """
        SELECT 
            c.Custkey,
            c.Name,
            c.Address,
            n.Name,
            c.Phone,
            c.Acctbal
        FROM Customer c
        JOIN Nation n ON c.Nationkey = n.Nationkey
        WHERE c.Custkey = %s OR c.Name LIKE %s
        """
        try:
            cust_id = int(keyword)
            self.cursor.execute(query, (cust_id, f"%{keyword}%"))
        except ValueError:
            self.cursor.execute(query, (-1, f"%{keyword}%"))  # 无效ID时仅按名称搜索

        self.customer_tree.delete(*self.customer_tree.get_children())
        for row in self.cursor.fetchall():
            self.customer_tree.insert("", "end", values=row)

    def add_customer(self):
        # 弹出对话框收集客户信息
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新客户")

        fields = ["姓名", "地址", "国家ID", "电话", "余额", "市场分区"]
        entries = []

        for i, field in enumerate(fields):
            tk.Label(dialog, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(dialog)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries.append(entry)

        def confirm_add():
            data = [entry.get() for entry in entries]
            try:
                query = """
                INSERT INTO Customer (Name, Address, Nationkey, Phone, Acctbal, Mktsegment)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (
                    data[0], data[1], int(data[2]), data[3],
                    float(data[4]), data[5]
                ))
                self.conn.commit()
                messagebox.showinfo("成功", "客户添加成功")
                dialog.destroy()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {e}")

        tk.Button(dialog, text="确认", command=confirm_add).grid(row=len(fields), columnspan=2, pady=10)

    def delete_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择客户")
            return

        customer_id = self.customer_tree.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("确认", f"确定删除客户ID {customer_id} 吗？")
        if confirm:
            try:
                self.cursor.execute("DELETE FROM Customer WHERE Custkey = %s", (customer_id,))
                self.conn.commit()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}（可能关联订单存在）")
    # -------------------- 订单管理模块 --------------------
    def show_orders(self):
        self.clear_main_frame()

        # 订单搜索区域
        search_frame = tk.Frame(self.main_frame)
        search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(search_frame, text="订单号:").pack(side="left")
        self.order_id_entry = tk.Entry(search_frame, width=20)
        self.order_id_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="搜索", command=self.search_orders).pack(side="left")
        tk.Button(search_frame, text="刷新", command=self.load_orders).pack(side="left", padx=10)

        # 订单表格
        columns = ("订单号", "客户", "总金额", "状态", "日期")
        self.order_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")

        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=120)

        self.order_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # 加载订单数据
        self.load_orders()

        # 订单操作按钮
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="查看明细", command=self.show_order_details).pack(side="left", padx=5)
        tk.Button(btn_frame, text="更新状态", command=self.update_order_status).pack(side="left", padx=5)

    def load_orders(self):
        # 清空表格
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)

        # 从数据库加载数据
        query = """
        SELECT 
            o.Orderkey, 
            c.Name, 
            o.Totalprice, 
            o.Orderstatus, 
            o.Orderdate 
        FROM Orders o
        JOIN Customer c ON o.Custkey = c.Custkey
        LIMIT 100
        """
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            self.order_tree.insert("", "end", values=row)

    # -------------------- 库存查询模块 --------------------
    def show_inventory(self):
        self.clear_main_frame()

        # 库存表格
        columns = ("零件号", "名称", "品牌", "库存量", "供应商", "成本价")
        self.inventory_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")

        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=120)

        self.inventory_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # 加载库存数据
        query = """
        SELECT 
            p.Partkey,
            p.Name,
            p.Brand,
            ps.Availqty,
            s.Name,
            ps.Supplycost
        FROM PartSupp ps
        JOIN Part p ON ps.Partkey = p.Partkey
        JOIN Supplier s ON ps.Suppkey = s.Suppkey
        """
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            self.inventory_tree.insert("", "end", values=row)

    # -------------------- 供应商分析模块 --------------------
    def show_suppliers(self):
        self.clear_main_frame()

        # 供应商统计表格
        columns = ("供应商ID", "名称", "国家", "供应零件数", "平均成本")
        self.supplier_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")

        for col in columns:
            self.supplier_tree.heading(col, text=col)
            self.supplier_tree.column(col, width=120)

        self.supplier_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # 加载供应商数据
        query = """
        SELECT 
            s.Suppkey,
            s.Name,
            n.Name,
            COUNT(ps.Partkey),
            AVG(ps.Supplycost)
        FROM Supplier s
        JOIN Nation n ON s.Nationkey = n.Nationkey
        JOIN PartSupp ps ON s.Suppkey = ps.Suppkey
        GROUP BY s.Suppkey
        """
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            self.supplier_tree.insert("", "end", values=row)

    # -------------------- 公共工具方法 --------------------
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def search_orders(self):
        order_id = self.order_id_entry.get()
        query = """
        SELECT 
            o.Orderkey, 
            c.Name, 
            o.Totalprice, 
            o.Orderstatus, 
            o.Orderdate 
        FROM Orders o
        JOIN Customer c ON o.Custkey = c.Custkey
        WHERE o.Orderkey = %s
        """
        self.cursor.execute(query, (order_id,))
        result = self.cursor.fetchone()
        if result:
            messagebox.showinfo("搜索结果", f"找到订单: {result}")
        else:
            messagebox.showerror("错误", "未找到该订单")

    def show_order_details(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择订单")
            return

        item = self.order_tree.item(selected[0])
        order_id = item["values"][0]

        # 弹出明细窗口
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"订单明细 - 订单号 {order_id}")

        # 显示 Lineitem 数据
        columns = ("零件号", "数量", "价格", "折扣", "发货状态")
        tree = ttk.Treeview(detail_win, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        query = """
        SELECT 
            l.Partkey,
            l.Quantity,
            l.Extendedprice,
            l.Discount,
            l.Linestatus
        FROM Lineitem l
        WHERE l.Orderkey = %s
        """
        self.cursor.execute(query, (order_id,))
        for row in self.cursor.fetchall():
            tree.insert("", "end", values=row)

    def update_order_status(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择订单")
            return

        item = self.order_tree.item(selected[0])
        order_id = item["values"][0]

        # 弹出状态更新窗口
        status_win = tk.Toplevel(self.root)
        status_win.title("更新订单状态")

        tk.Label(status_win, text="新状态:").pack(pady=10)
        status_var = tk.StringVar(value="pending")
        ttk.Combobox(status_win, textvariable=status_var,
                     values=["pending", "shipped", "delivered"]).pack()

        def confirm_update():
            new_status = status_var.get()
            query = "UPDATE Orders SET Orderstatus = %s WHERE Orderkey = %s"
            try:
                self.cursor.execute(query, (new_status, order_id))
                self.conn.commit()
                messagebox.showinfo("成功", "状态已更新")
                status_win.destroy()
                self.load_orders()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(status_win, text="确认", command=confirm_update).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = SCMApp(root)
    root.mainloop()
