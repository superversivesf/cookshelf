from cooksLibrary.ingest.section import section_recipe

SAMPLE_TEXT = """Salted Caramel Cheesecake with Pretzel Crumb Crust
Use your favorite salted caramel sauce—homemade or store-bought—for this
easy cheesecake that pairs a salty-malty pretzel crumb crust.

FOR THE CRUST
1 cup fine pretzel crumbs
2 tablespoons firmly packed light brown sugar
4 tablespoons unsalted butter, melted

FOR THE FILLING
2 packages (8 oz each) cream cheese, at room temperature
1/2 cup granulated sugar
1/4 cup sour cream

To make the crust, lightly spray a 7-inch springform pan.
To make the filling, in a stand mixer fitted with the paddle attachment.

Serves 8
"""

def test_section_title_from_arg():
    r = section_recipe(SAMPLE_TEXT, "Salted Caramel Cheesecake")
    assert r["description"].startswith("Use your favorite")

def test_section_ingredients_grouped():
    r = section_recipe(SAMPLE_TEXT, "Test Title")
    sections = {i["section"] for i in r["ingredients"]}
    assert "FOR THE CRUST" in sections
    assert "FOR THE FILLING" in sections

def test_section_servings():
    r = section_recipe(SAMPLE_TEXT, "Test Title")
    assert r["servings"] == "8"
    assert r["servings_min"] == 8
    assert r["servings_max"] == 8