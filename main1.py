import tkinter as tk
from tkinter import Entry, Label, Frame, Tk, Button,ttk, Scrollbar, VERTICAL, HORIZONTAL,StringVar,END
from tkinter import messagebox

from conexion import Registro_datos 

db = Registro_datos()

class Registro(Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.master.title("Registro de Datos")
        self.master.geometry('900x500')
        self.master.resizable(0, 0)
        
        self.db = Registro_datos()

        # Configuración de la interfaz
        self.setup_ui()

    def setup_ui(self):
        self.frame1 = Frame(self.master)
        self.frame1.grid(columnspan=2, column=0, row=0)
        self.frame2 = Frame(self.master)
        self.frame2.grid(column=0, row=1)
        self.frame3 = Frame(self.master)
        self.frame3.grid(rowspan=2, column=1, row=1)
        self.frame4 = Frame(self.master)
        self.frame4.grid(column=0, row=2)

        self.codigo = StringVar()
        self.nombre = StringVar()
        self.modelo = StringVar()
        self.precio = StringVar()
        self.cantidad = StringVar()
        self.buscar = StringVar()

        # Creación de widgets
        self.create_widgets()

    def create_widgets(self):
        Label(self.frame1, text='REGISTRO DE DATOS', font=('Orbitron', 15, 'bold')).grid(column=0, row=0)
        self.add_data_widgets()
        self.add_control_widgets()
        self.setup_treeview()
        self.configure_styles()

    def add_data_widgets(self):
        labels = ['Codigo', 'Nombre', 'Modelo', 'Precio', 'Cantidad']
        for idx, text in enumerate(labels):
            Label(self.frame2, text=text, font=('Rockwell', 13, 'bold')).grid(column=0, row=idx + 1, pady=15)
            entry = Entry(self.frame2, textvariable=getattr(self, text.lower()), font=('Arial', 12))
            entry.grid(column=1, row=idx + 1, padx=5)

    def add_control_widgets(self):
        Button(self.frame4, text='REGISTRAR', command=self.agregar_datos, font=('Arial', 10, 'bold')).grid(column=0, row=1, pady=10, padx=4)
        Button(self.frame4, text='LIMPIAR', command=self.limpiar_datos, font=('Arial', 10, 'bold')).grid(column=1, row=1, padx=10)
        Button(self.frame4, text='ELIMINAR', command=self.eliminar_fila, font=('Arial', 10, 'bold')).grid(column=2, row=1, padx=4)
        Button(self.frame4, text='BUSCAR POR NOMBRE', command=self.buscar_nombre, font=('Arial', 8, 'bold')).grid(columnspan=2, column=1, row=2)
        Entry(self.frame4, textvariable=self.buscar, font=('Arial', 12), width=10).grid(column=0, row=2, pady=1, padx=8)
        Button(self.frame4, text='MOSTRAR TODO', command=self.mostrar_todo, font=('Arial', 10, 'bold')).grid(columnspan=3, column=0, row=3, pady=8)




    def setup_treeview(self):
        self.tabla = ttk.Treeview(self.frame3, height=21)
        self.tabla.grid(column=0, row=0)
        Scrollbar(self.frame3, orient=HORIZONTAL, command=self.tabla.xview).grid(column=0, row=1, sticky='ew')
        Scrollbar(self.frame3, orient=VERTICAL, command=self.tabla.yview).grid(column=1, row=0, sticky='ns')
        self.tabla.configure(xscrollcommand=self.tabla.xview, yscrollcommand=self.tabla.yview)
        self.tabla['columns'] = ('Nombre', 'Modelo', 'Precio', 'Cantidad')
        for col in ['Nombre', 'Modelo', 'Precio', 'Cantidad']:
            self.tabla.column(col, minwidth=100, width=120, anchor='center')
            self.tabla.heading(col, text=col, anchor='center')
        self.tabla.column('#0', minwidth=100, width=120, anchor='center')
        self.tabla.heading('#0', text='Codigo', anchor='center')

    def configure_styles(self):
        estilo = ttk.Style(self.frame3)
        estilo.theme_use('alt')
        estilo.configure(".", font=('Helvetica', 12, 'bold'))
        estilo.configure("Treeview", font=('Helvetica', 10, 'bold'))
        estilo.map('Treeview', background=[('selected', 'SystemHighlight')], foreground=[('selected', 'SystemHighlightText')])

    def agregar_datos(self):
        self.tabla.get_children()
        codigo = self.codigo.get()
        nombre = self.nombre.get()
        modelo = self.modelo.get()
        precio = self.precio.get()
        cantidad = self.cantidad.get()
        datos = (nombre, modelo, precio, cantidad)
        if codigo and nombre and modelo and precio and cantidad !='':        
            self.tabla.insert('',0, text = codigo, values=datos)
            self.base_datos.inserta_producto(codigo, nombre, modelo, precio, cantidad)


    def limpiar_datos(self):
        self.tabla.delete(*self.tabla.get_children())
        self.codigo.set('')
        self.nombre.set('')
        self.modelo.set('')
        self.precio.set('')
        self.cantidad.set('')

    def eliminar_fila(self):
        fila = self.tabla.selection()
        if fila:
            item = self.tabla.item(fila)
            nombre = item['values'][0]
            self.base_datos.elimina_productos(nombre)
            self.tabla.delete(fila)


    def buscar_nombre(self):
        nombre_producto = self.buscar.get().strip()
        if nombre_producto:
            nombre_buscado = self.base_datos.busca_producto(nombre_producto)
            self.tabla.delete(*self.tabla.get_children())
            for i, dato in enumerate(nombre_buscado):
                self.tabla.insert('', 'end', text=dato[1], values=dato[2:6])
        else:
            messagebox.showerror("Error", "Ingrese un nombre para buscar.")


    def mostrar_todo(self):
        self.tabla.delete(*self.tabla.get_children())
        registro = self.base_datos.mostrar_productos()
        i = -1
        for dato in registro:
            i= i+1                       
            self.tabla.insert('',i, text = registro[i][1:2], values=registro[i][2:6])


    def obtener_fila(self, event):
        current_item = self.tabla.focus()
        if not current_item:
            return
        data = self.tabla.item(current_item)
        self.nombre_borar = data['values'][0]

if __name__ == "__main__":
    root = tk.Tk()
    app = Registro(root)
    app.mainloop()
