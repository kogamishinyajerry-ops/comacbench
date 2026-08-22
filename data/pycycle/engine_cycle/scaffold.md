# pycycle.engine_cycle — H2/H3 脚手架（蒸馏工作流资产 v1）

> 用途：harness 臂 H2/H3 的 prompt 注入件（`--scaffold data/pycycle/engine_cycle/scaffold.md`）。
> 蒸馏来源：om-pycycle 官方 simple_turbojet 范式（Apache-2.0，经 data/pycycle/engine_cycle/
> turbojet_engine.py 收敛性验证）+ 本 harness 审计的模型失败模式（API 幻觉为 M3/GLM
> 双模型 0/28 全灭的主因）。
> 防泄漏纪律：worked example 参数 (9300, 2380, 12.2) 经 grep 验证不在任何任务参数域；
> 不含任何任务的参考输出值。判分仍要求模型自行正确收敛与数值命中。

## 你要做的事

任务全部是：用已装好的 `pycycle`（om-pycycle，`import pycycle.api as pyc`）构造
simple turbojet 循环并在 SL 设计点求解，把结果写进 `result.json`。失败几乎都出在
API 组装细节，按下面的骨架写就能避开。

## 可运行的完整骨架（示例参数与任何考题不同）

```python
import json
import openmdao.api as om
import pycycle.api as pyc


class Turbojet(pyc.Cycle):
    def setup(self):
        self.options['thermo_method'] = 'TABULAR'
        self.options['thermo_data'] = pyc.AIR_JETA_TAB_SPEC
        design = self.options['design']

        self.add_subsystem('fc', pyc.FlightConditions())
        self.add_subsystem('inlet', pyc.Inlet())
        self.add_subsystem('comp', pyc.Compressor(map_data=pyc.AXI5, map_extrap=True),
                           promotes_inputs=['Nmech'])
        self.add_subsystem('burner', pyc.Combustor(fuel_type="FAR"))
        self.add_subsystem('turb', pyc.Turbine(map_data=pyc.LPT2269),
                           promotes_inputs=['Nmech'])
        self.add_subsystem('nozz', pyc.Nozzle(nozzType='CD', lossCoef='Cv'))
        self.add_subsystem('shaft', pyc.Shaft(num_ports=2), promotes_inputs=['Nmech'])
        self.add_subsystem('perf', pyc.Performance(num_nozzles=1, num_burners=1))

        self.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I', connect_w=False)
        self.pyc_connect_flow('inlet.Fl_O', 'comp.Fl_I')
        self.pyc_connect_flow('comp.Fl_O', 'burner.Fl_I')
        self.pyc_connect_flow('burner.Fl_O', 'turb.Fl_I')
        self.pyc_connect_flow('turb.Fl_O', 'nozz.Fl_I')

        self.connect('comp.trq', 'shaft.trq_0')
        self.connect('turb.trq', 'shaft.trq_1')
        self.connect('fc.Fl_O:stat:P', 'nozz.Ps_exhaust')
        self.connect('inlet.Fl_O:tot:P', 'perf.Pt2')
        self.connect('comp.Fl_O:tot:P', 'perf.Pt3')
        self.connect('burner.Wfuel', 'perf.Wfuel_0')
        self.connect('inlet.F_ram', 'perf.ram_drag')
        self.connect('nozz.Fg', 'perf.Fg_0')

        balance = self.add_subsystem('balance', om.BalanceComp())
        if design:
            balance.add_balance('W', units='lbm/s', eq_units='lbf', rhs_name='Fn_target')
            self.connect('balance.W', 'inlet.Fl_I:stat:W')
            self.connect('perf.Fn', 'balance.lhs:W')
            balance.add_balance('FAR', eq_units='degR', lower=1e-4, val=.017,
                                rhs_name='T4_target')
            self.connect('balance.FAR', 'burner.Fl_I:FAR')
            self.connect('burner.Fl_O:tot:T', 'balance.lhs:FAR')
            balance.add_balance('turb_PR', val=1.5, lower=1.001, upper=8,
                                eq_units='hp', rhs_val=0.)
            self.connect('balance.turb_PR', 'turb.PR')
            self.connect('shaft.pwr_net', 'balance.lhs:turb_PR')
        else:
            balance.add_balance('FAR', eq_units='lbf', lower=1e-4, val=.3,
                                rhs_name='Fn_target')
            self.connect('balance.FAR', 'burner.Fl_I:FAR')
            self.connect('perf.Fn', 'balance.lhs:FAR')
            balance.add_balance('Nmech', val=1.5, units='rpm', lower=500.,
                                eq_units='hp', rhs_val=0.)
            self.connect('balance.Nmech', 'Nmech')
            self.connect('shaft.pwr_net', 'balance.lhs:Nmech')
            balance.add_balance('W', val=168.0, units='lbm/s', eq_units='inch**2')
            self.connect('balance.W', 'inlet.Fl_I:stat:W')
            self.connect('nozz.Throat:stat:area', 'balance.lhs:W')

        newton = self.nonlinear_solver = om.NewtonSolver()
        newton.options['atol'] = 1e-6
        newton.options['rtol'] = 1e-6
        newton.options['maxiter'] = 15
        newton.options['solve_subsystems'] = True
        newton.options['max_sub_solves'] = 100
        newton.options['reraise_child_analysiserror'] = False
        self.linear_solver = om.DirectSolver()
        super().setup()


class MPTurbojet(pyc.MPCycle):
    def setup(self):
        self.pyc_add_pnt('DESIGN', Turbojet())
        self.set_input_defaults('DESIGN.Nmech', 8070.0, units='rpm')
        self.set_input_defaults('DESIGN.inlet.MN', 0.60)
        self.set_input_defaults('DESIGN.comp.MN', 0.020)
        self.set_input_defaults('DESIGN.burner.MN', 0.020)
        self.set_input_defaults('DESIGN.turb.MN', 0.4)
        self.pyc_add_cycle_param('burner.dPqP', 0.03)
        self.pyc_add_cycle_param('nozz.Cv', 0.99)

        self.od_pts = ['OD0', 'OD1']
        self.od_MNs = [0.000001, 0.2]
        self.od_alts = [0.0, 5000]
        self.od_Fns = [11000.0, 8000.0]
        for i, pt in enumerate(self.od_pts):
            self.pyc_add_pnt(pt, Turbojet(design=False))
            self.set_input_defaults(pt + '.fc.MN', val=self.od_MNs[i])
            self.set_input_defaults(pt + '.fc.alt', self.od_alts[i], units='ft')
            self.set_input_defaults(pt + '.balance.Fn_target', self.od_Fns[i], units='lbf')
        self.pyc_use_default_des_od_conns()
        self.pyc_connect_des_od('nozz.Throat:stat:area', 'balance.rhs:W')
        super().setup()


prob = om.Problem()
mp = prob.model = MPTurbojet()
prob.set_solver_print(level=-1)
prob.setup(check=False)

# ---- 设计点工况（示例值；考题按题面替换）----
prob.set_val('DESIGN.fc.alt', 0, units='ft')
prob.set_val('DESIGN.fc.MN', 0.000001)
prob.set_val('DESIGN.balance.Fn_target', 9300.0, units='lbf')   # 示例
prob.set_val('DESIGN.balance.T4_target', 2380.0, units='degR')  # 示例
prob.set_val('DESIGN.comp.PR', 12.2)                            # 示例
prob.set_val('DESIGN.comp.eff', 0.83)
prob.set_val('DESIGN.turb.eff', 0.86)

# ---- 初值（Newton 收敛关键；偏离太远会发散）----
prob['DESIGN.balance.FAR'] = 0.0175506829934
prob['DESIGN.balance.W'] = 168.453135137
prob['DESIGN.balance.turb_PR'] = 4.46138725662
prob['DESIGN.fc.balance.Pt'] = 14.6955113159
prob['DESIGN.fc.balance.Tt'] = 518.665288153
for pt in mp.od_pts:
    prob[pt + '.balance.W'] = 166.073
    prob[pt + '.balance.FAR'] = 0.01680
    prob[pt + '.balance.Nmech'] = 8197.38
    prob[pt + '.fc.balance.Pt'] = 15.703
    prob[pt + '.fc.balance.Tt'] = 558.31
    prob[pt + '.turb.PR'] = 4.6690

prob.run_model()

Fn = float(prob.get_val('DESIGN.perf.Fn', units='lbf')[0])
TSFC = float(prob.get_val('DESIGN.perf.TSFC', units='lbm/h/lbf')[0])
Wfuel = float(prob.get_val('DESIGN.burner.Wfuel', units='lbm/s')[0])
OPR = float(prob.get_val('DESIGN.comp.Fl_O:tot:P')[0]
            / prob.get_val('DESIGN.inlet.Fl_O:tot:P')[0])

json.dump({"Fn_lbf": Fn, "TSFC": TSFC, "OPR": OPR, "Wfuel_lbm_s": Wfuel},
          open("result.json", "w"), indent=1)
```

## 已知陷阱（本 harness 审计实证的失败点）

1. **`import pycycle` 直接失败**——包名是 `pycycle.api as pyc`（pip 名 om-pycycle）。
2. **不用 BalanceComp 手动调 FAR/W**——必须让 Newton 解设计平衡，手调不收敛。
3. **初值缺省**——官方初值（上面那组数）是收敛域内的；乱猜初值 15 次迭代内不收敛。
4. **单位串**——set_val 必须带 units（lbf/degR/ft/rpm），裸数按默认单位错位。
5. **OD 点必须有**——MPCycle 框架要求至少一个 OD 点且 `pyc_use_default_des_od_conns()`；
   只跑 DESIGN 也照样要建 OD 占位。
6. **Nmech 提升到顶层**——comp/turb/shaft 三个的 `promotes_inputs=['Nmech']` 缺一即
   未连接错误。
7. result.json 键名严格照题面（Fn_lbf/TSFC/OPR/Wfuel_lbm_s 等），数值键 1% 相对容差。
