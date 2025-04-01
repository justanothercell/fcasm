import sys
import math
import random
import inspect
from time import time
from time import sleep
from term import Term

BUILTINS = {
    'sin': math.sin, 'sinh': math.sinh, 'asin': math.asin, 'asinh': math.asinh,
    'cos': math.cos, 'cosh': math.cosh, 'acos': math.acos, 'acosh': math.acosh,
    'tan': math.tan, 'tanh': math.tanh, 'atan': math.atan, 'atan2': math.atan2, 'atanh': math.atanh,
    'pow': math.pow, 'sqrt': math.sqrt, 'isqrt': math.isqrt, 'cbrt': math.cbrt,
    'exp': math.exp, 'exp2': math.exp2, 'expm1': math.expm1, 'ldexp': math.ldexp, 'frexp': math.frexp,
    'log': math.log, 'log1p': math.log1p, 'log10': math.log10, 'log2': math.log2,
    'erf': math.erf, 'erfc': math.erfc, 'gamma': math.gamma, 'lgamma': math.lgamma,
    'dist2d': lambda x1, y1, x2, y2: dist((x1, y1), (x2, y2)),
    'dist3d': lambda x1, y1, z1, x2, y2, z2: dist((x1, y1, z1), (x2, y2, z2)),
    'floor': math.floor, 'ceil': math.ceil, 'abs': math.fabs, 'copysign': math.copysign, 'round': round,
    'degrees': math.degrees, 'radians': math.radians,
    'hypot': math.hypot,
    'gcd': math.gcd, 'lcm': math.lcm,
    'isclose': math.isclose, 'isfinite': math.isfinite, 'isinf': math.isinf, 'isnan': math.isnan,
    'remainder': math.remainder,
    'nextafter': math.nextafter, 'ulp': math.ulp,
    'perm': math.perm, 'comb': math.comb,
    'prod': lambda *x: math.prod(x), 'sum': lambda *x: math.fsum(x),
    'add': lambda a, b: a + b, 'sub': lambda a, b: a - b, 'mul': lambda a, b: a * b, 'div': lambda a, b: a / b, 'idiv': lambda a, b: a // b, 'mod': lambda a, b: a % b, 'fmod': math.fmod,
    'bitand': lambda a, b: a & b, 'bitor': lambda a, b: a | b, 'bitxor': lambda a, b: a ^ b,
    'and': lambda a, b: a and b, 'or': lambda a, b: a or b, 'xor': lambda a, b: (a and not b) or (not a and b),
    'eq': lambda a, b: a == b, 'ne': lambda a, b: a != b, 'not': lambda a: not a,
    'gt': lambda a, b: a > b, 'lt': lambda a, b: a < b, 'ge': lambda a, b: a >= b, 'le': lambda a, b: a <= b,
    'shl': lambda a, b: a << b, 'shr': lambda a, b: a >> b,
    'inv': lambda a: 1 / a, 'neg': lambda a: -a, 'fact': math.factorial, 'fma': math.fma,
    'ipart': lambda x: math.trunc(x), 'fpart': lambda x: math.modf(x)[0],
    'pi': lambda: math.pi, 'e': lambda: math.e, 'tau': lambda: math.tau, 'inf': lambda: math.inf, 'nan': lambda: math.nan,
    'int': lambda x: int(x), 'float': lambda x: float(x),

    'random': random.random, 'randint': lambda a, b: random.randrange(a, b), 'setseed': lambda seed: random.seed(seed),

    'id': lambda x: x,

    'ret': lambda r: print('dummy implementation'),
    'exit': lambda color: print('dummy implementation'),
    'if': lambda predicate, then_branch, else_branch: print('dummy implementation'),
    'jmp': lambda label: print('dummy implementation'),
    'pixels': lambda x, y: print('dummy implementation'),
    'x': lambda: print('dummy implementation'),
    'y': lambda: print('dummy implementation'),
    'w': lambda: print('dummy implementation'),
    'h': lambda: print('dummy implementation'),
    'frame': lambda: print('dummy implementation'),
    'input': lambda: print('dummy implementation'),
}

width, height = 24, 24
fps = 10
dry = False
benchmark = False
benchcount = 1
benchwarm = 0

sargs = iter(sys.argv)

try:
    thisfile = next(sargs)
    code_file_path = next(sargs)
    while True:
        try:
            arg = next(sargs)
        except StopIteration:
            break
        if arg == '-s' or arg == '--size':
            width = int(next(sargs))
            height = int(next(sargs))
        elif arg == '--fps':
            fps = float(next(sargs))
        elif arg == '--dry':
            dry = True
        elif arg == '--bench':
            benchmark = True
        elif arg == '--bcount':
            benchcount = int(next(sargs))
        elif arg == '--bwarm':
            benchwarm = int(next(sargs))
        else:
            raise Exception(f'Unknown argument `{arg}`')
except Exception as e:
    print(e)
    print(f'{thisfile} <code.fcasm> [args...]')
    print(f'\t-s/--size <w> <h>')
    print(f'\t--fps <fps>')
    print(f'\t--bench      | benchmark evaluation')
    print(f'\t--bcount <n> | how many frames to benchmark')
    print(f'\t--bwarm  <n> | how many frames to warm up before benchmarking')
    exit()


with open(code_file_path) as code_file:
   raw = code_file.readlines()

def error(line, error, keepalive=False):
    if line >= 0:
        print(f'Error in line {line+1}:')
        print(f'| {raw[line].rstrip("\n")}')
        print(f'{error}')
    else:
        print(f'Error: {error}')
    if keepalive:
        input('press [enter] to exit')
    exit()

code = []
labels = {}
forward_labels = {}
vars = []

class Var:
    def __init__(self, index):
        self.index = index
    def __repr__(self):
        return f'${vars[self.index]}'

for i, line in enumerate(raw):
    line = line.split('#')[0].strip()
    if len(line) == 0:
        continue
    if line.endswith(':'):
        label = line[:-1]
        if not label.isalnum():
            error(i, f'Label `@{label}` is not alphanumeric')
        if label in labels:
            error(i, f'Label `@{label}` already declared in line {labels[label][0]}')
        labels[label] = (i, len(code))
        if label in forward_labels:
            for line, index, argdex in forward_labels[label]:
                if argdex >= 0: # replace argument
                    cline, cret, (cfuncname, cfunc), cargs = code[index]
                    cargs = list(cargs)
                    cargs[argdex] = len(code)
                    code[index] = cline, cret, (cfuncname, cfunc), tuple(cargs)
                else: # argdex = -1: replace function
                    cline, cret, (cfuncname, cfunc), cargs = code[index]
                    cfunc = len(code)
                    code[index] = cline, cret, (cfuncname, cfunc), cargs
            del forward_labels[label]
        continue
    parts = line.split('=')
    if len(parts) == 1:
        ret = None
        rest = parts[0].strip().split()
    elif len(parts) == 2:
        ret, rest = parts
        ret = ret.strip()
        rest = rest.strip().split()
    else:
        error(i, 'Invalid syntax')
    if len(rest) == 0:
        error(i, 'Invalid syntax')
    funcname = rest[0]
    if len(rest) > 1:
        args = rest[1:]
    else:
        args = []
    if funcname.startswith('@'):
        funcname = funcname[1:]
        if not funcname.isalnum():
            error(i, f'Label `@{funcname}` is not alphanumeric')
        if funcname in labels:
            func = labels[funcname][1]
        else:
            if funcname not in forward_labels:
                forward_labels[funcname] = []
            forward_labels[funcname].append((i, len(code), -1))
            func = funcname
    else:
        if funcname not in BUILTINS:
            error(i, f'No such function `{funcname}`')
        func = BUILTINS[funcname]
        sig = inspect.signature(func)
        params = list(sig.parameters.items())
        if len(params) > 0:
            if params[-1][1].kind == inspect.Parameter.VAR_POSITIONAL:
                if len(args) < len(params):
                    error(i, f'Function `{funcname}` expects at least {len(params)} args, got {len(args)}')
            else:
                if len(args) != len(params):
                    error(i, f'Function `{funcname}` expects {len(params)} args, got {len(args)}')
        else:
            if len(args) > 0:
                error(i, f'Function `{funcname}` expects no args, got {len(args)}')
    if ret is not None:
        if not ret.startswith('$'):
            error(i, f'Expected $var, got `{ret}`')
        ret = ret[1:]
        if not ret.isalnum():
            error(i, f'Variable `${ret}` is not alphanumeric')
        if not ret in vars:
            vars.append(ret)
        ret = Var(vars.index(ret))
    for j, arg in enumerate(args):
        if arg.startswith('$'):
            arg = arg[1:]
            if not arg.isalnum():
                error(i, f'Variable `${arg}` is not alphanumeric')
            if not arg in vars:
                vars.append(arg)
            args[j] = Var(vars.index(arg))
        elif arg.startswith('@'):
            arg = arg[1:]
            args[j] = arg
            if not arg.isalnum():
                error(i, f'Label `@{arg}` is not alphanumeric')
            if arg in labels:
                args[j] = labels[arg][1]
            else:
                if arg not in forward_labels:
                    forward_labels[arg] = []
                forward_labels[arg].append((i, len(code), j))
        elif arg.replace('_', '').isnumeric():
            try:
                args[j] = int(arg.replace('_', ''), 10)
            except:
                error(i, f'Invalid base 10 int literal: `{arg}`')
        elif arg.replace('.', '').replace('_', '').isnumeric():
            try:
                args[j] = float(arg.replace('_', ''))
            except:
                error(i, f'Invalid float literal: `{arg}`')
        elif arg.startswith('0x'):
            try:
                args[j] = int(arg[2:].replace('_', ''), 16)
            except:
                error(i, f'Invalid base 16 int literal: `{arg}`')
        elif arg.startswith('0b'):
            try:
                args[j] = int(arg[2:].replace('_', ''), 2)
            except:
                error(i, f'Invalid base 2 int literal: `{arg}`')
        else:
            error(i, f'Expected $var, @label or number, got `{arg}`')
    code.append((i, ret, (funcname, func), tuple(args)))

if len(forward_labels) > 0:
    name, [(line, index, argdex), *rest] = next(iter(forward_labels.items()))
    error(line, f'Label @{name} used here but never declared')

pixels = [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]
new_pixels = [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]

framecount = 0

if dry:
    print('-------------')
    for line in code:
        print(line)
    print('-------------')
    print(f'{len(vars)} variables')
    print(f'{len(labels)} labels')
    exit()

input_char = 0

def eval_code(x, y):
    stack = [(-1, None, [None] * len(vars))]
    ip = 0
    try:
        while True:
            i, ret, (fname, func), rawargs = code[ip]
            args = []
            for x in rawargs:
                if type(x) == Var:
                    x = stack[-1][2][x.index]
                    if x is None:
                        error(i, f'Variable `{vars[x]}` no associated with a value', keepalive=True)
                args.append(x)
            ip += 1
            if type(func) == int: # dynamic func call
                stack.append((ip, ret, [None] * len(vars)))
                for j, v in enumerate(args):
                    stack[-1][2][vars.index(str(j))] = v
                ip = func
            elif fname == 'ret':
                if len(stack) <= 1:
                    error(i, 'Cannot return outside function', keepalive=True)
                r = args[0]
                ip, ret, old_vars = stack.pop()
                stack[-1][2][ret.index] = r
            elif fname == 'exit':
                return args[0]
            elif fname == 'jmp':
                ip = args[0]
            elif fname == 'if':
                cond = args[0]
                then = args[1]
                otherwise = args[2]
                ip = then if cond else otherwise
            elif fname == 'pixels':
                x = args[0]
                y = args[1]
                if x < 0 or y < 0 or x >= width or y >= height:
                    error(i, f'pixels coordinate {(x, y)} out of bounds for size {(width, height)}', keepalive=True)
                a, r, g, b = pixels[y][x]
                stack[-1][2][ret.index] = (a << 24) | (r << 16) | (g << 8) | (b << 0)
            elif fname == 'x':
                stack[-1][2][ret.index] = x
            elif fname == 'y':
                stack[-1][2][ret.index] = y
            elif fname == 'w':
                stack[-1][2][ret.index] = width
            elif fname == 'h':
                stack[-1][2][ret.index] = height
            elif fname == 'frame':
                stack[-1][2][ret.index] = framecount
            elif fname == 'input':
                stack[-1][2][ret.index] = input_char
            else:
                r = func(*args)
                if r == None:
                    r = 0
                stack[-1][2][ret.index] = r
    except Exception as e:
        error(i, f'{e}', keepalive=True)

def calc_pixel(x, y):
    ret = int(eval_code(x, y))
    a, r, g, b = (ret >> 24) & 0xFF, (ret >> 16) & 0xFF, (ret >> 8) & 0xFF, (ret >> 0) & 0xFF
    new_pixels[y][x] = a, r, g, b

if benchmark:
    if benchwarm > 0:
        print('Warming up...')
        for _ in range(benchwarm):
            for y in range(height):
                for x in range(width):
                    calc_pixel(x, y)
        pixels, new_pixels = new_pixels, pixels
        framecount += 1
        print(f'Warmed up {benchwarm} frames')
    print(f'Timing...')
    start = time()
    for _ in range(benchcount):
        for y in range(height):
            for x in range(width):
                calc_pixel(x, y)
    pixels, new_pixels = new_pixels, pixels
    framecount += 1
    end = time()
    print(f'Timed {benchcount} frame(s)')
    if benchcount == 1:
        print(f'Evaluating frame took {end-start}s')
    else:
        print(f'Evaluating frames took {end-start}s')
        print(f'\t{(end-start) / benchcount}s per frame')
        print(f'\t{1/((end-start) / benchcount)} fps')
    exit()

first = True
with Term() as term:
    while True:
        if term.kbhit():
            input_char = ord(term.getch())
            if input_char == 3: # Ctrl+C
                break
        else:
            input_char = 0
        if not first:
            print(f'\x1b[{height//2}A', end='')
        first = False

        for y in range(height):
            for x in range(width):
                calc_pixel(x, y)

        pixels, new_pixels = new_pixels, pixels

        for y in range(0, height, 2):
            for x in range(width):
                ua, ur, ug, ub = pixels[y][x]
                la, lr, lg, lb = pixels[y+1][x]
                print(f'\x1b[48;2;{ur};{ug};{ub}m\x1b[38;2;{lr};{lg};{lb}m▄', end='')
            print('\x1b[0m')
        framecount += 1
        sleep(1/fps)
