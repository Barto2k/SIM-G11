import { useState } from 'react';
import { LineChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Bar, BarChart } from 'recharts';
import GoodnessTestInterface from './GoodnessTestInterface.jsx';


const API_URL = 'http://localhost:5000/api';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [distribution, setDistribution] = useState('uniform');
  const [sampleSize, setSampleSize] = useState(1000);
  const [uniformParams, setUniformParams] = useState({ a: 0, b: 1 });
  const [exponentialParams, setExponentialParams] = useState({ lambda: 1 });
  const [normalParams, setNormalParams] = useState({ mean: 0, stdDev: 1 });
  const [numBins, setNumBins] = useState(10);
  const [randomNumbers, setRandomNumbers] = useState([]);
  const [histogramData, setHistogramData] = useState(null);
  const [goodnessTest, setGoodnessTest] = useState('chi-square');
  const [testResults, setTestResults] = useState(null);

  const handleGenerateNumbers = async () => {
    try {
      setLoading(true);
      setError(null);
      setTestResults(null);

      let requestParams = {
        distribution,
        sample_size: sampleSize
      };

      switch (distribution) {
        case 'uniform':
          requestParams = { ...requestParams, ...uniformParams };
          break;
        case 'exponential':
          requestParams = { ...requestParams, lambda: exponentialParams.lambda };
          break;
        case 'normal':
          requestParams = {
            ...requestParams,
            mean: normalParams.mean,
            std_dev: normalParams.stdDev
          };
          break;
        default:
          break;
      }

      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestParams),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al generar los números aleatorios');
      }

      setRandomNumbers(data.random_numbers);
      await calculateHistogram(data.random_numbers);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateHistogram = async (numbers) => {
    if (!numbers || numbers.length === 0) {
      setError('No hay números para calcular el histograma');
      return;
    }
    try {
      const response = await fetch(`${API_URL}/histogram`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          random_numbers: numbers,
          num_bins: numBins
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al calcular el histograma');
      }

      setHistogramData(data);

    } catch (err) {
      setError(err.message);
    }
  };

  const currentParams =
  distribution === 'uniform'
    ? uniformParams
    : distribution === 'exponential'
    ? exponentialParams
    : distribution === 'normal'
    ? normalParams
    : {};

  const performGoodnessTest = async () => {
    if (!randomNumbers || randomNumbers.length === 0) {
      setError('No hay números generados para realizar la prueba');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let endpoint = '';
      if (goodnessTest === 'chi-square') {
        endpoint = '/chi-square-test';
      } else if (goodnessTest === 'ks') {
        endpoint = '/ks-test';
      }

      let requestParams = {
        random_numbers: randomNumbers,
        distribution: distribution,
        num_bins: numBins
      };

      // Agregar parámetros según la distribución
      switch (distribution) {
        case 'uniform':
          requestParams = { ...requestParams, ...uniformParams };
          break;
        case 'exponential':
          requestParams = { ...requestParams, lambda: exponentialParams.lambda };
          break;
        case 'normal':
          requestParams = {
            ...requestParams,
            mean: normalParams.mean,
            std_dev: normalParams.stdDev
          };
          break;
        default:
          break;
      }

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestParams),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al realizar la prueba de bondad');
      }

      setTestResults(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8 flex items-center justify-center">
      <div className="max-w-6xl mx-auto bg-gray-50 p-8 rounded-2xl shadow-lg">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-800">
          Generador de Números Aleatorios
        </h1>

        <div className="bg-white p-8 rounded-2xl shadow-sm mb-8">
          <h2 className="text-xl font-semibold mb-6 text-gray-700">Configuración</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="relative mb-6">
                <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                  Distribución
                </label>
                <select
                  className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                  value={distribution}
                  onChange={(e) => setDistribution(e.target.value)}
                >
                  <option value="uniform">Uniforme</option>
                  <option value="exponential">Exponencial</option>
                  <option value="normal">Normal</option>
                </select>
              </div>

              <div className="relative mb-6">
                <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                  Tamaño de la muestra
                </label>
                <input
                  type="number"
                  placeholder="Tamaño de la muestra"
                  className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                  value={sampleSize}
                  onChange={(e) => setSampleSize(parseInt(e.target.value))}
                  min="1"
                  max="1000000"
                />
              </div>

              <div className="relative mb-6">
                <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                  Número de intervalos
                </label>
                <select
                  className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                  value={numBins}
                  onChange={(e) => setNumBins(parseInt(e.target.value))}
                >
                  <option value="10">10</option>
                  <option value="15">15</option>
                  <option value="20">20</option>
                  <option value="25">25</option>
                </select>
              </div>
            </div>

            <div>
              {distribution === 'uniform' && (
                <div>
                  <h3 className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                    Parámetros de la distribución uniforme
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="relative mb-6">
                      <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                        Valor mínimo (a)
                      </label>
                      <input
                        type="number"
                        className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                        value={uniformParams.a}
                        onChange={(e) => setUniformParams({ ...uniformParams, a: parseFloat(e.target.value) })}
                        step="0.01"
                      />
                    </div>
                    <div className="relative mb-6">
                      <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                        Valor máximo (b)
                      </label>
                      <input
                        type="number"
                        className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                        value={uniformParams.b}
                        onChange={(e) => setUniformParams({ ...uniformParams, b: parseFloat(e.target.value) })}
                        step="0.01"
                      />
                    </div>
                  </div>
                </div>
              )}

              {distribution === 'exponential' && (
                <div>
                  <h3 className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                    Parámetros de la distribución exponencial
                  </h3>
                  <div className="relative mb-6">
                    <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                      Lambda (λ)
                    </label>
                    <input
                      type="number"
                      className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                      value={exponentialParams.lambda}
                      onChange={(e) => setExponentialParams({ ...exponentialParams, lambda: parseFloat(e.target.value) })}
                      step="0.01"
                      min="0.01"
                    />
                  </div>
                </div>
              )}

              {distribution === 'normal' && (
                <div>
                  <h3 className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                    Parámetros de la distribución normal
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="relative mb-6">
                      <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                        Media (μ)
                      </label>
                      <input
                        type="number"
                        className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                        value={normalParams.mean}
                        onChange={(e) => setNormalParams({ ...normalParams, mean: parseFloat(e.target.value) })}
                        step="0.01"
                      />
                    </div>
                    <div className="relative mb-6">
                      <label className="flex items-center mb-2 text-gray-600 text-sm font-medium">
                        Desviación estándar (σ)
                      </label>
                      <input
                        type="number"
                        className="block w-full h-11 px-5 py-2.5 bg-white leading-7 text-base font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-full placeholder-gray-400 focus:outline-none"
                        value={normalParams.stdDev}
                        onChange={(e) => setNormalParams({ ...normalParams, stdDev: parseFloat(e.target.value) })}
                        step="0.01"
                        min="0.01"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 flex justify-center gap-4">
            <button
              className="w-52 h-12 bg-indigo-600 hover:bg-indigo-800 transition-all duration-300 rounded-full shadow-xs text-white text-base font-semibold leading-6 mb-2"
              onClick={() => {
                if (sampleSize <= 0) {
                  setError('El tamaño de la muestra debe ser mayor a 0.');
                  return;
                }
                if (distribution === 'exponential' && exponentialParams.lambda <= 0) {
                  setError('Lambda (λ) debe ser mayor a 0.');
                  return;
                }
                if (distribution === 'normal' && normalParams.stdDev <= 0) {
                  setError('La desviación estándar (σ) debe ser mayor a 0.');
                  return;
                }
                if (distribution === 'uniform' && uniformParams.a >= uniformParams.b) {
                  setError('El valor mínimo (a) no puede ser mayor o igual al valor máximo (b).');
                  return;
                }
                handleGenerateNumbers();
              }}
              disabled={loading}
            >
              {loading ? 'Generando...' : 'Generar números aleatorios'}
            </button>

            {randomNumbers.length > 0 && (
              <button
                className="w-52 h-12 bg-green-600 hover:bg-green-800 transition-all duration-300 rounded-full shadow-xs text-white text-base font-semibold leading-6 mb-2"
                onClick={performGoodnessTest}
                disabled={loading}
              >
                {loading ? 'Calculando...' : 'Realizar prueba de bondad'}
              </button>
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}
        </div>

        {randomNumbers.length > 0 && (
          <div className="bg-white p-8 rounded-2xl shadow-sm mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Números aleatorios generados</h2>
            <div className="max-h-40 overflow-y-auto overflow-x-auto border border-gray-200 p-4 rounded-lg">
              <p className="font-mono text-sm text-gray-600 break-words whitespace-normal">
                {randomNumbers.slice(0, 100).join(', ')}
                {randomNumbers.length > 100 && '...'}
              </p>
            </div>
            <p className="mt-4 text-sm text-gray-500">
              Se generaron {randomNumbers.length} números aleatorios.
              {randomNumbers.length > 100 && ' Se muestran los primeros 100.'}
            </p>
          </div>
        )}

        {histogramData && (
          <div className="bg-white p-8 rounded-2xl shadow-sm mb-8">
            <h2 className="text-xl font-semibold mb-6 text-gray-700">Histograma de frecuencias</h2>

            <div className="overflow-x-auto">
              <BarChart
                width={800}
                height={400}
                data={histogramData.frequency_table}
                margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="interval"
                  label={{ value: 'Intervalos', position: 'insideBottom', offset: -1, fill: '#6b7280' }}
                  tick={{ angle: -45, textAnchor: 'end', fontSize: 8, fill: '#6b7280', fontWeight: 'bold' }}
                  height={80}
                  ticks={histogramData.frequency_table.map((item) => item.interval)}
                  interval={0}
                  tickFormatter={(value) => value.replace(/,/g, ' - ')}
                />
                <YAxis
                  label={{ value: 'Frecuencia', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  formatter={(value) => [`${value} ocurrencias`, 'Frecuencia']}
                  contentStyle={{ borderRadius: '0.5rem', borderColor: '#e5e7eb' }}
                />
                <Legend />
                <Bar dataKey="frequency" fill="#818cf8" name="Frecuencia" radius={[4, 4, 0, 0]} />
              </BarChart>
            </div>

            <h3 className="text-lg font-semibold mt-8 mb-4 text-gray-700">Tabla de frecuencias</h3>
            <div className="max-h-60 overflow-y-auto overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full bg-white">
                <thead className="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <th className="py-3 px-4 border-b border-gray-200 text-left text-sm font-medium text-gray-600">Intervalo</th>
                    <th className="py-3 px-4 border-b border-gray-200 text-center text-sm font-medium text-gray-600">Frecuencia</th>
                    <th className="py-3 px-4 border-b border-gray-200 text-center text-sm font-medium text-gray-600">Frecuencia relativa</th>
                  </tr>
                </thead>
                <tbody>
                  {histogramData.frequency_table.map((item, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                      <td className="py-3 px-4 border-b border-gray-200 text-sm text-gray-600 break-words whitespace-normal">
                        {item.interval}
                      </td>
                      <td className="py-3 px-4 border-b border-gray-200 text-center text-sm text-gray-600">{item.frequency}</td>
                      <td className="py-3 px-4 border-b border-gray-200 text-center text-sm text-gray-600">
                        {(item.relative_frequency * 100).toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <GoodnessTestInterface
          randomNumbers={randomNumbers}
          distribution={distribution}
          distributionParams={currentParams}
        />
      </div>
    </div>
  );
}