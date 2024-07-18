import os
import random
import string
from typing import Optional, Callable, Type, Any

from chall import Cell


def rand_int() -> int:
    return random.randrange(1, 100)


def rand_str() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def cell_xy_to_str(x: int, y: int) -> str:
    if (i := x // len(ALPHABET)) > 0:
        xx = f'{ALPHABET[i - 1]}{ALPHABET[x % len(ALPHABET)]}'
    else:
        xx = ALPHABET[x % len(ALPHABET)]

    return f'{xx}{y + 1}'


FORMULA_TEMPLATES = [
    # ADD
    ('=ADD(%s, %s)', 2, lambda x, y: x + y, int),
    ('=ADD(%s, %s, %s)', 3, lambda x, y, z: x + y + z, int),
    ('=ADD(%s, %s, %s, %s)', 4, lambda x, y, z, k: x + y + z + k, int),

    # SUB
    ('=SUB(%s, %s)', 2, lambda x, y: x - y, int),

    # MUL
    ('=MUL(%s, %s)', 2, lambda x, y: x * y, int),
    ('=MUL(%s, %s, %s)', 3, lambda x, y, z: x * y * z, int),
    ('=MUL(%s, %s, %s, %s)', 4, lambda x, y, z, k: x * y * z * k, int),

    # DIV
    ('=DIV(%s, %s)', 2, lambda x, y: x // y, int),

    # AND
    ('=AND(%s, %s)', 2, lambda x, y: x & y, int),
    ('=AND(%s, %s, %s)', 3, lambda x, y, z: x & y & z, int),
    ('=AND(%s, %s, %s, %s)', 4, lambda x, y, z, k: x & y & z & k, int),

    # OR
    ('=OR(%s, %s)', 2, lambda x, y: x | y, int),
    ('=OR(%s, %s, %s)', 3, lambda x, y, z: x | y | z, int),
    ('=OR(%s, %s, %s, %s)', 4, lambda x, y, z, k: x | y | z | k, int),

    # XOR
    ('=XOR(%s, %s)', 2, lambda x, y: x ^ y, int),
    ('=XOR(%s, %s, %s)', 3, lambda x, y, z: x ^ y ^ z, int),
    ('=XOR(%s, %s, %s, %s)', 4, lambda x, y, z, k: x ^ y ^ z ^ k, int),

    # ABS
    ('=ABS(%s)', 1, lambda x: abs(x), int),

    # MIN
    ('=MIN(%s, %s)', 2, lambda x, y: min(x, y), int),
    ('=MIN(%s, %s, %s)', 3, lambda x, y, z: min(x, y, z), int),
    ('=MIN(%s, %s, %s, %s)', 4, lambda x, y, z, k: min(x, y, z, k), int),

    # MAX
    ('=MAX(%s, %s)', 2, lambda x, y: max(x, y), int),
    ('=MAX(%s, %s, %s)', 3, lambda x, y, z: max(x, y, z), int),
    ('=MAX(%s, %s, %s, %s)', 4, lambda x, y, z, k: max(x, y, z, k), int),

    # CONCAT
    ('=CONCAT("%s", "%s")', 2, lambda x, y: x + y, str),
    ('=CONCAT("%s", "%s", "%s")', 3, lambda x, y, z: x + y + z, str),
    ('=CONCAT("%s", "%s", "%s", "%s")', 4, lambda x, y, z, k: x + y + z + k, str),

    # JOIN
    ('=JOIN("%s", "%s")', 2, lambda x, y: ','.join([x, y]), str),
    ('=JOIN("%s", "%s", "%s")', 3, lambda x, y, z: ','.join([x, y, z]), str),
    ('=JOIN("%s", "%s", "%s", "%s")', 4, lambda x, y, z, k: ','.join([x, y, z, k]), str),

    # TRIM
    ('=TRIM("%s")', 1, lambda x: x.strip(), str),

    # LOWER
    ('=LOWER("%s")', 1, lambda x: x.lower(), str),

    # UPPER
    ('=UPPER("%s")', 1, lambda x: x.upper(), str),

    # LEN
    ('=LEN("%s")', 1, lambda x: str(len(x)), str)
]


class FormulaGenerator:
    cells: list[tuple[Cell, Optional[str]]]
    _special_cells: list[tuple[int, int, Callable[[int, int], None]]]
    _to_finalize: list[tuple[int, int, Callable[[], str]]]

    def __init__(self):
        self.cells = []
        self._special_cells = []
        self._to_finalize = []

    def _get_cell(self, x: int, y: int) -> Optional[tuple[Cell, Optional[str]]]:
        try:
            return next(filter(lambda c: c[0]['x'] == x and c[0]['y'] == y, self.cells))
        except StopIteration:
            return None

    def _is_special_cell(self, x: int, y: int) -> bool:
        try:
            next(filter(lambda c: c[0] == x and c[1] == y, self._special_cells))
            return True
        except StopIteration:
            return False

    def _get_random_empty_cell(self) -> Optional[tuple[int, int]]:
        while True:
            x, y = random.randrange(0, 64), random.randrange(0, 64)
            cell = self._get_cell(x, y)
            if cell is not None:
                continue

            if self._is_special_cell(x, y):
                continue

            return x, y

    def _get_all_formula_cells(self) -> list[tuple[int, int]]:
        cells = set()
        for x, y, _ in self._special_cells:
            cells.add((x, y))
        for cell, _ in self.cells:
            if cell['content'].startswith(b'='.hex()):
                cells.add((cell['x'], cell['y']))
        return list(cells)

    def _get_random_range(self, avoid: list[tuple[int, int]]) -> tuple[int, int, int, int]:
        while True:
            start_x, start_y = random.randrange(0, 63), random.randrange(0, 63)
            end_x, end_y = random.randrange(start_x, 64), random.randrange(start_y, 64)

            if all([not (start_x <= ax <= end_x and start_y <= ay <= end_y) for ax, ay in avoid]):
                return start_x, start_y, end_x, end_y

    def _count_non_empty_cells_in_range(self, rng: tuple[int, int, int, int]) -> int:
        count = 0
        for x in range(rng[0], rng[2] + 1):
            for y in range(rng[1], rng[3] + 1):
                cell = self._get_cell(x, y)
                if cell is not None or self._is_special_cell(x, y):
                    count += 1
        return count

    def generate_text(self):
        while (content := os.urandom(16)).startswith(b'='):
            pass

        x, y = self._get_random_empty_cell()
        self.cells.append(({'x': x, 'y': y, 'content': content.hex()}, None))

    def _place_rand_for_type(self, typ: Type) -> tuple[Any, str]:
        if typ == str:
            val = rand_str()
            return val, val
        elif typ == int:
            val = rand_int()
            if random.choice([True, False]):
                return val, str(val)

            x, y = self._get_random_empty_cell()
            self.cells.append(({'x': x, 'y': y, 'content': str(val).encode().hex()}, None))

            return val, cell_xy_to_str(x, y)
        else:
            assert False, f'Unknown type: {typ}'

    def generate_formula(self):
        f = random.choice(FORMULA_TEMPLATES)
        formula_template, formula_params_count, formula_calc, formula_type = f
        formula_params = [self._place_rand_for_type(formula_type) for _ in range(formula_params_count)]
        formula_result = formula_calc(*[p[0] for p in formula_params])
        content = formula_template % tuple(p[1] for p in formula_params)

        x, y = self._get_random_empty_cell()
        self.cells.append(({'x': x, 'y': y, 'content': content.encode().hex()}, str(formula_result)))

    def _special_formula_gen_counta(self, x: int, y: int):
        start_x, start_y, end_x, end_y = self._get_random_range(self._get_all_formula_cells())
        content = f'=COUNTA({cell_xy_to_str(start_x, start_y)}:{cell_xy_to_str(end_x, end_y)})'

        self.cells.append(({'x': x, 'y': y, 'content': content.encode().hex()}, None))
        self._to_finalize.append(
            (x, y, lambda: str(self._count_non_empty_cells_in_range((start_x, start_y, end_x, end_y))))
        )

    def _special_formula_gen_avg(self, x: int, y: int):
        while True:
            start_x, start_y, end_x, end_y = self._get_random_range(self._get_all_formula_cells())
            if self._count_non_empty_cells_in_range((start_x, start_y, end_x, end_y)) == 0:
                break

        cell_sum, cell_count = 0, 0
        for xx in range(start_x, end_x + 1):
            for yy in range(start_y, end_y + 1):
                val = random.randrange(1, 1000)

                self.cells.append(({'x': xx, 'y': yy, 'content': str(val).encode().hex()}, None))
                cell_sum += val
                cell_count += 1

        content = f'=AVG({cell_xy_to_str(start_x, start_y)}:{cell_xy_to_str(end_x, end_y)})'

        self.cells.append(({'x': x, 'y': y, 'content': content.encode().hex()}, None))
        self._to_finalize.append(
            (x, y, lambda: str(cell_sum // cell_count))
        )

    def generate_special_formula(self):
        x, y = self._get_random_empty_cell()
        f = random.choice([
            self._special_formula_gen_counta,
            self._special_formula_gen_avg
        ])

        self._special_cells.append((x, y, f))

    def finalize(self):
        for x, y, f in self._special_cells:
            f(x, y)

        for x, y, f in self._to_finalize:
            for i, (c, _) in enumerate(self.cells):
                if c['x'] == x and c['y'] == y:
                    self.cells[i] = (c, f())
                    break
