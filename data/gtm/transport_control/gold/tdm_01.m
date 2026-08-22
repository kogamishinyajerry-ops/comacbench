%% gold 解（gtm.transport_control / tdm_01）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
A = [-0.55 1.0; -3.9 -1.3];
B = [0.0; 1.0];
C = [1.0 0.0];
dt = 0.01; Tend = 30.0; N = round(Tend / dt);
Ad = expm(A * dt);
Bd = A \ ((Ad - eye(2)) * B);
x = zeros(2, 1); y = zeros(N + 1, 1); y(1) = C * x;
for kk = 1:N
  x = Ad * x + Bd;
  y(kk + 1) = C * x;
end
yinf = -(C * (A \ B)); yinf = yinf(1);
t = (0:N)' * dt;
t10 = NaN; t90 = NaN;
for kk = 1:N
  if isnan(t10) && (y(kk) - 0.1 * yinf) * (y(kk + 1) - 0.1 * yinf) <= 0 && y(kk + 1) ~= y(kk)
    t10 = t(kk) + dt * (0.1 * yinf - y(kk)) / (y(kk + 1) - y(kk));
  end
  if isnan(t90) && (y(kk) - 0.9 * yinf) * (y(kk + 1) - 0.9 * yinf) <= 0 && y(kk + 1) ~= y(kk)
    t90 = t(kk) + dt * (0.9 * yinf - y(kk)) / (y(kk + 1) - y(kk));
  end
end
overshoot = (max(y) - yinf) / abs(yinf) * 100;
band = 0.02 * abs(yinf);
viol = find(abs(y - yinf) > band);
tset = t(viol(end));
r = struct('rise_time_s', t90 - t10, 'overshoot_pct', overshoot, 'settling_time_s', tset);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
