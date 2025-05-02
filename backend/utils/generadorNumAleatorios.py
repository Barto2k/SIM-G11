import numpy as np
import pandas as pd


def generate_uniform(sample_size, a=0, b=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if a >= b:
        raise ValueError("El límite inferior debe ser menor que el límite superior")

    random_numbers = np.random.uniform(low=a, high=(b - 1e-5), size=sample_size)
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def generate_exponential(sample_size, lambd=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if lambd <= 0:
        raise ValueError("El parámetro lambda debe ser positivo")

    random_numbers = np.random.exponential(scale=1 / lambd, size=sample_size)
    random_numbers = (random_numbers / np.max(random_numbers)) * 0.9999
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def generate_normal(sample_size, mean=0, std_dev=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if std_dev <= 0:
        raise ValueError("La desviación estándar debe ser positiva")

    random_numbers = np.random.normal(loc=mean, scale=std_dev, size=sample_size)
    random_numbers = ((random_numbers - np.min(random_numbers)) /
                      (np.max(random_numbers) - np.min(random_numbers))) * 0.9999
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def calculate_histogram(data, num_bins):
    """
    Calcula el histograma de frecuencias para los datos proporcionados.

    Args:
        data (list): Lista de números para los que calcular el histograma
        num_bins (int): Número de intervalos para el histograma

    Returns:
        dict: Diccionario con los datos del histograma
    """
    # Validar el número de intervalos
    if num_bins not in [10, 15, 20, 25]:
        raise ValueError("El número de intervalos debe ser 10, 15, 20 o 25")

    # Convertir a numpy array para facilitar los cálculos
    data_array = np.array(data)

    # Calcular el histograma
    hist, bin_edges = np.histogram(data_array, bins=num_bins)

    # Construir la tabla de frecuencias
    frequency_table = []
    for i in range(len(hist)):
        interval_start = bin_edges[i]
        interval_end = bin_edges[i + 1]
        frequency = int(hist[i])  # Convertir a int para evitar problemas de serialización JSON

        frequency_table.append({
            "interval": f"[{interval_start:.4f}, {interval_end:.4f})",
            "frequency": frequency,
            "relative_frequency": float(frequency / len(data_array)),
            "lower_bound": float(interval_start),
            "upper_bound": float(interval_end)  # preguntar restar infinitesimo
        })

    return {
        "frequency_table": frequency_table,
        "bin_edges": bin_edges.tolist(),
        "frequencies": hist.tolist(),
        "sample_size": len(data_array)
    }
