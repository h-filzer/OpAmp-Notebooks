
import time
import sympy as sp
from sympy import solve, symbols, Rational,  Eq,  N
from enum import Enum
from decimal import Decimal


class ESeries:
    """Calculates a preferred resistor or cap for a given value """
    class Series(Enum):
        E24 = 24
        E48 = 48
        E96 = 96

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, series: Series):
        self.series = series

    # e24 and smaller series has rounding errors between 2.7 and 4.7, so we provide it statically
    e24_series = [1.00, 1.10, 1.20, 1.30, 1.50, 1.60, 1.80, 2.00, 2.20, 2.40, 2.70,
                  3.00, 3.30, 3.60, 3.90, 4.30, 4.70, 5.10, 5.60, 6.20, 6.80, 7.50, 8.20, 9.10]

    e96_series = []

    def calculate_series(self, series: Series):
        series_values = []
        e_series = (series.value)
        series_constant = pow(10, (1/e_series))
        for series_element in range(e_series):
            series_values.append(
                round(pow(series_constant, series_element), 2)
            )
        return series_values

    def preferred_value(self, r_value: float) -> tuple[float, float]:
        e_series = Rational(self.series.value)
        series_constant = sp.Pow(10, (1/e_series))
        # Normalize R to the Series and get multiplier
        multiplier = sp.floor(sp.log(r_value, 10))
        series_val = r_value/sp.Pow(10, multiplier)
        # print(f"SeriesVal {series_val}")
        # Find position in series
        series_element = symbols('series_element', real=True)
        series_element_eq = solve(Eq(series_val, sp.Pow(
            series_constant, series_element)), [series_element])[0].round()
        # resistor value in series
        r_series = 0
        if self.series == ESeries.Series.E24:
            r_series = self.e24_series[series_element_eq] * \
                sp.Pow(10, multiplier)
        else:
            r_series = N(sp.Pow(series_constant, (series_element_eq).round())).round(
                2)*sp.Pow(10, multiplier)
       # print(Decimal(repr(r_series))-Decimal(repr(r_value)))
        error = (100*(sp.Abs(Decimal(repr(r_series)) -
                 Decimal(repr(r_value))))/Decimal(repr(r_value))).round(2)
        return (r_series, error)

    def voltage_divider(self, vin: float, vout: float, scale: float = 10000, series: Series = Series.E96, include_e24: bool = True):
        start = time.time()
        v_ratio = (vin/vout)
        ratio_series = []
        series_elements = self.calculate_series(series)
        # print(series_elements[:10])
        series_elements_fraction: list = list(
            map(lambda x: round(x*0.1, 3), series_elements))
        series_elements_fraction.extend(series_elements)
        series_elements_fraction.extend(
            list(
                map(lambda x: round(x * 10, 3), series_elements)))
        for series_element_fraction in series_elements_fraction:
            for series_element in series_elements:
                current_r_ratio = 1 + \
                    series_element / series_element_fraction
                ratio_difference = abs(v_ratio - current_r_ratio)
                ratio_series.append(
                    (ratio_difference, (series_element * scale, series_element_fraction * scale)))
        ratio_series.sort(key=lambda a: a[0])
        stop = time.time()
        #print(f"Took {(stop-start)} Seconds")
        # print(ratio_series[:100])
        return (ratio_series[0][1][0], ratio_series[0][1][1])


if __name__ == '__main__':
    x = ESeries(ESeries.Series.E48)
    # print(x.calculate_series(ESeries.Series.E96))
    # start = time.time()
    # print(x.voltage_divider(10, 2.381, series=ESeries.Series.E48))
    # stop = time.time()
    # print(stop-start)
