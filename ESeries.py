
import time
import sympy as sp
from sympy import solve, symbols, Rational,  Eq,  N, S
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

    # e24 and smaller series has rounding errors between 2.7 and 4.7, so we provide it statically
    __e24_series = [S(1.00), S(1.10), S(1.20), S(1.30), S(1.50), S(1.60), S(1.80), S(2.00), S(2.20), S(2.40), S(2.70),
                    S(3.00), S(3.30), S(3.60), S(3.90), S(4.30), S(4.70), S(5.10), S(5.60), S(6.20), S(6.80), S(7.50), S(8.20), S(9.10)]

    def __voltage_divider_ratio(self, series_element_fraction, series_element): return (
        series_element / (series_element_fraction+series_element))

    def __gain_ratio(self, series_element_fraction, series_element): return (
        series_element_fraction / series_element)

    def __calculate_series(self, series: Series, include_e24: bool = False):
        if series == ESeries.Series.E24:
            return self.__e24_series
        series_values = []
        e_series = (series.value)
        series_constant = pow(10, (1/e_series))
        for series_element in range(e_series):
            series_values.append(
                round(pow(series_constant, series_element), 2)
            )
        if include_e24:
            set(series_values).union(self.__e24_series)
        return series_values

    def __calculate_series_fraction(self, series_elements: list):
        series_elements_fraction: list = list(
            map(lambda x: round(x*0.1, 3), series_elements))
        series_elements_fraction.extend(series_elements)
        series_elements_fraction.extend(
            list(
                map(lambda x: round(x * 10, 3), series_elements)))
        return series_elements_fraction

    def preferred_value(self, r_value: float, series: Series = Series.E96) -> tuple[float, float]:
        e_series = Rational(series.value)
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
        if series.value == ESeries.Series.E24.value:
            r_series = self.__e24_series[series_element_eq] * \
                sp.Pow(10, multiplier)
        else:
            r_series = N(sp.Pow(series_constant, (series_element_eq).round())).round(
                2)*sp.Pow(10, multiplier)
       # print(Decimal(repr(r_series))-Decimal(repr(r_value)))
        error = (100*(sp.Abs(Decimal(repr(r_series)) -
                 Decimal(repr(r_value))))/Decimal(repr(r_value))).round(2)
        return (r_series, error)

    def __resolve_resistor_pair(self, ratio: float, calculation, scale=100000, series: Series = Series.E96, include_e24: bool = True):
        multiplier = sp.floor(sp.log(scale, 10))
        ratio_series = []
        series_elements = self.__calculate_series(series, include_e24)
        series_elements_fraction = self.__calculate_series_fraction(
            series_elements)
        for series_element_fraction in series_elements_fraction:
            for series_element in series_elements:
                current_r_ratio = calculation(
                    series_element_fraction, series_element)
                ratio_difference = abs(ratio - current_r_ratio)
                ratio_series.append(
                    {
                        "r2": series_element * pow(10, multiplier),
                        "r1": series_element_fraction * pow(10, multiplier),
                        "ratio_difference": ratio_difference,
                    }
                )
        ratio_series.sort(key=lambda a: a['ratio_difference'])
        # print(ratio_series[:100])
        # (ratio_series[0][1][0], ratio_series[0][1][1], ratio_series[0])
        return ratio_series

    def voltage_divider(self, vin: float, vout: float, scale: float = 10000, series: Series = Series.E96, include_e24: bool = True):
        ratio = abs(vout/vin)
        if ratio <= 1/100:
            print("Ratio too high, resistor vales might not provide expected outcome")
        pairs = self.__resolve_resistor_pair(ratio=ratio, scale=scale,
                                             calculation=self.__voltage_divider_ratio, series=series, include_e24=include_e24)

        return pairs[0]

    def voltage_divider(self, ratio: float, scale: float = 10000, series: Series = Series.E96, include_e24: bool = True):
        if ratio <= 1/100:
            print("Ratio too high, resistor vales might not provide expected outcome")
        pairs = self.__resolve_resistor_pair(ratio=ratio, scale=scale,
                                             calculation=self.__voltage_divider_ratio, series=series, include_e24=include_e24)

        return pairs[0]

    def inverting_gain_resistors(self, gain: float, rf_min: float = 100000, series: Series = Series.E96, include_e24: bool = True):
        pairs = self.__resolve_resistor_pair(ratio=abs(gain), scale=rf_min,
                                             calculation=self.__gain_ratio, series=series, include_e24=include_e24)
        pairs = list(
            filter(lambda x: x['r2'] >= rf_min, pairs))
        pairs.sort(key=lambda a: a['r2'])
        chosen_divider = pairs[0]
        chosen_divider['rf'] = chosen_divider.pop('r1')
        chosen_divider['rg'] = chosen_divider.pop('r2')
        return chosen_divider


if __name__ == '__main__':
    x = ESeries()
    #print(x.voltage_divider(vin=10, vout=.101, series=ESeries.Series.E24))
   # print(x.calculate_gain_resistors(gain=-10/9, rf_min=40000, series=ESeries.Series.E24))

    # print(x.calculate_series(ESeries.Series.E96))
    # start = time.time()
    # print(x.voltage_divider(10, 2.381, series=ESeries.Series.E48))
    # stop = time.time()
    # print(stop-start)
