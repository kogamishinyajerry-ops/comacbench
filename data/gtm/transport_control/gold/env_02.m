%% gold 解（gtm.transport_control / env_02）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A1 = [-0.0058 0.05 0.0 -32.174; -0.046 -0.84 800.0 0.0; 0.0 -0.0068 -1.1 0.0; 0.0 0.0 1.0 0.0];
A2 = [-0.006 0.04 0.0 -32.174; -0.034 -0.72 745.0 0.0; 0.0 -0.0054 -0.94 0.0; 0.0 0.0 1.0 0.0];
A3 = [-0.0062 0.03 0.0 -32.174; -0.024 -0.6 680.0 0.0; 0.0 -0.0042 -0.76 0.0; 0.0 0.0 1.0 0.0];
for jj = 1:3
  if jj == 1, Acur = A1; elseif jj == 2, Acur = A2; else, Acur = A3; end
  ev = eig(Acur);
  lam = ev(imag(ev) > 0);
  [~, ord] = sort(abs(lam), 'descend');
  lam = lam(ord);
  wnv(jj) = abs(lam(1)); zev(jj) = -real(lam(1)) / abs(lam(1));
end
r = struct('omega_sp_1', wnv(1), 'zeta_sp_1', zev(1), ...
           'omega_sp_2', wnv(2), 'zeta_sp_2', zev(2), ...
           'omega_sp_3', wnv(3), 'zeta_sp_3', zev(3));
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
