# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import  stor4build

int_schedule = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1]
too_early_int_schedule = [3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]
too_late_int_schedule = [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3]

def test_process_int_schedule():
    results = stor4build.process_energy_schedule(int_schedule)
    assert len(results) == 4
    assert results[0] == '18:00'
    assert results[1] == '11:00'
    assert results[2] == '12:00'
    assert results[3] == '17:00'
    results = stor4build.process_energy_schedule(too_early_int_schedule)
    assert len(results) == 4
    assert results[0] == '07:00'
    assert results[1] == '24:00'
    assert results[2] == '01:00'
    assert results[3] == '06:00'
    results = stor4build.process_energy_schedule(too_late_int_schedule)
    assert len(results) == 4
    assert results[0] == '01:00'
    assert results[1] == '18:00'
    assert results[2] == '19:00'
    assert results[3] == '24:00'

