from cooksLibrary.ingest.ingredients import parse_line

def test_simple_quantity_unit_name():
    r = parse_line("2 cups all-purpose flour")
    assert r["quantity"] == "2"
    assert r["unit"] == "cups"
    assert r["ingredient_name"] == "all-purpose flour"
    assert r["note"] == ""

def test_fraction_quantity():
    r = parse_line("1/2 cup granulated sugar")
    assert r["quantity"] == "1/2"
    assert r["unit"] == "cup"
    assert r["ingredient_name"] == "granulated sugar"

def test_mixed_number_quantity():
    r = parse_line("1 ¼ cups/300 ml buttermilk")
    assert r["quantity"] == "1 ¼"
    assert r["unit"] == "cups"
    assert r["ingredient_name"] == "buttermilk"

def test_with_note():
    r = parse_line("4 garlic cloves, minced")
    assert r["quantity"] == "4"
    assert r["unit"] == ""
    assert r["ingredient_name"] == "garlic cloves"
    assert r["note"] == "minced"

def test_dual_unit_stripped():
    r = parse_line("½ cup/60 g all-purpose flour")
    assert r["quantity"] == "½"
    assert r["unit"] == "cup"
    assert r["ingredient_name"] == "all-purpose flour"

def test_no_quantity():
    r = parse_line("Salted caramel sauce, for drizzling")
    assert r is None

def test_empty_line():
    assert parse_line("") is None

def test_section_header_not_ingredient():
    assert parse_line("FOR THE CRUST") is None

def test_package_quantity():
    r = parse_line("2 packages (8 oz each) cream cheese, at room temperature")
    assert r["quantity"] == "2"
    assert r["unit"] == "packages"
    assert r["ingredient_name"] == "(8 oz each) cream cheese"
    assert r["note"] == "at room temperature"

def test_ounces():
    r = parse_line("6 oz/170 g thick slab bacon, finely diced")
    assert r["quantity"] == "6"
    assert r["unit"] == "oz"
    assert r["ingredient_name"] == "thick slab bacon"
    assert r["note"] == "finely diced"

def test_tsp():
    r = parse_line("3 tsp coarse salt")
    assert r["quantity"] == "3"
    assert r["unit"] == "tsp"
    assert r["ingredient_name"] == "coarse salt"