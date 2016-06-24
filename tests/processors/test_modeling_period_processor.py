from datetime import datetime
import pytz

from eemeter.processors.interventions import get_modeling_period_set
from eemeter.structures import Intervention
from eemeter.processors.collector import LogCollector


def test_empty():
    lc = LogCollector()

    with lc.collect_logs("modeling_period_set") as logger:
        mps = get_modeling_period_set(logger, [])
    assert mps is None

    logs = lc.items["modeling_period_set"].splitlines()
    assert "INFO - No interventions, so no modeling period set" in logs[0]


def test_basic_usage():
    start_date = datetime(2000, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(2001, 1, 1, tzinfo=pytz.UTC)
    interventions = [Intervention(start_date, end_date)]

    lc = LogCollector()

    with lc.collect_logs("modeling_period_set") as logger:
        mps = get_modeling_period_set(logger, interventions)

    groups = list(mps.get_modeling_period_groups())
    assert len(groups) == 1
    assert groups[0][0][0] == 'baseline'
    assert groups[0][0][1].start_date is None
    assert groups[0][0][1].end_date is start_date
    assert groups[0][1][0] == 'reporting'
    assert groups[0][1][1].start_date is end_date
    assert groups[0][1][1].end_date is None

    modeling_periods = list(mps.get_modeling_periods())
    assert len(modeling_periods) == 2

    logs = lc.items["modeling_period_set"].splitlines()
    assert "INFO - Created one modeling period group." in logs[0]
