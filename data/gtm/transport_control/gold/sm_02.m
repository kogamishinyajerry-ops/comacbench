%% gold 解（gtm.transport_control / sm_02）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
CLa = 4.8; Cma = -1.1; hcg = 0.3;
sm = -Cma / CLa;          % 静稳定裕度（无量纲，弦长分数）
hn = hcg + sm;            % 中性点位置
r = struct('static_margin', sm, 'h_n', hn);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
