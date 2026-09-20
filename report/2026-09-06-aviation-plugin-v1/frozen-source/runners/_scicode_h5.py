"""_scicode_h5.py — SciCode test_data.h5 目标加载器。

逐行取自 scicode-bench/SciCode `src/scicode/parse/parse.py`（Apache-2.0，
仓库 commit e3158ea，仅改函数签名以传入 h5 路径与去掉相对路径常量）。
归属：SciCode: A Research Coding Benchmark Curated by Scientists (arXiv:2407.13168)。
许可副本见 data/scicode/physics/LICENSE.apache-2.0。
"""

from __future__ import annotations

import h5py
import numpy as np
import scipy.sparse


def _process_list(group):
    lst = []
    for key in group.keys():
        lst.append(group[key][()])
    return lst


def _process_dict(group):
    d = {}
    for key, obj in group.items():
        if isinstance(obj, h5py.Group):
            d[key] = _process_sparse_matrix(obj["sparse_matrix"])
        elif isinstance(obj[()], bytes):
            d[key] = obj[()].decode("utf-8", errors="strict")
        else:
            try:
                tmp = float(key)
                d[tmp] = obj[()]
            except ValueError:
                d[key] = obj[()]
    return d


def _process_sparse_matrix(group):
    data = group["data"][()]
    shape = tuple(group["shape"][()])
    if "row" in group and "col" in group:
        row = group["row"][()]
        col = group["col"][()]
        return scipy.sparse.coo_matrix((data, (row, col)), shape=shape)
    elif "blocksize" in group:
        indices = group["indices"][()]
        indptr = group["indptr"][()]
        blocksize = tuple(group["blocksize"][()])
        return scipy.sparse.bsr_matrix((data, indices, indptr), shape=shape,
                                       blocksize=blocksize)
    else:
        indices = group["indices"][()]
        indptr = group["indptr"][()]
        return scipy.sparse.csr_matrix((data, indices, indptr), shape=shape)


def _process_datagroup(group):
    for key in group.keys():
        if key == "list":
            return _process_list(group[key])
        if key == "sparse_matrix":
            return _process_sparse_matrix(group[key])
        else:
            return _process_dict(group)


def load_targets(h5_path: str, step_id: str, test_num: int) -> list:
    """官方 process_hdf5_to_tuple 语义：返回每 test case 的期望值列表。"""
    data_lst = []
    with h5py.File(h5_path, "r") as f:
        for test_id in range(test_num):
            group_path = f"{step_id}/test{test_id + 1}"
            if group_path not in f:
                raise FileNotFoundError(f"Path {group_path} not found in h5.")
            group = f[group_path]
            if isinstance(group, h5py.Dataset):
                v = group[()]
                data_lst.append(v.decode("utf-8") if isinstance(v, bytes) else v)
                continue
            keys = list(group.keys())
            if len(keys) == 1:
                sub = group[keys[0]]
                if isinstance(sub, h5py.Dataset):
                    v = sub[()]
                    data_lst.append(v.decode("utf-8") if isinstance(v, bytes) else v)
                else:
                    data_lst.append(_process_datagroup(sub))
            else:
                var_lst = []
                for key in keys:
                    sub = group[key]
                    if isinstance(sub, h5py.Dataset):
                        v = sub[()]
                        var_lst.append(v.decode("utf-8") if isinstance(v, bytes) else v)
                    else:
                        var_lst.append(_process_datagroup(sub))
                data_lst.append(tuple(var_lst))
    return data_lst
