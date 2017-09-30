import pytest
from query_raw.query_raw import *
from query_raw.test import test_data

def test_lst_lens_equal():
    with pytest.raises(RuntimeError):
        check_lens_equal([1, 2, 3], [1, 2, 3, 4])

def test_nested_lst_lens_equal():
    with pytest.raises(RuntimeError):
        check_nested_lens_equal(
            [[1], [2], [3, 4]],
            [[1], [2], [3, 4, 5]]
        )

def test_flatten():
    assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    assert flatten([[1, 2, [3, 4]]]) == [1, 2, [3, 4]]
    assert flatten([[1, 2], []]) == [1, 2]
    assert flatten([]) == []

def test_zip_nested():
    assert zip_nested([['a', 'b']], [['y', 'z']]) == (
        [[('a', 'y'), ('b', 'z')]]
    )
    assert zip_nested([['a', 'b'], ['c', 'd']], [['w', 'x'], ['y', 'z']]) == (
        [[('a', 'w'), ('b', 'x')], [('c', 'y'), ('d', 'z')]]
    )

def test_concat_fields():
    assert concat([[['a', 'b']]]) == ['a', 'b']
    assert concat([[['a', 'b']], [['y', 'z']], [['s', 't']]]) == (
        ['a,y,s', 'b,z,t']
    )

def test_parse_msgs():
    assert parse_msgs('DG1.6', test_data.msgs) == test_data.DG_1_6

def test_parse_msg_ids():
    assert parse_msg_id(['PID.3.4', 'PID.3.1', 'PID.18.1'], test_data.msgs) == (
        test_data.msg_ids
    )

    # field w/ multiple segments and therefore multiple values
    with pytest.raises(RuntimeError):
        parse_msg_id(['AL1.1.1'], test_data.msg_ids)

    non_unique_msg_ids = test_data.msgs + [test_data.msgs[0]]
    with pytest.raises(RuntimeError):
        parse_msg_id(['PID.3.4', 'PID.3.1', 'PID.18.1'], non_unique_msg_ids)


def test_parse_field_txt():
    field_d2 = parse_field_txt('PR1.3')
    assert field_d2['depth'] == 2
    assert field_d2['seg'] == 'PR1'
    assert field_d2['comp'] == 3

    field_d3 = parse_field_txt('DG1.3.1')
    assert field_d3['depth'] == 3
    assert field_d3['seg'] == 'DG1'
    assert field_d3['comp'] == 3
    assert field_d3['subcomp'] == 0

    msh_d3 = parse_field_txt('MSH.3.1')
    assert msh_d3['depth'] == 3
    assert msh_d3['seg'] == 'MSH'
    assert msh_d3['comp'] == 2
    assert msh_d3['subcomp'] == 0

    with pytest.raises(ValueError):
        parse_field_txt('DG1')
    with pytest.raises(ValueError):
        parse_field_txt('DG1.2.3.4')

def test_main():
    df = main(
        ['PID.3.4', 'PID.3.1', 'PID.18.1'],
        ['DG1.3.1', 'DG1.3.2', 'DG1.6', 'DG1.15'],
        test_data.msgs
    )
    print('\n')
    print(df)

    with pytest.raises(RuntimeError):
        main(
            ['PID.3.4', 'PID.3.1', 'PID.18.1'],
            ['DG1.3.1', 'DG1.3.2', 'AL.15'],
            test_data.msgs
        )
