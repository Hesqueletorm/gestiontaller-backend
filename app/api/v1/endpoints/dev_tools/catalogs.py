"""
Catálogos de datos de prueba para DevTools
"""
import random
import string

# --- Catálogos de datos ---

VERSIONES_POR_MARCA = {
    "FORD": ["Ranger", "Maverick", "Kuga", "Ka", "Mustang", "Territory", "Everest", "F-150", "Falcon", "Fiesta", "Focus", "EcoSport", "Mondeo"],
    "CHEVROLET": ["Onix", "Onix Plus", "Spin", "Tracker", "Trailblazer", "Equinox", "Montana", "S10", "Silverado", "Cruze", "Prisma"],
    "VOLKSWAGEN": ["Gol", "Gol Trend", "Suran", "Fox", "Voyage", "Vento", "Golf", "Polo", "Virtus", "Nivus", "T-Cross", "Taos", "Tiguan", "Amarok"],
    "RENAULT": ["Clio", "Sandero", "Stepway", "Logan", "Kangoo", "Duster", "Oroch", "Captur", "Alaskan", "Kwid"],
    "FIAT": ["Palio", "Siena", "Cronos", "Argo", "Mobi", "Toro", "Strada", "Fiorino", "Uno", "Punto"],
    "PEUGEOT": ["206", "207", "208", "308", "408", "2008", "3008", "Partner", "Boxer"],
    "CITROEN": ["C3", "C4", "C4 Cactus", "Berlingo", "Jumper"],
    "TOYOTA": ["Hilux", "Corolla", "Etios", "Yaris", "Corolla Cross", "SW4", "RAV4"],
    "NISSAN": ["Frontier", "Sentra", "Versa", "Kicks", "March"],
    "JEEP": ["Renegade", "Compass", "Wrangler", "Cherokee", "Gladiator"],
    "HONDA": ["Civic", "Fit", "HR-V", "CR-V", "Accord", "City"],
    "MERCEDES-BENZ": ["Clase A", "Clase C", "Clase E", "GLA", "GLB", "GLC", "GLE", "Sprinter"],
}

NOMBRES_STOCK = [
    "Aceite Motor 10W-40", "Aceite Motor 5W-30", "Aceite Caja ATF", "Grasa Multiuso",
    "Filtro de Aceite", "Filtro de Aire", "Filtro de Combustible", "Filtro de Cabina",
    "Líquido de Frenos DOT4", "Refrigerante Long Life", "Aditivo Limpiainyectores",
    "Limpiaparabrisas", "Silicona Protectora", "Shampoo para Auto", "Cera Líquida",
    "Bujía Iridium", "Correa de Accesorios", "Lámpara H7 55W", "Líquido Dirección Hidráulica"
]

CATEGORIAS_STOCK = ["Aceites", "Filtros", "Aditivos", "Limpieza", "Electricidad", "Repuestos"]

ARTICULOS_FACTURA = [
    "Cambio de Aceite", "Filtro de Aceite", "Filtro de Aire", "Líquido de Frenos",
    "Refrigerante", "Aditivo Limpiainyectores", "Lavado Premium", "Pulido y Encerado",
    "Revisión General", "Alineación y Balanceo"
]

SERVICIOS_POR_CATEGORIA = {
    "Lubricación": [
        "Cambio de Aceite Motor",
        "Cambio de Aceite de Caja",
        "Cambio de Aceite de Diferencial",
        "Engrase General"
    ],
    "Filtros": [
        "Cambio de Filtro de Aceite",
        "Cambio de Filtro de Aire",
        "Cambio de Filtro de Combustible",
        "Cambio de Filtro de Cabina"
    ],
    "Frenos": [
        "Cambio de Pastillas Delanteras",
        "Cambio de Pastillas Traseras",
        "Cambio de Líquido de Frenos",
        "Rectificación de Discos"
    ],
    "Refrigeración": [
        "Cambio de Refrigerante",
        "Limpieza de Radiador",
        "Cambio de Termostato"
    ],
    "Electricidad": [
        "Cambio de Batería",
        "Revisión de Alternador",
        "Cambio de Bujías"
    ],
    "Estética": [
        "Lavado Completo",
        "Pulido y Encerado",
        "Tratamiento de Tapizados"
    ]
}

PROVEEDORES = [
    {"nombre": "Distribuidora Automotriz SA", "cuit": "30-12345678-9"},
    {"nombre": "Lubricantes del Sur SRL", "cuit": "33-98765432-1"},
    {"nombre": "Repuestos Norte", "cuit": "20-55544433-2"},
    {"nombre": "Aceites Premium Argentina", "cuit": "30-11223344-5"},
    {"nombre": "Filtros y Más", "cuit": "27-99887766-4"},
    {"nombre": "Todo Auto Mayorista", "cuit": "33-44556677-8"},
    {"nombre": "Importadora JM", "cuit": "30-77889900-1"},
    {"nombre": "Distribuidora Central", "cuit": "20-33221100-3"},
]


# --- Generadores de datos aleatorios ---

def generar_nombre_completo():
    nombres = ["Juan", "Ana", "Carlos", "Lucía", "Pedro", "Sofía", "Martín", "Valentina", "Diego", "Camila", "Mateo", "Julieta", "Lucas", "Mía", "Tomás", "Emma", "Facundo", "Abril", "Joaquín", "Lola"]
    apellidos = ["Gómez", "Pérez", "Rodríguez", "López", "Fernández", "García", "Martínez", "Sánchez", "Romero", "Díaz", "Alvarez", "Torres", "Ruiz", "Ramírez", "Flores", "Acosta", "Benítez", "Molina", "Castro", "Ortiz"]
    return f"{random.choice(nombres)} {random.choice(apellidos)}"


def generar_dni():
    return str(random.randint(20000000, 49999999))


def generar_cuit(dni):
    prefijos = ["20", "27", "23", "24"]
    return f"{random.choice(prefijos)}-{dni}-{random.randint(0,9)}"


def generar_email(nombre_completo):
    parts = nombre_completo.lower().split()
    dominios = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]
    return f"{parts[0]}.{parts[1]}{random.randint(1,999)}@{random.choice(dominios)}"


def generar_telefono():
    prefijos = ["11", "221", "351", "261", "299", "341", "381", "387"]
    pref = random.choice(prefijos)
    restantes = 8 - len(pref)
    numero = pref + ''.join(random.choice(string.digits) for _ in range(restantes))
    return numero


def generar_direccion():
    calles = ["San Martín", "Belgrano", "Rivadavia", "Mitre", "Sarmiento", "Moreno", "Alberdi", "Urquiza", "9 de Julio", "Independencia"]
    return f"{random.choice(calles)} {random.randint(1, 9999)}"


def generar_patente():
    # Formato nuevo: AA 123 BB
    letras1 = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
    numeros = ''.join(random.choice(string.digits) for _ in range(3))
    letras2 = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
    return f"{letras1}{numeros}{letras2}"


def generar_vehiculo():
    """Genera datos de vehículo con campos separados"""
    marca = random.choice(list(VERSIONES_POR_MARCA.keys()))
    versiones = VERSIONES_POR_MARCA.get(marca, [f"{marca} Base"])
    version = random.choice(versiones)
    modelo = str(random.randint(2005, 2025))
    patente = generar_patente()
    kilometraje = random.randint(0, 250000)
    
    return {
        "marca": marca,
        "version": version,
        "modelo": modelo,
        "patente": patente,
        "kilometraje": kilometraje,
        "descripcion": f"{marca} {version} {modelo}"
    }


def generar_vehiculo_descripcion():
    """Función legacy para compatibilidad - genera solo descripción"""
    vehiculo = generar_vehiculo()
    return vehiculo["descripcion"]
