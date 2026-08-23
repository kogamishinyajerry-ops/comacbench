# gtm.transport_control_hard — H2/H3 脚手架（蒸馏工作流资产 v1）

> 用途：harness 臂 H2/H3 的 prompt 注入件（`--scaffold data/gtm/transport_control_hard/scaffold.md`）。
> 蒸馏来源：本 harness 自身 gold 脚本范式（`data/gtm/transport_control_hard/gold/*.m`，
> MATLAB R2026a + Control System Toolbox，自建任务）+ 本 harness 审计到的双模型
> 失败模式（minimax-m3 0.7059 / glm-4.6 0.6520 / glm-5.3 0.6471 三套基线的逐题取证）。
> 靶准两个失败族：**识辨识族（H1，三模型 0.25/0.0/0.0 最大缺口）** 与
> **裕度族（H2，margin 输出 wcg/wcp 语义对调）**。不追求覆盖全 17 题。
> 防泄漏纪律：下面所有 worked-example 参数（dt=0.05/N=400/wn=2.8/ζ=0.55/自造
> 三阶 type-1 与级联回路）经 grep 验证不与任何任务参数域重合；本文件不含任何
> 任务的参考输出值或采样种子。判分仍要求模型自行正确执行与数值命中。

---

## 你要做的事

任务全部是：被隔离目录内以 `matlab -batch model` 执行你写出的 `model.m`，在 cwd
写出 `result.json`（MATLAB `jsonencode` 的顶层 struct），用 Control System Toolbox。
失败几乎都出在「数据处理管线的结构」与「margin 输出顺序的语义」，不是纯数学。
按下面两个骨架写就能避开。

## 通用执行契约（每条适用）

- 脚本自包含、无 shell/网络/文件系统逃逸：只用内嵌变量 + `fopen/fwrite/fclose`
  写 `result.json`。
- `result.json` 顶层必须是 struct（object），键名逐字照题面；数值键 1% 相对容差。
- 矩阵/向量**列优先**：题目给的 `X` 与 `u` 是 `N×4` 与 `N×1`（`[元素; ...]` 行用
  `;` 分隔、`[...]` 内逗号/空格分列），直接照抄即可，不要自作主张转置。
- 响应格式：只输出一个 ```matlab 代码块，无其余文字（围栏由适配器剥离）。

---

## H1 辨识族骨架（最重要：短周期模态辨识）

给 `X`（N×4 状态响应，列 `[u_x, w, q, theta]`）与 `u`（N×1 升降舵输入），
`dt` 采样间隔。要辨短周期(SP)自然频率 `omega_sp_id` 与阻尼比 `zeta_sp_id`。
管线四步，下面是一个**自造、与任何考题不同**的完整可运行 worked example
（自造 `A_true`/`dt=0.05`/`N=400`/PRBS 幅值 ±0.06/周期 9，目标 SP wn=2.8、ζ=0.55，
无噪声；这套数据证明管线语义，不泄露任何考题数值）：

```matlab
% ===== worked example：短周期辨识全管线（参数与任何考题都不同）=====
rng(2024); dt = 0.05; N = 400;          % 自造：dt/初值/长度均避开考题

% —— 自造一个连续 4 阶纵向模型（分块构造，短周期+长周期两个共轭对）——
Zsp = 0.55; wsp = 2.8;                   % 短周期目标：wn=2.8, 阻尼 0.55
a = Zsp*wsp; om = wsp*sqrt(1-Zsp^2);
Asp = [-a, -om; om, -a];                 % 2x2 短周期块
Zph = 0.04; wph = 0.30;                  % 长周期(phugoid)块：慢、低阻尼
ap = Zph*wph; op = wph*sqrt(1-Zph^2);
Aph = [-ap, -op; op, -ap];
A_true = blkdiag(Asp, Aph);              % 4x4，两对模态互不耦合
B_true = [0.11; 0.90; 0.04; 0.18];       % 自造升降舵效能

% —— ZOH 离散化：Ad = expm(A*dt)，Bd = A\(Ad - I)*B ——
Ad_true = expm(A_true * dt);
Bd_true = (A_true \ (Ad_true - eye(4))) * B_true;

% —— 自造 PRBS 输入并仿真（无噪声，证明管线而非噪声鲁棒性）——
u = zeros(N,1);
for k = 1:N, u(k) = 0.06 * (2*mod(floor((k-1)/9),2) - 1); end
X = zeros(N,4); x = zeros(4,1);
for k = 1:N-1, X(k,:) = x'; x = Ad_true*x + Bd_true*u(k); end
X(N,:) = x';

% ========== 管线本体（考题照此四步；step 2/3/4 逐字复用）==========
% step 1 — 最小二乘回归 x[k+1] = Ad x[k] + Bd u[k]
X1 = X(1:end-1,:); X2 = X(2:end,:);
reg = [X1, u(1:end-1)];              % (N-1) x 5 回归矩阵
coef = reg \ X2;                     % coef 是 5x4 = [Ad'; Bd']
Ad_hat = coef(1:4,:)';               % 前 4 行转置 => Ad (4x4)
Bd_hat = coef(5,:)';                 % 第 5 行转置   => Bd (4x1)
% step 2 — 离散极点 -> 连续：s = log(lam_d)/dt（一次性批量）
ev = eig(Ad_hat);
s  = log(ev) / dt;
% step 3 — 选短周期共轭对：|s| 最大的那对（长周期贴近单位圆，|s| 小）
[~, idx] = sort(abs(s), 'descend');
lam_sp = s(idx(1));                  % 最大 |s| 的那一支（共轭对任一支即可）
% step 4 — 自然频率与阻尼比
wn   = abs(lam_sp);
zeta = -real(lam_sp) / wn;

% —— 输出（键名逐字照题面：omega_sp_id / zeta_sp_id）——
r = struct('omega_sp_id', wn, 'zeta_sp_id', zeta);
fid = fopen('result.json','w'); fwrite(fid, jsonencode(r)); fclose(fid);
```

worked example 在 MATLAB 实跑，辨识误差 `<1e-6`（约 `1e-15`，机器精度）。

> ⚠️ **数据转写是硬要求**：题面说的「数据已给 / given / sampled at dt=…」是指
> **数值写在题目文字里**，不是预置在你的工作区。你必须在 `model.m` 里**完整照抄**
> 题面给的 `X = [...];`、`u = [...];`、`dt = 0.02;` 三行（整段数值一字不落），
> 再执行 step 1–4 与输出段。`model.m` 被保存到一个**空的隔离目录**单独执行，
> 脚本里没有出现的变量就不存在（会报「无法对 'X' 进行索引」→ code_not_executable）。
> 考题只需：把上面 worked example 里自造的 `X`/`u`/`dt`/`A_true` 等参数与数据段，
> 整体替换成题面给的 `X`/`u`/`dt` 数值（自造仿真段删掉，管线段原样保留）。

要点（每一条都是双模型栽过的坑，见下方陷阱清单）：

- `coef = reg \ X2` 直接用反斜杠（或 `pinv`），不要手写 `inv`。
- `coef` 的形状是 `(4+1)×4`：`Ad = coef(1:4,:)'`（转置！），`Bd = coef(5,:)'`。
  忘了转置会让 Ad 维度错、`eig` 结果错。
- 连续映射用**主值对数** `log(ev)/dt`（不是 `logm`、不是 `(ev-1)/dt`）。
- 选 SP 对看 **`abs(s)` 最大**，不是 `abs(eig(Ad))` 最大——长周期数贴近单位圆
  （|λ|≈1）但映射到连续 s≈0，`|s|` 很小，天然被排除。
- 只判 SP 对（共轭对两支任取一支，`wn=abs`、`zeta=-real/wn` 对两支一致）。

---

## H2 裕度族骨架（margin 输出顺序是核心陷阱）

给单回路 `L(s)=num/den`，或内环+外环级联，求 `gm_db / pm_deg / w_gc / w_pc`。
自造 worked example（单回路 type-1 `num=[2] den=[1,7,12,0]`，级联内环
`1/(s(s+7))` ki=5、外环 `2.2/(s(s+5))`，均避开考题参数）：

```matlab
% ===== worked example A：单回路 type-1 裕度 =====
num = [2.0]; den = [1.0, 7.0, 12.0, 0.0];   % = s(s+3)(s+4)，含积分器
L = tf(num, den);
% margin(L) 返回顺序 [Gm, Pm, Wcg, Wcp]，四个输出**逐个按序**落键：
[Gm, Pm, Wcg, Wcp] = margin(L);
gm_db  = 20 * log10(Gm);    % 线性增益裕度 -> dB（不要直接把 Gm 当 dB）
pm_deg = Pm;                % 相位裕度，已是度
w_gc   = Wcg;               % 第 3 输出 -> w_gc（增益穿越频率）
w_pc   = Wcp;               % 第 4 输出 -> w_pc（相位穿越频率）
r = struct('gm_db', gm_db, 'pm_deg', pm_deg, 'w_gc', w_gc, 'w_pc', w_pc);
fid = fopen('result.json','w'); fwrite(fid, jsonencode(r)); fclose(fid);
```

```matlab
% ===== worked example B：级联回路（内环先闭合再级联）=====
s = tf('s');
G_in    = 1 / (s * (s + 7.0));        % 内环被控对象
G_in_cl = feedback(5.0 * G_in, 1);    % 内环单位负反馈闭合（feedback 默认负反馈）
G_out   = 2.2 / (s * (s + 5.0));      % 外环
Lcasc   = G_out * G_in_cl;            % 总开环 = 外环 × 闭合后的内环
[Gm, Pm, Wcg, Wcp] = margin(Lcasc);
r = struct('gm_db', 20*log10(Gm), 'pm_deg', Pm, 'w_gc', Wcg, 'w_pc', Wcp);
fid = fopen('result.json','w'); fwrite(fid, jsonencode(r)); fclose(fid);
```

要点（裕度族的核心，双模型都栽在对调上）：

- **`margin(L)` 的第三输出 `Wcg` 直接落 `w_gc`，第四输出 `Wcp` 直接落 `w_pc`**，
  按序、不做任何「物理语义」重命名。判分参考就是按这个原始顺序生成的，
  任何「`w_gc` 听起来是增益穿越所以应该取另一个输出」的再映射都会得 0.5 分
  （见陷阱 #2）。
- `gm_db` 必须 `20*log10(Gm)`；`Gm` 是线性的，直接写 `Gm` 当 dB 会错一个量级。
- `pm_deg` 就是 `margin` 的第二输出 `Pm`，单位已是度。
- 级联顺序不可颠倒：**先** `feedback` 闭合内环（`G_in_cl`），**再**乘外环得到
  总开环 `L`；`feedback(ki*G_in, 1)` 第二参 `1` 表示单位负反馈（缺省即负反馈）。

---

## 已知陷阱（本 harness 三套基线实测的失败点，只写实证过的）

1. **辨识族：管线结构错 → `code_not_executable`（全灭主因）**。minimax-m3 辨识族
   3/4、glm-4.6 与 glm-5.3 全 4/4 都栽在「LS 回归 + 离散→连续 + 选 SP 对」的脚本
   上（matlab 退出码 1）。三处结构性坑：`coef` 转置、`log(ev)/dt` 主值映射、
   按 `abs(s)` 而非 `abs(eig)` 选对——严格照 H1 骨架的 step 1–4 即避开。
2. **裕度族：`w_gc`/`w_pc` 对调（三家共犯）**。minimax-m3 在 margin_01/03、
   glm-4.6 与 glm-5.3 都出现 0.5 分——模型把「增益穿越频率/相位穿越频率」按
   物理直觉去重新分配 `Wcg`/`Wcp`，而判分参考按 `margin` 的**原始输出顺序**
   （第三→`w_gc`、第四→`w_pc`）生成。正确做法就是直接按序落键，不要重命名。
3. **`gm_db` 忘乘 `20*log10`**。`margin` 给出的 `Gm`（第一个输出）是线性增益裕度；
   题面 `gm_db` 要求 dB——写 `Gm` 原值当 dB，数值错十几个 dB。
4. **级联回路直接 `margin(G_out*G_in)` 漏掉内环闭合**。级联题必须先把内环用
   `feedback` 闭合（`G_in_cl`）再乘外环；跳过闭合会拿到另一个对象的裕度。
5. **辨识族只输出题给的键**。`result.json` 键须逐字为 `omega_sp_id`/`zeta_sp_id`
   （裕度族为 `gm_db/pm_deg/w_gc/w_pc`）；多写、错写键都触发 requirements 与
   physics 双重扣分。
6. **辨识族：忘记照抄题面数据 → `code_not_executable`**。minimax-m3 在注入
   脚手架后仍把「数据已给」误读成「X/u 是预置变量」，脚本里只写
   `X1 = X(1:end-1,:)` 而不写 `X = [...];`，结果 matlab 报「无法对 'X' 进行索引」。
   **必须把题面的 `X`/`u`/`dt` 三行数值整段抄进脚本**（见 H1 骨架的 ⚠️ 警告）。

不确定的（参数取值细节、各题具体数值）不写——上面每条都能在
`results/gtm.transport_control_hard/` 既有基线逐题取证。
