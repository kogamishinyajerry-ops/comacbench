# AeroEngQA 金标集镜像溯源（PROVENANCE）

> assets_revision: `aeroengqa@zenodo.14215677-v1.0`
> 镜像日期: 2026-08-19 · 镜像执行: M1 收尾会话（dev 终端）

## 镜像内容（Zenodo record 14215677，v1.0，2024-11-25，全部 md5 核验通过）

| 文件 | 大小 | md5 |
| --- | --- | --- |
| `AeroEngQA_single-hop.json` | 21463 | `c697b0dff639d4abda58577285063525` |
| `AeroEngQA_multi-hop.json` | 28784 | `487e94feb1c02358b86fea7a9050e88d` |
| `AeroEngQA_single-hop-unanswerable.json` | 22453 | `840a8dd313c509571048f00d8ca02f4a` |
| `AeroEngQA_multi-hop-unanswerable.json` | 26569 | `59a515a1e174cc17782b506d59b8df40` |
| `AeroEngQA.xlsx` | 69115 | `05ff4897523e60757d182f793892aff9` |
| `zenodo-dataset-ArgoEngQA.txt` | 2152 | `1b695df0cebc31543e1d177a2d79c0bf` |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

- Zenodo API `metadata.license.id = cc-by-4.0`，`access_right = open`（license-notes.md 同日已记 confirmed-dataset）；
- BY 归属义务：再分发须署名 —— Silva, E.A. Marsh, R. Yong, H.K. Middleton, S.E. Sóbester, A., *Retrieval-Augmented Generation and In-Context Prompted Large Language Models in Aircraft Engineering*, AIAA-2025, doi:10.2514/6.2025-0700；
- 本镜像随目录保留 `zenodo-dataset-ArgoEngQA.txt`（Zenodo 自述文件）满足署名链。

## 权威口径裁定（镜像时核验）

- **评测集 = 4 个 JSON，共 80 题**（single/multi × answerable/unanswerable，各 20）——与 registry `content` 字段及论文口径一致；
- xlsx 为同题超集（25/25/20/25 行，含 source-domain/source-title/source-url 溯源列，多出行为重复题面），仅作溯源参考，不用于出题；
- JSON 与 xlsx 题面逐一核对：4 个 JSON 的 80 题全部存在于 xlsx 对应 sheet（交集=JSON 题数，无独有题）。

## 数据校验（镜像时核验）

- answerable（40 题）：含 `answer` 参考答案；single-hop 1 段 context，multi-hop 恒 2 段 context（20/20）；
- unanswerable（40 题）：无 `answer` 字段（应拒答），context 同上结构；
- 任务生成器逐题校验 needed_citations：single-hop=[1]，multi-hop=[1,2]。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
python3 - <<'EOF'
import json, urllib.request, hashlib, pathlib
rec = json.load(urllib.request.urlopen("https://zenodo.org/api/records/14215677"))
for f in rec["files"]:
    data = urllib.request.urlopen(f["links"]["self"]).read()
    algo, want = f["checksum"].split(":")
    assert hashlib.new(algo, data).hexdigest() == want, f["key"]
    pathlib.Path(f["key"]).write_bytes(data)
EOF
# 任一 md5 不再匹配 => Zenodo 版本变更 => assets_revision 变更 => 新评测周期
```
