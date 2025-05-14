import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api'; // Cambia esto si tu backend está en otro puerto o dominio

const GoodnessTestInterface = ({ randomNumbers, distribution, distributionParams }) => {
  const [goodnessTest, setGoodnessTest] = useState('chi');
  const [testResults, setTestResults] = useState(null);
  const [testParams, setTestParams] = useState({ num_bins: 10 });
  const [error, setError] = useState('');

  const handleRunTest = async () => {
    try {
      const endpoint = goodnessTest === 'chi'
        ? `${API_URL}/chi-square-test`
        : `${API_URL}/ks-test`; // Usa la URL completa del backend

      const response = await axios.post(endpoint, {
        random_numbers: randomNumbers,
        distribution: distribution,
        ...distributionParams,
        ...testParams
      });

      setTestResults(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Error al ejecutar la prueba');
    }
  };

  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">
        Pruebas de Bondad de Ajuste
      </h2>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setGoodnessTest('chi')}
          className={`px-4 py-2 rounded ${goodnessTest === 'chi'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700'}`}
        >
          Chi-cuadrado
        </button>

        <button
          onClick={() => setGoodnessTest('ks')}
          className={`px-4 py-2 rounded ${goodnessTest === 'ks'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700'}`}
        >
          Kolmogorov-Smirnov
        </button>
      </div>

      {goodnessTest === 'chi' && (
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">
            Número de intervalos:
            <select
              value={testParams.num_bins}
              onChange={(e) => setTestParams({ ...testParams, num_bins: parseInt(e.target.value) })}
              className="ml-2 p-1 border rounded"
            >
              {[10, 15, 20, 25].map((bins) => (
                <option key={bins} value={bins}>{bins}</option>
              ))}
            </select>
          </label>
        </div>
      )}

      <button
        onClick={handleRunTest}
        className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 mb-4"
      >
        Ejecutar Prueba
      </button>

      {error && <div className="text-red-600 mb-4">{error}</div>}

      {testResults && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-800">
            Resultados de la prueba {testResults.test_type}
          </h3>

          <div>
            <p className="text-gray-700">
              <strong>Valor de la estadística:</strong>{" "}
              {goodnessTest === 'chi' ? testResults.chi_square_stat : testResults.ks_stat}
            </p>
            <p className="text-gray-700">
              <strong>Valor crítico:</strong> {testResults.critical_value}
            </p>
            <p className="text-gray-700">
              <strong>p-valor:</strong> {testResults.p_value}
            </p>
            <p className={`text-gray-700 ${testResults.decision === 'No se rechaza H0' ? 'text-green-600' : 'text-red-600'}`}>
              <strong>Resultado:</strong> {testResults.conclusion}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GoodnessTestInterface;