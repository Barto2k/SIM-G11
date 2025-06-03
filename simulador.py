import random
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.align import Align
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

@dataclass
class Estudiante:
    """Objeto Estudiante con sus atributos"""
    id: int
    hora_llegada: float
    estado: str  # 'UT' (usando terminal), 'ET' (esperando en cola), 'R' (retirado)
    hora_regreso: Optional[float] = None
    terminal_asignada: Optional[int] = None
    hora_inicio_servicio: Optional[float] = None

@dataclass
class Terminal:
    """Objeto Terminal con sus atributos"""
    id: int
    estado: str  # 'L' (libre), 'O' (ocupada)
    estudiante_id: Optional[int] = None
    fin_servicio: Optional[float] = None

@dataclass
class Tecnico:
    """Objeto Técnico con sus atributos"""
    estado: str  # 'D' (disponible), 'R' (revisando)
    terminal_revisando: Optional[int] = None
    fin_revision: Optional[float] = None
    proxima_ronda: Optional[float] = None

@dataclass
class Evento:
    """Evento en la simulación"""
    tiempo: float
    tipo: str
    datos: Dict

class SimuladorCertificados:
    def __init__(self, servicio_min=5, servicio_max=8, revision_min=3, revision_max=10,
                 ronda_min=57, ronda_max=63, media_llegada=2):
        # Estados de los objetos
        self.terminales = [Terminal(i+1, 'L') for i in range(4)]
        self.tecnico = Tecnico('D')
        self.estudiantes = {}
        self.cola_estudiantes = []
        
        # Variables de control
        self.reloj = 0.0
        self.siguiente_estudiante_id = 1
        self.eventos_futuros = []
        
        # Variables auxiliares (acumuladores)
        self.estudiantes_atendidos = 0
        self.estudiantes_retirados = 0
        self.acum_tiempo_espera = 0.0
        
        # Para el vector de estados
        self.vector_estados = []
        
        # Variables aleatorias usadas
        self.rnd_usados = {}

        # Parámetros del modelo (fijos y configurables)
        self.servicio_min = servicio_min
        self.servicio_max = servicio_max
        self.revision_min = revision_min
        self.revision_max = revision_max
        self.ronda_min = ronda_min
        self.ronda_max = ronda_max
        self.media_llegada = media_llegada
        self.max_cola = 5           # Fijo: máximo en cola
        self.tiempo_regreso = 30    # Fijo: tiempo de regreso

        self.indice_terminal_ronda = 0  # Para saber cuál es la próxima terminal a revisar en la ronda

        # Nueva lista para llevar el control de las terminales pendientes de revisión
        self.terminales_pendientes_revision = []

    def generar_tiempo_llegada_estudiante(self) -> Tuple[float, float]:
        rnd = random.random()
        tiempo = -self.media_llegada * math.log(1 - rnd)
        self.rnd_usados['llegada_estudiante'] = rnd
        return tiempo, rnd

    def generar_tiempo_servicio(self, terminal) -> Tuple[float, float]:
        rnd = random.random()
        tiempo = self.servicio_min + (self.servicio_max - self.servicio_min) * rnd
        self.rnd_usados[f'servicio_{terminal.id}'] = rnd
        return tiempo, rnd

    def generar_tiempo_revision(self, terminal) -> Tuple[float, float]:
        rnd = random.random()
        tiempo = self.revision_min + (self.revision_max - self.revision_min) * rnd
        self.rnd_usados[f'revision_{terminal.id}'] = rnd
        return tiempo, rnd

    def generar_tiempo_entre_rondas(self) -> Tuple[float, float]:
        rnd = random.random()
        tiempo = self.ronda_min + (self.ronda_max - self.ronda_min) * rnd
        self.rnd_usados['ronda'] = rnd
        return tiempo, rnd

    def agregar_evento(self, tiempo: float, tipo: str, datos: Dict = None):
        """Agrega un evento futuro"""
        if datos is None:
            datos = {}
        evento = Evento(tiempo, tipo, datos)
        self.eventos_futuros.append(evento)
        self.eventos_futuros.sort(key=lambda x: x.tiempo)

    def obtener_proximo_evento(self) -> Optional[Evento]:
        """Obtiene y remueve el próximo evento"""
        if self.eventos_futuros:
            return self.eventos_futuros.pop(0)
        return None

    def obtener_terminal_libre(self) -> Optional[Terminal]:
        """Obtiene la primera terminal libre"""
        for terminal in self.terminales:
            if terminal.estado == 'L':
                return terminal
        return None

    def contar_personas_esperando(self) -> int:
        """Cuenta cuántas personas están esperando en cola"""
        return len(self.cola_estudiantes)

    def procesar_llegada_estudiante(self):
        """Procesa la llegada de un estudiante"""
        estudiante = Estudiante(
            id=self.siguiente_estudiante_id,
            hora_llegada=self.reloj,
            estado='ET'
        )
        self.siguiente_estudiante_id += 1

        # CORREGIDO: Si hay 5 o más en cola, se retira
        if self.contar_personas_esperando() >= self.max_cola:
            estudiante.estado = 'R'
            estudiante.hora_regreso = self.reloj + self.tiempo_regreso
            self.estudiantes_retirados += 1
            self.agregar_evento(estudiante.hora_regreso, 'regreso_estudiante', {'estudiante_id': estudiante.id})
        else:
            self.cola_estudiantes.append(estudiante.id)
            terminal_libre = self.obtener_terminal_libre()
            if terminal_libre and (self.tecnico.estado != 'R' or self.tecnico.terminal_revisando != terminal_libre.id):
                self.asignar_estudiante_terminal(estudiante, terminal_libre)

        self.estudiantes[estudiante.id] = estudiante
        tiempo_llegada, rnd = self.generar_tiempo_llegada_estudiante()
        self.agregar_evento(self.reloj + tiempo_llegada, 'llegada_estudiante')

    def asignar_estudiante_terminal(self, estudiante: Estudiante, terminal: Terminal):
        """Asigna un estudiante a una terminal"""
        # No asignar si la terminal está en revisión
        if terminal.estado == 'ER':
            return
        
        # Remover estudiante de la cola si está ahí
        if estudiante.id in self.cola_estudiantes:
            self.cola_estudiantes.remove(estudiante.id)
        
        # Actualizar estados
        estudiante.estado = 'UT'
        estudiante.terminal_asignada = terminal.id
        estudiante.hora_inicio_servicio = self.reloj
        
        terminal.estado = 'O'
        terminal.estudiante_id = estudiante.id
        
        # Programar fin de servicio
        tiempo_servicio, rnd = self.generar_tiempo_servicio(terminal)
        terminal.fin_servicio = self.reloj + tiempo_servicio
        self.agregar_evento(terminal.fin_servicio, 'fin_servicio', 
                          {'terminal_id': terminal.id})

    def procesar_fin_servicio(self, terminal_id: int):
        """Procesa el fin de servicio de una terminal"""
        terminal = self.terminales[terminal_id - 1]
        estudiante = self.estudiantes[terminal.estudiante_id]
        
        # Calcular tiempo de espera
        tiempo_espera = estudiante.hora_inicio_servicio - estudiante.hora_llegada
        self.acum_tiempo_espera += tiempo_espera
        self.estudiantes_atendidos += 1
        
        # Liberar terminal
        terminal.estado = 'L'
        terminal.estudiante_id = None
        terminal.fin_servicio = None
        
        # Remover estudiante del sistema
        del self.estudiantes[estudiante.id]
        
        # Asignar siguiente estudiante SOLO a la terminal recién liberada
        if self.cola_estudiantes:
            if terminal.estado == 'L' and (self.tecnico.estado != 'R' or self.tecnico.terminal_revisando != terminal.id):
                siguiente_id = self.cola_estudiantes[0]
                siguiente_estudiante = self.estudiantes[siguiente_id]
                self.asignar_estudiante_terminal(siguiente_estudiante, terminal)
        # Si el técnico está disponible y la terminal recién liberada está pendiente de revisión, iniciar revisión
        if (self.tecnico.estado == 'D' and
            hasattr(self, 'terminales_pendientes_revision') and
            terminal.id in self.terminales_pendientes_revision):
            self.iniciar_revision_proxima_terminal()

    def procesar_inicio_ronda_tecnico(self):
        """Procesa el inicio de una ronda del técnico"""
        if self.tecnico.estado == 'D':
            # Al iniciar la ronda, marca todas las terminales como pendientes de revisión
            self.terminales_pendientes_revision = [t.id for t in self.terminales]
            self.iniciar_revision_proxima_terminal()

    def iniciar_revision_proxima_terminal(self):
        """Inicia la revisión de la próxima terminal pendiente (espera a que se libere si está ocupada)"""
        # Si no quedan terminales pendientes, termina la ronda
        if not self.terminales_pendientes_revision:
            self.tecnico.estado = 'D'
            self.tecnico.terminal_revisando = None
            self.tecnico.fin_revision = None
            # Programar próxima ronda
            tiempo_ronda, rnd = self.generar_tiempo_entre_rondas()
            self.tecnico.proxima_ronda = self.reloj + tiempo_ronda
            self.agregar_evento(self.tecnico.proxima_ronda, 'inicio_ronda')
            return

        # Busca la próxima terminal pendiente que esté libre
        for terminal_id in self.terminales_pendientes_revision:
            terminal = self.terminales[terminal_id - 1]
            if terminal.estado == 'L':
                self.tecnico.estado = 'R'
                self.tecnico.terminal_revisando = terminal.id
                terminal.estado = 'ER'
                tiempo_revision, rnd = self.generar_tiempo_revision(terminal)
                self.tecnico.fin_revision = self.reloj + tiempo_revision
                # Guarda demora y fin de revisión para el vector de estados
                if not hasattr(self, 'demora_revision'):
                    self.demora_revision = [None]*4
                    self.fin_revision = [None]*4
                self.demora_revision[terminal.id-1] = tiempo_revision
                self.fin_revision[terminal.id-1] = self.tecnico.fin_revision
                self.agregar_evento(self.tecnico.fin_revision, 'fin_revision')
                return
        # Si ninguna terminal pendiente está libre, el técnico espera (no hace nada hasta que alguna se libere)

    def procesar_fin_revision(self):
        """Procesa el fin de revisión del técnico"""
        # Marca la terminal como revisada y pasa a la siguiente
        if self.tecnico.terminal_revisando:
            terminal = self.terminales[self.tecnico.terminal_revisando - 1]
            terminal.estado = 'L'  # Libera la terminal revisada
            # Quita la terminal de las pendientes de revisión
            if hasattr(self, 'terminales_pendientes_revision') and terminal.id in self.terminales_pendientes_revision:
                self.terminales_pendientes_revision.remove(terminal.id)
        self.tecnico.estado = 'D'
        self.tecnico.terminal_revisando = None
        self.tecnico.fin_revision = None
        self.iniciar_revision_proxima_terminal()

    def guardar_estado_actual(self, evento: Evento):
        """Guarda el estado actual en el vector de estados"""
        # Obtener próximos eventos
        proximos_eventos = []
        for evento_fut in self.eventos_futuros[:3]:  # Mostrar los próximos 3
            proximos_eventos.append(f"{evento_fut.tipo}@{evento_fut.tiempo:.2f}")
        
        # Estado de terminales
        estados_terminales = []
        for idx, terminal in enumerate(self.terminales):
            estados_terminales.append({
                'estado': terminal.estado,
                'fin_servicio': terminal.fin_servicio or '',
                'estudiante_id': terminal.estudiante_id or ''
            })
        
        # Estado del técnico
        estado_tecnico = {
            'estado': self.tecnico.estado,
            'proxima_ronda': self.tecnico.proxima_ronda or '',
            'fin_revision': self.tecnico.fin_revision or '',
            'terminal_revisando': self.tecnico.terminal_revisando or ''
        }
        
        # Métricas
        porcentaje_retiros = 0
        tiempo_promedio_espera = 0
        if self.estudiantes_atendidos + self.estudiantes_retirados > 0:
            porcentaje_retiros = (self.estudiantes_retirados / 
                                (self.estudiantes_atendidos + self.estudiantes_retirados)) * 100
        if self.estudiantes_atendidos > 0:
            tiempo_promedio_espera = self.acum_tiempo_espera / self.estudiantes_atendidos
        
        estado = {
            'reloj': self.reloj,
            'evento': evento.tipo,
            'proximos_eventos': '; '.join(proximos_eventos) if proximos_eventos else '',
            'tecnico': estado_tecnico,
            # Estado de terminales
            'terminales': [
                {
                    'estado': terminal.estado,
                    'fin_servicio': terminal.fin_servicio or '',
                    'estudiante_id': terminal.estudiante_id or ''
                }
                for terminal in self.terminales
            ],
            'cola_length': len(self.cola_estudiantes),
            'estudiantes_sistema': len(self.estudiantes),
            'estudiantes_atendidos': self.estudiantes_atendidos,
            'estudiantes_retirados': self.estudiantes_retirados,
            'porcentaje_retiros': porcentaje_retiros,
            'tiempo_promedio_espera': tiempo_promedio_espera,
            'rnd_usados': self.rnd_usados.copy(),
            'demora_revision': getattr(self, 'demora_revision', [None]*4),
            'fin_revision': getattr(self, 'fin_revision', [None]*4)
        }

        self.vector_estados.append(estado)
        self.rnd_usados.clear()

    def simular(self, tiempo_simulacion: float, max_iteraciones: int = 100000) -> Dict:
        """Ejecuta la simulación"""
        # Inicialización
        self.reloj = 0.0
        
        # Programar primera llegada de estudiante
        tiempo_llegada, rnd = self.generar_tiempo_llegada_estudiante()
        self.agregar_evento(tiempo_llegada, 'llegada_estudiante')
        
        # Programar primera ronda del técnico
        tiempo_ronda, rnd = self.generar_tiempo_entre_rondas()
        self.tecnico.proxima_ronda = tiempo_ronda
        self.agregar_evento(tiempo_ronda, 'inicio_ronda')
        
        # Guardar estado inicial
        evento_inicial = Evento(0, 'inicio', {})
        self.guardar_estado_actual(evento_inicial)
        
        iteraciones = 0
        
        while (iteraciones < max_iteraciones and 
               self.reloj < tiempo_simulacion and 
               self.eventos_futuros):
            
            # Obtener próximo evento
            evento = self.obtener_proximo_evento()
            if not evento:
                break
            
            # Avanzar reloj
            self.reloj = evento.tiempo
            
            # Procesar evento según tipo
            if evento.tipo == 'llegada_estudiante':
                self.procesar_llegada_estudiante()
            elif evento.tipo == 'fin_servicio':
                self.procesar_fin_servicio(evento.datos['terminal_id'])
            elif evento.tipo == 'inicio_ronda':
                self.procesar_inicio_ronda_tecnico()
            elif evento.tipo == 'fin_revision':
                self.procesar_fin_revision()
            elif evento.tipo == 'regreso_estudiante':
                estudiante_id = evento.datos['estudiante_id']
                if estudiante_id in self.estudiantes:
                    estudiante = self.estudiantes[estudiante_id]
                    estudiante.estado = 'ET'
                    estudiante.hora_llegada = self.reloj
                    if self.contar_personas_esperando() < self.max_cola:
                        self.cola_estudiantes.append(estudiante_id)
                        terminal_libre = self.obtener_terminal_libre()
                        if (terminal_libre and 
                            (self.tecnico.estado != 'R' or 
                             self.tecnico.terminal_revisando != terminal_libre.id)):
                            self.asignar_estudiante_terminal(estudiante, terminal_libre)

            # Guardar estado
            self.guardar_estado_actual(evento)
            iteraciones += 1
        
        # Calcular métricas finales
        total_llegadas = self.estudiantes_atendidos + self.estudiantes_retirados
        porcentaje_retiros = (self.estudiantes_retirados / total_llegadas * 100) if total_llegadas > 0 else 0
        tiempo_promedio_espera = (self.acum_tiempo_espera / self.estudiantes_atendidos) if self.estudiantes_atendidos > 0 else 0
        
        return {
            'vector_estados': self.vector_estados,
            'iteraciones_realizadas': iteraciones,
            'tiempo_final': self.reloj,
            'estudiantes_atendidos': self.estudiantes_atendidos,
            'estudiantes_retirados': self.estudiantes_retirados,
            'porcentaje_retiros': porcentaje_retiros,
            'tiempo_promedio_espera': tiempo_promedio_espera
        }

    def mostrar_vector_estados(self, desde_iteracion: int = 0, 
                             cantidad_iteraciones: int = None, 
                             mostrar_ultima: bool = False):
        """Muestra el vector de estados según los parámetros especificados"""
        if mostrar_ultima:
            # Mostrar solo la última fila
            if self.vector_estados:
                self.imprimir_estado(self.vector_estados[-1], len(self.vector_estados)-1)
        else:
            # Mostrar desde iteración j, i cantidad de iteraciones
            inicio = desde_iteracion
            fin = len(self.vector_estados)
            
            if cantidad_iteraciones:
                fin = min(inicio + cantidad_iteraciones, len(self.vector_estados))
            
            print(f"\n=== VECTOR DE ESTADOS (iteraciones {inicio} a {fin-1}) ===")
            for i in range(inicio, fin):
                if i < len(self.vector_estados):
                    self.imprimir_estado(self.vector_estados[i], i)

    def imprimir_estado(self, estado: Dict, iteracion: int):
        """Imprime un estado individual del vector"""
        print(f"\n--- Iteración {iteracion} ---")
        print(f"Reloj: {estado['reloj']:.2f}")
        print(f"Evento: {estado['evento']}")
        print(f"Próximos eventos: {estado['proximos_eventos']}")
        
        print(f"\nTécnico: Estado={estado['tecnico']['estado']}, "
              f"Próxima ronda={estado['tecnico']['proxima_ronda']}, "
              f"Fin revisión={estado['tecnico']['fin_revision']}")
        
        print(f"\nTerminales:")
        for i, terminal in enumerate(estado['terminales']):
            print(f"  Terminal {i+1}: Estado={terminal['estado']}, "
                  f"Fin servicio={terminal['fin_servicio']}")
        
        print(f"\nCola: {estado['cola_length']} estudiantes esperando")
        print(f"Estudiantes en sistema: {estado['estudiantes_sistema']}")
        print(f"Estudiantes atendidos: {estado['estudiantes_atendidos']}")
        print(f"Estudiantes retirados: {estado['estudiantes_retirados']}")
        print(f"% Retiros: {estado['porcentaje_retiros']:.2f}%")
        print(f"Tiempo promedio espera: {estado['tiempo_promedio_espera']:.2f} min")
        
        if estado['rnd_usados']:
            print(f"RND usados: {estado['rnd_usados']}")

class InterfazSimulador:
    """Interfaz de usuario usando Rich"""
    
    def __init__(self):
        self.console = Console()
        self.simulador = None
        
    def mostrar_titulo(self):
        """Muestra el título de la aplicación"""
        titulo = Text("SIMULADOR SISTEMA AUTOGESTIÓN CERTIFICADOS", style="bold blue")
        subtitulo = Text("Universidad Nacional del Centro", style="italic cyan")
        
        panel = Panel(
            Align.center(titulo + "\n" + subtitulo),
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def solicitar_parametros(self) -> Tuple[float, int, int]:
        """Solicita los parámetros de simulación al usuario"""
        self.console.print("[bold cyan]Configuración de la Simulación[/bold cyan]")
        
        tiempo_sim = FloatPrompt.ask(
            "Tiempo de simulación (minutos)",
            default=120.0,
            console=self.console
        )
        
        desde_iter = IntPrompt.ask(
            "Desde qué iteración mostrar el vector (j)",
            default=0,
            console=self.console
        )
        
        cant_iter = IntPrompt.ask(
            "Cantidad de iteraciones a mostrar (i)",
            default=10,
            console=self.console
        )
        
        return tiempo_sim, desde_iter, cant_iter

    def ejecutar_simulacion(self, tiempo_sim: float) -> Dict:
        """Ejecuta la simulación con indicador de progreso"""
        self.simulador = SimuladorCertificados(
            servicio_min=self.servicio_min.get(),
            servicio_max=self.servicio_max.get(),
            revision_min=self.revision_min.get(),
            revision_max=self.revision_max.get(),
            ronda_min=self.ronda_min.get(),
            ronda_max=self.ronda_max.get(),
            media_llegada=self.media_llegada.get(),
            max_cola=self.max_cola.get(),
            tiempo_regreso=self.tiempo_regreso.get()
        )
        random.seed(42)  # Para reproducibilidad
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Simulando {tiempo_sim} minutos...", total=None)
            resultados = self.simulador.simular(tiempo_sim)
            progress.update(task, completed=True)
        
        return resultados

    def mostrar_resumen_resultados(self, resultados: Dict):
        """Muestra el resumen de resultados en una tabla"""
        tabla = Table(title="Resumen de Resultados", show_header=True, header_style="bold magenta")
        tabla.add_column("Métrica", style="cyan", no_wrap=True)
        tabla.add_column("Valor", style="green")
        
        tabla.add_row("Iteraciones realizadas", str(resultados['iteraciones_realizadas']))
        tabla.add_row("Tiempo final", f"{resultados['tiempo_final']:.2f} min")
        tabla.add_row("Estudiantes atendidos", str(resultados['estudiantes_atendidos']))
        tabla.add_row("Estudiantes retirados", str(resultados['estudiantes_retirados']))
        tabla.add_row("% Estudiantes que se retiran", f"{resultados['porcentaje_retiros']:.2f}%")
        tabla.add_row("Tiempo promedio de espera", f"{resultados['tiempo_promedio_espera']:.2f} min")
        
        self.console.print(tabla)

    def crear_tabla_vector_estados(self, estados: List[Dict], inicio: int, fin: int) -> Table:
        """Crea una tabla con el vector de estados"""
        tabla = Table(title=f"Vector de Estados (iteraciones {inicio} a {fin-1})", 
                     show_header=True, header_style="bold yellow")
        
        # Columnas principales
        tabla.add_column("Iter", style="dim", width=4)
        tabla.add_column("Reloj", style="cyan", width=8)
        tabla.add_column("Evento", style="magenta", width=15)
        tabla.add_column("Técnico", style="blue", width=12)
        tabla.add_column("T1", style="green", width=6)
        tabla.add_column("T2", style="green", width=6)
        tabla.add_column("T3", style="green", width=6)
        tabla.add_column("T4", style="green", width=6)
        tabla.add_column("Cola", style="red", width=6)
        tabla.add_column("Atendidos", style="yellow", width=10)
        tabla.add_column("Retirados", style="orange1", width=10)
        tabla.add_column("% Retiros", style="purple", width=10)
        
        for i in range(inicio, min(fin, len(estados))):
            estado = estados[i]
            
            # Estado del técnico
            tecnico_estado = estado['tecnico']['estado']
            if estado['tecnico']['terminal_revisando']:
                tecnico_estado += f"(T{estado['tecnico']['terminal_revisando']})"
            
            # Estados de terminales
            terminales_estado = []
            for j, terminal in enumerate(estado['terminales']):
                est = terminal['estado']
                if terminal['estudiante_id']:
                    est += f"({terminal['estudiante_id']})"
                terminales_estado.append(est)
            
            tabla.add_row(
                str(i),
                f"{estado['reloj']:.2f}",
                estado['evento'][:14],
                tecnico_estado,
                terminales_estado[0],
                terminales_estado[1], 
                terminales_estado[2],
                terminales_estado[3],
                str(estado['cola_length']),
                str(estado['estudiantes_atendidos']),
                str(estado['estudiantes_retirados']),
                f"{estado['porcentaje_retiros']:.1f}%"
            )
        
        return tabla

    def mostrar_vector_estados(self, desde_iter: int, cant_iter: int):
        """Muestra el vector de estados"""
        if not self.simulador or not self.simulador.vector_estados:
            self.console.print("[red]No hay datos de simulación para mostrar[/red]")
            return
        
        estados = self.simulador.vector_estados
        inicio = desde_iter
        fin = min(inicio + cant_iter, len(estados))
        
        if inicio >= len(estados):
            self.console.print(f"[red]La iteración {inicio} no existe. Máximo: {len(estados)-1}[/red]")
            return
        
        tabla = self.crear_tabla_vector_estados(estados, inicio, fin)
        self.console.print(tabla)

    def mostrar_ultima_fila(self):
        """Muestra la última fila de simulación"""
        if not self.simulador or not self.simulador.vector_estados:
            self.console.print("[red]No hay datos de simulación para mostrar[/red]")
            return
        
        estados = self.simulador.vector_estados
        ultima_fila = len(estados) - 1
        
        tabla = self.crear_tabla_vector_estados(estados, ultima_fila, ultima_fila + 1)
        tabla.title = "Última Fila de Simulación"
        self.console.print(tabla)

    def mostrar_detalle_iteracion(self, iteracion: int):
        """Muestra el detalle completo de una iteración"""
        if not self.simulador or not self.simulador.vector_estados:
            self.console.print("[red]No hay datos de simulación para mostrar[/red]")
            return
        
        estados = self.simulador.vector_estados
        
        if iteracion >= len(estados) or iteracion < 0:
            self.console.print(f"[red]Iteración {iteracion} no válida. Rango: 0-{len(estados)-1}[/red]")
            return
        
        estado = estados[iteracion]
        
        # Panel principal con información detallada
        info_detalle = []
        info_detalle.append(f"[bold cyan]Reloj:[/bold cyan] {estado['reloj']:.2f} min")
        info_detalle.append(f"[bold cyan]Evento:[/bold cyan] {estado['evento']}")
        info_detalle.append(f"[bold cyan]Próximos eventos:[/bold cyan] {estado['proximos_eventos']}")
        info_detalle.append("")
        
        # Técnico
        tecnico = estado['tecnico']
        info_detalle.append(f"[bold blue]Técnico:[/bold blue] Estado={tecnico['estado']}")
        if tecnico['terminal_revisando']:
            info_detalle.append(f"  Revisando Terminal {tecnico['terminal_revisando']}")
        if tecnico['fin_revision']:
            info_detalle.append(f"  Fin revisión: {tecnico['fin_revision']:.2f}")
        if tecnico['proxima_ronda']:
            info_detalle.append(f"  Próxima ronda: {tecnico['proxima_ronda']:.2f}")
        info_detalle.append("")
        
        # Terminales
        info_detalle.append("[bold green]Terminales:[/bold green]")
        for i, terminal in enumerate(estado['terminales']):
            estado_terminal = f"  Terminal {i+1}: {terminal['estado']}"
            if terminal['estudiante_id']:
                estado_terminal += f" (Estudiante {terminal['estudiante_id']})"
            if terminal['fin_servicio']:
                estado_terminal += f" - Fin: {terminal['fin_servicio']:.2f}"
            info_detalle.append(estado_terminal)
        info_detalle.append("")
        
        # Variables auxiliares
        info_detalle.append("[bold yellow]Variables auxiliares:[/bold yellow]")
        info_detalle.append(f"  Estudiantes en cola: {estado['cola_length']}")
        info_detalle.append(f"  Estudiantes en sistema: {estado['estudiantes_sistema']}")
        info_detalle.append(f"  Estudiantes atendidos: {estado['estudiantes_atendidos']}")
        info_detalle.append(f"  Estudiantes retirados: {estado['estudiantes_retirados']}")
        info_detalle.append(f"  % Retiros: {estado['porcentaje_retiros']:.2f}%")
        info_detalle.append(f"  Tiempo promedio espera: {estado['tiempo_promedio_espera']:.2f} min")
        
        # RND usados
        if estado['rnd_usados']:
            info_detalle.append("")
            info_detalle.append("[bold red]Números aleatorios usados:[/bold red]")
            for var, rnd in estado['rnd_usados'].items():
                info_detalle.append(f"  {var}: {rnd:.6f}")
        
        panel = Panel(
            "\n".join(info_detalle),
            title=f"Detalle Iteración {iteracion}",
            border_style="cyan"
        )
        
        self.console.print(panel)

    def menu_principal(self):
        """Muestra el menú principal y maneja la interacción"""
        while True:
            self.console.print("\n[bold cyan]MENÚ PRINCIPAL[/bold cyan]")
            self.console.print("1. Nueva simulación")
            if self.simulador:
                self.console.print("2. Ver vector de estados")
                self.console.print("3. Ver última fila")
                self.console.print("4. Ver detalle de iteración")
                self.console.print("5. Ver resumen de resultados")
            self.console.print("0. Salir")
            
            opcion = Prompt.ask("Seleccione una opción", choices=['0', '1', '2', '3', '4', '5'] if self.simulador else ['0', '1'])
            
            if opcion == '0':
                self.console.print("[yellow]¡Hasta luego![/yellow]")
                break
            elif opcion == '1':
                self.ejecutar_nueva_simulacion()
            elif opcion == '2' and self.simulador:
                self.ver_vector_estados()
            elif opcion == '3' and self.simulador:
                self.mostrar_ultima_fila()
            elif opcion == '4' and self.simulador:
                self.ver_detalle_iteracion()
            elif opcion == '5' and self.simulador:
                self.ver_resumen()

    def ejecutar_nueva_simulacion(self):
        """Ejecuta una nueva simulación"""
        try:
            tiempo_sim, desde_iter, cant_iter = self.solicitar_parametros()
            
            self.console.print(f"\n[green]Iniciando simulación...[/green]")
            resultados = self.ejecutar_simulacion(tiempo_sim)
            
            self.console.print(f"\n[green]¡Simulación completada![/green]")
            self.mostrar_resumen_resultados(resultados)
            
            # Mostrar vector de estados solicitado
            self.console.print(f"\n[cyan]Vector de Estados Solicitado:[/cyan]")
            self.mostrar_vector_estados(desde_iter, cant_iter)
            
            # Guardar parámetros para uso posterior
            self.ultimo_desde_iter = desde_iter
            self.ultimo_cant_iter = cant_iter
            
        except Exception as e:
            self.console.print(f"[red]Error durante la simulación: {e}[/red]")

    def ver_vector_estados(self):
        """Permite ver el vector de estados con parámetros personalizados"""
        desde_iter = IntPrompt.ask(
            "Desde qué iteración",
            default=getattr(self, 'ultimo_desde_iter', 0),
            console=self.console
        )
        cant_iter = IntPrompt.ask(
            "Cantidad de iteraciones",
            default=getattr(self, 'ultimo_cant_iter', 10),
            console=self.console
        )
        
        self.mostrar_vector_estados(desde_iter, cant_iter)

    def ver_detalle_iteracion(self):
        """Permite ver el detalle de una iteración específica"""
        max_iter = len(self.simulador.vector_estados) - 1
        iteracion = IntPrompt.ask(
            f"Número de iteración (0-{max_iter})",
            console=self.console
        )
        
        self.mostrar_detalle_iteracion(iteracion)

    def ver_resumen(self):
        """Muestra el resumen de la última simulación"""
        if hasattr(self, 'ultimo_resultado'):
            self.mostrar_resumen_resultados(self.ultimo_resultado)
        else:
            self.console.print("[red]No hay resultados para mostrar[/red]")

class SimuladorApp(tk.Tk):
    """
    Interfaz gráfica principal del simulador usando Tkinter.
    Permite al usuario ingresar parámetros, ejecutar la simulación y visualizar resultados.
    """
    def __init__(self):
        super().__init__()
        self.title("Simulador Sistema Autogestión Certificados")
        self.geometry("1100x650")
        self.simulador = None
        self.resultados = None

        # --- Parámetros de simulación configurables por el usuario ---
        frame_params = ttk.LabelFrame(self, text="Parámetros de Simulación")
        frame_params.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_params, text="Tiempo de simulación (min):").grid(row=0, column=0, padx=5, pady=5)
        self.tiempo_sim_var = tk.DoubleVar(value=120.0)
        ttk.Entry(frame_params, textvariable=self.tiempo_sim_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_params, text="Desde iteración:").grid(row=0, column=2, padx=5, pady=5)
        self.desde_iter_var = tk.IntVar(value=0)
        ttk.Entry(frame_params, textvariable=self.desde_iter_var, width=6).grid(row=0, column=3, padx=5, pady=5)

        # --- Parámetros del modelo (solo los configurables) ---
        ttk.Label(frame_params, text="Servicio min:").grid(row=1, column=0, padx=5, pady=2)
        self.servicio_min = tk.DoubleVar(value=5)
        ttk.Entry(frame_params, textvariable=self.servicio_min, width=6).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(frame_params, text="Servicio max:").grid(row=1, column=2, padx=5, pady=2)
        self.servicio_max = tk.DoubleVar(value=8)
        ttk.Entry(frame_params, textvariable=self.servicio_max, width=6).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame_params, text="Revisión min:").grid(row=1, column=4, padx=5, pady=2)
        self.revision_min = tk.DoubleVar(value=3)
        ttk.Entry(frame_params, textvariable=self.revision_min, width=6).grid(row=1, column=5, padx=5, pady=2)
        ttk.Label(frame_params, text="Revisión max:").grid(row=1, column=6, padx=5, pady=2)
        self.revision_max = tk.DoubleVar(value=10)
        ttk.Entry(frame_params, textvariable=self.revision_max, width=6).grid(row=1, column=7, padx=5, pady=2)

        ttk.Label(frame_params, text="Ronda min:").grid(row=2, column=0, padx=5, pady=2)
        self.ronda_min = tk.DoubleVar(value=57)
        ttk.Entry(frame_params, textvariable=self.ronda_min, width=6).grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(frame_params, text="Ronda max:").grid(row=2, column=2, padx=5, pady=2)
        self.ronda_max = tk.DoubleVar(value=63)
        ttk.Entry(frame_params, textvariable=self.ronda_max, width=6).grid(row=2, column=3, padx=5, pady=2)

        ttk.Label(frame_params, text="Media llegada:").grid(row=2, column=4, padx=5, pady=2)
        self.media_llegada = tk.DoubleVar(value=2)
        ttk.Entry(frame_params, textvariable=self.media_llegada, width=6).grid(row=2, column=5, padx=5, pady=2)

        # --- Parámetros fijos (no editables) ---
        ttk.Label(frame_params, text="Máx. en cola: 5 (fijo)").grid(row=2, column=6, padx=5, pady=2)
        ttk.Label(frame_params, text="Tiempo regreso: 30 (fijo)").grid(row=2, column=7, padx=5, pady=2)

        ttk.Button(frame_params, text="Ejecutar Simulación", command=self.ejecutar_simulacion).grid(row=0, column=8, rowspan=2, padx=10, pady=5)

        # --- Resumen de resultados ---
        self.frame_resumen = ttk.LabelFrame(self, text="Resumen de Resultados")
        self.frame_resumen.pack(fill="x", padx=10, pady=5)
        self.resumen_vars = [tk.StringVar() for _ in range(6)]
        for i, label in enumerate(["Iteraciones", "Tiempo final", "Atendidos", "Retirados", "% Retiros", "Prom. espera"]):
            ttk.Label(self.frame_resumen, text=label + ":").grid(row=0, column=2*i, padx=5, pady=2, sticky="e")
            ttk.Label(self.frame_resumen, textvariable=self.resumen_vars[i]).grid(row=0, column=2*i+1, padx=5, pady=2, sticky="w")

        # --- Vector de estados (tabla principal) con scrollbars y columnas extendidas ---
        self.frame_vector = ttk.LabelFrame(self, text="Vector de Estados (detalle extendido)")
        self.frame_vector.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_scroll_y = ttk.Scrollbar(self.frame_vector, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(self.frame_vector, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        # Definición de columnas extendidas
        columns = [
            "evento", "reloj",  # Tipo Evento, Reloj
            "rnd_llegada", "tiempo_entre_llegadas", "prox_llegada",  # Estudiante
            "rnd_ronda", "tiempo_entre_rondas", "prox_ronda", "tec_estado",  # Técnico
            "t1_estado", "t2_estado", "t3_estado", "t4_estado", "cola",  # Terminales y cola
            # Terminales servicio
            "t1_rnd_serv", "t1_demora_serv", "t1_fin_serv",
            "t2_rnd_serv", "t2_demora_serv", "t2_fin_serv",
            "t3_rnd_serv", "t3_demora_serv", "t3_fin_serv",
            "t4_rnd_serv", "t4_demora_serv", "t4_fin_serv",
            # Terminales revisión
            "t1_rnd_rev", "t1_demora_rev", "t1_fin_rev",
            "t2_rnd_rev", "t2_demora_rev", "t2_fin_rev",
            "t3_rnd_rev", "t3_demora_rev", "t3_fin_rev",
            "t4_rnd_rev", "t4_demora_rev", "t4_fin_rev",
            # Acumuladores y métricas
            "acum_retirados", "acum_atendidos", "porc_retirados", "acum_espera", "prom_espera"
        ]
        headers = [
            "Tipo Evento", "Reloj",
            "RND", "Tiempo entre llegadas", "Próxima llegada",
            "RND", "Tiempo entre rondas", "Próxima llegada", "Estado Técnico",
            "Estado T1", "Estado T2", "Estado T3", "Estado T4", "Cola",
            # Terminales servicio
            "RND", "Demora", "Fin de servicio",
            "RND", "Demora", "Fin de servicio",
            "RND", "Demora", "Fin de servicio",
            "RND", "Demora", "Fin de servicio",
            # Terminales revisión
            "RND", "Demora", "Fin de revisión",
            "RND", "Demora", "Fin de revisión",
            "RND", "Demora", "Fin de revisión",
            "RND", "Demora", "Fin de revisión",
            # Acumuladores y métricas
            "Est. retiran/regresan", "Est. atendidos", "% retiran/regresan", "Acum. espera", "Prom. espera"
        ]

        self.tree = ttk.Treeview(
            self.frame_vector,
            columns=columns,
            show="headings",
            height=15,
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set
        )
        for c, h in zip(columns, headers):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=90)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle_iteracion)

        # --- Detalle de iteración (texto) ---
        self.text_detalle = scrolledtext.ScrolledText(self, height=10, font=("Consolas", 10))
        self.text_detalle.pack(fill="both", expand=False, padx=10, pady=5)

    def ejecutar_simulacion(self):
        """
        Ejecuta la simulación con los parámetros ingresados y muestra los resultados.
        Solo permite hasta 100000 iteraciones o hasta el tiempo indicado.
        """
        try:
            tiempo_sim = self.tiempo_sim_var.get()
            desde_iter = self.desde_iter_var.get()
            # Crear el simulador con los parámetros configurables
            self.simulador = SimuladorCertificados(
                servicio_min=self.servicio_min.get(),
                servicio_max=self.servicio_max.get(),
                revision_min=self.revision_min.get(),
                revision_max=self.revision_max.get(),
                ronda_min=self.ronda_min.get(),
                ronda_max=self.ronda_max.get(),
                media_llegada=self.media_llegada.get()
            )
            random.seed(42)
            # Ejecutar simulación con máximo 100000 iteraciones
            self.resultados = self.simulador.simular(tiempo_simulacion=tiempo_sim, max_iteraciones=100000)
            self.mostrar_resumen()
            self.mostrar_vector_estados(desde_iter)
            self.text_detalle.delete("1.0", tk.END)
            messagebox.showinfo("Simulación", "¡Simulación completada!")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la simulación:\n{e}")

    def mostrar_resumen(self):
        """
        Muestra el resumen de métricas principales de la simulación.
        """
        r = self.resultados
        self.resumen_vars[0].set(r['iteraciones_realizadas'])
        self.resumen_vars[1].set(f"{r['tiempo_final']:.2f}")
        self.resumen_vars[2].set(r['estudiantes_atendidos'])
        self.resumen_vars[3].set(r['estudiantes_retirados'])
        self.resumen_vars[4].set(f"{r['porcentaje_retiros']:.2f}%")
        self.resumen_vars[5].set(f"{r['tiempo_promedio_espera']:.2f} min")

    def mostrar_vector_estados(self, desde_iter):
        """
        Muestra el vector de estados en la tabla principal, desde la iteración indicada hasta el final.
        Incluye columnas extendidas y métricas por iteración.
        """
        self.tree.delete(*self.tree.get_children())
        vector = self.resultados['vector_estados']
        inicio = int(desde_iter)
        fin = len(vector)
        for i in range(inicio, fin):
            estado = vector[i]
            # --- Evento y reloj ---
            evento = estado['evento']
            reloj = f"{estado['reloj']:.2f}"

            # --- Llegadas ---
            rnd_llegada = estado['rnd_usados'].get('llegada_estudiante', "")
            tiempo_entre_llegadas = ""
            prox_llegada = ""
            # Buscar próximo evento de llegada
            for ev in estado['proximos_eventos'].split(";"):
                if "llegada_estudiante" in ev:
                    prox_llegada = ev.split("@")[1] if "@" in ev else ""
            if i > 0 and 'llegada_estudiante' in estado['rnd_usados']:
                tiempo_entre_llegadas = f"{estado['reloj'] - vector[i-1]['reloj']:.2f}"

            # --- Técnico ---
            rnd_ronda = estado['rnd_usados'].get('ronda', "")
            tiempo_entre_rondas = ""
            prox_ronda = estado['tecnico']['proxima_ronda'] if estado['tecnico']['proxima_ronda'] else ""
            tec_estado = estado['tecnico']['estado']

            # --- Estados terminales y cola ---
            t_estados = [t['estado'] for t in estado['terminales']]
            cola = estado['cola_length']

            # --- Terminales servicio ---
            t_serv_rnd, t_serv_demora, t_serv_fin = [], [], []
            t_rev_rnd, t_rev_demora, t_rev_fin = [], [], []
            for j in range(4):
                # Servicio
                rnd_serv = estado['rnd_usados'].get(f'servicio_{j+1}', None)
                t_serv_rnd.append(f"{rnd_serv:.4f}" if rnd_serv not in [None, ""] else "-")
                demora_serv = estado.get('demora_servicio', [None]*4)[j] if 'demora_servicio' in estado else None
                t_serv_demora.append(f"{demora_serv:.2f}" if demora_serv not in [None, ""] else "-")
                fin_serv = estado['terminales'][j]['fin_servicio']
                t_serv_fin.append(f"{fin_serv:.2f}" if fin_serv not in [None, ""] else "-")
                # Revisión
                rnd_rev = estado['rnd_usados'].get(f'revision_{j+1}', None)
                t_rev_rnd.append(f"{rnd_rev:.4f}" if rnd_rev not in [None, ""] else "-")
                demora_rev = estado.get('demora_revision', [None]*4)[j] if 'demora_revision' in estado else None
                t_rev_demora.append(f"{demora_rev:.2f}" if demora_rev not in [None, ""] else "-")
                fin_rev = estado.get('fin_revision', [None]*4)[j] if 'fin_revision' in estado else None
                t_rev_fin.append(f"{fin_rev:.2f}" if fin_rev not in [None, ""] else "-")

            # --- Acumuladores y métricas ---
            acum_retirados = estado['estudiantes_retirados']
            acum_atendidos = estado['estudiantes_atendidos']
            porc_retirados = f"{estado['porcentaje_retiros']:.2f}"
            acum_espera = f"{getattr(self.simulador, 'acum_tiempo_espera', 0):.2f}"
            prom_espera = f"{estado['tiempo_promedio_espera']:.2f}"

            row = [
                evento, reloj,
                rnd_llegada, tiempo_entre_llegadas, prox_llegada,
                rnd_ronda, tiempo_entre_rondas, prox_ronda, tec_estado,
                *t_estados, cola,
                *t_serv_rnd, *t_serv_demora, *t_serv_fin,
                *t_rev_rnd, *t_rev_demora, *t_rev_fin,
                acum_retirados, acum_atendidos, porc_retirados, acum_espera, prom_espera
            ]
            self.tree.insert("", "end", iid=str(i), values=row)

    def mostrar_detalle_iteracion(self, event):
        """
        Muestra el detalle completo de la iteración seleccionada en la tabla.
        """
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        estado = self.resultados['vector_estados'][idx]
        lines = []
        lines.append(f"--- Iteración {idx} ---")
        lines.append(f"Reloj: {estado['reloj']:.2f}")
        lines.append(f"Evento: {estado['evento']}")
        lines.append(f"Próximos eventos: {estado['proximos_eventos']}")
        lines.append("")
        lines.append(f"Técnico: Estado={estado['tecnico']['estado']}, Próxima ronda={estado['tecnico']['proxima_ronda']}, Fin revisión={estado['tecnico']['fin_revision']}")
        lines.append("")
        lines.append("Terminales:")
        for i, terminal in enumerate(estado['terminales']):
            lines.append(f"  Terminal {i+1}: Estado={terminal['estado']}, Fin servicio={terminal['fin_servicio']}, Estudiante={terminal['estudiante_id']}")
        lines.append("")
        lines.append(f"Cola: {estado['cola_length']} estudiantes esperando")
        lines.append(f"Estudiantes en sistema: {estado['estudiantes_sistema']}")
        lines.append(f"Estudiantes atendidos: {estado['estudiantes_atendidos']}")
        lines.append(f"Estudiantes retirados: {estado['estudiantes_retirados']}")
        lines.append(f"% Retiros: {estado['porcentaje_retiros']:.2f}%")
        lines.append(f"Tiempo promedio espera: {estado['tiempo_promedio_espera']:.2f} min")
        if estado['rnd_usados']:
            lines.append("RND usados:")
            for var, rnd in estado['rnd_usados'].items():
                lines.append(f"  {var}: {rnd:.6f}")
        self.text_detalle.delete("1.0", tk.END)
        self.text_detalle.insert(tk.END, "\n".join(lines))

if __name__ == "__main__":
    # Inicia la interfaz gráfica
    app = SimuladorApp()
    app.mainloop()