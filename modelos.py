from dataclasses import dataclass
from typing import Optional, Dict

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