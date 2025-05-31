# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import json

# Make some assumptions
#this_dir = os.path.abspath(os.path.dirname(__file__))
#results_dir = os.path.join(this_dir, '..', 'resources', 'LargeOfficeCSV')
    
def test_step():
    step = s4b.Step("Add CSV Output", "add_csv_output")
    assert step.name == "Add CSV Output"
    assert step.measure_dir_name == "add_csv_output"
    assert len(step.arguments) == 0
    data = {'steps': [step]}
    result = json.dumps(data, cls=s4b.DataclassJSONEncoder)
    assert result == '{"steps": [{"name": "Add CSV Output", "measure_dir_name": "add_csv_output", "arguments": {}}]}'

def test_vintage_lookup():
    assert 'pre1980' == s4b.map_to_vintage(1977)
    assert 'pre1980' == s4b.map_to_vintage(1978)
    assert 'pre1980' == s4b.map_to_vintage(1979)
    assert 'post1980' == s4b.map_to_vintage(1980)
    assert 'post1980' == s4b.map_to_vintage(1981)
    assert 'post1980' == s4b.map_to_vintage(1982)
    assert 'post1980' == s4b.map_to_vintage(2001)
    assert 'post1980' == s4b.map_to_vintage(2002)
    assert 'post1980' == s4b.map_to_vintage(2003)
    assert '2004' == s4b.map_to_vintage(2004)
    assert '2004' == s4b.map_to_vintage(2005)
    assert '2004' == s4b.map_to_vintage(2006)
    assert '2007' == s4b.map_to_vintage(2007)
    assert '2007' == s4b.map_to_vintage(2008)
    assert '2007' == s4b.map_to_vintage(2009)
    assert '2010' == s4b.map_to_vintage(2010)
    assert '2010' == s4b.map_to_vintage(2011)
    assert '2010' == s4b.map_to_vintage(2012)
    assert '2013' == s4b.map_to_vintage(2013)
    assert '2013' == s4b.map_to_vintage(2014)
    assert '2013' == s4b.map_to_vintage(2015)
    assert '2016' == s4b.map_to_vintage(2016)
    assert '2016' == s4b.map_to_vintage(2017)
    assert '2016' == s4b.map_to_vintage(2018)
    assert '2019' == s4b.map_to_vintage(2019)
    assert '2019' == s4b.map_to_vintage(2020)
    assert '2019' == s4b.map_to_vintage(2021)
    assert '2019' == s4b.map_to_vintage(2022)
    assert '2019' == s4b.map_to_vintage(2023)
    assert '2019' == s4b.map_to_vintage(2024)
