from flask import Blueprint, request, jsonify
from backend.utils.generadorNumAleatorios import (
    generate_uniform,
    generate_exponential,
    generate_normal,
    calculate_histogram
)

api = Blueprint('api', __name__)


@api.route('/generate', methods=['POST'])
def generate_random_numbers():
    """
    Endpoint para generar números aleatorios según la distribución seleccionada.
    """
    try:
        # Obtener datos del request
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        distribution = data.get('distribution')
        sample_size = int(data.get('sample_size', 0))

        # Validar que el tamaño de muestra sea válido
        if sample_size <= 0 or sample_size > 1000000:
            return jsonify({"error": "El tamaño de muestra debe estar entre 1 y 1.000.000"}), 400

        # Generar números aleatorios según la distribución
        if distribution == 'uniform':
            a = float(data.get('a', 0))
            b = float(data.get('b', 1))

            if a >= b:
                return jsonify({"error": "El límite inferior debe ser menor que el límite superior"}), 400

            random_numbers = generate_uniform(sample_size, a, b)

        elif distribution == 'exponential':
            lambd = float(data.get('lambda', 1))

            if lambd <= 0:
                return jsonify({"error": "El parámetro lambda debe ser positivo"}), 400

            random_numbers = generate_exponential(sample_size, lambd)

        elif distribution == 'normal':
            mean = float(data.get('mean', 0))
            std_dev = float(data.get('std_dev', 1))

            if std_dev <= 0:
                return jsonify({"error": "La desviación estándar debe ser positiva"}), 400

            random_numbers = generate_normal(sample_size, mean, std_dev)

        else:
            return jsonify({"error": "Distribución no válida"}), 400

        # Devolver los números generados
        return jsonify({
            "random_numbers": random_numbers,
            "sample_size": sample_size,
            "distribution": distribution
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/histogram', methods=['POST'])
def calculate_histogram_route():
    """
    Endpoint para calcular el histograma de frecuencias para los datos proporcionados.
    """
    try:
        # Obtener datos del request
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        random_numbers = data.get('random_numbers')
        num_bins = int(data.get('num_bins', 10))

        # Validar que haya datos
        if not random_numbers or len(random_numbers) == 0:
            return jsonify({"error": "No se proporcionaron datos para el histograma"}), 400

        # Validar que el número de intervalos sea válido
        if num_bins not in [10, 15, 20, 25]:
            return jsonify({"error": "El número de intervalos debe ser 10, 15, 20 o 25"}), 400

        # Calcular el histograma
        histogram_data = calculate_histogram(random_numbers, num_bins)

        return jsonify(histogram_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
