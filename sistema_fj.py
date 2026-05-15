import logging
from abc import ABC, abstractmethod
from datetime import datetime
import re
import traceback

# Configuración de logging
logging.basicConfig(
    filename='sistema_fj.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Excepciones personalizadas
class ErrorSistema(Exception):
    """Clase base para excepciones del sistema."""
    def __init__(self, mensaje, causa=None):
        self.mensaje = mensaje
        self.causa = causa
        super().__init__(self.mensaje)
        logging.error(f"{mensaje} | Causa: {causa}")

class ClienteInvalidoError(ErrorSistema):
    pass

class ServicioInvalidoError(ErrorSistema):
    pass

class ReservaError(ErrorSistema):
    pass

# Clase abstracta general para entidades
class Entidad(ABC):
    """Clase abstracta que representa entidades generales del sistema."""
    @abstractmethod
    def obtener_info(self):
        """Método abstracto para obtener información de la entidad."""
        pass

# Clase Cliente con encapsulación y validaciones robustas
class Cliente(Entidad):
    def __init__(self, id_cliente: str, nombre: str, email: str, telefono: str):
        self._id_cliente = id_cliente
        self._validar_datos(nombre, email, telefono)
        self._nombre = nombre
        self._email = email
        self._telefono = telefono
        logging.info(f"Cliente registrado: {id_cliente} - {nombre}")

    def _validar_datos(self, nombre, email, telefono):
        if not nombre or len(nombre.strip()) < 3:
            raise ClienteInvalidoError("El nombre debe tener al menos 3 caracteres.", "Nombre inválido")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ClienteInvalidoError("Email con formato inválido.", email)
        if not telefono.isdigit() or len(telefono) < 7:
            raise ClienteInvalidoError("Teléfono debe ser numérico y tener al menos 7 dígitos.", telefono)

    # Properties para encapsulación
    @property
    def nombre(self):
        return self._nombre

    @property
    def email(self):
        return self._email

    def obtener_info(self):
        return f"Cliente {self._id_cliente}: {self.nombre} ({self.email})"

    def __str__(self):
        return self.obtener_info()

# Clase abstracta Servicio
class Servicio(ABC):
    def __init__(self, id_servicio: str, nombre: str, precio_base: float):
        self.id_servicio = id_servicio
        self.nombre = nombre
        if precio_base <= 0:
            raise ServicioInvalidoError("Precio base debe ser positivo.")
        self.precio_base = precio_base

    @abstractmethod
    def calcular_costo(self, duracion: float = 1.0, **kwargs):
        """Método polimórfico y sobrecargado vía **kwargs (impuestos, descuentos, etc.)."""
        pass

    @abstractmethod
    def describir(self):
        pass

# Servicios especializados (herencia + polimorfismo)
class ReservaDeSala(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, capacidad: int):
        super().__init__(id_servicio, nombre, precio_base)
        self.capacidad = capacidad

    def calcular_costo(self, duracion: float = 1.0, **kwargs):
        costo = self.precio_base * duracion
        impuesto = kwargs.get('impuesto', 0.19)
        descuento = kwargs.get('descuento', 0.0)
        costo *= (1 + impuesto)
        costo *= (1 - descuento)
        return round(costo, 2)

    def describir(self):
        return f"Reserva de Sala '{self.nombre}' - Capacidad: {self.capacidad} personas. Precio base/hora: ${self.precio_base}"

class AlquilerDeEquipo(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, tipo_equipo: str):
        super().__init__(id_servicio, nombre, precio_base)
        self.tipo_equipo = tipo_equipo

    def calcular_costo(self, duracion: float = 1.0, **kwargs):
        costo = self.precio_base * duracion
        if kwargs.get('seguro', False):
            costo *= 1.1
        impuesto = kwargs.get('impuesto', 0.19)
        costo *= (1 + impuesto)
        return round(costo, 2)

    def describir(self):
        return f"Alquiler de Equipo '{self.nombre}' ({self.tipo_equipo}). Precio base/hora: ${self.precio_base}"

class AsesoriaEspecializada(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, especialidad: str):
        super().__init__(id_servicio, nombre, precio_base)
        self.especialidad = especialidad

    def calcular_costo(self, duracion: float = 1.0, **kwargs):
        costo = self.precio_base * duracion
        if kwargs.get('urgente', False):
            costo *= 1.5
        descuento = kwargs.get('descuento', 0.0)
        costo *= (1 - descuento)
        return round(costo, 2)

    def describir(self):
        return f"Asesoría Especializada en '{self.especialidad}': {self.nombre}. Precio base/hora: ${self.precio_base}"

# Clase Reserva
class Reserva:
    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio, duracion: float):
        self.id_reserva = id_reserva
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "pendiente"
        self.fecha = datetime.now()
        self._validar_reserva()

    def _validar_reserva(self):
        if not isinstance(self.cliente, Cliente) or not isinstance(self.servicio, Servicio):
            raise ReservaError("Cliente o servicio inválido.")
        if self.duracion <= 0:
            raise ReservaError("Duración debe ser positiva.")

    def confirmar(self):
        try:
            if self.estado != "pendiente":
                raise ReservaError("La reserva ya fue procesada.")
            self.servicio.calcular_costo(self.duracion)  # validación extra
            self.estado = "confirmada"
            logging.info(f"Reserva {self.id_reserva} confirmada para {self.cliente.nombre}")
            print(f"✅ Reserva {self.id_reserva} confirmada exitosamente.")
        except Exception as e:
            raise ReservaError(f"Error al confirmar reserva {self.id_reserva}", str(e)) from e
        finally:
            logging.info(f"Operación de confirmación finalizada para reserva {self.id_reserva}")

    def cancelar(self):
        try:
            self.estado = "cancelada"
            logging.info(f"Reserva {self.id_reserva} cancelada.")
            print(f"❌ Reserva {self.id_reserva} cancelada.")
        except Exception as e:
            logging.error(f"Error al cancelar: {e}")

    def procesar(self):
        try:
            costo = self.servicio.calcular_costo(self.duracion)
            print(f"Procesando pago de ${costo} para reserva {self.id_reserva}")
        except ValueError as ve:
            logging.error(f"Error de procesamiento: {ve}")
            raise ReservaError("Error en procesamiento") from ve
        else:
            self.estado = "procesada"
            print("✅ Procesamiento exitoso.")
        finally:
            print("Limpieza de recursos completada.")

    def __str__(self):
        return f"Reserva {self.id_reserva} - {self.cliente.nombre} - {self.servicio.nombre} ({self.duracion}h) - Estado: {self.estado}"

# Sistema principal
class SistemaFJ:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []
        self.contador_id = 1000

    def _generar_id(self):
        self.contador_id += 1
        return str(self.contador_id)

    def registrar_cliente(self, nombre, email, telefono):
        try:
            cliente = Cliente(self._generar_id(), nombre, email, telefono)
            self.clientes.append(cliente)
            print(f"Cliente registrado: {cliente}")
            return cliente
        except ClienteInvalidoError as e:
            logging.error(f"Error registro cliente: {e.mensaje}")
            print(f"❌ Error: {e.mensaje}")
            return None

    def registrar_servicio(self, tipo, **kwargs):
        try:
            if tipo == "sala":
                serv = ReservaDeSala(self._generar_id(), kwargs['nombre'], kwargs['precio'], kwargs.get('capacidad', 10))
            elif tipo == "equipo":
                serv = AlquilerDeEquipo(self._generar_id(), kwargs['nombre'], kwargs['precio'], kwargs.get('tipo', ''))
            elif tipo == "asesoria":
                serv = AsesoriaEspecializada(self._generar_id(), kwargs['nombre'], kwargs['precio'], kwargs.get('especialidad', ''))
            else:
                raise ServicioInvalidoError("Tipo de servicio desconocido.")
            self.servicios.append(serv)
            print(f"Servicio registrado: {serv.describir()}")
            return serv
        except Exception as e:
            logging.error(f"Error al registrar servicio: {e}")
            print(f"❌ Error servicio: {e}")
            return None

    def crear_reserva(self, cliente, servicio, duracion):
        try:
            reserva = Reserva(self._generar_id(), cliente, servicio, duracion)
            self.reservas.append(reserva)
            print(f"Reserva creada: {reserva}")
            return reserva
        except Exception as e:
            logging.error(f"Error creando reserva: {e}")
            print(f"❌ Error reserva: {e}")
            return None

    def simular_operaciones(self):
        """Simula al menos 10 operaciones completas (válidas e inválidas)."""
        print("\n=== INICIANDO SIMULACIÓN DE 10+ OPERACIONES ===\n")

        # 1. Cliente válido
        c1 = self.registrar_cliente("Julian Esmik Cumbe", "julian@ejemplo.com", "3123456789")
        # 2. Cliente inválido
        self.registrar_cliente("Ana", "ana-invalido", "123")

        # 3-5. Servicios
        s1 = self.registrar_servicio("sala", nombre="Sala de Conferencias A", precio=50000, capacidad=20)
        s2 = self.registrar_servicio("equipo", nombre="Laptop Pro", precio=30000, tipo="Computador")
        s3 = self.registrar_servicio("asesoria", nombre="Consultoría Python OOP", precio=120000, especialidad="Programación")

        # 6. Reserva exitosa
        if c1 and s1:
            r1 = self.crear_reserva(c1, s1, 4.0)
            if r1: r1.confirmar()

        # 7. Reserva inválida (duración negativa)
        if c1 and s1:
            try:
                Reserva("ERR001", c1, s1, -2)
            except ReservaError as e:
                print(f"✅ Error capturado correctamente: {e}")

        # 8. Otra reserva + cancelación
        if c1 and s2:
            r2 = self.crear_reserva(c1, s2, 2.0)
            if r2: r2.cancelar()

        # 9. Procesamiento con polimorfismo y parámetros extras
        if c1 and s3:
            r3 = self.crear_reserva(c1, s3, 3.0)
            if r3:
                r3.procesar()
                costo = s3.calcular_costo(3.0, urgente=True, descuento=0.1)
                print(f"Costo calculado con parámetros extras: ${costo}")

        # 10+. Más operaciones
        c2 = self.registrar_cliente("Yulieth Calderon", "yuli@ejemplo.com", "3159876543")
        s4 = self.registrar_servicio("sala", nombre="Sala B", precio=45000, capacidad=15)
        if c2 and s4:
            r4 = self.crear_reserva(c2, s4, 5.0)
            if r4: r4.confirmar()

        print("\n=== RESUMEN DEL SISTEMA ===")
        print(f"Clientes: {len(self.clientes)} | Servicios: {len(self.servicios)} | Reservas: {len(self.reservas)}")
        print("=== Sistema continúa funcionando a pesar de errores ===")
        print("Revisa el archivo **sistema_fj.log** para ver todos los eventos y errores.")

if __name__ == "__main__":
    sistema = SistemaFJ()
    sistema.simular_operaciones()
