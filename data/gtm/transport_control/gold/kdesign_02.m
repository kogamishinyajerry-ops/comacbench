%% gold 解（gtm.transport_control / kdesign_02）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A = [-0.0062 0.048 0.0 -32.174; -0.044 -0.82 640.0 0.0; 0.0 -0.0068 -1.08 0.0; 0.0 0.0 1.0 0.0];
B = [0.0; -5.0; -5.5; 0.0];
wn_cl = 2.3; z_cl = 0.55;
ev = eig(A);
lam = ev(imag(ev) > 0);
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);
ph = lam(2);                                   % 长周期对（保持不动）
sp_cl = -z_cl * wn_cl + 1i * wn_cl * sqrt(1 - z_cl^2);
K = place(A, B, [ph; conj(ph); sp_cl; conj(sp_cl)]);
evcl = eig(A - B * K);
lamcl = evcl(imag(evcl) > 0);
[~, ordc] = sort(abs(lamcl), 'descend');
lamcl = lamcl(ordc);
wn1 = abs(lamcl(1)); ze1 = -real(lamcl(1)) / wn1;
r = struct('cl_omega_sp', wn1, 'cl_zeta_sp', ze1);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
