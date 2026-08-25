from cooksLibrary.ingest.books import prettify_filename, make_slug

def test_prettify_filename_simple():
    assert prettify_filename("williamssonomafavoritecookies") == "Williams Sonoma Favorite Cookies"

def test_prettify_filename_with_underscores():
    assert prettify_filename("fresh_and_green_table") == "Fresh And Green Table"

def test_prettify_filename_underscore_and_concat():
    assert prettify_filename("williamssonomatestkitchen_thedoughnutcookbook") == \
        "Williams Sonoma Test Kitchen The Doughnut Cookbook"

def test_make_slug_from_title():
    assert make_slug("The Eat Like a Man Guide to Feeding a Crowd") == \
        "the-eat-like-a-man-guide-to-feeding-a-crowd"

def test_make_slug_collapses_dashes():
    assert make_slug("A  B  C") == "a-b-c"