%% gold 解（gtm.transport_control / trim_02）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
W = 280000.0; S = 2730.0; h = 35000.0; V = 780.0;
CLa = 5.6; CL0 = 0.18; CD0 = 0.019; kk = 0.045;
rho0 = 0.0023769;
rho = rho0 * exp(-h / 23800.0);
qbar = 0.5 * rho * V^2;
CLfun = @(al) CL0 + CLa * al;          % alpha in rad
al = fzero(@(a) qbar * S * CLfun(a) - W, deg2rad(2.0));   % L = W
CL = CLfun(al);
CD = CD0 + kk * CL^2;
Thr = qbar * S * CD;                   % 定直平飞 D = T
r = struct('alpha_trim_deg', rad2deg(al), 'thrust_lbf', Thr);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
