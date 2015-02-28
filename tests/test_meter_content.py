from eemeter.config.yaml_parser import load
from eemeter.consumption import ConsumptionHistory
from fixtures.consumption import consumption_history_1
from fixtures.weather import gsod_722880_2012_2014_weather_source
from fixtures.weather import tmy3_722880_weather_source

import pytest

from datetime import datetime

from helpers import arrays_similar
from numpy.testing import assert_almost_equal

EPSILON = 1e-5

@pytest.mark.slow
def test_temperature_sensitivity_parameter_optimization(
        consumption_history_1,gsod_722880_2012_2014_weather_source):

    meter_yaml = """
        !obj:eemeter.meter.TemperatureSensitivityParameterOptimizationMeter {
            fuel_unit_str: "kWh",
            fuel_type: "electricity",
            temperature_unit_str: "degF",
            model: !obj:eemeter.models.HDDCDDBalancePointModel {
                x0: [1.,1.,1.,60.,7.],
                bounds: [[0,200],[0,200],[0,2000],[55,65],[2,12]],
            }
        }
        """
    meter = load(meter_yaml)

    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source)

    assert_almost_equal(result['temp_sensitivity_params'],
            [  0.39869173,   1.05457994,   8.61849954,  65.,   4.96891554])

@pytest.mark.slow
def test_weather_normalization(consumption_history_1,
                               gsod_722880_2012_2014_weather_source,
                               tmy3_722880_weather_source):

    meter_yaml = """
        !obj:eemeter.meter.SequentialMeter {
            sequence: [
                !obj:eemeter.meter.TemperatureSensitivityParameterOptimizationMeter {
                    fuel_unit_str: "kWh",
                    fuel_type: "electricity",
                    temperature_unit_str: "degF",
                    model: !obj:eemeter.models.HDDCDDBalancePointModel &model {
                        x0: [1.,1.,1.,60.,7.],
                        bounds: [[0,200],[0,200],[0,2000],[55,65],[2,12]],
                    }
                },
                !obj:eemeter.meter.AnnualizedUsageMeter {
                    temperature_unit_str: "degF",
                    model: *model
                }
            ]
        }
        """
    meter = load(meter_yaml)

    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source,
                            weather_normal_source=tmy3_722880_weather_source)

    assert_almost_equal(result['temp_sensitivity_params'],
            [  0.39869173,   1.05457994,   8.61849954,  65.        ,   4.96891554])

    assert abs(result['annualized_usage'] - 4433.4780966742328) < EPSILON

@pytest.mark.slow
def test_pre_post_parameters(consumption_history_1,
                             gsod_722880_2012_2014_weather_source):

    meter_yaml = """
        !obj:eemeter.meter.PrePostMeter {
            splittable_args: ["consumption_history"],
            meter: !obj:eemeter.meter.TemperatureSensitivityParameterOptimizationMeter {
                fuel_unit_str: "kWh",
                fuel_type: "electricity",
                temperature_unit_str: "degF",
                model: !obj:eemeter.models.HDDCDDBalancePointModel {
                    x0: [1.,1.,1.,60.,7.],
                    bounds: [[0,200],[0,200],[0,2000],[55,65],[2,12]],
                }
            },
        }
        """
    meter = load(meter_yaml)

    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source,
                            retrofit_start_date=datetime(2013,9,25),
                            retrofit_end_date=datetime(2013,9,25))

    assert_almost_equal(result['temp_sensitivity_params_pre'],
            [0.57594211, 1.49516273, 5.7084898, 65., 3.6])
    assert_almost_equal(result['temp_sensitivity_params_post'],
            [  0.87413646,   0.26644479,   9.68123769,  62.70000006,   2.00000025])

    assert isinstance(result["consumption_history_pre"],ConsumptionHistory)
    assert isinstance(result["consumption_history_post"],ConsumptionHistory)

@pytest.mark.slow
def test_gross_savings_metric(consumption_history_1,
                              gsod_722880_2012_2014_weather_source):

    meter_yaml = """
        !obj:eemeter.meter.SequentialMeter {
            sequence: [
                !obj:eemeter.meter.PrePostMeter {
                    splittable_args: ["consumption_history"],
                    meter: !obj:eemeter.meter.TemperatureSensitivityParameterOptimizationMeter {
                        fuel_unit_str: "kWh",
                        fuel_type: "electricity",
                        temperature_unit_str: "degF",
                        model: !obj:eemeter.models.HDDCDDBalancePointModel &model {
                            x0: [1.,1.,1.,60.,7.],
                            bounds: [[0,200],[0,200],[0,2000],[55,65],[2,12]],
                        }
                    },
                },
                !obj:eemeter.meter.GrossSavingsMeter {
                    fuel_unit_str: "kWh",
                    fuel_type: "electricity",
                    temperature_unit_str: "degF",
                    model: *model,
                }
            ]
        }
        """
    meter = load(meter_yaml)

    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source,
                            retrofit_start_date=datetime(2013,9,25),
                            retrofit_end_date=datetime(2013,9,25))

    assert_almost_equal(result['temp_sensitivity_params_pre'],
            [0.57594211, 1.49516273,  5.7084898 ,  65.,   3.6])
    assert_almost_equal(result['temp_sensitivity_params_post'],
            [  0.87413646,   0.26644479,   9.68123769,  62.70000006,   2.00000025])

    assert isinstance(result["consumption_history_pre"],ConsumptionHistory)
    assert isinstance(result["consumption_history_post"],ConsumptionHistory)
    assert abs(result["gross_savings"] - -117118.12044707313) < EPSILON

@pytest.mark.slow
def test_annualized_gross_savings_metric(consumption_history_1,
                                         gsod_722880_2012_2014_weather_source,
                                         tmy3_722880_weather_source):

    meter_yaml = """
        !obj:eemeter.meter.SequentialMeter {
            sequence: [
                !obj:eemeter.meter.PrePostMeter {
                    splittable_args: ["consumption_history"],
                    meter: !obj:eemeter.meter.TemperatureSensitivityParameterOptimizationMeter {
                        fuel_unit_str: "kWh",
                        fuel_type: "electricity",
                        temperature_unit_str: "degF",
                        model: !obj:eemeter.models.HDDCDDBalancePointModel &model {
                            x0: [1.,1.,1.,60.,7.],
                            bounds: [[0,200],[0,200],[0,2000],[55,65],[2,12]],
                        }
                    },
                },
                !obj:eemeter.meter.AnnualizedGrossSavingsMeter {
                    fuel_type: "electricity",
                    temperature_unit_str: "degF",
                    model: *model,
                }
            ]
        }
        """
    meter = load(meter_yaml)

    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source,
                            weather_normal_source=tmy3_722880_weather_source,
                            retrofit_start_date=datetime(2013,9,25),
                            retrofit_end_date=datetime(2013,9,25))

    assert_almost_equal(result['temp_sensitivity_params_pre'],
            [0.57594211, 1.49516273, 5.7084898 , 65., 3.6])
    assert_almost_equal(result['temp_sensitivity_params_post'],
            [0.87413646, 0.26644479, 9.68123769, 62.70000006, 2.00000025])

    assert abs(result["annualized_gross_savings"] - -688.27346615653278) < EPSILON

def test_fuel_type_presence_meter(consumption_history_1):

    meter_yaml = """
        !obj:eemeter.meter.FuelTypePresenceMeter {
            fuel_types: [electricity,natural_gas]
        }
        """
    meter = load(meter_yaml)
    result = meter.evaluate(consumption_history=consumption_history_1)

    assert result["electricity_presence"]
    assert not result["natural_gas_presence"]

@pytest.mark.slow
def test_princeton_scorekeeping_method(consumption_history_1,
                                       gsod_722880_2012_2014_weather_source,
                                       tmy3_722880_weather_source):
    meter = load("!obj:eemeter.meter.PRISMMeter {}")
    result = meter.evaluate(consumption_history=consumption_history_1,
                            weather_source=gsod_722880_2012_2014_weather_source,
                            weather_normal_source=tmy3_722880_weather_source)

    assert result.get("electricity_presence")
    assert_almost_equal(result.get("temp_sensitivity_params_electricity"),
            [0.44667569,0.96903377,8.26148838,65.,4.10000001])
    assert_almost_equal(result.get("annualized_usage_electricity"),4411.3924204)
    assert_almost_equal(result.get("daily_standard_error_electricity"),14.1469073)

    assert not result.get("natural_gas_presence")
    assert result.get("temp_sensitivity_params_natural_gas") is None
    assert result.get("annualized_usage_natural_gas") is None
    assert result.get("daily_standard_error_natural_gas") is None

