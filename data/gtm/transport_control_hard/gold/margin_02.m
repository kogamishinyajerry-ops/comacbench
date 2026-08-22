%% gold 解（gtm.transport_control_hard / margin_02）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
num = [9.0];
den = [1.0; 5.0; 6.0; 0.0];
L = tf(num', den');
[Gm, Pm, Wcg, Wcp] = margin(L);
gm_db = 20 * log10(Gm);
r = struct('gm_db', gm_db, 'pm_deg', Pm, 'w_gc', Wcg, 'w_pc', Wcp);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
