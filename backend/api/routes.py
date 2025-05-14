from flask import Blueprint, request, jsonify
from backend.utils.generadorNumAleatorios import (
    generate_uniform,
    generate_exponential,
    generate_normal,
    calculate_histogram,
    chi_square_test,
    kolmogorov_smirnov_test
)

api = Blueprint('api', __name__)

@api.route('/generate', methods=['POST'])
def generate_random_numbers():
    """
    Endpoint para generar números aleatorios según la distribución seleccionada.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        distribution = data.get('distribution')
        sample_size = data.get('sample_size')

        if not isinstance(sample_size, int) or sample_size <= 0 or sample_size > 1000000:
            return jsonify({"error": "El tamaño de muestra debe ser un entero entre 1 y 1.000.000"}), 400

        if distribution == 'uniform':
            a = data.get('a', 0)
            b = data.get('b', 1)

            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or a >= b:
                return jsonify({"error": "El límite inferior debe ser menor que el límite superior"}), 400

            random_numbers = generate_uniform(sample_size, a, b)

        elif distribution == 'exponential':
            lambd = data.get('lambda', 1)

            if not isinstance(lambd, (int, float)) or lambd <= 0:
                return jsonify({"error": "El parámetro lambda debe ser un número positivo"}), 400

            random_numbers = generate_exponential(sample_size, lambd)

        elif distribution == 'normal':
            mean = data.get('mean', 0)
            std_dev = data.get('std_dev', 1)

            if not isinstance(mean, (int, float)) or not isinstance(std_dev, (int, float)) or std_dev <= 0:
                return jsonify({"error": "La media debe ser un número y la desviación estándar debe ser positiva"}), 400

            random_numbers = generate_normal(sample_size, mean, std_dev)

        else:
            return jsonify({"error": "Distribución no válida"}), 400

        return jsonify({
            "random_numbers": random_numbers,
            "sample_size": sample_size,
            "distribution": distribution
        })

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@api.route('/histogram', methods=['POST'])
def calculate_histogram_route():
    """
    Endpoint para calcular el histograma de frecuencias para los datos proporcionados.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        random_numbers = data.get('random_numbers')
        num_bins = data.get('num_bins', 10)

        if not isinstance(random_numbers, list) or len(random_numbers) == 0:
            return jsonify({"error": "No se proporcionaron datos válidos para el histograma"}), 400

        if not isinstance(num_bins, int) or num_bins not in [10, 15, 20, 25]:
            return jsonify({"error": "El número de intervalos debe ser 10, 15, 20 o 25"}), 400

        histogram_data = calculate_histogram(random_numbers, num_bins)

        return jsonify(histogram_data)

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@api.route('/chi-square-test', methods=['POST'])
def chi_square_test_route():
    """
    Endpoint para realizar la prueba de bondad de ajuste Chi-cuadrado.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        random_numbers = data.get('random_numbers')
        distribution = data.get('distribution')
        num_bins = data.get('num_bins', 10)

        if not isinstance(random_numbers, list) or len(random_numbers) == 0:
            return jsonify({"error": "No se proporcionaron datos válidos para la prueba"}), 400

        if not isinstance(num_bins, int) or num_bins not in [10, 15, 20, 25]:
            return jsonify({"error": "El número de intervalos debe ser 10, 15, 20 o 25"}), 400

        params = {}
        if distribution == 'uniform':
            params = {'a': data.get('a', 0), 'b': data.get('b', 1)}
        elif distribution == 'exponential':
            params = {'lambda': data.get('lambda', 1)}
        elif distribution == 'normal':
            params = {'mean': data.get('mean', 0), 'std_dev': data.get('std_dev', 1)}
        else:
            return jsonify({"error": "Distribución no válida"}), 400

        test_results = chi_square_test(random_numbers, distribution, params, num_bins)

        return jsonify(test_results)

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@api.route('/ks-test', methods=['POST'])
def kolmogorov_smirnov_test_route():
    """
    Endpoint para realizar la prueba de bondad de ajuste Kolmogorov-Smirnov.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        random_numbers = data.get('random_numbers')
        distribution = data.get('distribution')

        if not isinstance(random_numbers, list) or len(random_numbers) == 0:
            return jsonify({"error": "No se proporcionaron datos válidos para la prueba"}), 400

        params = {}
        if distribution == 'uniform':
            params = {'a': data.get('a', 0), 'b': data.get('b', 1)}
        elif distribution == 'exponential':
            params = {'lambda': data.get('lambda', 1)}
        elif distribution == 'normal':
            params = {'mean': data.get('mean', 0), 'std_dev': data.get('std_dev', 1)}
        else:
            return jsonify({"error": "Distribución no válida"}), 400

        test_results = kolmogorov_smirnov_test(random_numbers, distribution, params)

        return jsonify(test_results)

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500