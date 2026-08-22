%% gold 解（gtm.transport_control_hard / mc_01）——判分参考预计算用，模型不可见。
% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。
V = 710.0; 
Xu = -0.0066; Xw = 0.039; Zu = -0.032;
Zw0 = -0.72; Mw0 = -0.0053; Mq0 = -0.9;
Zde = -6.0; Mde = -4.0;
wn_cl = 2.0; z_cl = 0.6;
pct = 0.25; wn_lo = 1.88; wn_hi = 2.12; z_th = 0.51;
seed = 20260827; Ns = 200;
G = 32.174;
A0 = [Xu Xw 0 -G; Zu Zw0 V 0; 0 Mw0 Mq0 0; 0 0 1 0];
B = [0; Zde; Mde; 0];
ev0 = eig(A0);
lam0 = ev0(imag(ev0) > 0); [~, ord0] = sort(abs(lam0), 'descend'); lam0 = lam0(ord0);
ph = lam0(2);
sp = -z_cl*wn_cl + 1i*wn_cl*sqrt(1-z_cl^2);
K = place(A0, B, [ph; conj(ph); sp; conj(sp)]);
% 200 确定性采样：rng(seed) 独立均匀盒缩放 Mw/Zw/Mq
rng(seed);
fM = 1 + pct * (2*rand(Ns,1) - 1);
rng(seed + 1000);
fZ = 1 + pct * (2*rand(Ns,1) - 1);
rng(seed + 2000);
fx = 1 + pct * (2*rand(Ns,1) - 1);
npass = 0;
for jj = 1:Ns
  Acur = [Xu Xw 0 -G; Zu Zw0*fZ(jj) V 0; 0 Mw0*fM(jj) Mq0*fx(jj) 0; 0 0 1 0];
  evc = eig(Acur - B*K);
  lamc = evc(imag(evc) > 0);
  [~, ordc] = sort(abs(lamc), 'descend');
  lamc = lamc(ordc);
  wnx = abs(lamc(1)); zex = -real(lamc(1))/abs(lamc(1));
  if wnx >= wn_lo && wnx <= wn_hi && zex >= z_th
    npass = npass + 1;
  end
end
r = struct('pass_fraction', npass / Ns, 'failing_case_count', Ns - npass);
fid = fopen('result.json', 'w');
fwrite(fid, jsonencode(r));
fclose(fid);
