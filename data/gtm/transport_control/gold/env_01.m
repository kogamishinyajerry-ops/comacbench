%% gold 解（gtm.transport_control / env_01）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A1 = [-0.006 0.046 0.0 -32.174; -0.043 -0.8 760.0 0.0; 0.0 -0.0062 -1.02 0.0; 0.0 0.0 1.0 0.0];
A2 = [-0.0058 0.036 0.0 -32.174; -0.031 -0.68 710.0 0.0; 0.0 -0.0048 -0.88 0.0; 0.0 0.0 1.0 0.0];
A3 = [-0.0056 0.026 0.0 -32.174; -0.021 -0.56 650.0 0.0; 0.0 -0.0036 -0.66 0.0; 0.0 0.0 1.0 0.0];
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
