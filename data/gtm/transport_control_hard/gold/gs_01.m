%% gold 解（gtm.transport_control_hard / gs_01）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A1 = [-0.0064 0.038 0.0 -32.174; -0.031 -0.71 740.0 0.0; 0.0 -0.0051 -0.9 0.0; 0.0 0.0 1.0 0.0];
B1 = [0.0; -6.0; -4.0; 0.0];
A2 = [-0.0059 0.026 0.0 -32.174; -0.019 -0.55 700.0 0.0; 0.0 -0.0034 -0.64 0.0; 0.0 0.0 1.0 0.0];
B2 = [0.0; -6.0; -4.0; 0.0];
A3 = [-0.0057 0.02 0.0 -32.174; -0.015 -0.5 660.0 0.0; 0.0 -0.003 -0.58 0.0; 0.0 0.0 1.0 0.0];
B3 = [0.0; -6.0; -4.0; 0.0];
wnt = [2.0, 1.9, 1.7]; zet = [0.6, 0.55, 0.5];
clw = zeros(1,3); clz = zeros(1,3);
for jj = 1:3
  if jj == 1, Acur = A1; Bcur = B1; elseif jj == 2, Acur = A2; Bcur = B2; else, Acur = A3; Bcur = B3; end
  wn = wnt(jj); ze = zet(jj);
  ev = eig(Acur);
  lam = ev(imag(ev) > 0);
  [~, ord] = sort(abs(lam), 'descend');
  lam = lam(ord);
  ph = lam(2);                          % 长周期对保持不动
  sp = -ze*wn + 1i*wn*sqrt(1-ze^2);
  K = place(Acur, Bcur, [ph; conj(ph); sp; conj(sp)]);
  evcl = eig(Acur - Bcur*K);
  lamcl = evcl(imag(evcl) > 0);
  [~, ordc] = sort(abs(lamcl), 'descend');
  lamcl = lamcl(ordc);
  clw(jj) = abs(lamcl(1)); clz(jj) = -real(lamcl(1))/abs(lamcl(1));
end
r = struct('cl_omega_sp_1', clw(1), 'cl_zeta_sp_1', clz(1), ...
           'cl_omega_sp_2', clw(2), 'cl_zeta_sp_2', clz(2), ...
           'cl_omega_sp_3', clw(3), 'cl_zeta_sp_3', clz(3));
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
