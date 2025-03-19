import os

cpu_lim = 1
os.environ['OMP_NUM_THREADS'] = str(cpu_lim)
os.environ['OPENBLAS_NUM_THREADS'] = str(cpu_lim)
os.environ['MKL_NUM_THREADS'] = str(cpu_lim)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(cpu_lim)
os.environ['NUMEXPR_NUM_THREADS'] = str(cpu_lim)
import autograd.numpy as np
import torch
import time
import pickle
import re
import math
import cma

def perf_recovery(perf0):
    y = np.zeros(6)
    y[0] = - perf0[0]*1e3  # FOM=-y[0]*1e3
    y[1] = - perf0[1]*85+85
    y[3] = - perf0[3]*55+55
    y[2] = - perf0[2]*7e5+7e5
    y[4] = perf0[4]*(2.5e-4)+(2.5e-4)
    y[5] = perf0[5]*0.7+0.7
    s = "current performance: gain: {}, GBW: {}, PM: {}, power: {}, Q: {}, FOM: {}".format(y[1], y[2], y[3], y[4], y[5], y[0])
    return s, y


def sizing_recovery(x0, names, bounds):
    print('x0', x0)
    print('bounds', bounds)
    x = x0*(bounds[1]-bounds[0])+bounds[0]
    s0 = ['{}: {}'.format(names[i], x[i]) for i in range(len(x))]
    s = 'current sizing: {'+', '.join(s0) + '}\n'
    return s, x
    

def opt_summary(best_x, obj, cons, names, bounds):
    best_cons = np.sum(np.maximum(cons, 0))
    best_sizing_r, best_sizing = sizing_recovery(best_x, names, bounds)
    best_perf_r, best_perf = perf_recovery(np.concatenate(([obj], cons)))
    print(best_sizing_r)
    print(best_perf_r)
    return {'current_sizing': best_sizing_r, 'current_metrics': best_perf_r, 'current_fom': obj, 'current_cons': best_cons, 'current_sizing': best_sizing, 'current_perf': best_perf}
    

def parse_pz_analysis(file_path):
    poles = []
    with open(file_path, 'r') as file:
        lines = file.readlines()

        pz_section = False
        for line in lines:
            if "poles ( hertz)" in line:
                pz_section = True
                continue

            if "zeros ( hertz)" in line:
                pz_section = False
                continue

            if pz_section:
                match = re.match(
                    r"(-?\d+\.\d+[a-zA-Z]?)\s+(-?\d+\.\d*[a-zA-Z]?)\s+(-?\d+\.\d+[a-zA-Z]?)\s+(-?\d+\.\d*[a-zA-Z]?)",
                    line.strip())
                if match:
                    real_part_hz = match.group(3)
                    imag_part_hz = match.group(4)
                    real_val_hz = convert(real_part_hz)
                    imag_val_hz = convert(imag_part_hz)

                    poles.append((real_val_hz, imag_val_hz))

    return poles


def calculate_quality_factor(poles):
    q_factor = 0
    seen_pairs = set()
    for i in range(len(poles)):
        real1, imag1 = poles[i]
        for j in range(i + 1, len(poles)):
            real2, imag2 = poles[j]
            if real1 == real2 and imag1 == -imag2:
                q_factor = math.sqrt(real1 * real1 + imag1 * imag1) / (2 * abs(real1))
                seen_pairs.add((real1, imag1))
        if q_factor:
            break
    return q_factor


class CachedClosure:
    def __init__(self, function, extra_args):
        self.function = function
        self.extra_args = extra_args
        self.cache = {}
 
    def __call__(self, x):
        x = tuple(x)
        if x not in self.cache:
            self.cache[x] = self.function(x, *self.extra_args)
        return self.cache[x]
 
def circuit_simulation(x, names, bounds, circuit_dir):
    mean = bounds[0]
    delta = bounds[1] - bounds[0]
    sizing = x * delta + mean

    param_file = os.path.join(circuit_dir, 'param')
    performance_file = os.path.join(circuit_dir, '3stage.ma0')
    sp_file = os.path.join(circuit_dir, '3stage.sp')
    output_name = os.path.join(circuit_dir, '3stage')

    power = 0
    assert len(names) == len(sizing), "unequal parameter and sizing length"

    with open(param_file, 'w') as f:
        for i in range(len(names)):
            if names[i][0] in ['g', 'G']:
                power += np.abs(sizing[i])
            f.write('.param ' + names[i] + ' = ' + str(sizing[i]) + '\n')

    power = power * 1.8 / 20

    # hspice simulation
    os.system('hspice64 -C -i {} -o {}'.format(sp_file, output_name))

    # get results
    with open(performance_file, 'r') as f:
        lines = f.readlines()
        line = lines[4].strip().split()
        gain = convert(line[0])

        if convert(line[0]) < 0 or line[1] == "failed":
            ugf = 0
            pm = 0
            q = 1
        else:
            ugf = convert(line[1])
            ph = float(line[2])

            result_file = os.path.join(circuit_dir, '3stage.lis')
            poles = parse_pz_analysis(result_file)
            q = calculate_quality_factor(poles)
            id = []
            gain_list = []
            phase_list = []
            with open(result_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line = line.strip().split()
                    if len(line) > 0 and line[0] == 'freq':
                        id.append(i)
                    if len(id) == 2:
                        break
                for i in range(901):
                    gain_list.append(convert(lines[id[0] + i + 2].strip().split()[1]))
                    phase_list.append(convert(lines[id[1] + i + 2].strip().split()[1]))
            gain_id = 0
            for i in range(len(gain_list)):
                if gain_list[i] < 0:
                    gain_id = i
                    break
            if -180 < phase_list[0] < -90 or 0 < phase_list[0] < 90:
                pm = -180
            else:
                phase_id = 0
                valid_phase = True
                if 90 < phase_list[0] < 180:
                    rev = True
                    for i in range(len(phase_list)):
                        if phase_list[i] < 0:
                            phase_id = i
                            break
                else:
                    rev = False
                    for i in range(len(phase_list)):
                        if phase_list[i] > 0:
                            phase_id = i
                            break
                for i in range(1, max(gain_id + 1, phase_id)):
                    if phase_list[i] > phase_list[i - 1]:
                        valid_phase = False
                        break
                if not valid_phase:
                    pm = -180
                else:
                    valid_gain = True
                    for i in range(1, max(gain_id, phase_id) + 1):
                        if gain_list[i] > gain_list[i - 1]:
                            valid_gain = False
                            break
                    if gain_list[phase_id - 1] > 0:
                        valid_gain = False
                    if not valid_gain:
                        pm = -180
                    elif rev:
                        pm = ph
                    else:
                        pm = ph + 180

        y = np.zeros(6)
        y[0] = - ugf / power / 1e11  # FOM=-y[0]*1e3
        y[1] = - (gain - 85) / 85
        y[3] = - (pm - 55) / 55
        y[2] = - (ugf - 7e5) / 7e5
        y[4] = (power - 2.5e-4) / (2.5e-4)
        y[5] = (q - 0.7) / 0.7
    return y[0], y[1:]


 

def sizing(circuit_dir, param_names, sizing_bounds):
    iteration = 100
    cached_closure = CachedClosure(circuit_simulation, (param_names, sizing_bounds, circuit_dir))

    def objective_functions(x):
        obj, _ = cached_closure(x)
        return obj
    
    def constraint_functions(x):
        _, constr = cached_closure(x)
        return constr

    cfun = cma.ConstrainedFitnessAL(objective_functions, constraint_functions, find_feasible_first=True)
    es = cma.CMAEvolutionStrategy(len(param_names) * [0.5], 0.2, {'bounds': [[0] * len(param_names), [1] * len(param_names)], 'tolstagnation': 0, 'verbose':-9, 'maxfevals': iteration})  # verbosity for doctest only
    es = es.optimize(cfun, callback=cfun.update)
    best_x = cfun.best_feas.x
    x = es.result.xfavorite
    if best_x is None:
        best_x = x

    obj = objective_functions(best_x)
    cons = constraint_functions(best_x)
    print("best_x", best_x)
    print("fbestx", obj)
    print("cbestx", cons)
    #print("best_f", best_f)
    return best_x, obj, cons


def convert(s):
    if s[-1] == 'm' or s[-1] == 'M':
        v = float(s[:-1]) * 1e-3
    elif s[-1] == 'u' or s[-1] == 'U':
        v = float(s[:-1]) * 1e-6
    elif s[-1] == 'n' or s[-1] == 'N':
        v = float(s[:-1]) * 1e-9
    elif s[-1] == 'p' or s[-1] == 'P':
        v = float(s[:-1]) * 1e-12
    elif s[-1] == 'k' or s[-1] == 'K':
        v = float(s[:-1]) * 1e3
    elif s[-1] == 'g' or s[-1] == 'G':
        v = float(s[:-1]) * 1e9
    elif s[-1] == 'x' or s[-1] == 'X':
        v = float(s[:-1]) * 1e6
    elif s[-1] == 'f' or s[-1] == 'F':
        v = float(s[:-1]) * 1e-15
    else:
        v = float(s)
    return v
