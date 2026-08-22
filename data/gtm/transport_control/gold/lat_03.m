%% gold 解（gtm.transport_control / lat_03）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A = [-0.14 0.02 -0.88 0.055; -8.5 -1.45 -0.06 0.0; 1.55 -0.05 -0.42 0.0; 0.0 1.0 0.0 0.0];
ev = eig(A);
cpx = ev(imag(ev) > 0);            % 荷兰滚对（结构已验证：恰一对）
rl  = ev(abs(imag(ev)) < 1e-9);    % 两个实根（结构已验证）
lam = cpx(1);
wn_dr = abs(lam); z_dr = -real(lam) / wn_dr;
roll_lam = min(real(rl)); spiral_lam = max(real(rl));
r = struct('dutch_roll_omega', wn_dr, 'dutch_roll_zeta', z_dr, ...
           'roll_mode_lambda', roll_lam, 'spiral_mode_lambda', spiral_lam);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
