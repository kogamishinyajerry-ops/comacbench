%% gold 解（gtm.transport_control / lon_04）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A = [-0.0075 0.055 0.0 -32.174; -0.048 -0.78 660.0 0.0; 0.0 -0.0072 -1.05 0.0; 0.0 0.0 1.0 0.0];
ev = eig(A);
lam = ev(imag(ev) > 0);            % 每对共轭取一个（结构已验证：恰两对）
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);                    % 大模=短周期，小模=长周期
wn = abs(lam); ze = -real(lam) ./ wn;
r = struct('omega_sp', wn(1), 'zeta_sp', ze(1), 'omega_ph', wn(2), 'zeta_ph', ze(2));
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
