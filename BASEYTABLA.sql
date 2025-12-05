DROP DATABASE IF EXISTS gestion_de_Ventas;
CREATE DATABASE gestion_de_Ventas;
USE gestion_de_Ventas;

CREATE TABLE productos (
    idProductos INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR (100) NOT NULL,
    categoria VARCHAR (50) NOT NULL,
    precio DECIMAL (10,2) NOT NULL CHECK (precio >=0),
    stock INT NOT NULL CHECK (stock >=0)
); 

CREATE TABLE clientes (
    idClientes INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR (100) NOT NULL,
    email VARCHAR (100) NOT NULL UNIQUE,
    telefono VARCHAR (20) NOT NULL,
    direccion VARCHAR (150) NOT NULL
    
);

CREATE TABLE ordenes (
    idOrden INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantProductos INT NOT NULL CHECK (cantProductos >=1),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(idClientes) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(idProductos) ON DELETE CASCADE

);
