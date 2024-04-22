import tkinter as tk
from tkinter import ttk, messagebox
from conexion import Registro_datos  # Importa la clase desde conexion.py

# Instancia de la clase para conectar con la base de datos
db = Registro_datos()

def registrar():
    try:
        db.inserta_producto(codigo_entry.get(), nombre_entry.get(), modelo_entry.get(), precio_entry.get(), cantidad_entry.get())
        messagebox.showinfo("Registro", "Producto registrado con éxito")
        limpiar_campos()
        mostrar_datos()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def limpiar_campos():
    codigo_entry.delete(0, tk.END)
    nombre_entry.delete(0, tk.END)
    modelo_entry.delete(0, tk.END)
    precio_entry.delete(0, tk.END)
    cantidad_entry.delete(0, tk.END)

def eliminar():
    selected_item = tree.selection()  # Obtén la selección actual del TreeView
    if selected_item:  # Verifica si hay algo seleccionado
        item = tree.item(selected_item)
        record_id = item['values'][0]  # Asume que el ID es el primer elemento en tus valores
        try:
            db.elimina_productos_por_id(record_id)  # Función de eliminación basada en ID
            tree.delete(selected_item)  # Elimina el ítem del TreeView
            messagebox.showinfo("Eliminar", "Producto eliminado con éxito")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "No hay ningún producto seleccionado")


def buscar_por_nombre():
    try:
        resultados = db.busca_producto(nombre_buscar_entry.get())
        if resultados:
            limpiar_treeview()
            for resultado in resultados:
                tree.insert("", tk.END, values=resultado)
        else:
            messagebox.showinfo("Buscar", "No se encontró ningún producto")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def mostrar_datos():
    try:
        registros = db.mostrar_productos()
        limpiar_treeview()
        for registro in registros:
            # Asegúrate de que el ID esté incluido aquí como el primer valor
            tree.insert("", tk.END, values=(registro[0], registro[1], registro[2], registro[3], registro[4]))
    except Exception as e:
        messagebox.showerror("Error", str(e))


def limpiar_treeview():
    for i in tree.get_children():
        tree.delete(i)

# Creación de la ventana principal
ventana = tk.Tk()
ventana.geometry("900x500")
ventana.title("Registro de productos")

# Etiquetas y campos de entrada
codigo_label = tk.Label(ventana, text="Código:")
codigo_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
codigo_entry = tk.Entry(ventana)
codigo_entry.grid(row=0, column=1, padx=10, pady=5)

nombre_label = tk.Label(ventana, text="Nombre:")
nombre_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
nombre_entry = tk.Entry(ventana)
nombre_entry.grid(row=1, column=1, padx=10, pady=5)

modelo_label = tk.Label(ventana, text="Modelo:")
modelo_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
modelo_entry = tk.Entry(ventana)
modelo_entry.grid(row=2, column=1, padx=10, pady=5)

precio_label = tk.Label(ventana, text="Precio:")
precio_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
precio_entry = tk.Entry(ventana)
precio_entry.grid(row=3, column=1, padx=10, pady=5)

cantidad_label = tk.Label(ventana, text="Cantidad:")
cantidad_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
cantidad_entry = tk.Entry(ventana)
cantidad_entry.grid(row=4, column=1, padx=10, pady=5)

# Campo de entrada para buscar por nombre
nombre_buscar_label = tk.Label(ventana, text="Buscar por nombre:")
nombre_buscar_label.grid(row=5, column=0, sticky="w", padx=10, pady=5)
nombre_buscar_entry = tk.Entry(ventana)
nombre_buscar_entry.grid(row=5, column=1, padx=10, pady=5)

# Botones para operaciones
registrar_btn = tk.Button(ventana, text="Registrar", command=registrar)
registrar_btn.grid(row=6, column=0, padx=10, pady=20, sticky="ew")
limpiar_btn = tk.Button(ventana, text="Limpiar", command=limpiar_campos)
limpiar_btn.grid(row=6, column=1, padx=10, pady=20, sticky="ew")
eliminar_btn = tk.Button(ventana, text="Eliminar", command=eliminar)
eliminar_btn.grid(row=7, column=0, padx=10, pady=20, sticky="ew")
buscar_btn = tk.Button(ventana, text="Buscar por nombre", command=buscar_por_nombre)
buscar_btn.grid(row=7, column=1, padx=10, pady=20, sticky="ew")
mostrar_btn = tk.Button(ventana, text="Mostrar datos", command=mostrar_datos)
mostrar_btn.grid(row=8, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

# Treeview para mostrar los productos
tree_frame = tk.Frame(ventana)
tree_frame.grid(row=0, column=2, rowspan=9, padx=10, pady=10, sticky="nsew")
tree_scroll = tk.Scrollbar(tree_frame)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
tree = ttk.Treeview(tree_frame, columns=("Código", "Nombre", "Modelo", "Precio", "Cantidad"), show="headings")
tree.pack(fill="both", expand=True)
tree_scroll.config(command=tree.yview)
tree.config(yscrollcommand=tree_scroll.set)
tree.heading("Código", text="Código")
tree.heading("Nombre", text="Nombre")
tree.heading("Modelo", text="Modelo")
tree.heading("Precio", text="Precio")
tree.heading("Cantidad", text="Cantidad")

# Iniciar la aplicación
ventana.mainloop()
