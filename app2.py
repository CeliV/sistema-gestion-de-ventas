# gestion_ventas_cli.py
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import sys

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345678",
    "database": "gestion_de_ventas",
    "autocommit": False
}

#me conecto a la base de datos
def get_connection(create_db_if_missing=True):
    cfg = DB_CONFIG.copy()
    database = cfg.pop("database", None)
    try:
        conn = mysql.connector.connect(**cfg, database=database)
        return conn
    except mysql.connector.Error as err:
        if create_db_if_missing and err.errno == errorcode.ER_BAD_DB_ERROR:
            # creo la BD por las dudas y vuelvo a conectarla
            tmp = mysql.connector.connect(**cfg)
            cur = tmp.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} DEFAULT CHARACTER SET 'utf8mb4'")
            tmp.commit()
            cur.close()
            tmp.close()
            cfg["database"] = DB_CONFIG["database"]
            conn = mysql.connector.connect(**cfg)
            return conn
        else:
            raise


# inicializo las tablas si no existen
def init_db(conn):
    cursor = conn.cursor()

    create_tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS clientes (
            idClientes INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            telefono VARCHAR(50),
            direccion VARCHAR(255)
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS productos (
            idProductos INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            categoria VARCHAR(100),
            precio DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL,
            INDEX idx_producto_nombre (nombre)
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS ordenes (
            idOrden INT AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT,
            producto_id INT,
            cantProductos INT NOT NULL,
            fecha DATE,
            FOREIGN KEY (cliente_id) REFERENCES clientes(idClientes)
                ON UPDATE CASCADE
                ON DELETE RESTRICT,
            FOREIGN KEY (producto_id) REFERENCES productos(idProductos)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        ) ENGINE=InnoDB;
        """
    ]

    try:
        for sql in create_tables_sql:
            cursor.execute(sql)

        cursor.close()  
        conn.commit()

        print("Tablas verificadas/creadas exitosamente.")

    except mysql.connector.Error as err:
        print("ERROR al crear tablas:", err)
        conn.rollback()

#------ EL CRUD DE PRODUCTOS -------

#hago la funcion para agregar productos 
def agregar_producto(conn):
    print("=== Agregar Nuevo Producto ===")
    
    nombre = input("Nombre del producto: ").strip()
    if not nombre:
        print("El nombre del producto no puede estar vacío.")
        return

    categoria = input("Categoría: ").strip()
    if not categoria:
        print("La categoría no puede estar vacía.")
        return

    precio = input("Precio (ej 1000.00): ").strip()
    try:
        precio = float(precio)
        if precio <= 0:
            print("El precio debe ser mayor que 0.")
            return
    except ValueError:
        print("Precio inválido. Debe ser un número.")
        return

    stock = input("Stock inicial (int, >0): ").strip()
    try:
        stock = int(stock)
        if stock <= 0:
            print("El stock inicial debe ser mayor que 0.")
            return
    except ValueError:
        print("Stock inválido. Debe ser un número entero mayor que 0.")
        return

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (%s, %s, %s, %s)",
            (nombre, categoria, precio, stock)
        )
        conn.commit()
        print("Producto agregado con id:", cur.lastrowid)
    except mysql.connector.Error as e:
        conn.rollback()
        print("Error al agregar producto:", e)
    finally:
        cur.close()



#hago la funcion para ver los productos que hay en la tabla de productos
def ver_productos(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT idProductos, nombre, categoria, precio, stock FROM productos ORDER BY nombre")
    rows = cur.fetchall()
    if not rows:
        print("No hay productos.")
    else:
        for r in rows:
            print(f"{r['idProductos']}: {r['nombre']} | {r['categoria']} | ${r['precio']} | stock: {r['stock']}")
    cur.close()

#hago la funcion para actualizar cualquier dato de cualquier producto
def actualizar_producto(conn):
    ver_productos(conn)
    pid = input("ID producto a actualizar: ").strip()
    try:
        pid = int(pid)
    except ValueError:
        print("ID inválido.")
        return

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM productos WHERE idProductos=%s", (pid,))
    producto = cur.fetchone()
    if not producto:
        print("Producto no encontrado.")
        cur.close()
        return

    print("Dejar vacío para mantener el valor actual.")
    nombre = input(f"Nuevo nombre [{producto['nombre']}]: ").strip()
    categoria = input(f"Nueva categoría [{producto['categoria']}]: ").strip()
    precio = input(f"Nuevo precio [{producto['precio']}]: ").strip()
    stock = input(f"Nuevo stock [{producto['stock']}]: ").strip()

    updates = []
    params = []

    if nombre:
        updates.append("nombre=%s")
        params.append(nombre)
    if categoria:
        updates.append("categoria=%s")
        params.append(categoria)
    if precio:
        try:
            precio_val = float(precio)
            if precio_val > 0:
                updates.append("precio=%s")
                params.append(precio_val)
            else:
                print("El precio debe ser mayor que 0. Se omite la actualización de precio.")
        except ValueError:
            print("Precio inválido. Se omite la actualización de precio.")
    if stock:
        try:
            stock_val = int(stock)
            if stock_val > 0:
                updates.append("stock=%s")
                params.append(stock_val)
            else:
                print("El stock debe ser mayor que 0. Se omite la actualización de stock.")
        except ValueError:
            print("Stock inválido. Se omite la actualización de stock.")

    if updates:
        sql = f"UPDATE productos SET {', '.join(updates)} WHERE idProductos=%s"
        params.append(pid)
        try:
            cur.execute(sql, tuple(params))
            conn.commit()
            print("Producto actualizado correctamente. Campos modificados:", ", ".join(
                [f for f in ["nombre","categoria","precio","stock"] if f in [u.split('=')[0] for u in updates]]
            ))
        except mysql.connector.Error as e:
            conn.rollback()
            print("Error al actualizar:", e)
    else:
        print("Nada para actualizar, se mantienen los valores actuales.")

    cur.close()



#hago la funcion para eliminar a un producto en especifico
def eliminar_producto(conn):
    ver_productos(conn)
    pid = input("ID producto a eliminar: ").strip()
    try:
        pid = int(pid)
    except:
        print("ID inválido.")
        return
    cur = conn.cursor()
    try:
        
        cur.execute("DELETE FROM productos WHERE idProductos=%s", (pid,))
        if cur.rowcount == 0:
            print("Producto no encontrado o no se pudo eliminar (quizá tiene órdenes).")
            conn.rollback()
        else:
            conn.commit()
            print("Producto eliminado.")
    except mysql.connector.Error as e:
        conn.rollback()
        print("Error al eliminar producto:", e)
    finally:
        cur.close()



# ------------ EL CRUD DE CLIENTES -------------
import re

#hago la funcion para agregar clientes
def agregar_cliente(conn):
    print("=== Agregar Nuevo Cliente ===")

    nombre = input("Nombre del cliente: ").strip()
    if not nombre:
        print("El nombre del cliente no puede estar vacío.")
        return

    email = input("Email: ").strip()
    if not email:
        print("El email no puede estar vacío.")
        return
    # validoque el email tenga un formato basico
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print("Email inválido.")
        return

    telefono = input("Teléfono: ").strip()
    if not telefono:
        print("El teléfono no puede estar vacío.")
        return
    # valido que el telefono tenga un formato basico
    if not re.match(r"^[0-9+\-\s]+$", telefono):
        print("Teléfono inválido. Solo se permiten números, +, - y espacios.")
        return

    direccion = input("Dirección: ").strip()
    if not direccion:
        print("La dirección no puede estar vacía.")
        return

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO clientes (nombre, email, telefono, direccion) VALUES (%s, %s, %s, %s)",
            (nombre, email, telefono, direccion)
        )
        conn.commit()
        print("Cliente agregado con id:", cur.lastrowid)
    except mysql.connector.Error as e:
        conn.rollback()
        print("Error al agregar cliente:", e)
    finally:
        cur.close()


#hago la funcion para ver los clientes que hay en la tabla de clientes
def ver_clientes(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT idClientes, nombre, email, telefono, direccion FROM clientes ORDER BY nombre")
    rows = cur.fetchall()
    if not rows:
        print("No hay clientes.")
    else:
        for r in rows:
            print(f"{r['idClientes']}: {r['nombre']} | {r['email']} | {r['telefono']} | {r['direccion']}")
    cur.close()


#hago la funcion para actualizar cualquier dato de cualquier cliente
def actualizar_cliente(conn):
    ver_clientes(conn)
    cid = input("ID cliente a actualizar: ").strip()
    try:
        cid = int(cid)
    except:
        print("ID inválido.")
        return
    cur = conn.cursor()
    cur.execute("SELECT idClientes FROM clientes WHERE idClientes=%s", (cid,))
    if cur.fetchone() is None:
        print("Cliente no encontrado.")
        cur.close()
        return
    nombre = input("Nuevo nombre (vacío para no cambiar): ").strip()
    email = input("Nuevo email (vacío para no cambiar): ").strip()
    telefono = input("Nuevo teléfono (vacío para no cambiar): ").strip()
    direccion = input("Nueva dirección (vacío para no cambiar): ").strip()
    updates = []; params=[]
    if nombre:
        updates.append("nombre=%s"); params.append(nombre)
    if email:
        updates.append("email=%s"); params.append(email)
    if telefono:
        updates.append("telefono=%s"); params.append(telefono)
    if direccion:
        updates.append("direccion=%s"); params.append(direccion)
    if updates:
        sql = f"UPDATE clientes SET {', '.join(updates)} WHERE idClientes=%s"
        params.append(cid)
        try:
            cur.execute(sql, tuple(params))
            conn.commit()
            print("Cliente actualizado.")
        except mysql.connector.Error as e:
            conn.rollback()
            print("Error al actualizar cliente:", e)
    else:
        print("Nada para actualizar.")
    cur.close()

#hago la funcion para eliminar a un cliente en especifico
def eliminar_cliente(conn):
    ver_clientes(conn)
    cid = input("ID cliente a eliminar: ").strip()
    try:
        cid = int(cid)
    except ValueError:
        print("ID inválido.")
        return

    cur = conn.cursor()
    try:
        # Intento de eliminacion
        cur.execute("DELETE FROM clientes WHERE idClientes=%s", (cid,))
        if cur.rowcount == 0:
            print("Cliente no encontrado o no se pudo eliminar (quizá tiene órdenes).")
            conn.rollback()
        else:
            conn.commit()
            print("Cliente eliminado.")
    except mysql.connector.Error as e:
        conn.rollback()
        print("Error al eliminar cliente:", e)
    finally:
        cur.close()


# ------------ CRUD DE ORDENES -------------

#hago la funcion para crear ordenes
def crear_orden(conn):
    print("=== Crear Nueva Orden ===")
    ver_clientes(conn)
    cid = input("ID cliente: ").strip()
    ver_productos(conn)
    pid = input("ID producto: ").strip()
    cant = input("Cantidad: ").strip()

    # Valido las entradas
    try:
        cid = int(cid)
        pid = int(pid)
        cant = int(cant)
        if cant <= 0:
            print("La cantidad debe ser mayor que 0.")
            return
    except ValueError:
        print("IDs o cantidad inválida.")
        return

    cur = conn.cursor(dictionary=True)
    try:
        # Verifico si existe el cliente
        cur.execute("SELECT idClientes FROM clientes WHERE idClientes=%s", (cid,))
        if cur.fetchone() is None:
            print("Cliente no encontrado.")
            return

        # Verifico que el producto existe y obtener stock
        cur.execute("SELECT idProductos, stock FROM productos WHERE idProductos=%s FOR UPDATE", (pid,))
        producto = cur.fetchone()
        if producto is None:
            print("Producto no encontrado.")
            return

        stock = producto['stock']
        if cant > stock:
            print(f"Stock insuficiente. Disponible: {stock}")
            return

        # Insercion de orden y obtener el ID generado
        cur.execute(
            "INSERT INTO ordenes (cliente_id, producto_id, cantProductos, fecha) VALUES (%s, %s, %s, %s)",
            (cid, pid, cant, datetime.now().date())
        )
        orden_id = cur.lastrowid  # ← LEER ID AQUÍ

        # Actualizo el stock
        cur.execute(
            "UPDATE productos SET stock = stock - %s WHERE idProductos=%s",
            (cant, pid)
        )

        conn.commit()
        print("Orden creada correctamente. idOrden:", orden_id)

    except mysql.connector.Error as e:
        conn.rollback()
        print("Error creando orden:", e)

    finally:
        cur.close()


#hago la funcion para mostrar las ordenes de un cliente en especifico
def mostrar_ordenes_por_cliente(conn):
    ver_clientes(conn)
    cid = input("ID cliente para ver sus órdenes: ").strip()
    try:
        cid = int(cid)
    except:
        print("ID inválido.")
        return
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.idOrden, o.fecha, o.cantProductos, p.idProductos, p.nombre AS producto_nombre, p.categoria, p.precio
        FROM ordenes o
        INNER JOIN productos p ON o.producto_id = p.idProductos
        WHERE o.cliente_id = %s
        ORDER BY o.fecha DESC
    """, (cid,))
    rows = cur.fetchall()
    if not rows:
        print("No hay órdenes para ese cliente.")
    else:
        for r in rows:
            total = r['cantProductos'] * float(r['precio'])
            print(f"Orden {r['idOrden']} | Fecha: {r['fecha']} | Producto: {r['producto_nombre']} ({r['categoria']}) | Cant: {r['cantProductos']} | Precio unit: ${r['precio']} | Total: ${total:.2f}")
    cur.close()


# ----------- BUSQUEDAS AVANZADAS Y REPORTES ------------

# busco los productos mas vendidos (top 10)
def buscar_productos_vendidos(conn, top_n=10):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.idProductos, p.nombre, p.categoria, SUM(o.cantProductos) AS total_vendido
        FROM productos p
        LEFT JOIN ordenes o ON p.idProductos = o.producto_id
        GROUP BY p.idProductos
        ORDER BY total_vendido DESC
        LIMIT %s
    """, (top_n,))
    rows = cur.fetchall()
    if not rows:
        print("No hay datos de ventas.")
    else:
        for r in rows:
            print(f"{r['idProductos']}: {r['nombre']} | {r['categoria']} | Vendido total: {r['total_vendido'] or 0}")
    cur.close()

def reporte_producto_mas_vendido(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.idProductos, p.nombre, SUM(o.cantProductos) AS total_vendido
        FROM productos p
        JOIN ordenes o ON p.idProductos = o.producto_id
        GROUP BY p.idProductos
        ORDER BY total_vendido DESC
        LIMIT 1
    """)
    r = cur.fetchone()
    if not r:
        print("No hay ventas registradas.")
    else:
        print(f"Producto más vendido: {r['idProductos']} | {r['nombre']} | Cantidad total pedida: {r['total_vendido']}")
    cur.close()


# hago la funcion para ajustar ordenes de un producto a una cantidad maxima
def ajustar_ordenes_producto_maximo(conn):
    print("=== Ajustar órdenes de un producto a cantidad máxima ===")
    ver_productos(conn)
    pid = input("ID producto a ajustar órdenes: ").strip()
    maximo = input("Cantidad máxima por orden (int): ").strip()

    # Valido las entradas
    try:
        pid = int(pid)
        maximo = int(maximo)
        if maximo <= 0:
            print("La cantidad máxima debe ser mayor que 0.")
            return
    except ValueError:
        print("Valores inválidos.")
        return

    cur = conn.cursor(dictionary=True)
    try:
        # Verifico que el producto existe
        cur.execute("SELECT idProductos FROM productos WHERE idProductos=%s", (pid,))
        if cur.fetchone() is None:
            print("Producto no encontrado.")
            return

        # Selecciono las ordenes que exedene el limite para bloquearlas
        cur.execute("""
            SELECT idOrden, cantProductos
            FROM ordenes
            WHERE producto_id = %s AND cantProductos > %s
            FOR UPDATE
        """, (pid, maximo))
        rows = cur.fetchall()
        if not rows:
            print("No hay órdenes que excedan ese máximo.")
            return

        total_devuelto = 0
        for r in rows:
            delta = r['cantProductos'] - maximo
            total_devuelto += delta
            # actualizo la orden a la cantidad maxima
            cur.execute("UPDATE ordenes SET cantProductos = %s WHERE idOrden = %s", (maximo, r['idOrden']))

        # aumento el stock del producto por el total devuelto
        cur.execute("UPDATE productos SET stock = stock + %s WHERE idProductos = %s", (total_devuelto, pid))
        conn.commit()
        print(f"Ajustadas {len(rows)} órdenes. Stock incrementado en {total_devuelto}.")

    except mysql.connector.Error as e:
        conn.rollback()
        print("Error ajustando órdenes:", e)

    finally:
        cur.close()


# ------------ BUSQUEDA CON FILTROS -------------


#hago la funcion para buscar productos con filtros
def busqueda_productos_filtro(conn):
    print("Filtros posibles (dejar vacío para omitir):")
    nombre = input("Nombre contiene: ").strip()
    categoria = input("Categoría: ").strip()
    min_price = input("Precio mínimo: ").strip()
    max_price = input("Precio máximo: ").strip()
    sql = "SELECT idProductos, nombre, categoria, precio, stock FROM productos WHERE 1=1"
    params = []
    if nombre:
        sql += " AND nombre LIKE %s"; params.append(f"%{nombre}%")
    if categoria:
        sql += " AND categoria = %s"; params.append(categoria)
    if min_price:
        try:
            float(min_price); sql += " AND precio >= %s"; params.append(min_price)
        except: print("min_price inválido, ignorado")
    if max_price:
        try:
            float(max_price); sql += " AND precio <= %s"; params.append(max_price)
        except: print("max_price inválido, ignorado")
    sql += " ORDER BY nombre"
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    if not rows:
        print("No se encontraron productos con esos filtros.")
    else:
        for r in rows:
            print(f"{r['idProductos']}: {r['nombre']} | {r['categoria']} | ${r['precio']} | stock: {r['stock']}")
    cur.close()


# MENU PRINCIPAL

#hago la funcion para mostrar el menu principal
def menu():
    print("""
    ==== Sistema de Gestión de Ventas  ====
    1) Agregar producto
    2) Ver productos
    3) Actualizar producto
    4) Eliminar producto
    5) Agregar cliente
    6) Ver clientes
    7) Actualizar cliente
    8) Crear orden
    9) Mostrar órdenes por cliente
    10) Buscar productos (filtros)
    11) Productos más vendidos (top 10)
    12) Reporte: producto más vendido
    13) Ajustar órdenes de un producto a una cantidad máxima
    14) Eliminar cliente
    0) Salir
    """)

#hago el main para ejecutar el programa
def main():
    try:
        conn = get_connection()
    except Exception as e:
        print("No se pudo conectar a la base de datos:", e)
        sys.exit(1)
    init_db(conn)
    actions = {
        "1": agregar_producto,
        "2": ver_productos,
        "3": actualizar_producto,
        "4": eliminar_producto,
        "5": agregar_cliente,
        "6": ver_clientes,
        "7": actualizar_cliente,
        "8": crear_orden,
        "9": mostrar_ordenes_por_cliente,
        "10": busqueda_productos_filtro,
        "11": buscar_productos_vendidos,
        "12": reporte_producto_mas_vendido,
        "13": ajustar_ordenes_producto_maximo,
        "14": eliminar_cliente 
    }

    while True:
        menu()
        opc = input("Opción: ").strip()
        if opc == "0":
            print("Saliendo...")
            conn.close()
            break
        func = actions.get(opc)
        if func:
            try:
                func(conn)
            except Exception as e:
                print("Error en operación:", e)
        else:
            print("Opción inválida.")



if __name__ == "__main__":
    main()
