Small pixel-based gpu-like python-simulated assembly rendered with ansi escapes in the terminal


## Example
This is run for every pixel every frame, the resulting pixel color is set with `exit <color>`
```php
$x = x
$y = y
$w = w
$h = h
$sw = div 255 $w
$sh = div 255 $h
$d = add $w $h
$sd = div 255 $d

$r = mul $x $sw
$r = int $r
$r = shl $r 16

$g = mul $y $sh
$g = int $g
$g = shl $g 8

$b = add $x $y
$b = mul $b $sd
$b = int $b
$b = sub 255 $b

$c = sum $r $g $b

exit $c
```
