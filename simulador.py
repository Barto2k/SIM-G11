import random
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from modelos import Estudiante, Terminal, Tecnico, Evento

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
            'acum_tiempo_espera': self.acum_tiempo_espera,
            'tiempo_promedio_espera': tiempo_promedio_espera,
            'rnd_usados': self.rnd_usados.copy(),
            'demora_revision': list(getattr(self, 'demora_revision', [None]*4)),
            'fin_revision': list(getattr(self, 'fin_revision', [None]*4))
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
            'tiempo_promedio_espera': tiempo_promedio_espera,
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