# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b

def test_intervals():
    vec = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    
    start = '12:00'
    end = '18:00'
    i0, i1 = s4b.convert_string_time_interval(start, end)
    assert i0 == 12
    assert i1 == 18
    assert vec[i0:i1] == [12, 13, 14, 15, 16, 17]
    
    start = '18:00'
    end = '24:00'
    i0, i1 = s4b.convert_string_time_interval(start, end)
    assert i0 == 18
    assert i1 == 24
    assert vec[i0:i1] == [18, 19, 20, 21, 22, 23]
