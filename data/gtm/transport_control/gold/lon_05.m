%% gold 解（gtm.transport_control / lon_05）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A = [-0.0055 0.03 0.0 -32.174; -0.025 -0.62 745.0 0.0; 0.0 -0.0042 -0.75 0.0; 0.0 0.0 1.0 0.0];
ev = eig(A);
lam = ev(imag(ev) > 0);            % 每对共轭取一个（结构已验证：恰两对）
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);                    % 大模=短周期，小模=长周期
wn = abs(lam); ze = -real(lam) ./ wn;
r = struct('omega_sp', wn(1), 'zeta_sp', ze(1), 'omega_ph', wn(2), 'zeta_ph', ze(2));
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
