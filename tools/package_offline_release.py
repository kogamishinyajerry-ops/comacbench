"""Finalize selected public benchmark payloads, without model calls or private inputs."""
from __future__ import annotations
import os, json, pathlib, hashlib, zipfile, tarfile, subprocess, urllib.request, urllib.error, time, shutil, sys

PROJECT=os.environ['PROJECT']
REPO='kogamishinyajerry-ops/comacbench'
RUN='39932445808'
ROOT=pathlib.Path.cwd()
TOKEN=os.environ['GH_TOKEN']
OUT=ROOT/'release'; OUT.mkdir()
B=ROOT/('COMAC-'+PROJECT+'-offline-linux-amd64'); B.mkdir()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def api(path):
    r=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+TOKEN,'User-Agent':'comac-public-offline-build'})
    with urllib.request.urlopen(r,timeout=60) as f:return json.load(f)
def cmd(args,**kwargs):return subprocess.run(list(map(str,args)),check=True,**kwargs)
def capture(args):return subprocess.check_output(list(map(str,args)),text=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None
artifact=None
for _ in range(120):
    artifacts=api('actions/runs/'+RUN+'/artifacts')['artifacts']
    artifact=next((x for x in artifacts if x['name']=='offline-'+PROJECT+'-payload' and not x['expired']),None)
    if artifact:break
    state=api('actions/runs/'+RUN)
    if state['status']=='completed':raise RuntimeError('payload missing after completed build')
    time.sleep(10)
if not artifact:raise RuntimeError('payload not available within collection limit')
request=urllib.request.Request(artifact['archive_download_url'],headers={'Authorization':'Bearer '+TOKEN,'User-Agent':'comac-public-offline-build'})
try:
    response=urllib.request.build_opener(NoRedirect()).open(request,timeout=60)
except urllib.error.HTTPError as e:
    if e.code not in (301,302,303,307,308):raise
    location=e.headers['Location']
    # The temporary blob URL receives NO GitHub authorization header.
    response=urllib.request.urlopen(location,timeout=120)
archive=ROOT/'incoming.zip'
with response,archive.open('wb') as f:shutil.copyfileobj(response,f)
assert sha(archive)==artifact['digest'].split(':',1)[1]
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name in z.namelist():
        p=pathlib.PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('unsafe archive path')
    z.extractall(B)
config=json.loads((B/'evidence/build-config.json').read_text())
print('UPSTREAM_PAYLOAD_TESTS',json.dumps(config['tests']),flush=True)
print('UPSTREAM_PAYLOAD_STATUS',(B/'payload-status.json').read_text(),flush=True)
if not (B/'images.tar.gz').is_file():raise RuntimeError('image archive missing')
# Record honest upstream build failures without converting a green workflow into acceptance.
original_pass=all(t['status']=='PASS' for t in config['tests'])

scripts={}
scripts['doctor.sh']=r'''#!/usr/bin/env bash
set -euo pipefail
[[ "$(uname -s)" == Linux ]] || { echo 'Required: Linux execution host. Windows uses SSH to that host.' >&2; exit 2; }
case "$(uname -m)" in x86_64|amd64) ;; *) echo 'This package is linux/amd64, not ARM/Kunpeng.' >&2; exit 2;; esac
for x in docker sha256sum gzip tar timeout; do command -v "$x" >/dev/null || { echo "Missing prerequisite: $x" >&2; exit 2; }; done
docker info >/dev/null
server=$(docker info --format '{{.OSType}}/{{.Architecture}}')
case "$server" in linux/x86_64|linux/amd64) ;; *) echo "Unsupported Docker server: $server" >&2; exit 2;; esac
uname -a
docker version --format 'Docker client={{.Client.Version}} server={{.Server.Version}}'
df -h .
echo 'Host prerequisites available. This is not an engineering or model-performance approval.'
'''
scripts['verify.sh']=r'''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sha256sum --check --strict SHA256SUMS
'''
scripts['install.sh']=r'''#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT"
bash doctor.sh
bash verify.sh
mkdir -p local-records
docker load --input images.tar.gz | tee "local-records/install-$(date -u +%Y%m%dT%H%M%SZ).log"
while IFS=$'\t' read -r image expected; do
  [[ -n "$image" ]] || continue
  actual=$(docker image inspect --format '{{.Id}}' "$image")
  [[ "$actual" == "$expected" ]] || { echo "IMAGE ID MISMATCH: $image" >&2; exit 2; }
done < images.tsv
echo 'Images installed locally; no pull, build, pip, apt, or model request was made.'
echo 'Next: bash selftest.sh /absolute/path/to/NEW-output-directory'
'''
scripts['common.sh']=r'''#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CURRENT_CONTAINER=''
cleanup(){ if [[ -n "$CURRENT_CONTAINER" ]]; then docker rm -f "$CURRENT_CONTAINER" >/dev/null 2>&1 || true; fi; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
check_images(){
  bash "$ROOT/doctor.sh" >/dev/null
  while IFS=$'\t' read -r image expected; do
    [[ -n "$image" ]] || continue
    [[ "$(docker image inspect --format '{{.Id}}' "$image")" == "$expected" ]] || { echo "Missing/wrong image: $image; run install.sh" >&2; return 2; }
  done < "$ROOT/images.tsv"
}
new_output(){
  [[ "$1" = /* && ! -e "$1" ]] || { echo 'Output must be an ABSOLUTE, NEW directory.' >&2; return 2; }
  mkdir -p -- "$1"; OUTPUT=$(cd -- "$1" && pwd)
}
run_container(){
  local seconds="$1"; shift
  CURRENT_CONTAINER="comac-bench-${RANDOM}-${RANDOM}"
  local result=0
  timeout --signal=TERM --kill-after=10s "$seconds" docker run --rm --pull=never --name "$CURRENT_CONTAINER" --network=none --memory=6g --cpus=2 "$@" || result=$?
  cleanup; CURRENT_CONTAINER=''
  return "$result"
}
'''
scripts['Run-Remote.ps1']=r'''param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9@._-]+$')][string]$Target,
  [Parameter(Mandatory=$true)][ValidatePattern('^/[a-zA-Z0-9_./-]+$')][string]$PackagePath,
  [ValidateSet('doctor','install','selftest')][string]$Action='doctor',
  [ValidatePattern('^/[a-zA-Z0-9_./-]+$')][string]$OutputPath='/tmp/comac-benchmark-acceptance'
)
$ErrorActionPreference='Stop'
if (-not (Get-Command ssh.exe -ErrorAction SilentlyContinue)) { throw 'Windows OpenSSH client is required.' }
$script="$PackagePath/$Action.sh"
$remote=if ($Action -eq 'selftest') { "bash '$script' '$OutputPath'" } else { "bash '$script'" }
& ssh.exe $Target $remote
exit $LASTEXITCODE
'''
if PROJECT in ('simulcost','engibench'):
    image=config['images'][0]['tag']
    scripts['selftest.sh']='#!/usr/bin/env bash\nsource "$(dirname "${BASH_SOURCE[0]}")/common.sh"\ncheck_images\n[[ $# == 1 ]] || { echo "usage: bash selftest.sh /absolute/NEW-output"; exit 2; }\nnew_output "$1"\nrun_container 600 -v "$OUTPUT:/work" '+image+' python /opt/offline/smoke.py 2>&1 | tee "$OUTPUT/console.log"\necho "Numerical installation self-test finished. No Agent/model was called."\n'
    if PROJECT=='simulcost':
        scripts['run.sh']='#!/usr/bin/env bash\nsource "$(dirname "${BASH_SOURCE[0]}")/common.sh"\ncheck_images\n[[ $# -ge 2 ]] || { echo "usage: bash run.sh heat_1d|burgers_1d|diff_react_1d /absolute/NEW-output [Hydra key=value...]"; exit 2; }\nfamily="$1"; shift; case "$family" in heat_1d|burgers_1d|diff_react_1d) ;; *) exit 2;; esac\nnew_output "$1"; shift\nrun_container 600 -v "$OUTPUT:/work" '+image+' python "costsci_tools/runners/$family.py" --config-name=p1 n_space=64 cfl=0.25 "$@" dump_dir=/work/result +max_wall_time=300 2>&1 | tee "$OUTPUT/console.log"\n'
    else:
        scripts['run.sh']='#!/usr/bin/env bash\nsource "$(dirname "${BASH_SOURCE[0]}")/common.sh"\ncheck_images\n[[ $# == 2 && -f "$1" ]] || { echo "usage: bash run.sh /path/design_program.py /absolute/NEW-output"; exit 2; }\nprogram=$(realpath "$1"); new_output "$2"\nrun_container 600 -v "$program:/work/program.py:ro" -v "$OUTPUT:/work/output" -w /work '+image+' python /work/program.py 2>&1 | tee "$OUTPUT/console.log"\n'
else:
    scripts['task.sh']=r'''#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
check_images
[[ $# -ge 3 ]] || { echo 'usage: task.sh prepare|exec|oracle|verify TASK /absolute/workspace [command ...]'; exit 2; }
action="$1"; task="$2"; work="$3"; shift 3
case "$task" in baseline-free-localization|guided-wave-localization|inelastic-constitutive-discovery) ;; *) echo 'Unknown task' >&2; exit 2;; esac
agent="comac-offline/tbs-$task:v0.1-agent"
verifier="comac-offline/tbs-$task:v0.1-verifier"
source_task="$ROOT/build-context/tbscience/tasks/engineering-sciences/mechanical-engineering/$task"
[[ "$work" = /* ]] || { echo 'Use an absolute workspace'; exit 2; }
case "$action" in
 prepare)
   new_output "$work"; work="$OUTPUT"
   CURRENT_CONTAINER=$(docker create --pull=never "$agent")
   docker cp "$CURRENT_CONTAINER:/app" "$work/app"
   cleanup; CURRENT_CONTAINER=''
   chmod -R a+rX "$work/app"
   cp "$source_task/instruction.md" "$work/instruction.md"
   echo "Prepared public workspace: $work. Keep the installer, source solutions and verifier files away from the subject Agent."
   ;;
 exec)
   [[ -d "$work/app" && $# -gt 0 ]] || exit 2
   run_container 1800 -v "$work/app:/app" -w /app "$agent" "$@"
   ;;
 oracle)
   [[ -d "$work/app" && ! -e "$work/oracle.log" ]] || exit 2
   run_container 1800 -v "$work/app:/app" -v "$source_task/solution:/solution:ro" "$agent" bash /solution/solve.sh 2>&1 | tee "$work/oracle.log"
   echo 'REFERENCE run only, never a model score.'
   ;;
 verify)
   [[ -d "$work/app" && ! -e "$work/verifier" ]] || exit 2
   mkdir "$work/verifier"
   run_container 1800 -v "$work/app:/app:ro" -v "$work/verifier:/logs/verifier" "$verifier" bash /tests/test.sh 2>&1 | tee "$work/verify-console.log"
   [[ -f "$work/verifier/reward.txt" ]] || { echo 'Verifier produced no reward'; exit 2; }
   reward=$(tr -d '\r\n ' < "$work/verifier/reward.txt")
   echo "reward=$reward"
   [[ "$reward" == 1 || "$reward" == 1.0 ]] || exit 1
   ;;
 *) echo 'Unknown action'; exit 2;;
esac
'''
    scripts['selftest.sh']=r'''#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
check_images
[[ $# == 1 ]] || { echo 'usage: selftest.sh /absolute/NEW-output'; exit 2; }
new_output "$1"
# One complete reference/verifier round tests the installed archive, not model ability.
task=baseline-free-localization
bash "$ROOT/task.sh" prepare "$task" "$OUTPUT/$task"
bash "$ROOT/task.sh" oracle "$task" "$OUTPUT/$task"
bash "$ROOT/task.sh" verify "$task" "$OUTPUT/$task"
echo 'Reference/verifier installation check passed. Other task build checks are in evidence/.'
'''
for name,content in scripts.items():
    p=B/name;p.write_text(content,encoding='utf-8');p.chmod(0o755)
    if name.endswith('.sh'):cmd(['bash','-n',p])

scope={
 'simulcost':('SimulCost','一维传热、Burgers、扩散反应三个求解器与对应原始任务生成资料。','不含二维/Taichi/EPOCH/FEM 全套后端，也不含大体积仿真缓存。随包数据由固定源码的原始生成器产生，不冒充另行下载的官方 HF 完整数据集。数值模式保留 HDF5/JSON，关闭 PNG 保存；未改数值公式或成本公式。'),
 'engibench':('EngiBench','Beams2D v1：给定条件下的二维材料布局、仿真和原生优化器。','没有下载关联的 CC-BY-NC-SA 数据集。HeatConduction2D、Airfoil 等源码可能在对应源码档中，但其额外求解后端不在本镜像运行支持范围。首跑只证明原生优化器环境，不是 LLM 设计成绩。'),
 'tbscience':('Terminal-Bench-Science','v0.1.0 中 baseline-free-localization、guided-wave-localization、inelastic-constitutive-discovery 三项。','这是三项任务的本地 Docker 执行剖面，包含独立 Agent/Verifier 镜像，不含完整 Harbor 编排器或全部70题；不得把改变预算或运行器后的成绩直接等同官方榜单。')
}[PROJECT]
readme=f'''# {scope[0]}：COMAC 内网离线部署包

制作日期：2026-10-23。架构：Linux / x86_64 / CPU。它不是 Windows EXE，也不是 ARM/鲲鹏镜像。

## 交付范围
{scope[1]}

{scope[2]}

镜像已经编译并包含 Python 与选定依赖。内网安装使用 images.tar.gz，不调用 pip、apt、GitHub、Hugging Face 或镜像仓库。请勿在内网照 upstream README 重新联网安装。

## 机器要求
需要公司允许使用的 Docker Engine（客户端和运行中的服务）、Bash、tar、gzip、sha256sum、GNU timeout。Docker Engine/操作系统本身不随本包安装；缺少时 doctor.sh 会明确停止。建议独立 Linux x86_64 测试主机、8GB以上内存，并为三个包合计预留20GB可用空间；这是资源建议，不是全部大型任务的性能承诺。容器默认限制2CPU/6GB。Windows工程电脑可以通过SSH调用该Linux主机。

## 安装与首跑
解压整个ZIP到管理员控制的新目录，在Linux执行：

```bash
bash doctor.sh
bash install.sh
bash selftest.sh /absolute/path/to/new-acceptance
```

install.sh 先核对全部SHA256，再docker load并核对镜像ID。自检使用 --network=none；不调用模型。请使用新输出目录，失败日志不得覆盖。首次自检成功也不等于COMAC工程方法批准。

## 文件
- images.tar.gz / images.tsv：完整离线镜像及锁定ID。
- install.sh / doctor.sh / verify.sh：安装、前置检查与完整性检查。
- evidence/：原始构建检查、数值/参考产物及本次重新导入测试记录。
- sources/：固定版本原始源码档；build-context/：实际构建输入与少量部署设置。
- SHA256SUMS：包内文件清单。来源与依赖版本见 evidence/build-config.json 和 *pip-freeze.txt。
- Run-Remote.ps1：Windows使用既有SSH客户端调用Linux主机；不安装Docker Desktop。

## 模型与隔离
模型权重、DSH安装包和API凭据不包含。先运行无模型自检，再由内网DSH的现有工具接口调用这些任务。所有自带脚本默认容器断网，模型服务应由宿主的受控接口访问；不要为了接模型把容器改成能访问互联网，也不要把Docker socket、用户目录、完整安装目录和参考答案交给受试Agent。

本次没有运行真实模型；Agent适配、真实预算统计和内网目标机验收仍需现场完成。安装包包含参考答案/隐藏测试，必须由维护者保管。只把公开输入工作区提供给受试Agent。

## 结果边界
README的上游能力不等于本包全部已验收。先看 release-status.json 中原始构建检查与重新导入检查；没有运行的项目不能标为通过。所有镜像只针对本包固定CPU任务配置；不是StarCCM+、CATIA、Amesim的软件安装或操作能力证明。
'''
if PROJECT=='simulcost':
    readme+='''
## 调用求解器
```bash
bash run.sh heat_1d /absolute/new-heat n_space=128 cfl=0.25
bash run.sh burgers_1d /absolute/new-burgers n_space=128
bash run.sh diff_react_1d /absolute/new-diffusion n_space=128
```
参数写法沿用原Hydra配置；不能用删除输出或改变方程来制造提效。任务生成资料在generated-data/，大规模缓存不包含。模型接入说明在build-context/SimulCost-Bench/custom_model/README.md；本次只做安装与数值检查，未完成任何模型精度/成本排名。元数据里的cost沿用上游定义，不等于完整系统墙钟或会话外算力。
'''
elif PROJECT=='engibench':
    (B/'example_design.py').write_text('''import json,numpy as np
from pathlib import Path
from engibench.problems.beams2d.v1 import Beams2D
p=Beams2D(seed=0,config={"nelx":32,"nely":16,"max_iter":12,"volfrac":0.35,"rmin":2.0})
x0=np.full(p.design_space.shape,0.35)
baseline=p.simulate(x0);p.reset(seed=0)
x,hist=p.optimize(starting_point=x0)
p.reset(seed=0);final=p.simulate(x)
out=Path('/work/output');out.mkdir(exist_ok=True)
np.save(out/'design.npy',x)
(out/'result.json').write_text(json.dumps({"baseline":np.asarray(baseline).tolist(),"final":np.asarray(final).tolist(),"steps":len(hist),"model_calls":0},indent=2))
''')
    readme+='''
## 执行一个设计程序
```bash
bash run.sh "$PWD/example_design.py" /absolute/new-design
```
示例使用上游原生优化器，不是模型成绩。Agent可以编写自己的设计程序，产物写到/work/output；不把一次optimize调用等同一次内部数值计算。Beams2D v1原源码和约束定义随包提供。
'''
else:
    readme+='''
## 执行任务
```bash
bash task.sh prepare guided-wave-localization /absolute/new-task
# 只给Agent instruction.md及app/公开工作区；执行命令示例：
bash task.sh exec guided-wave-localization /absolute/new-task python /app/solution.py
# 维护者在Agent结束后独立验证：
bash task.sh verify guided-wave-localization /absolute/new-task
```
`oracle`操作是参考解自检，不属于受试成绩，禁止用于正式模型试验。`verify`可能在pytest失败时仍由上游脚本返回0，本包装器会继续读取reward.txt并据实返回非零。
Agent和Verifier镜像分离；不要把tests/、solution/、authoring/、evidence/或本安装包所在目录挂载到受试容器。受试进程不要获得宿主Docker控制权。固定两个CPU、内存和超时是部署检查配置；正式跑榜须另行遵守原task.toml预算并记录改变。
'''
(B/'00-开始这里.md').write_text(readme,encoding='utf-8')
license_note='''# 第三方来源与使用范围

原始LICENSE/COPYING/NOTICE保留在sources和build-context中；Python包版本在evidence/*pip-freeze.txt，其许可随镜像dist-info和系统copyright文件保留。锁定源码及镜像ID不是公司开源准入、漏洞扫描或法律批准。正式导入仍按单位流程审查。

'''
if PROJECT=='engibench':license_note+='EngiBench代码GPLv3；附带完整对应工程源码与构建文件。关联HF数据集为CC-BY-NC-SA 4.0，本包没有下载或捆绑该数据集。自检设计由均匀初始材料分布计算生成。依赖（含CVXOPT等）各按各自许可，不能把整个镜像标成Apache或MIT。\n'
if PROJECT=='simulcost':license_note+='SimulCost-Bench主项目Apache-2.0。costsci_tools是按主项目gitlink固定的另一个公开仓库；未确认其根目录存在独立的主许可声明，不能因主仓库有Apache就替它作授权保证。请维护者确认该子模块及其第三方来源的使用授权后走正式企业准入；本包记录为技术试用候选，不声称完成法律审查。\n'
if PROJECT=='tbscience':license_note+='Terminal-Bench-Science代码Apache-2.0；各任务来源和数据说明按原task文件保留。保留canary标记及原始任务说明；公开任务不等于未见泛化测试。\n'
(B/'THIRD-PARTY-NOTICE.md').write_text(license_note,encoding='utf-8')
(B/'LOCAL-HANDOFF-PROMPT.md').write_text(f'''在Linux x86_64目标机接手 {scope[0]} 离线包。先读00-开始这里.md、THIRD-PARTY-NOTICE.md和release-status.json。不得联网安装、拉取镜像、替换任务或修改评分阈值；不得启动付费/外部模型。执行doctor、完整性校验、install，再在全新绝对路径运行selftest。保留所有失败、主机架构、Docker版本、镜像ID、原始输出和检查日志。目标不兼容或Docker缺失时输出具体BLOCKED，不偷偷切ARM仿真或以缓存当新求解。参考解自检不能计模型成绩；DSH适配单独记录未验证项。运行后将新日志与结果打包回传，不覆盖包内原始证据。\n''',encoding='utf-8')

# No font binaries are to be distributed in plain files, sources or image layers.
font_suffix=('.ttf','.otf','.woff','.woff2','.ttc','.pfa','.pfb')
for p in B.rglob('*'):
    if p.is_file() and p.name.lower().endswith(font_suffix):raise RuntimeError('font binary unexpectedly present: '+str(p.relative_to(B)))
# Save original metadata and verify image transport with real docker load on this fresh runner.
with (B/'evidence/reload.log').open('w') as f:cmd(['docker','load','--input',B/'images.tar.gz'],stdout=f,stderr=subprocess.STDOUT)
for r in config['images']:
    actual=json.loads(capture(['docker','image','inspect',r['tag']]))[0]
    assert actual['Id']==r['id'] and actual['Architecture']=='amd64' and actual['Os']=='linux'
    raw=B/'evidence'/('font-scan-'+r['tag'].replace('/','_').replace(':','_')+'.txt')
    code="from pathlib import Path; files=[str(p) for root in ['/usr/local','/usr/share/fonts','/opt','/app'] for p in Path(root).rglob('*') if p.is_file() and p.suffix.lower() in ['.ttf','.otf','.woff','.woff2','.ttc','.pfa','.pfb']]; print('\\n'.join(files)); assert not files"
    with raw.open('w') as f:cmd(['docker','run','--rm','--network=none',r['tag'],'python','-c',code],stdout=f,stderr=subprocess.STDOUT)
# Repeat the package's numerical/reference first-run, no model service available.
accept=ROOT/('acceptance-'+PROJECT)
with (B/'evidence/reload-selftest.log').open('w') as f:
    try:
        result=subprocess.run(['bash',str(B/'selftest.sh'),str(accept)],stdout=f,stderr=subprocess.STDOUT,timeout=1800)
        reloaded=result.returncode==0;rc=result.returncode
    except subprocess.TimeoutExpired:reloaded=False;rc=124
if accept.exists():shutil.copytree(accept,B/'evidence/reload-selftest-output')
status={'project':PROJECT,'version':'2026-10-23-cpu-pilot','original_build_checks_pass':original_pass,'image_load_and_id_check':True,'network_disabled_selftest_pass':reloaded,'selftest_returncode':rc,'model_calls':0,'target_COMAC_machine_tested':False,'runtime':'Linux x86_64 + preinstalled Docker Engine','host_engine_included':False,'full_upstream_suite':False,'DSH_integration_tested':False,'source_run':int(RUN),'payload_artifact':artifact['id']}
(B/'release-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
# Per-file hashes include the original/source archives, images and results.
files=sorted(p for p in B.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(B/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(B).as_posix()+'\n' for p in files))
# The ACTUAL installation script is now checked too; all inputs already present.
with (B/'evidence/install-script-replay.log').open('w') as f:cmd(['bash',B/'install.sh'],stdout=f,stderr=subprocess.STDOUT)
shutil.rmtree(B/'local-records',ignore_errors=True)
files=sorted(p for p in B.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(B/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(B).as_posix()+'\n' for p in files))
# Store already compressed image payload rather than recompressing hundreds of MB.
final=OUT/(B.name+'-20261023.zip')
with zipfile.ZipFile(final,'w',allowZip64=True) as z:
    for p in sorted(B.rglob('*')):
        if p.is_file():z.write(p,(pathlib.Path(B.name)/p.relative_to(B)).as_posix(),compress_type=zipfile.ZIP_STORED if p.name=='images.tar.gz' else zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(final) as z:assert z.testzip() is None
summary={**status,'filename':final.name,'size_bytes':final.stat().st_size,'sha256':sha(final),'file_count':len(files)+1}
(OUT/'DELIVERY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'SHA256SUMS').write_text(summary['sha256']+'  '+final.name+'\n')
print('FINAL_DELIVERY',json.dumps(summary,ensure_ascii=False),flush=True)
if not original_pass or not reloaded:
    print('WARNING: Not all checks passed. Package retains failure evidence; do not represent as accepted.')
