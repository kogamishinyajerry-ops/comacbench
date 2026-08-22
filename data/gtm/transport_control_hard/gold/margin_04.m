%% gold 解（gtm.transport_control_hard / margin_04）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
s = tf('s');
ai = 4.0; ki = 9.0; aout = 4.0; Kout = 3.0;
G_in = 1 / (s * (s + ai));
G_in_cl = feedback(ki * G_in, 1);        % 内环单位反馈闭合
G_out = Kout / (s * (s + aout));          % 外环
L = G_out * G_in_cl;                       % 级联总开环
[Gm, Pm, Wcg, Wcp] = margin(L);
gm_db = 20 * log10(Gm);
r = struct('gm_db', gm_db, 'pm_deg', Pm, 'w_gc', Wcg, 'w_pc', Wcp);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
