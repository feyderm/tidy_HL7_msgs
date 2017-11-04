'''
Helpers
'''

import re
import pandas as pd

def are_lens_equal(*lsts):
    ''' Are lengths equal?

    Parameters
    ----------
    *lsts : one or more lists

    Returns
    -------
    Boolean

    Examples
    -------
    >>> are_lens_equal([1, 2], [1, 2])
    True
    >>> are_lens_equal([1, 2], [1, 2, 3])
    False

    '''
    lens = [len(x) for x in lsts]
    return len(set(lens)) == 1

def are_nested_lens_equal(lst1, lst2):
    ''' Are the lengths of nested lists equal?

    Parameters
    ----------
    lst1 : list
    lst2 : list

    Returns
    -------
    Boolean

    Examples
    -------
    >>> are_nested_lens_equal(
    ...     [[1, 2], [1, 2], [1, 2]],
    ...     [[1, 2], [1, 2], [1, 2]]
    ... )
    True
    >>> are_nested_lens_equal(
    ...     [[1, 2], [1, 2], [1, 2]],
    ...     [[1, 2], [1, 2], [1, 2, 3]]
    ... )
    False
    '''
    assert are_lens_equal(lst1, lst2), "List lengths are not equal"
    len_lsts = range(len(lst1))
    return all([len(lst1[i]) == len(lst2[i]) for i in len_lsts]) is True

def are_segs_identical(locs):
    ''' Are all locations from the same segment?

    Parameters
    ----------
    locs : list(string)

    Returns
    -------
    Boolean

    Examples
    -------
    >>> are_segs_identical(['DG1.3.1', 'DG1.3.2', 'DG1.6'])
    True
    >>> are_segs_identical(['DG1.3.1', 'DG1.3.2', 'PID.3.4'])
    False

    '''
    segs = [re.match('\\w*', loc).group() for loc in locs]
    return len(set(segs)) == 1

def flatten(lst):
    ''' Flatten lists nested one level deep

    Parameters
    ----------
    lst : list(list)

    Returns
    -------
    List

    Examples
    -------
    >>> flatten([[1, 2], [3, 4], [5, 6]])
    [1, 2, 3, 4, 5, 6]

    >>> flatten([[1, 2], [3, 4], []])
    [1, 2, 3, 4]

    >>> flatten([[1, 2], [3, 4], [5, 6, [7, 8]]])
    [1, 2, 3, 4, 5, 6, [7, 8]]
    '''
    return [item for sublist in lst for item in sublist]

def zip_nested(lst1, lst2):
    ''' Zip nested lists of equal length

    Parameters
    ----------
    lst1 : list(string)
    lst2 : list(string)

    Returns
    -------
    List(list(tuple))

    Exampless
    --------
    >>> zip_nested([['a', 'b']], [['y', 'z']])
    [[('a', 'y'), ('b', 'z')]]

    >>> zip_nested([['a', 'b'],['c', 'd']], [['w', 'x'],['y', 'z']])
    [[('a', 'w'), ('b', 'x')], [('c', 'y'), ('d', 'z')]]
    '''
    assert are_nested_lens_equal(lst1, lst2), "Lengths of nested lists are not equal"
    return [list(zip(lst1[i], lst2[i])) for i in range(len(lst1))]

def concat(lsts):
    ''' Concatinate lists of strings

    Parameters
    ----------
    lsts : list(list(list(string)))

    Returns
    -------
    List(string)

    Examples
    --------
    >>> concat([[['a', 'y']], [['b', 'z']]])
    ['a,b', 'y,z']

    >>> concat([[['a', 'w']], [['b', 'x']], [['c', 'y']], [['d', 'z']]])
    ['a,b,c,d', 'w,x,y,z']
    '''
    lsts = [flatten(lst) for lst in lsts]

    lst_lens = [len(lst) for lst in lsts]
    assert len(set(lst_lens)) == 1, "Message ID fields are unequal length"

    concatted = []
    for i in range(len(lsts[0])):
        concatted.append([",".join(el[i] for el in lsts)])

    return flatten(concatted)

def zip_msg_ids(lst, msg_ids):
    ''' Zip message IDs of equal length

    Parameters
    ----------
    lst : list
    msg_ids : list(string)

    Returns
    -------
    List(tuple)
    '''
    assert are_lens_equal(msg_ids, lst), "List lengths are not equal"
    return list(zip(msg_ids, lst))

def to_df(lst, loc_txt):
    ''' Convert list of zipped values to dataframe

    Parameters
    ----------
    lst : list(tuple(string))

        List of tuples, where the first element is the message ID and the
        second element is a list of parsed values

    loc_txt : string

        Location text

    Returns
    -------
    Dataframe

    Examples
    -------
    >>> to_df(
    ...    [('msg_id1', ['val1']), ('msg_id2', ['val1', 'val2'])],
    ...    "field_name")
    ... )
       msg_id   seg        field_name
    0  msg_id1  seg_0      val1
    1  msg_id2  seg_0      val1
    2  msg_id1  seg_1      None
    3  msg_id2  seg_1      val2
    '''
    # pylint: disable=invalid-name

    df = pd.DataFrame.from_dict(
        dict(lst),
        orient="index"
    )

    n_cols = range(len(df.columns))
    df.columns = ["seg_{n}".format(n=n) for n in n_cols]

    df["msg_id"] = df.index
    df = pd.melt(df, id_vars=["msg_id"])
    df.rename(
        columns={
            "variable": "seg",
            "value": loc_txt
        },
        inplace=True
    )
    return df

def join_dfs(dfs):
    ''' Join a list of dataframes

    Parameters
    ----------
    dfs : list(dataframes)

    Returns
    -------
    Dataframe
    '''
    # pylint: disable=no-else-return

    if len(dfs) == 1:
        return dfs[0]
    else:
        df_join = pd.merge(
            dfs[0],
            dfs[1],
            how="inner",
            on=["msg_id", "seg"],
            sort=False
        )
        dfs_to_join = dfs[2:]
        dfs_to_join.append(df_join)
        return join_dfs(dfs_to_join)