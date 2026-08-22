%% gold 解（gtm.transport_control / repair_01）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
% 真机构纵向模型（修复后）；损坏参数 Mw 的正确值 = -0.0055。
A_true = [-0.0068 0.04 0.0 -32.174; -0.035 -0.72 700.0 0.0; 0.0 -0.0055 -0.95 0.0; 0.0 0.0 1.0 0.0];
ev = eig(A_true);
lam = ev(imag(ev) > 0);
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);
wn = abs(lam); ze = -real(lam) ./ wn;
% 复核：修复后 SP 模态与题面参考一致（wn(1)=omega_sp, ze(1)=zeta_sp）
assert(abs(wn(1) - 2.1294093202125235) < 1e-6);
assert(abs(ze(1) - 0.3921769206877866) < 1e-6);
r = struct('corrupted_param', 'Mw', 'restored_value', -0.0055);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
