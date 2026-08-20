# vendor_shim/scicode — SciCode 官方包最小 shim

仅含 `compare/cmp.py`（Apache-2.0，逐行取自 scicode-bench/SciCode @ e3158ea
src/scicode/compare/cmp.py）：SciCode 部分测试用例显式
`from scicode.compare.cmp import cmp_tuple_or_list`，官方评测环境安装 scicode 包；
本 harness 以 shim 提供同一符号，避免整包安装。
归属：arXiv:2407.13168；许可副本 data/scicode/physics/LICENSE.apache-2.0。
