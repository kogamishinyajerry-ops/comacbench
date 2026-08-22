%% gold 解（gtm.transport_control_hard / trimnl_03）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
W = 200000.0; S = 2100.0; h = 27000.0; V = 700.0;
gam = deg2rad(4.0); phi = deg2rad(25.0);
CLa = 4.9; CL0 = 0.12; CLde = 0.4; CD0 = 0.023; kk = 0.041;
iT = deg2rad(2.0); zT = 1.8; cbar = 16.0;
Cm0 = 0.018; Cma = -0.28; Cmde = -0.8;
rho0 = 0.0023769;
rho = rho0 * exp(-h / 23800.0);
q = 0.5 * rho * V^2;
res = @(x) [ q*S*(CL0 + CLa*x(1) + CLde*x(3))*cos(phi) + x(2)*sin(x(1)+iT) - W*cos(gam);
             x(2)*cos(x(1)+iT) - q*S*(CD0 + kk*(CL0+CLa*x(1)+CLde*x(3))^2) - W*sin(gam);
             q*S*cbar*(Cm0 + Cma*x(1) + Cmde*x(3)) + x(2)*sin(iT)*zT ];
x = [deg2rad(3.0); 20000.0; deg2rad(-1.0)];   % 初值
for it = 1:60
  f = res(x);
  if norm(f) < 1e-12, break; end
  J = zeros(3,3); eps = 1e-6;
  for j = 1:3
    xp = x; xp(j) = xp(j) + eps;
    J(:, j) = (res(xp) - f) / eps;
  end
  x = x - J \ f;
end
nf = cos(gam) / cos(phi);
r = struct('alpha_trim_deg', rad2deg(x(1)), 'thrust_lbf', x(2), ...
           'delta_e_trim_deg', rad2deg(x(3)), 'load_factor', nf);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
