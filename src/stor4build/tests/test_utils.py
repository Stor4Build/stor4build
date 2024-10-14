# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build

def test_vintage_lookup():
    assert '2010' == stor4build.map_to_vintage(2010)
