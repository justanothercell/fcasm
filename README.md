Small pixel-based gpu-like python-simulated assembly rendered with ansi escapes in the terminal


## Example
This is run for every pixel every frame, the resulting pixel color is set with `exit <color>`.<br>
Run with `py fcasm.py examples/gradient.fcasm`
```php
$x = x
$y = y
$w = w
$h = h
$sw = div 255 $w
$sh = div 255 $h
$d = add $w $h
$sd = div 255 $d

# r = int(x * x_scale) << 16
$r = mul $x $sw
$r = int $r
$r = shl $r 16

# g = int(y * y_scale) << 8
$g = mul $y $sh
$g = int $g
$g = shl $g 8

# b = 255-int((x+y) * diag_scale)
$b = add $x $y
$b = mul $b $sd
$b = int $b
$b = sub 255 $b

$c = sum $r $g $b

exit $c
```
## Usage
Each `*.fcasm` script is a shader-like assembly script which is run for each pixel every frame, whose color is set by the return value on exit.

You can query any pixel state with `$color = pixels <x> <y>`.
## Syntax
### Variables
Variables can be used with `$var` and they are all local. Calling a function saves all variables and restores them upon return 
### Inputs and constants
Constants are just argumentless functions and need to be converted to variables
```php
$x = x # the x coordinate of this pixel
$y = y # the x coordinate of this pixel
$frame = frame # frame number
$input = input # the current key pressed (as charcode), 0 if none pressed
$pi = pi # 3.14159...
```
### Functions
Call functions with `$ret = func $arg0 $arg1 $arg2 ...` or just `$func $arg0 ...`

You can define custom functions by callign a label: `@label`.<br>
Arguments will be stored in `$0 $1 $2 ...`. The number of arguments can be accessed via `argc`<br>
Return from a fucntion with `ret <value>`
### Labels
A label can be declared with `label:` and can be used with
- `jmp @label` - unconditional jump
- `if $cond @label @otherwise` - conditional jump
- `@label` call the function at `label`. Arguments will be stored in `$0 $1 $2 ...`. The number of arguments can be accessed via `argc`
### Literals
- `12345`
- `0xF00F`
- `0b01`
- `2.7`
