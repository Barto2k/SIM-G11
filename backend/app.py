from flask import Flask, jsonify
from flask_cors import CORS
from backend.api.routes import api

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde el frontend

# Registrar el blueprint de la API
app.register_blueprint(api, url_prefix='/api')


@app.route('/', methods=['GET'])
def index():
    """
    Endpoint raíz para verificar que la aplicación esté funcionando.
    """
    return jsonify({
        "message": "API de generación de números aleatorios",
        "endpoints": {
            "/api/generate": "POST - Genera números aleatorios según la distribución seleccionada",
            "/api/histogram": "POST - Calcula el histograma de frecuencias para los datos proporcionados"
        }
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
