import numpy as np
import pandas as pd
import scipy.stats as stats


def generate_uniform(sample_size, a=0, b=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if a >= b:
        raise ValueError("El límite inferior debe ser menor que el límite superior")

    random_numbers = np.random.uniform(low=a, high=b, size=sample_size)
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def generate_exponential(sample_size, lambd=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if lambd <= 0:
        raise ValueError("El parámetro lambda debe ser positivo")

    random_numbers = np.random.exponential(scale=1 / lambd, size=sample_size)
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def generate_normal(sample_size, mean=0, std_dev=1):
    if sample_size <= 0 or sample_size > 1000000:
        raise ValueError("El tamaño de muestra debe estar entre 1 y 1.000.000")
    if std_dev <= 0:
        raise ValueError("La desviación estándar debe ser positiva")

    random_numbers = np.random.normal(loc=mean, scale=std_dev, size=sample_size)
    random_numbers = np.round(random_numbers, 4)
    return random_numbers.tolist()


def calculate_histogram(data, num_bins):
    if num_bins not in [10, 15, 20, 25]:
        raise ValueError("El número de intervalos debe ser 10, 15, 20 o 25")

    data_array = np.array(data)
    hist, bin_edges = np.histogram(data_array, bins=num_bins)

    frequency_table = []
    for i in range(len(hist)):
        interval_start = bin_edges[i]
        interval_end = bin_edges[i + 1]
        frequency = int(hist[i])

        frequency_table.append({
            "interval": f"[{interval_start:.4f}, {interval_end:.4f})",
            "frequency": frequency,
            "relative_frequency": float(frequency / len(data_array)),
            "lower_bound": float(interval_start),
            "upper_bound": float(interval_end)
        })

    return {
        "frequency_table": frequency_table,
        "bin_edges": bin_edges.tolist(),
        "frequencies": hist.tolist(),
        "sample_size": len(data_array)
    }


def chi_square_test(data, distribution, params=None, num_bins=10):
    data_array = np.array(data)
    n = len(data_array)

    if params is None:
        params = {}
    if distribution == 'normal':
        params['mean'] = params.get('mean', np.mean(data_array))
        params['std_dev'] = params.get('std_dev', np.std(data_array, ddof=1))
    elif distribution == 'exponential':
        params['lambda'] = params.get('lambda', 1 / np.mean(data_array))
    elif distribution == 'uniform':
        params['a'] = params.get('a', np.min(data_array))
        params['b'] = params.get('b', np.max(data_array))

    prob_bins = np.linspace(0, 1, num_bins + 1)
    if distribution == 'normal':
        bin_edges = stats.norm.ppf(prob_bins, loc=params['mean'], scale=params['std_dev'])
    elif distribution == 'exponential':
        bin_edges = stats.expon.ppf(prob_bins, scale=1 / params['lambda'])
    elif distribution == 'uniform':
        bin_edges = stats.uniform.ppf(prob_bins, loc=params['a'], scale=params['b'] - params['a'])

    bin_edges[0] = min(bin_edges[0], np.min(data_array))
    bin_edges[-1] = max(bin_edges[-1], np.max(data_array))

    hist, _ = np.histogram(data_array, bins=bin_edges)
    expected_freq = np.full(num_bins, n / num_bins)

    chi_squared_stat = np.sum((hist - expected_freq) ** 2 / expected_freq)

    if distribution == 'normal':
        dof = num_bins - 1 - 2
    elif distribution == 'exponential':
        dof = num_bins - 1 - 1
    elif distribution == 'uniform':
        dof = num_bins - 1 - 2

    dof = max(1, dof)

    p_value = 1 - stats.chi2.cdf(chi_squared_stat, dof)
    critical_value = stats.chi2.ppf(0.95, dof)
    decision = "No se rechaza H0" if chi_squared_stat <= critical_value else "Se rechaza H0"
    conclusion = "Los datos siguen la distribución teórica" if chi_squared_stat <= critical_value else "Los datos no siguen la distribución teórica"

    return {
        "test_type": "Chi-cuadrado",
        "distribution": distribution,
        "chi_square_stat": float(chi_squared_stat),
        "degrees_of_freedom": int(dof),
        "p_value": float(p_value),
        "critical_value": float(critical_value),
        "alpha": 0.05,
        "decision": decision,
        "conclusion": conclusion
    }


def kolmogorov_smirnov_test(data, distribution, params=None):
    data_array = np.array(data)

    if params is None:
        params = {}
    if distribution == 'normal':
        params['mean'] = params.get('mean', np.mean(data_array))
        params['std_dev'] = params.get('std_dev', np.std(data_array, ddof=1))
        d, p_value = stats.kstest(data_array, 'norm', args=(params['mean'], params['std_dev']))
    elif distribution == 'exponential':
        params['lambda'] = params.get('lambda', 1 / np.mean(data_array))
        d, p_value = stats.kstest(data_array, 'expon', args=(0, 1 / params['lambda']))
    elif distribution == 'uniform':
        params['a'] = params.get('a', np.min(data_array))
        params['b'] = params.get('b', np.max(data_array))
        d, p_value = stats.kstest(data_array, 'uniform', args=(params['a'], params['b'] - params['a']))

    n = len(data_array)
    critical_value = 1.36 / np.sqrt(n)
    decision = "No se rechaza H0" if d <= critical_value else "Se rechaza H0"
    conclusion = "Los datos siguen la distribución teórica" if d <= critical_value else "Los datos no siguen la distribución teórica"

    return {
        "test_type": "Kolmogorov-Smirnov",
        "distribution": distribution,
        "ks_stat": float(d),
        "critical_value": float(critical_value),
        "p_value": float(p_value),
        "alpha": 0.05,
        "decision": decision,
        "conclusion": conclusion
    }

muestra = generate_normal(1000, mean=0, std_dev=1)
print(kolmogorov_smirnov_test(muestra, 'normal'))
print(chi_square_test(muestra, 'normal', num_bins=10))
