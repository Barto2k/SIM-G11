import tkinter as tk
import random
from tkinter import ttk, messagebox, scrolledtext
from simulador import SimuladorCertificados

class SimuladorApp(tk.Tk):
    """
    Interfaz gráfica principal del simulador usando Tkinter.
    Permite al usuario ingresar parámetros, ejecutar la simulación y visualizar resultados.
    """
    def __init__(self):
        super().__init__()
        self.title("Simulador Sistema Autogestión Certificados")
        self.geometry("1100x650")
        self.simulador = None  # Instancia del simulador, se inicializa al ejecutar la simulación
        self.resultados = None  # Resultados de la simulación

        # --- Parámetros de simulación configurables por el usuario ---
        frame_params = ttk.LabelFrame(self, text="Parámetros de Simulación")
        frame_params.pack(fill="x", padx=10, pady=5)

        # Tiempo de simulación (en minutos)
        ttk.Label(frame_params, text="Tiempo de simulación (min):").grid(row=0, column=0, padx=5, pady=5)
        self.tiempo_sim_var = tk.DoubleVar(value=120.0)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.tiempo_sim_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        # Iteración desde la cual mostrar resultados
        ttk.Label(frame_params, text="Desde iteración:").grid(row=0, column=2, padx=5, pady=5)
        self.desde_iter_var = tk.IntVar(value=0)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.desde_iter_var, width=6).grid(row=0, column=3, padx=5, pady=5)

        # --- Parámetros del modelo (solo los configurables) ---
        # Servicio mínimo y máximo
        ttk.Label(frame_params, text="Servicio min:").grid(row=1, column=0, padx=5, pady=2)
        self.servicio_min = tk.DoubleVar(value=5)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.servicio_min, width=6).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(frame_params, text="Servicio max:").grid(row=1, column=2, padx=5, pady=2)
        self.servicio_max = tk.DoubleVar(value=8)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.servicio_max, width=6).grid(row=1, column=3, padx=5, pady=2)

        # Revisión mínima y máxima
        ttk.Label(frame_params, text="Revisión min:").grid(row=1, column=4, padx=5, pady=2)
        self.revision_min = tk.DoubleVar(value=3)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.revision_min, width=6).grid(row=1, column=5, padx=5, pady=2)
        ttk.Label(frame_params, text="Revisión max:").grid(row=1, column=6, padx=5, pady=2)
        self.revision_max = tk.DoubleVar(value=10)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.revision_max, width=6).grid(row=1, column=7, padx=5, pady=2)

        # Ronda mínima y máxima
        ttk.Label(frame_params, text="Ronda min:").grid(row=2, column=0, padx=5, pady=2)
        self.ronda_min = tk.DoubleVar(value=57)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.ronda_min, width=6).grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(frame_params, text="Ronda max:").grid(row=2, column=2, padx=5, pady=2)
        self.ronda_max = tk.DoubleVar(value=63)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.ronda_max, width=6).grid(row=2, column=3, padx=5, pady=2)

        # Media de llegada de estudiantes
        ttk.Label(frame_params, text="Media llegada:").grid(row=2, column=4, padx=5, pady=2)
        self.media_llegada = tk.DoubleVar(value=2)  # Valor inicial por defecto
        ttk.Entry(frame_params, textvariable=self.media_llegada, width=6).grid(row=2, column=5, padx=5, pady=2)

        # --- Parámetros fijos (no editables) ---
        # Estos valores son constantes y no pueden ser modificados por el usuario
        ttk.Label(frame_params, text="Máx. en cola: 5 (fijo)").grid(row=2, column=6, padx=5, pady=2)
        ttk.Label(frame_params, text="Tiempo regreso: 30 (fijo)").grid(row=2, column=7, padx=5, pady=2)

        # Botón para ejecutar la simulación
        ttk.Button(frame_params, text="Ejecutar Simulación", command=self.ejecutar_simulacion).grid(row=0, column=8, rowspan=2, padx=10, pady=5)

        # --- Resumen de resultados ---
        self.frame_resumen = ttk.LabelFrame(self, text="Resumen de Resultados")
        self.frame_resumen.pack(fill="x", padx=10, pady=5)

        # Variables para mostrar los resultados principales de la simulación
        self.resumen_vars = [tk.StringVar() for _ in range(6)]
        for i, label in enumerate(["Iteraciones", "Tiempo final", "Atendidos", "Retirados", "% Retiros", "Prom. espera"]):
            ttk.Label(self.frame_resumen, text=label + ":").grid(row=0, column=2*i, padx=5, pady=2, sticky="e")
            ttk.Label(self.frame_resumen, textvariable=self.resumen_vars[i]).grid(row=0, column=2*i+1, padx=5, pady=2, sticky="w")

        # --- Vector de estados (tabla principal) con scrollbars y columnas extendidas ---
        self.frame_vector = ttk.LabelFrame(self, text="Vector de Estados (detalle extendido)")
        self.frame_vector.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollbars para la tabla principal
        self.tree_scroll_y = ttk.Scrollbar(self.frame_vector, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(self.frame_vector, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        # Definición de columnas extendidas
        columns = [
            "evento", "reloj",  # Tipo Evento, Reloj
            "rnd_llegada", "prox_llegada",  # Estudiante
            "rnd_ronda", "prox_ronda", "tec_estado",  # Técnico
            "t1_estado", "t2_estado", "t3_estado", "t4_estado", "cola",  # Terminales y cola
            # Terminales servicio
            "t1_rnd_serv", "t1_fin_serv",
            "t2_rnd_serv", "t2_fin_serv",
            "t3_rnd_serv", "t3_fin_serv",
            "t4_rnd_serv", "t4_fin_serv",
            # Terminales revisión
            "t1_rnd_rev", "t1_fin_rev",
            "t2_rnd_rev", "t2_fin_rev",
            "t3_rnd_rev", "t3_fin_rev",
            "t4_rnd_rev", "t4_fin_rev",
            # Acumuladores y métricas
            "acum_retirados", "acum_atendidos", "porc_retirados", "acum_espera", "prom_espera"
        ]
        headers = [
            "Tipo Evento", "Reloj",
            "RND", "Próxima llegada",
            "RND", "Próxima llegada", "Estado Técnico",
            "Estado T1", "Estado T2", "Estado T3", "Estado T4", "Cola",
            # Terminales servicio
            "RND T1", "Fin de servicio T1",
            "RND T2", "Fin de servicio T2",
            "RND T3", "Fin de servicio T3",
            "RND T4", "Fin de servicio T4",
            # Terminales revisión
            "RND", "Fin de revisión T1",
            "RND", "Fin de revisión T2",
            "RND", "Fin de revisión T3",
            "RND", "Fin de revisión T4",
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
            self.tree.column(c, width=100)
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
            # --- Validaciones ---
            servicio_min = self.servicio_min.get()
            servicio_max = self.servicio_max.get()
            revision_min = self.revision_min.get()
            revision_max = self.revision_max.get()
            ronda_min = self.ronda_min.get()
            ronda_max = self.ronda_max.get()
            media_llegada = self.media_llegada.get()
            desde_iter = self.desde_iter_var.get()
            tiempo_sim = self.tiempo_sim_var.get()

            if servicio_min < 0 or servicio_max <= 0 or servicio_min >= servicio_max:
                messagebox.showerror("Error de validación", "Servicio mínimo debe ser >= 0 y menor que servicio máximo, ambos positivos.")
                return
            if revision_min < 0 or revision_max <= 0 or revision_min >= revision_max:
                messagebox.showerror("Error de validación", "Revisión mínima debe ser >= 0 y menor que revisión máxima, ambos positivos.")
                return
            if ronda_min < 0 or ronda_max <= 0 or ronda_min >= ronda_max:
                messagebox.showerror("Error de validación", "Ronda mínima debe ser >= 0 y menor que ronda máxima, ambos positivos.")
                return
            if media_llegada <= 0:
                messagebox.showerror("Error de validación", "La media de llegada debe ser un valor positivo.")
                return
            if desde_iter < 0:
                messagebox.showerror("Error de validación", "El campo 'Desde iteración' debe ser mayor o igual a 0.")
                return
            if tiempo_sim <= 0:
                messagebox.showerror("Error de validación", "El tiempo de simulación debe ser mayor a 0.")
                return

            # --- Si todo es válido, ejecutar simulación ---
            self.simulador = SimuladorCertificados(
                servicio_min=servicio_min,
                servicio_max=servicio_max,
                revision_min=revision_min,
                revision_max=revision_max,
                ronda_min=ronda_min,
                ronda_max=ronda_max,
                media_llegada=media_llegada
            )
            random.seed(42)
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
            prox_llegada = ""
            # Buscar próximo evento de llegada
            for ev in estado['proximos_eventos'].split(";"):
                if "llegada_estudiante" in ev:
                    prox_llegada = ev.split("@")[1] if "@" in ev else ""

            # --- Técnico ---
            rnd_ronda = estado['rnd_usados'].get('ronda', "")
            prox_ronda = estado['tecnico']['proxima_ronda'] if estado['tecnico']['proxima_ronda'] else ""
            tec_estado = estado['tecnico']['estado']

            # --- Estados terminales y cola ---
            t_estados = [t['estado'] for t in estado['terminales']]
            cola = estado['cola_length']

            # --- Terminales servicio ---
            t_serv_rnd, t_serv_fin = [], []
            t_rev_rnd, t_rev_fin = [], []
            for j in range(4):
                # Servicio
                rnd_serv = estado['rnd_usados'].get(f'servicio_{j+1}', None)
                t_serv_rnd.append(f"{rnd_serv:.4f}" if rnd_serv not in [None, ""] else "-")
                fin_serv = estado['terminales'][j]['fin_servicio']
                t_serv_fin.append(f"{fin_serv:.2f}" if fin_serv not in [None, ""] else "-")
                # Revisión
                rnd_rev = estado['rnd_usados'].get(f'revision_{j+1}', None)
                fin_revs = estado.get('fin_revision', [None]*4)
                fin_rev = fin_revs[j] if j < len(fin_revs) else None

                # Mostrar t_rev_rnd y t_rev_fin desde que aparece el rnd hasta que el reloj alcance fin_rev
                if rnd_rev not in [None, ""]:
                    t_rev_rnd.append(f"{rnd_rev:.4f}")
                    if fin_rev not in [None, ""]:
                        t_rev_fin.append(f"{fin_rev:.2f}")
                    else:
                        t_rev_fin.append("-")
                else:
                    # Si ya apareció el rnd_rev en una iteración anterior y el reloj actual < fin_rev, seguir mostrando fin_rev
                    # Para esto, buscamos hacia atrás en el vector de estados si hubo un rnd_rev para este terminal y si el fin_rev es el mismo
                    mostrar = False
                    if fin_rev not in [None, ""] and estado['reloj'] < fin_rev:
                        # Buscar si hubo un rnd_rev para este terminal con este fin_rev en una iteración anterior
                        for k in range(i-1, -1, -1):
                            prev_estado = vector[k]
                            prev_rnd_rev = prev_estado['rnd_usados'].get(f'revision_{j+1}', None)
                            prev_fin_revs = prev_estado.get('fin_revision', [None]*4)
                            prev_fin_rev = prev_fin_revs[j] if j < len(prev_fin_revs) else None
                            if prev_rnd_rev not in [None, ""] and prev_fin_rev == fin_rev:
                                mostrar = True
                                break
                    if mostrar and estado['reloj'] < fin_rev:
                        t_rev_rnd.append("-")
                        t_rev_fin.append(f"{fin_rev:.2f}")
                    else:
                        t_rev_rnd.append("-")
                        t_rev_fin.append("-")
            
            # --- Acumuladores y métricas ---
            acum_retirados = estado['estudiantes_retirados']
            acum_atendidos = estado['estudiantes_atendidos']
            porc_retirados = f"{estado['porcentaje_retiros']:.2f}"
            acum_espera = f"{estado.get('acum_tiempo_espera', 0):.2f}"
            prom_espera = f"{estado['tiempo_promedio_espera']:.2f}"

            row = [
                evento, reloj,
                rnd_llegada, prox_llegada,
                rnd_ronda, prox_ronda, tec_estado,
                *t_estados, cola,
                t_serv_rnd[0], t_serv_fin[0],
                t_serv_rnd[1], t_serv_fin[1],
                t_serv_rnd[2], t_serv_fin[2],
                t_serv_rnd[3], t_serv_fin[3],
                t_rev_rnd[0], t_rev_fin[0],
                t_rev_rnd[1], t_rev_fin[1],
                t_rev_rnd[2], t_rev_fin[2],
                t_rev_rnd[3], t_rev_fin[3],
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