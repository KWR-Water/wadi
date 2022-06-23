from pint import UnitRegistry

ureg = UnitRegistry()

Q_ = ureg.Quantity

C = 2.54 * ureg('nmol/l')
print(C)