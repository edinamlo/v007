def test_normalize_text():
    assert normalize_text('Ｔｅｓｔ') == 'Test'
    assert normalize_text('über') == 'über'
    assert normalize_text('Test　Test') == 'Test Test'

def test_clean_title_websites():
    assert clean_title('www.site.com - Title') == 'Title'
    assert clean_title('[Group] Title') == 'Title'
    
def test_clean_title_languages():
    assert clean_title('標題 / Title') == 'Title'
    assert clean_title('Título / Title') == 'Title'